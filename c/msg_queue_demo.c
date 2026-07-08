#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <sys/wait.h>
#include <unistd.h>

struct message {
    long type;
    char text[128];
};

int main(void) {
    int qid = msgget(IPC_PRIVATE, 0600 | IPC_CREAT);
    if (qid == -1) {
        perror("msgget");
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        msgctl(qid, IPC_RMID, NULL);
        return 1;
    }

    if (pid == 0) {
        struct message msg;
        if (msgrcv(qid, &msg, sizeof(msg.text), 7, 0) == -1) {
            perror("msgrcv");
            exit(1);
        }
        printf("child_received_message_queue:%ld:%s\n", msg.type, msg.text);
        exit(0);
    }

    struct message msg;
    msg.type = 7;
    snprintf(msg.text, sizeof(msg.text), "%s", "hello via System V message queue");
    if (msgsnd(qid, &msg, strlen(msg.text) + 1, 0) == -1) {
        perror("msgsnd");
        msgctl(qid, IPC_RMID, NULL);
        return 1;
    }

    int status = 0;
    waitpid(pid, &status, 0);
    msgctl(qid, IPC_RMID, NULL);
    printf("parent_sent_message_queue:%ld\n", msg.type);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
