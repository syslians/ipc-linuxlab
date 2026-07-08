#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    int fds[2];
    if (pipe(fds) == -1) {
        perror("pipe");
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        close(fds[1]);
        char buf[128] = {0};
        ssize_t n = read(fds[0], buf, sizeof(buf) - 1);
        if (n < 0) {
            perror("child read");
            exit(1);
        }
        close(fds[0]);
        printf("child_received:%s\n", buf);
        exit(0);
    }

    close(fds[0]);
    const char *msg = "hello over unnamed pipe";
    if (write(fds[1], msg, strlen(msg)) < 0) {
        perror("parent write");
        return 1;
    }
    close(fds[1]);

    int status = 0;
    waitpid(pid, &status, 0);
    printf("parent_sent:%s\n", msg);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
