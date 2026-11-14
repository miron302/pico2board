"""Pico 2 detection helpers (shared by the launchers)."""

import time
from pathlib import Path

try:
    from serial.tools import list_ports
except Exception:  # pyserial not installed
    list_ports = None

RASPBERRY_PI_VID = 0x2E8A  # Raspberry Pi / Pico USB vendor id
_USB_VENDOR = "%04x" % RASPBERRY_PI_VID
SYS_USB = Path("/sys/bus/usb/devices")


def _is_pico(port) -> bool:
    if getattr(port, "is_bluetooth", False):
        return False
    if getattr(port, "vid", None) == RASPBERRY_PI_VID:
        return True
    name = (port.device or "").lower()
    return "ttyacm" in name or "ttyusb" in name or name.startswith("com")


def find_ports():
    """Return serial ports that look like a Raspberry Pi Pico 2."""
    if list_ports is None:
        return []
    try:
        return [p.device for p in list_ports.comports() if _is_pico(p)]
    except Exception:
        return []


def find_usb_devices():
    """Return USB device sysfs paths with the Raspberry Pi vendor id.

    This also matches a Pico in BOOTSEL mode (RPI-RP2 mass storage), which has
    no serial port yet.
    """
    found = []
    if not SYS_USB.is_dir():
        return found
    try:
        entries = list(SYS_USB.iterdir())
    except Exception:
        return found
    for dev in entries:
        try:
            vid = (dev / "idVendor").read_text().strip().lower()
        except Exception:
            continue
        if vid == _USB_VENDOR:
            found.append(str(dev))
    return found


def present() -> bool:
    """True if the Pico 2 is attached in any USB mode (serial or BOOTSEL)."""
    return bool(find_ports() or find_usb_devices())


def connected(timeout_min: float = 1.0) -> bool:
    """Wait until a Pico 2 appears on USB (up to ``timeout_min`` minutes)."""
    deadline = time.monotonic() + timeout_min * 60
    while True:
        if present():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(2)
