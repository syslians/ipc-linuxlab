#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    int sv[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) == -1) {
        perror("socketpair");
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        close(sv[0]);
        char buf[128] = {0};
        ssize_t n = read(sv[1], buf, sizeof(buf) - 1);
        if (n < 0) {
            perror("child read socket");
            exit(1);
        }
        const char *reply = "ack from child";
        write(sv[1], reply, strlen(reply));
        printf("child_socket_received:%s\n", buf);
        close(sv[1]);
        exit(0);
    }

    close(sv[1]);
    const char *msg = "hello over unix socket";
    write(sv[0], msg, strlen(msg));
    char reply[128] = {0};
    read(sv[0], reply, sizeof(reply) - 1);
    close(sv[0]);

    int status = 0;
    waitpid(pid, &status, 0);
    printf("parent_socket_reply:%s\n", reply);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
