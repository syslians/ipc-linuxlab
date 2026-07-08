#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "/tmp/ipc_lab_shared_file.txt";
    const char *message = argc > 2 ? argv[2] : "hello from shared file";

    FILE *fp = fopen(path, "w");
    if (!fp) {
        fprintf(stderr, "open %s failed: %s\n", path, strerror(errno));
        return 1;
    }
    fprintf(fp, "%s\n", message);
    fclose(fp);
    printf("wrote:%s:%s\n", path, message);
    return 0;
}
