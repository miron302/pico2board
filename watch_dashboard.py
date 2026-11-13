#!/usr/bin/env python3
"""Background watcher for miron's board.

Waits for the Raspberry Pi Pico 2 to be plugged in, and when it is:
  1. Stops any previous dashboard server instance.
  2. Starts the dashboard server.
  3. Opens the dashboard in the browser.

Once triggered it keeps running (stop it with: pkill -f watch_dashboard.py).
For fully automatic startup with no command at all, install the systemd user
service included in this folder (see README.md).
"""

import socket
import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path
from serial.tools import list_ports

BASE_DIR = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8000/"


def log(msg: str) -> None:
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def port_open(port: int = 8000) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def pico_connected(timeout_min: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout_min * 60
    while time.monotonic() < deadline:
        try:
            ports = list_ports.comports()
        except Exception as e:
            log("serial port scan error: %s" % e)
            ports = []
        for p in ports:
            if getattr(p, "is_bluetooth", False):
                continue
            name = (p.device or "").lower()
            if "ttyacm" in name or "ttyusb" in name or name.startswith("com"):
                return True
        time.sleep(2)
    return False


def start() -> bool:
    log("starting dashboard server...")
    subprocess.run(["pkill", "-f", "run.py"], check=False)
    # wait for the old server to release the port
    for _ in range(15):
        if not port_open():
            break
        time.sleep(1)
    proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=str(BASE_DIR),
        env={**os.environ, "PICO_DASHBOARD_NO_OPEN": "1"},
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        if port_open():
            break
        time.sleep(1)
    else:
        proc.kill()
        log("dashboard server failed to start")
        return False
    log("dashboard server is up, opening browser...")
    try:
        ok = webbrowser.open(URL)
        log("webbrowser.open returned %s" % ok)
    except Exception as e:
        log("webbrowser.open failed: %s" % e)
    return True


def main() -> None:
    log("watchdog started, waiting for Pico 2...")
    started = False
    while True:
        if pico_connected() and not started:
            if start():
                started = True
        elif not pico_connected():
            started = False
        time.sleep(3)


if __name__ == "__main__":
    main()
