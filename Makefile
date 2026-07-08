CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2 -g
LDFLAGS ?= -pthread
BIN_DIR := bin
SRC_DIR := c
PROGRAMS := shared_file_writer shared_file_reader pipe_demo shm_sem_demo msg_queue_demo socket_demo signal_demo
BINS := $(addprefix $(BIN_DIR)/,$(PROGRAMS))

.PHONY: all clean test demo docker-build docker-test docker-demo plan

all: $(BINS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/%: $(SRC_DIR)/%.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -rf $(BIN_DIR) /tmp/ipc_lab_shared_file.txt

test: all
	pytest -q tests

demo: all
	python3 src/ipc_lab.py run shared-file
	python3 src/ipc_lab.py run pipe
	python3 src/ipc_lab.py run shared-memory
	python3 src/ipc_lab.py run message-queue
	python3 src/ipc_lab.py run socket
	python3 src/ipc_lab.py run signal

plan:
	python3 src/ipc_lab.py plan all --depth 3

docker-build:
	docker build -t ipc-linux-lab:local .

docker-test:
	docker run --rm ipc-linux-lab:local make test

docker-demo:
	docker run --rm ipc-linux-lab:local make demo
