#!/usr/bin/env python3
"""Diagnose why the Pico 2 is not being detected.

Usage:
    python3 doctor.py          (or: ./pico2board --doctor)
"""

import os
import shutil
import subprocess
import sys

import pico
import server

OK = "  [ok]   "
WARN = "  [warn] "
BAD = "  [fail] "


def _run(cmd):
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return ""


def _kernel_usb_lines():
    for cmd in (["journalctl", "-k", "-n", "200", "--no-pager"],):
        out = _run(cmd)
        if out:
            return [l for l in out.splitlines() if "usb" in l.lower()]
    return []


def main() -> int:
    print("\nmiron's board - Pico 2 diagnostics\n")
    problems = []

    # 1. pyserial
    if pico.list_ports is None:
        print(BAD + "pyserial is not installed  ->  pip install -r requirements.txt")
        problems.append("pyserial missing")
    else:
        print(OK + "pyserial installed")

    # 2. serial ports
    ports = pico.find_ports()
    if ports:
        print(OK + "Pico serial port(s): " + ", ".join(ports))
    else:
        others = []
        if pico.list_ports is not None:
            try:
                others = [p.device for p in pico.list_ports.comports()]
            except Exception:
                others = []
        print(WARN + "no Pico serial port (e.g. /dev/ttyACM0) found")
        if others:
            print("         other serial devices: " + ", ".join(others[:5]))
        problems.append("no serial port")

    # 3. USB device by Raspberry Pi vendor id (incl. BOOTSEL mode)
    usbs = pico.find_usb_devices()
    if usbs:
        print(OK + "Raspberry Pi USB device present: " + ", ".join(usbs))
    else:
        print(WARN + "no USB device with Raspberry Pi vendor id 2e8a")
        problems.append("no usb device")

    # 4. kernel enumeration errors
    lines = _kernel_usb_lines()
    enum_errors = [l for l in lines if "unable to enumerate" in l or "error -71" in l]
    if enum_errors:
        print(BAD + "USB enumeration failures in kernel log:")
        for l in enum_errors[-4:]:
            print("         " + l.strip())
        problems.append("usb enumeration failure")

    # 5. dashboard server
    if server.port_open():
        print(OK + "dashboard server is running on port %d" % server.PORT)
    else:
        print(WARN + "dashboard server is not running (this is fine if waiting for the board)")

    # 6. platform browser
    if shutil.which("firefox"):
        print(OK + "browser: firefox")
    elif shutil.which("xdg-open"):
        print(WARN + "firefox not found; will fall back to xdg-open")
    elif sys.platform == "darwin":
        print(OK + "browser: Safari (open -a Safari)")
    elif os.name == "nt":
        print(OK + "browser: Microsoft Edge")
    else:
        print(WARN + "no supported browser found")

    # verdict
    print()
    if not problems:
        print("Everything looks good. Plug the Pico 2 in and the dashboard should open.\n")
        return 0

    print("Likely problem: the Pico 2 is not showing up over USB.\n")
    if "usb enumeration failure" in problems:
        print("The board is being powered on but USB enumeration fails")
        print("('device descriptor read ... error -71'). Common causes:\n")
        print("  1. CHARGE-ONLY USB CABLE - use a data cable (very common!).")
        print("  2. Faulty USB port/hub - try another port directly on the PC.")
        print("  3. Firmware crash/USB stack - hold BOOTSEL while plugging in;")
        print("     a drive called 'RPI-RP2' should appear. Reflash the sketch.")
        print("  4. Bad board/USB connector.\n")
    else:
        print("  - Check the cable is a DATA cable (not charge-only).")
        print("  - Try another USB port (directly on the PC, not a hub).")
        print("  - Hold BOOTSEL while plugging in: an 'RPI-RP2' drive should appear;")
        print("    reflash the firmware from firmware/.")
        print("  - After flashing, unplug and plug the board back in.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
