import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


def run(args):
    return subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout


def test_shared_file_roundtrip(tmp_path):
    path = tmp_path / "shared.txt"
    out1 = run([str(BIN / "shared_file_writer"), str(path), "hello test"])
    out2 = run([str(BIN / "shared_file_reader"), str(path)])
    assert "wrote:" in out1
    assert "read:" in out2
    assert "hello test" in out2


def test_pipe_demo():
    out = run([str(BIN / "pipe_demo")])
    assert "child_received:hello over unnamed pipe" in out
    assert "parent_sent:hello over unnamed pipe" in out


def test_shared_memory_with_semaphore_demo():
    out = run([str(BIN / "shm_sem_demo")])
    assert "child_read_shared_memory:hello via mmap shared memory" in out
    assert "parent_wrote_shared_memory" in out


def test_message_queue_demo():
    out = run([str(BIN / "msg_queue_demo")])
    assert "child_received_message_queue:7:hello via System V message queue" in out
    assert "parent_sent_message_queue:7" in out


def test_socket_demo():
    out = run([str(BIN / "socket_demo")])
    assert "child_socket_received:hello over unix socket" in out
    assert "parent_socket_reply:ack from child" in out


def test_signal_demo():
    out = run([str(BIN / "signal_demo")])
    assert "child_sent_signal:SIGUSR1" in out
    assert "parent_received_signal:SIGUSR1" in out


def test_recursive_plan_json():
    out = run(["python3", "src/ipc_lab.py", "plan", "pipe", "--depth", "3", "--format", "json"])
    assert '"topic": "pipe"' in out
    assert '"subtasks"' in out
    assert "strace" in out
