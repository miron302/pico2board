#!/usr/bin/env python3
"""Background watcher for miron's board.

Waits for the Raspberry Pi Pico 2 to be plugged in, and when it is:
  1. Starts the dashboard server (reusing one that is already running).
  2. Opens the dashboard in the platform browser:
       Windows -> Microsoft Edge, Linux -> Firefox, macOS -> Safari.

Once triggered it keeps running (stop it with: pkill -f watch_dashboard.py).
For fully automatic startup with no command at all, install the systemd user
service included in this folder (see README.md).
"""

import sys
import time

import browser
import pico
import server

URL = "http://127.0.0.1:%d/" % server.PORT


def log(msg: str) -> None:
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def start() -> bool:
    log("Pico 2 detected on %s" % (", ".join(pico.find_ports()) or "unknown port"))
    log("starting dashboard server...")
    proc, ok = server.ensure_server()
    if not ok:
        log("dashboard server failed to start")
        return False
    if proc is None:
        log("dashboard server already running")
    else:
        log("dashboard server is up")
    log("opening browser...")
    try:
        opened = browser.open_url(URL)
        log("browser open returned %s" % opened)
    except Exception as e:
        log("browser open failed: %s" % e)
    return True


def main() -> None:
    log("watchdog started, waiting for Pico 2...")
    started = False
    last_beat = 0.0
    while True:
        present = pico.present()
        if present and not started:
            started = start()
        elif not present:
            started = False
            now = time.time()
            if now - last_beat >= 30:
                last_beat = now
                log(
                    "waiting for Pico 2 ... serial=%s usb=%s"
                    % (pico.find_ports() or "none", pico.find_usb_devices() or "none")
                )
        time.sleep(2)


if __name__ == "__main__":
    main()
