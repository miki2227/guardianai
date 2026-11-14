"""Linux x86-64 virtual-file adapter; protected snapshots have no backing agent path."""
import array
import ctypes
import errno
import fcntl
import json
import os
import select
import socket
import subprocess


class Data(ctypes.Structure):
    _fields_ = [("nr", ctypes.c_int), ("arch", ctypes.c_uint32),
                ("instruction_pointer", ctypes.c_uint64), ("args", ctypes.c_uint64 * 6)]


class Notification(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint64), ("pid", ctypes.c_uint32), ("flags", ctypes.c_uint32), ("data", Data)]


class Response(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint64), ("val", ctypes.c_int64), ("error", ctypes.c_int32), ("flags", ctypes.c_uint32)]


class Addfd(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint64), ("flags", ctypes.c_uint32), ("srcfd", ctypes.c_uint32),
                ("newfd", ctypes.c_uint32), ("newfd_flags", ctypes.c_uint32)]


class SeccompGate:
    """Emulate /protected/NAME opens using the broker's launch-bound task epoch.

    Ordinary runtime opens are continued without treating their pathname as an
    authorization decision. Protected snapshots are never mounted, so changing
    a continued pathname cannot access a broker resource through the filesystem.
    """

    def __init__(self, broker, principal, launcher):
        self.broker, self.principal = broker, principal
        self.epoch = broker.epoch
        self.abi = json.loads(subprocess.check_output([str(launcher), "--abi"]))
        if (self.abi["notif_size"] != ctypes.sizeof(Notification)
                or self.abi["response_size"] != ctypes.sizeof(Response)):
            raise RuntimeError("Unsupported seccomp notification ABI")
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.libc.ioctl.restype = ctypes.c_int
        self.audit = []

    def ioctl(self, listener, operation, value):
        result = self.libc.ioctl(ctypes.c_int(listener), ctypes.c_ulong(self.abi[operation]), ctypes.byref(value))
        if result < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return result

    def memory(self, notification, address, length):
        # Pin the proc directory before opening mem. Never authorize by a later
        # lookup of an untrusted/reused numeric PID, nor execute a copied path.
        directory = os.open(f"/proc/{notification.pid}", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            memory = os.open("mem", os.O_RDONLY | os.O_CLOEXEC, dir_fd=directory)
            try:
                return os.pread(memory, length, address)
            finally:
                os.close(memory)
        finally:
            os.close(directory)

    def path(self, notification):
        address = notification.data.args[0 if notification.data.nr == 2 else 1]
        value = b""
        for offset in range(0, 4096, 256):
            chunk = self.memory(notification, address + offset, 256)
            if b"\0" in chunk:
                return value + chunk.split(b"\0", 1)[0]
            value += chunk
        raise ValueError("Unterminated pathname")

    def _reply(self, listener, notification, error=0, flags=0):
        self.ioctl(listener, "send", Response(notification.id, 0, -error, flags))

    def _snapshot_fd(self, content):
        descriptor = os.memfd_create("guardian-approved-snapshot", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        try:
            with os.fdopen(os.dup(descriptor), "wb") as stream:
                stream.write(content)
            fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS,
                        fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
            # Inject a read-only descriptor, not the original writable handle.
            return os.open(f"/proc/self/fd/{descriptor}", os.O_RDONLY | os.O_CLOEXEC)
        finally:
            os.close(descriptor)

    def serve(self, connection):
        listener = None
        try:
            with connection:
                connection.settimeout(5)
                packet, ancillary, flags, address = connection.recvmsg(4, socket.CMSG_SPACE(4), socket.MSG_CMSG_CLOEXEC)
                received = []
                for level, kind, value in ancillary:
                    if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                        descriptors = array.array("i")
                        descriptors.frombytes(value)
                        received.extend(descriptors)
                if packet != b"GNF1" or len(received) != 1 or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                    for descriptor in received:
                        os.close(descriptor)
                    raise RuntimeError("Invalid listener handoff")
                listener = received[0]
            poller = select.poll()
            poller.register(listener, select.POLLIN | select.POLLHUP | select.POLLERR)
            while not self.broker.stop_event.is_set():
                ready = poller.poll(50)
                if not ready:
                    continue
                if ready[0][1] & (select.POLLHUP | select.POLLERR):
                    return
                notification = Notification()
                try:
                    self.ioctl(listener, "recv", notification)
                    self.ioctl(listener, "valid", ctypes.c_uint64(notification.id))
                    path = self.path(notification)
                    self.ioctl(listener, "valid", ctypes.c_uint64(notification.id))
                    if not path.startswith(b"/protected/"):
                        self._reply(listener, notification, flags=1)  # CONTINUE: no broker authority used.
                        continue
                    if notification.data.nr == 437:
                        if notification.data.args[3] < 8:
                            raise ValueError("Incomplete open_how")
                        raw = self.memory(notification, notification.data.args[2], 8)
                        flags = int.from_bytes(raw, "little")
                    else:
                        flags = notification.data.args[1 if notification.data.nr == 2 else 2]
                    self.audit.append({"event": "protected_open", "pid": notification.pid,
                                       "syscall": notification.data.nr, "ip": notification.data.instruction_pointer,
                                       "path": path.decode("utf-8", errors="strict"), "epoch": self.epoch})
                    if flags & ~(os.O_CLOEXEC | os.O_LARGEFILE):
                        self._reply(listener, notification, errno.EPERM)
                        self.broker.stop_event.set()
                        return
                    def commit(content, epoch, digest):
                        descriptor = self._snapshot_fd(content)
                        try:
                            self.ioctl(listener, "addfd", Addfd(notification.id, 2, descriptor, 0, flags & os.O_CLOEXEC))
                            return True
                        finally:
                            os.close(descriptor)
                    request = {"operation": "read", "resource": path[len(b"/protected/"):].decode("utf-8", errors="strict"), "epoch": self.epoch}
                    origin = {"pid": notification.pid, "syscall": notification.data.nr,
                              "instruction_pointer": notification.data.instruction_pointer,
                              "notification_id": notification.id}
                    if not self.broker.authorize(self.principal, request, commit, origin=origin):
                        self._reply(listener, notification, errno.EPERM)
                        return
                except OSError as error:
                    if error.errno == errno.ENOENT:
                        continue  # Notification abandoned when its target exited.
                    raise
        except Exception as error:
            self.audit.append({"event": "gate_fault", "reason": type(error).__name__})
            self.broker.stop_event.set()
        finally:
            if listener is not None:
                os.close(listener)
