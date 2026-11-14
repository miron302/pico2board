"""Start and stop the dashboard server safely (no fragile pkill patterns)."""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("PICO_DASHBOARD_PORT", "8000"))
RUN_PY = str(BASE_DIR / "run.py")


def port_open(port: int = PORT) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _server_pids():
    """PIDs of python processes running this folder's run.py (Linux /proc scan)."""
    if os.name == "nt" or not os.path.isdir("/proc"):
        return []
    me = os.getpid()
    target = os.path.realpath(RUN_PY)
    pids = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        try:
            with open("/proc/%s/cmdline" % pid, "rb") as f:
                argv = [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
        except Exception:
            continue
        if not argv:
            continue
        if not os.path.basename(argv[0]).lower().startswith("python"):
            continue
        for arg in argv[1:]:
            if not (arg == "run.py" or arg.endswith("/run.py") or arg.endswith("\\run.py")):
                continue
            try:
                cwd = os.readlink("/proc/%s/cwd" % pid)
            except Exception:
                cwd = ""
            if os.path.realpath(os.path.join(cwd, arg)) == target:
                pids.append(int(pid))
            break
    return pids


def stop_previous_server(wait: float = 5.0) -> None:
    for pid in _server_pids():
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    deadline = time.time() + wait
    while time.time() < deadline and _server_pids():
        time.sleep(0.2)
    for pid in _server_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass


def ensure_server(timeout: float = 30.0):
    """Make sure the dashboard server is running.

    Returns ``(proc, ok)`` where ``proc`` is None when a server was already up
    (it is then reused), or the new process when one was started.
    """
    if port_open():
        return None, True

    stop_previous_server()

    env = dict(os.environ)
    env["PICO_DASHBOARD_NO_OPEN"] = "1"
    try:
        proc = subprocess.Popen([sys.executable, RUN_PY], cwd=str(BASE_DIR), env=env)
    except Exception:
        return None, False

    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_open():
            return proc, True
        if proc.poll() is not None:
            return proc, False
        time.sleep(0.5)

    try:
        proc.kill()
    except Exception:
        pass
    return proc, False
