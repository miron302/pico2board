#!/usr/bin/env python3
"""Start the miron's board dashboard and open the browser once the Pico 2 is plugged in.

Usage:
    python3 open_dashboard.py

Flow:
    1. Stop any previous dashboard server instance.
    2. Start the dashboard server (run.py) in the background.
    3. Wait for it to come up on http://127.0.0.1:8000/.
    4. Wait for the Raspberry Pi Pico 2 to be detected over USB.
    5. Open the dashboard in the browser.
"""

import subprocess
import sys
import time
import socket
import os
import webbrowser
from pathlib import Path
from serial.tools import list_ports

BASE_DIR = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8000/"


def port_open(port: int = 8000) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def pico_connected(timeout_min: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_min * 60
    while time.monotonic() < deadline:
        try:
            ports = list_ports.comports()
        except Exception:
            ports = []
        for p in ports:
            if getattr(p, "is_bluetooth", False):
                continue
            name = (p.device or "").lower()
            if "ttyacm" in name or "ttyusb" in name or name.startswith("com"):
                return True
        time.sleep(2)
    return False


def main() -> None:
    # Require the Raspberry Pi Pico 2 to be plugged in before doing anything.
    if not pico_connected(timeout_min=10):
        print("No Pico 2 detected - not starting the dashboard.", file=sys.stderr)
        sys.exit(1)

    # Stop any previous dashboard instance, then start the server.
    subprocess.run(["pkill", "-f", "python3 run.py"], check=False)
    time.sleep(2)

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
        print("Dashboard server failed to start", file=sys.stderr)
        sys.exit(1)

    webbrowser.open(URL)
    proc.wait()


if __name__ == "__main__":
    main()
