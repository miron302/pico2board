#!/usr/bin/env python3
"""Start the miron's board dashboard and open the browser once the Pico 2 is plugged in.

Usage:
    python3 open_dashboard.py

Flow:
    1. Require the Raspberry Pi Pico 2 to be plugged in.
    2. Start the dashboard server (run.py) unless it is already running.
    3. Open the dashboard in the platform browser
       (Windows -> Edge, Linux -> Firefox, macOS -> Safari).
"""

import sys

import browser
import pico
import server

BASE_DIR = server.BASE_DIR
URL = "http://127.0.0.1:%d/" % server.PORT


def main() -> None:
    # Require the Raspberry Pi Pico 2 to be plugged in before doing anything.
    if not pico.connected(timeout_min=10):
        print("No Pico 2 detected - not starting the dashboard.", file=sys.stderr)
        sys.exit(1)

    proc, ok = server.ensure_server()
    if not ok:
        print("Dashboard server failed to start", file=sys.stderr)
        sys.exit(1)

    browser.open_url(URL)

    if proc is not None:
        proc.wait()


if __name__ == "__main__":
    main()
