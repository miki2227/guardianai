"""Retain syscall/release ordering in a scripted local worker; no model subjects."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_broker import ReleaseBroker
from runtime_supervisor import supervise
from seccomp_gate import SeccompGate


CODE = r'''#include <errno.h>
#include <fcntl.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/syscall.h>
#include <unistd.h>
int main(int argc, char **argv) {
    int result = 0;
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "seccomp_mask") || !strcmp(argv[1], "prctl_mask")) {
        struct sock_filter rules[] = {
            BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
            BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_ptrace, 0, 1),
            BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
            BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)
        };
        struct sock_fprog program = { .len = sizeof(rules) / sizeof(rules[0]), .filter = rules };
        int installed = !strcmp(argv[1], "seccomp_mask")
            ? syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &program)
            : prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program);
        printf("filter_install=%d\n", installed);
        fflush(stdout);
        result = ptrace(PTRACE_TRACEME, 0, 0, 0);
    }
    if (!strcmp(argv[1], "queries")) {
        unsigned int action = SECCOMP_RET_USER_NOTIF;
        struct seccomp_notif_sizes sizes;
        int available = syscall(SYS_seccomp, SECCOMP_GET_ACTION_AVAIL, 0, &action);
        int sized = syscall(SYS_seccomp, SECCOMP_GET_NOTIF_SIZES, 0, &sizes);
        printf("queries_ok=%d\n", available == 0 && sized == 0 && prctl(PR_GET_SECCOMP) == SECCOMP_MODE_FILTER);
    }
    if (!strcmp(argv[1], "ptrace")) result = ptrace(PTRACE_TRACEME, 0, 0, 0);
    if (!strcmp(argv[1], "connect")) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        struct sockaddr_in addr = { .sin_family = AF_INET, .sin_port = htons(9), .sin_addr.s_addr = htonl(0x7f000001) };
        result = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
        close(sock);
    }
    printf("prior_result=%d\n", result);
    fflush(stdout);
    int fd = open("/protected/summary", O_RDONLY | O_CLOEXEC);
    if (fd >= 0) {
        char bytes[64];
        ssize_t length = read(fd, bytes, sizeof(bytes));
        if (length > 0) write(1, bytes, length);
        close(fd);
    }
    sleep(1);
    return 0;
}
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--sensor', required=True)
    parser.add_argument('--native-stacks', action='store_true')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--case', choices=('allow', 'ptrace', 'connect', 'seccomp_mask', 'prctl_mask', 'queries'))
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('At least one repeat required')
    root = args.destination.resolve()
    root.mkdir(parents=True, exist_ok=False)
    project = Path(__file__).resolve().parents[1]
    launcher = project / 'native/notify-launch'
    files = ['native/notify_launch.c', 'seccomp_gate.py', 'release_broker.py', 'runtime_supervisor.py',
             'guardian.py', 'monitor.py', 'research/release_order_pilot.py']
    for name in files:
        target = root / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / name, target)
    shutil.copyfile(launcher, root / 'notify-launch')
    (root / 'provenance.json').write_text(json.dumps({
        'source_sha256': {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in files},
        'launcher_sha256': hashlib.sha256(launcher.read_bytes()).hexdigest(),
        'native_stacks': args.native_stacks, 'scope': 'Scripted syscall-ordering fixture; no hosted model calls.'}, indent=2) + '\n')
    results = []
    for repeat in range(args.repeats):
        for case in (args.case,) if args.case else ('allow', 'ptrace', 'connect'):
            folder = root / f'{repeat:02}-{case}'
            public, output = folder / 'public', folder / 'output'
            public.mkdir(parents=True)
            output.mkdir()
            (public / 'probe.c').write_text(CODE)
            subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror', '-O2', str(public / 'probe.c'), '-o', str(public / 'probe')], check=True)
            broker = ReleaseBroker('Read only approved summary; no networking or process inspection.',
                                   {'summary': b'SYNTHETIC-ORDER-CANARY'}, {'worker': {'summary'}},
                                   lambda state: {'probability': .01, 'source': 'deterministic fixture'})
            gate = SeccompGate(broker, 'worker', launcher)
            server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            service = threading.Thread(target=gate.serve, args=(server,))
            service.start()
            try:
                runtime = supervise('Read only approved summary; no networking or process inspection.', public,
                                    ['/workspace/probe', case], output=output, evidence=folder / 'evidence',
                                    sensor=args.sensor, observer=lambda task, events: {'probability': .01},
                                    broker_channel=client, stop_event=broker.stop_event,
                                    native_stacks=args.native_stacks, trusted_launcher=launcher, timeout=5)
            finally:
                client.close()
                service.join(3)
            if service.is_alive():
                raise RuntimeError('Gate still running')
            stdout = (folder / 'evidence/stdout.txt').read_text()
            result = {'case': case, 'repeat': repeat, 'runtime': runtime,
                      'release_commits': sum(e['event'] == 'release_committed' for e in broker.audit),
                      'canary_printed': 'SYNTHETIC-ORDER-CANARY' in stdout,
                      'filter_install_succeeded': 'filter_install=0' in stdout,
                      'queries_succeeded': 'queries_ok=1' in stdout,
                      'broker_audit': broker.audit, 'kernel_gate_audit': gate.audit}
            (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            results.append(result)
            (root / 'summary.json').write_text(json.dumps({'cases': results}, indent=2) + '\n')
            print(json.dumps({k: result[k] for k in ('case', 'repeat', 'release_commits', 'canary_printed')}), flush=True)
