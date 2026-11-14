"""Independent kernel-containment probes. Run on the WSL host, never as a payload.

Payloads execute only through guardian.sandbox_argv. Canaries are synthetic.
"""
import json
import os
import socket
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/home/pratz/guardianai-pilot")
import guardian  # noqa: E402


ROOT = Path("/home/pratz/guardianai-kernel-probe")
SENTINEL = ROOT / "host-sentinel.txt"
SENTINEL_TEXT = "FAKE-CANARY-NOT-A-SECRET"
ABSTRACT = "\0guardianai-grok-probe"
results = []


def record(name, ok, detail, kind):
    results.append({"probe": name, "ok": ok, "kind": kind, "detail": detail})


def sandbox(workspace, code, env=None, pass_fds=()):
    merged = {"PATH": "/usr/bin:/bin"}
    if env:
        merged.update(env)
    argv = guardian.sandbox_argv(workspace, ["python3", "-c", code])
    return subprocess.run(
        argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env=merged, timeout=20, pass_fds=pass_fds,
    )


def payload_json(result):
    line = next((x for x in result.stdout.splitlines() if x.startswith("PROBE ")), "")
    if not line:
        return None
    return json.loads(line[6:])


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    ws_a = ROOT / "ws-a"
    ws_b = ROOT / "ws-b"
    for path in (ws_a, ws_b):
        path.mkdir(exist_ok=True)
    SENTINEL.write_text(SENTINEL_TEXT)
    host_pid = os.getpid()
    host_name = socket.gethostname()
    host_sock = ROOT / "host.sock"
    if host_sock.exists():
        host_sock.unlink()
    unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    unix.bind(str(host_sock))
    unix.listen(1)
    abstract = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        abstract.bind(ABSTRACT)
        abstract.listen(1)
        abstract_bound = True
    except OSError as error:
        abstract_bound = False
        abstract_error = str(error)

    # 1. Mount table and host-path absence.
    code = r"""
import json, os
from pathlib import Path
mounts = Path("/proc/self/mountinfo").read_text()
targets = [line.split()[4] for line in mounts.splitlines() if len(line.split()) > 4]
checked = ["/home", "/etc", "/mnt", "/opt", "/run", "/var", "/sys", "/workspace", "/tmp", "/usr", "/proc"]
print("PROBE " + json.dumps({
  "targets": targets,
  "exists": {p: Path(p).exists() for p in checked},
  "sentinel": Path(%r).exists(),
}))
""" % str(SENTINEL)
    result = sandbox(ws_a, code)
    data = payload_json(result)
    hostish = {"/home", "/etc", "/mnt", "/opt", "/run", "/var", "/sys"}
    visible = set(data["targets"]) if data else set()
    record(
        "mount-visibility",
        bool(data) and result.returncode == 0 and not (visible & hostish)
        and data["exists"].get("/workspace") and not data["sentinel"]
        and not any(data["exists"].get(p) for p in ("/home", "/etc", "/mnt", "/sys")),
        {"returncode": result.returncode, "data": data, "stderr": result.stderr[-500:]},
        "containment",
    )

    # 2. PID namespace and /proc root/fd walk.
    code = r"""
import json, os
from pathlib import Path
procs = [name for name in os.listdir("/proc") if name.isdigit()]
host_pid = %d
fd = os.open("/workspace", os.O_RDONLY | os.O_DIRECTORY)
walk = f"/proc/self/fd/{fd}/../../../../../../home/pratz/guardianai-kernel-probe/host-sentinel.txt"
root_walk = "/proc/self/root/home/pratz/guardianai-kernel-probe/host-sentinel.txt"
proc1 = "/proc/1/root/home/pratz/guardianai-kernel-probe/host-sentinel.txt"
def hit(path):
    try:
        return Path(path).read_text()[:80]
    except OSError as error:
        return type(error).__name__
print("PROBE " + json.dumps({
  "procs": procs,
  "host_pid_visible": str(host_pid) in procs,
  "fd_walk": hit(walk),
  "root_walk": hit(root_walk),
  "proc1": hit(proc1),
  "realpath_fd_parent": os.path.realpath(f"/proc/self/fd/{fd}/.."),
}))
""" % host_pid
    result = sandbox(ws_a, code)
    data = payload_json(result)
    record(
        "proc-fd-and-pid",
        bool(data) and result.returncode == 0 and not data["host_pid_visible"]
        and data["fd_walk"] != SENTINEL_TEXT and data["root_walk"] != SENTINEL_TEXT
        and data["proc1"] != SENTINEL_TEXT and len(data["procs"]) <= 8,
        {"returncode": result.returncode, "data": data, "stderr": result.stderr[-500:]},
        "containment",
    )

    # 3. Inherited descriptor and environment canary.
    canary_path = ROOT / "env-canary.txt"
    canary_path.write_text("FAKE-FD-CANARY")
    held = os.open(canary_path, os.O_RDONLY)
    code = r"""
import json, os
fds = os.listdir("/proc/self/fd")
texts = []
for name in fds:
    if name in {"0", "1", "2"}:
        continue
    try:
        texts.append(os.readlink(f"/proc/self/fd/{name}") + ":" + open(f"/proc/self/fd/{name}", "r").read(40))
    except OSError as error:
        texts.append(name + ":" + type(error).__name__)
print("PROBE " + json.dumps({"fds": fds, "extra": texts, "env": os.environ.get("FAKE_CANARY")}))
"""
    leaked = sandbox(ws_a, code, env={"FAKE_CANARY": "fake-canary"}, pass_fds=(held,))
    data = payload_json(leaked)
    os.close(held)
    record(
        "fd-and-env-inheritance",
        bool(data) and leaked.returncode == 0 and data["env"] is None
        and not any("FAKE-FD-CANARY" in item for item in data["extra"]),
        {"returncode": leaked.returncode, "data": data, "stderr": leaked.stderr[-500:]},
        "containment",
    )

    # 4. Pre-planted and in-sandbox symlinks.
    planted = ws_a / "planted-link"
    if planted.is_symlink() or planted.exists():
        planted.unlink()
    planted.symlink_to(SENTINEL)
    code = r"""
import json, os
from pathlib import Path
os.symlink(%r, "live-link")
def hit(path):
    try:
        return Path(path).read_text()[:80]
    except OSError as error:
        return type(error).__name__
print("PROBE " + json.dumps({"planted": hit("planted-link"), "live": hit("live-link")}))
""" % str(SENTINEL)
    result = sandbox(ws_a, code)
    data = payload_json(result)
    record(
        "symlink-host-targets",
        bool(data) and result.returncode == 0
        and data["planted"] != SENTINEL_TEXT and data["live"] != SENTINEL_TEXT,
        {"returncode": result.returncode, "data": data, "stderr": result.stderr[-500:]},
        "containment",
    )

    # 5. Grandchild process inheritance.
    code = r"""
import json, subprocess, os
script = "import os,pathlib; print(os.environ.get('FAKE_CANARY')); print(pathlib.Path(%r).exists())"
inner = subprocess.run(["python3", "-c", script], capture_output=True, text=True)
print("PROBE " + json.dumps({"code": inner.returncode, "out": inner.stdout.strip(), "err": inner.stderr[-200:]}))
""" % str(SENTINEL)
    result = sandbox(ws_a, code, env={"FAKE_CANARY": "fake-canary"})
    data = payload_json(result)
    record(
        "grandchild-inheritance",
        bool(data) and result.returncode == 0 and data["out"] == "None\nFalse",
        {"returncode": result.returncode, "data": data, "stderr": result.stderr[-500:]},
        "containment",
    )

    # 6. Network namespace: host unix, abstract unix, loopback, external.
    code = r"""
import json, socket
def attempt(kind, fn):
    try:
        fn()
        return "connected"
    except OSError as error:
        return type(error).__name__
def inet():
    s = socket.socket(); s.settimeout(1); s.connect(("192.0.2.1", 443))
def loop():
    s = socket.socket(); s.settimeout(1); s.connect(("127.0.0.1", 9))
def unix():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(1); s.connect(%r)
def abstract():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(1); s.connect(%r)
print("PROBE " + json.dumps({
  "inet": attempt("inet", inet),
  "loop": attempt("loop", loop),
  "unix": attempt("unix", unix),
  "abstract": attempt("abstract", abstract),
  "hostname": socket.gethostname(),
}))
""" % (str(host_sock), ABSTRACT)
    result = sandbox(ws_a, code)
    data = payload_json(result)
    record(
        "network-namespace",
        bool(data) and result.returncode == 0
        and data["inet"] != "connected" and data["unix"] != "connected"
        and (not abstract_bound or data["abstract"] != "connected"),
        {"returncode": result.returncode, "data": data, "host_hostname": host_name,
         "abstract_bound": abstract_bound,
         "abstract_error": None if abstract_bound else abstract_error,
         "stderr": result.stderr[-500:]},
        "containment",
    )

    # 7. Expected workspace write versus private /tmp.
    marker = "workspace-visible-marker"
    code = r"""
from pathlib import Path
Path("visible.txt").write_text(%r)
Path("/tmp/guardian-grok-marker").write_text("tmp-marker")
print("PROBE {}")
""" % marker
    result = sandbox(ws_a, code)
    host_visible = (ws_a / "visible.txt").read_text() if (ws_a / "visible.txt").exists() else None
    tmp_visible = Path("/tmp/guardian-grok-marker").exists()
    record(
        "workspace-versus-tmp",
        result.returncode == 0 and host_visible == marker and not tmp_visible,
        {"returncode": result.returncode, "host_workspace_file": host_visible,
         "host_tmp_marker": tmp_visible, "stderr": result.stderr[-500:]},
        "expected-workspace-effect",
    )

    # 8. Separate workspaces versus same workspace storage channel.
    (ws_a / "channel.txt").write_text("SHARED-FAKE-CANARY")
    code_other = r"""
import json
from pathlib import Path
print("PROBE " + json.dumps({
  "same_name": Path("channel.txt").exists(),
  "foreign": Path(%r).exists(),
}))
""" % str(ws_a / "channel.txt")
    other = sandbox(ws_b, code_other)
    other_data = payload_json(other)
    same = sandbox(ws_a, 'from pathlib import Path; print("PROBE " + Path("channel.txt").read_text())')
    record(
        "shared-storage",
        bool(other_data) and other.returncode == 0 and not other_data["same_name"]
        and not other_data["foreign"] and same.returncode == 0
        and same.stdout.strip() == "PROBE SHARED-FAKE-CANARY",
        {"other": other_data, "same_stdout": same.stdout.strip(),
         "other_code": other.returncode, "same_code": same.returncode},
        "documented-limitation",
    )

    # 9. Dropped capabilities, read-only runtime, no host devices.
    code = r"""
import json, subprocess
from pathlib import Path
status = Path("/proc/self/status").read_text().splitlines()
caps = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in status if line.startswith("Cap")}
mount = subprocess.run(["mount", "-t", "tmpfs", "tmpfs", "/workspace/submount"],
                       capture_output=True, text=True)
dev = {name: Path("/dev/" + name).exists() for name in ("mem", "kmsg", "sda", "null", "urandom")}
usr = "allowed"
try:
    open("/usr/guardian-grok", "w").close()
except OSError as error:
    usr = type(error).__name__
print("PROBE " + json.dumps({
  "caps": caps, "mount_code": mount.returncode, "mount_err": mount.stderr[-200:],
  "dev": dev, "usr_write": usr,
}))
"""
    result = sandbox(ws_a, code)
    data = payload_json(result)
    cap_clear = bool(data) and all(
        set(data["caps"].get(key, "").replace("0", "")) <= set("x")
        for key in ("CapEff", "CapPrm", "CapAmb")
    )
    # Cap fields are hex. Zero is "0000000000000000".
    def is_zero(value):
        return value is not None and set(value) <= {"0"}
    record(
        "caps-mount-devices",
        bool(data) and result.returncode == 0 and is_zero(data["caps"].get("CapEff"))
        and is_zero(data["caps"].get("CapPrm")) and data["mount_code"] != 0
        and data["usr_write"] != "allowed" and not data["dev"]["mem"] and not data["dev"]["sda"],
        {"returncode": result.returncode, "data": data, "stderr": result.stderr[-500:]},
        "containment",
    )

    # 10. execute() API strips supervisor env and still hides the sentinel.
    code = (
        "import json,os; from pathlib import Path; "
        "print(json.dumps({'key': 'TYPESAFE_API_KEY' in os.environ, "
        "'sentinel': Path(%r).exists(), 'home': os.environ.get('HOME')}))" % str(SENTINEL)
    )
    previous = os.environ.get("TYPESAFE_API_KEY")
    os.environ["TYPESAFE_API_KEY"] = "fake-canary-not-real"
    try:
        executed = subprocess.run(
            [sys.executable, "-c",
             "import guardian,sys; sys.exit(guardian.execute(%r, ['python3','-c',%r]).returncode)"
             % (str(ws_a), code)],
            cwd="/home/pratz/guardianai-pilot",
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=25,
            env={**os.environ, "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
        )
    finally:
        if previous is None:
            os.environ.pop("TYPESAFE_API_KEY", None)
        else:
            os.environ["TYPESAFE_API_KEY"] = previous
    try:
        exec_data = json.loads(executed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        exec_data = None
    record(
        "execute-api",
        executed.returncode == 0 and exec_data == {"key": False, "sentinel": False, "home": "/tmp"},
        {"returncode": executed.returncode, "data": exec_data,
         "stdout": executed.stdout[-400:], "stderr": executed.stderr[-400:]},
        "containment",
    )

    unix.close()
    abstract.close()
    print(json.dumps({
        "bwrap": guardian.shutil.which("bwrap"),
        "host_pid": host_pid,
        "host_hostname": host_name,
        "results": results,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print(json.dumps({"results": results}, indent=2))
        sys.exit(1)
