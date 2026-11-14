#include <errno.h>
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
