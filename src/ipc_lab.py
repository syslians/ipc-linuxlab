#!/usr/bin/env python3
"""IPC Linux Lab helper CLI.

이 파일은 학습용 오케스트레이터다. C 바이너리를 실행하고, PDF 주제 흐름을 따라
recursive learning plan을 출력한다.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


@dataclass(frozen=True)
class Topic:
    key: str
    title: str
    concept: str
    binary: str | None
    observe: list[str]
    next_questions: list[str]


TOPICS: list[Topic] = [
    Topic(
        "shared-file",
        "Shared files",
        "두 프로세스가 같은 파일 경로를 통해 데이터를 교환한다. 가장 단순하지만 동기화와 원자성이 핵심 문제다.",
        None,
        ["파일 생성 시점", "reader가 writer보다 먼저 실행될 때의 실패", "append/write atomicity"],
        ["파일 잠금 flock/fcntl은 언제 필요한가?", "rename 기반 atomic update는 왜 유용한가?"],
    ),
    Topic(
        "shared-memory",
        "Shared memory with semaphore",
        "프로세스별 주소 공간은 분리되어 있지만 mmap MAP_SHARED로 같은 물리 메모리를 볼 수 있다. semaphore로 ready 상태를 동기화한다.",
        "shm_sem_demo",
        ["sem_wait 이전 child block", "sem_post 이후 child read", "공유 메모리 lifetime"],
        ["POSIX shm_open 방식으로 바꾸면 cleanup은 어떻게 달라지는가?", "semaphore 없이 실행하면 어떤 race가 생기는가?"],
    ),
    Topic(
        "pipe",
        "Unnamed pipe",
        "부모/자식 프로세스가 pipe fd를 상속하고 byte stream을 주고받는다. 단방향이며 close discipline이 중요하다.",
        "pipe_demo",
        ["read end/write end close", "EOF 발생 조건", "fork 전 생성한 fd 상속"],
        ["named pipe FIFO와 unnamed pipe의 차이는?", "pipe buffer가 꽉 차면 write는 어떻게 되는가?"],
    ),
    Topic(
        "message-queue",
        "System V message queue",
        "커널이 관리하는 queue에 typed message를 넣고 꺼낸다. byte stream이 아니라 message boundary가 보존된다.",
        "msg_queue_demo",
        ["message type", "IPC_RMID cleanup", "msgrcv가 특정 type을 기다리는 방식"],
        ["POSIX message queue와 System V queue는 어떻게 다른가?", "queue limit은 어디서 확인하는가?"],
    ),
    Topic(
        "socket",
        "UNIX domain socket",
        "같은 머신 안에서 socket API로 양방향 통신한다. pipe보다 네트워크 프로그래밍 모델에 가깝다.",
        "socket_demo",
        ["socketpair", "full-duplex communication", "request/reply pattern"],
        ["AF_UNIX path socket 서버로 바꾸면 어떻게 되는가?", "TCP loopback과 비교하면 장단점은?"],
    ),
    Topic(
        "signal",
        "Signals",
        "signal은 작은 payload 없는 비동기 알림에 가깝다. 데이터 전달보다 이벤트 통지에 적합하다.",
        "signal_demo",
        ["SIGUSR1 handler", "pause wakeup", "async-signal-safe 제약"],
        ["sigaction이 signal보다 선호되는 이유는?", "sigqueue로 값을 전달하려면 어떻게 하나?"],
    ),
]

ALIASES = {
    "shared_file": "shared-file",
    "file": "shared-file",
    "shm": "shared-memory",
    "mq": "message-queue",
    "pipes": "pipe",
    "sockets": "socket",
    "signals": "signal",
}


def find_topic(name: str) -> Topic:
    key = ALIASES.get(name, name)
    for topic in TOPICS:
        if topic.key == key:
            return topic
    valid = ", ".join(t.key for t in TOPICS)
    raise SystemExit(f"unknown topic {name!r}; valid topics: {valid}")


def run_cmd(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return proc.stdout


def run_topic(topic: Topic) -> None:
    if topic.key == "shared-file":
        path = "/tmp/ipc_lab_shared_file.txt"
        print(run_cmd([str(BIN / "shared_file_writer"), path, "hello via shared file"]).strip())
        print(run_cmd([str(BIN / "shared_file_reader"), path]).strip())
        return
    if not topic.binary:
        raise SystemExit(f"topic {topic.key} has no binary")
    print(run_cmd([str(BIN / topic.binary)]).strip())


def recursive_plan(topic: Topic, depth: int) -> dict:
    node = {
        "topic": topic.key,
        "title": topic.title,
        "concept": topic.concept,
        "lab": f"make all && python3 src/ipc_lab.py run {topic.key}",
        "observe": topic.observe,
        "reflection_questions": topic.next_questions,
    }
    if depth <= 1:
        return node
    node["subtasks"] = [
        {
            "step": "read",
            "prompt": f"PDF의 {topic.title} 절을 읽고 핵심 개념, system call, failure mode를 5줄로 요약해라.",
        },
        {
            "step": "run",
            "prompt": f"Docker 컨테이너에서 `{node['lab']}`를 실행하고 stdout을 관찰해라.",
        },
        {
            "step": "trace",
            "prompt": f"`strace -f bin/{topic.binary or 'shared_file_writer'}`로 system call 흐름을 관찰하고 user-space API와 kernel API를 연결해라.",
        },
        {
            "step": "break",
            "prompt": "동기화/cleanup/권한/EOF 중 하나를 의도적으로 깨고 어떤 실패가 나는지 기록해라.",
        },
        {
            "step": "extend",
            "prompt": "예제를 10~20줄만 수정해서 새로운 관찰 포인트를 하나 추가해라. 수정 전 실패 테스트를 먼저 작성해라.",
        },
    ]
    if depth >= 3:
        node["subtasks"].append(
            {
                "step": "compare",
                "prompt": "다른 IPC 메커니즘 하나와 latency, coupling, cleanup, message boundary, debugging 난이도를 비교해라.",
            }
        )
    return node


def cmd_topics(_: argparse.Namespace) -> None:
    for t in TOPICS:
        print(f"{t.key:15} {t.title}")


def cmd_run(args: argparse.Namespace) -> None:
    run_topic(find_topic(args.topic))


def cmd_plan(args: argparse.Namespace) -> None:
    if args.topic == "all":
        data = [recursive_plan(t, args.depth) for t in TOPICS]
    else:
        data = recursive_plan(find_topic(args.topic), args.depth)
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        plans = data if isinstance(data, list) else [data]
        for p in plans:
            print(f"\n# {p['title']} ({p['topic']})")
            print(p["concept"])
            print(f"Lab: `{p['lab']}`")
            print("Observe:")
            for item in p["observe"]:
                print(f"- {item}")
            print("Questions:")
            for item in p["reflection_questions"]:
                print(f"- {item}")
            for sub in p.get("subtasks", []):
                print(f"  - {sub['step']}: {sub['prompt']}")


def cmd_doctor(_: argparse.Namespace) -> None:
    print(run_cmd(["make", "all"]).strip())
    for t in TOPICS:
        print(f"\n== {t.key} ==")
        run_topic(t)


def main() -> None:
    parser = argparse.ArgumentParser(description="Linux IPC learning lab")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("topics", help="list IPC topics")
    p.set_defaults(func=cmd_topics)

    p = sub.add_parser("run", help="run one lab")
    p.add_argument("topic")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("plan", help="generate recursive learning plan")
    p.add_argument("topic", help="topic key or all")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("doctor", help="build and run every lab")
    p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
