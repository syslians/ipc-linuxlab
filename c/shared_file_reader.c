#include <errno.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "/tmp/ipc_lab_shared_file.txt";
    char buf[512];

    FILE *fp = fopen(path, "r");
    if (!fp) {
        fprintf(stderr, "open %s failed: %s\n", path, strerror(errno));
        return 1;
    }
    if (!fgets(buf, sizeof(buf), fp)) {
        fprintf(stderr, "read %s failed\n", path);
        fclose(fp);
        return 1;
    }
    fclose(fp);
    buf[strcspn(buf, "\n")] = '\0';
    printf("read:%s:%s\n", path, buf);
    return 0;
}
