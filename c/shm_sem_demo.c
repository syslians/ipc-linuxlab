#define _GNU_SOURCE
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

struct shared_state {
    sem_t ready;
    char message[128];
};

int main(void) {
    struct shared_state *state = mmap(NULL, sizeof(*state), PROT_READ | PROT_WRITE,
                                      MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (state == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    if (sem_init(&state->ready, 1, 0) == -1) {
        perror("sem_init");
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        if (sem_wait(&state->ready) == -1) {
            perror("sem_wait");
            exit(1);
        }
        printf("child_read_shared_memory:%s\n", state->message);
        exit(0);
    }

    snprintf(state->message, sizeof(state->message), "%s", "hello via mmap shared memory");
    sem_post(&state->ready);

    int status = 0;
    waitpid(pid, &status, 0);
    sem_destroy(&state->ready);
    munmap(state, sizeof(*state));
    printf("parent_wrote_shared_memory\n");
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
