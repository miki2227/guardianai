#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
int main(int argc, char **argv) {
    int result = 0;
    if (argc != 2) return 2;
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
