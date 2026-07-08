#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t got_usr1 = 0;

static void on_usr1(int signo) {
    (void)signo;
    got_usr1 = 1;
}

int main(void) {
    struct sigaction sa;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sa.sa_handler = on_usr1;
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        struct timespec delay = {.tv_sec = 0, .tv_nsec = 100000000};
        nanosleep(&delay, NULL);
        kill(getppid(), SIGUSR1);
        printf("child_sent_signal:SIGUSR1\n");
        exit(0);
    }

    while (!got_usr1) {
        pause();
    }
    int status = 0;
    waitpid(pid, &status, 0);
    printf("parent_received_signal:SIGUSR1\n");
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
