# IPC Linux Lab

`ipc-linux-lab`는 Linux IPC(Inter-Process Communication)를 Docker 안에서 직접 빌드하고 실행하며 관찰하기 위한 학습용 실습 프로젝트다. macOS 호스트에서도 Linux 동작을 재현할 수 있도록 Debian 기반 Docker 이미지를 기준 실행 환경으로 삼는다.

이 프로젝트는 Red Hat/OpenSource.com의 `A guide to inter-process communication in Linux` 주제 흐름을 참고해 구성했다. 원본 PDF 자체는 저작권/개인 파일 경로 이슈가 있으므로 저장소에 포함하지 않는다.

## 목표

이 lab의 목표는 단순히 IPC 개념을 읽는 것이 아니라, 다음 과정을 직접 확인하는 것이다.

1. C 예제를 컴파일한다.
2. 각 IPC 방식의 stdout 결과를 확인한다.
3. pytest로 동작을 검증한다.
4. Docker Linux 컨테이너에서 macOS와 다른 Linux IPC semantics를 안정적으로 재현한다.
5. `strace`로 system call 흐름을 추적한다.
6. 재귀적 학습 계획을 생성해 주제별로 확장 학습한다.

## 다루는 IPC 주제

| 주제 | 예제 | 핵심 관찰 포인트 |
|---|---|---|
| Shared file | `shared_file_writer.c`, `shared_file_reader.c` | 여러 프로세스가 파일을 통해 상태를 공유하는 가장 단순한 IPC 패턴 |
| Unnamed pipe | `pipe_demo.c` | `pipe()`, `fork()`, fd 상속, read/write end close discipline |
| Shared memory + semaphore | `shm_sem_demo.c` | `mmap()` 기반 공유 메모리와 semaphore 동기화 |
| System V message queue | `msg_queue_demo.c` | kernel-managed message queue, message type, `msgsnd()`/`msgrcv()` |
| UNIX domain socket | `socket_demo.c` | 같은 host 안의 socketpair 기반 양방향 통신 |
| Signal | `signal_demo.c` | `SIGUSR1`, signal handler, parent/child synchronization |

## 디렉터리 구조

```text
ipc-linux-lab/
├── Dockerfile
├── Makefile
├── README.md
├── .dockerignore
├── .gitignore
├── c/
│   ├── shared_file_writer.c
│   ├── shared_file_reader.c
│   ├── pipe_demo.c
│   ├── shm_sem_demo.c
│   ├── msg_queue_demo.c
│   ├── socket_demo.c
│   └── signal_demo.c
├── src/
│   └── ipc_lab.py
├── tests/
│   └── test_labs.py
└── docs/
    ├── source-notes.md
    └── recursive-planning-prompt.md
```

## 빠른 시작

Docker Desktop 또는 Docker Engine이 실행 중이어야 한다.

```bash
cd ipc-linux-lab
make docker-build
make docker-test
make docker-demo
```

예상 테스트 결과:

```text
pytest -q tests
.......                                                                  [100%]
7 passed
```

예상 demo 결과:

```text
wrote:/tmp/ipc_lab_shared_file.txt:hello via shared file
read:/tmp/ipc_lab_shared_file.txt:hello via shared file

child_received:hello over unnamed pipe
parent_sent:hello over unnamed pipe

child_read_shared_memory:hello via mmap shared memory
parent_wrote_shared_memory

child_received_message_queue:7:hello via System V message queue
parent_sent_message_queue:7

child_socket_received:hello over unix socket
parent_socket_reply:ack from child

child_sent_signal:SIGUSR1
parent_received_signal:SIGUSR1
```

## Docker 명령어

이미지 빌드:

```bash
make docker-build
```

컨테이너 안에서 테스트 실행:

```bash
make docker-test
```

컨테이너 안에서 전체 demo 실행:

```bash
make docker-demo
```

직접 shell에 들어가기:

```bash
docker run --rm -it ipc-linux-lab:local bash
```

Docker Desktop에서 실습용 컨테이너를 유지하고 싶으면:

```bash
docker rm -f ipc-linux-lab-shell 2>/dev/null || true
docker create --name ipc-linux-lab-shell -it ipc-linux-lab:local bash
docker start ipc-linux-lab-shell
docker exec -it ipc-linux-lab-shell bash
```

## 로컬 Linux에서 실행

Linux 환경이라면 Docker 없이도 실행할 수 있다.

```bash
make all
make test
make demo
```

macOS에서도 일부 예제는 컴파일될 수 있지만, System V/POSIX IPC 동작과 compiler warning이 Linux와 다를 수 있다. 이 프로젝트의 기준 실행 환경은 Docker Debian Linux다.

## CLI 사용법

주제 목록 보기:

```bash
python3 src/ipc_lab.py topics
```

특정 lab 실행:

```bash
python3 src/ipc_lab.py run pipe
python3 src/ipc_lab.py run shared-file
python3 src/ipc_lab.py run shared-memory
python3 src/ipc_lab.py run message-queue
python3 src/ipc_lab.py run socket
python3 src/ipc_lab.py run signal
```

재귀적 학습 계획 생성:

```bash
python3 src/ipc_lab.py plan all --depth 3
python3 src/ipc_lab.py plan pipe --depth 3 --format json
```

## strace로 system call 관찰

컨테이너 안에서 다음처럼 실행하면 사용자 공간 C 코드가 어떤 system call로 이어지는지 볼 수 있다.

```bash
strace -f bin/pipe_demo
strace -f bin/shm_sem_demo
strace -f bin/msg_queue_demo
strace -f bin/socket_demo
strace -f bin/signal_demo
```

예를 들어 pipe demo에서는 다음 흐름을 관찰할 수 있다.

1. `pipe()`로 read/write fd 생성
2. `fork()`로 child process 생성
3. parent는 read end를 닫고 write
4. child는 write end를 닫고 read
5. 양쪽이 필요 없는 fd를 닫아 EOF와 blocking 조건을 제어

## 테스트 설계

테스트는 단순히 exit code만 확인하지 않고, 각 예제의 관찰 가능한 stdout을 검증한다.

예:

- pipe: parent/child 양쪽 출력 확인
- shared memory: parent write와 child read 확인
- message queue: message type과 payload 확인
- socket: child receive와 parent reply 확인
- signal: child signal send와 parent signal receive 확인

실행:

```bash
make test
```

Docker 기준:

```bash
make docker-test
```

## 학습 순서 추천

1. `shared-file`로 가장 단순한 IPC를 이해한다.
2. `pipe`로 parent/child fd 상속과 단방향 byte stream을 본다.
3. `shared-memory`로 메모리 공유와 semaphore 동기화를 본다.
4. `message-queue`로 kernel-managed queue와 message type을 본다.
5. `socket`으로 양방향 local IPC를 본다.
6. `signal`로 data channel이 아닌 event notification을 이해한다.
7. 각 예제를 `strace -f`로 다시 실행해 library call과 system call을 연결한다.

## 확장 아이디어

다음 주제를 추가하면 더 완성도 높은 Linux IPC lab이 된다.

- named pipe / FIFO
- POSIX message queue
- POSIX shared memory: `shm_open()`
- eventfd
- signalfd
- epoll 기반 event loop
- netlink socket
- file locking: `flock()`, `fcntl()`
- namespace/container boundary에서 IPC visibility 비교

## 주의사항

- build output인 `bin/`은 Git에 포함하지 않는다.
- 원본 PDF 파일은 저장소에 포함하지 않는다.
- macOS host compile 결과는 참고용이고, 검증 기준은 Docker Linux다.
- child process에서 `_exit()`를 쓰면 stdout buffering 때문에 pytest capture가 비어 보일 수 있다. 이 프로젝트의 예제는 교육 목적상 출력 flush가 보장되도록 작성했다.

## 주요 Make target

```bash
make all          # C 예제 컴파일
make test         # pytest 실행
make demo         # 모든 예제 실행
make plan         # 전체 주제 재귀 학습 계획 출력
make clean        # build output 정리
make docker-build # Docker image build
make docker-test  # Docker 안에서 test
make docker-demo  # Docker 안에서 demo
```

## 라이선스 / 출처 메모

이 저장소의 코드는 학습용 예제로 작성되었다. 문서 구조와 주제 선정은 공개 Linux IPC guide의 주제 흐름을 참고했지만, 원본 PDF 내용 전문은 포함하지 않는다.
