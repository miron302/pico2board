#!/usr/bin/env python3
"""Pico Weather Dashboard - local launcher.

Serves the dashboard in dashboard/ and exposes /api/time, which reads the
current time from the Raspberry Pi Pico 2 (RP2350) over USB serial when the
firmware is running and connected, falling back to the local clock.

Run:
    python3 run.py
"""

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PICO_DASHBOARD_PORT", "8000"))

try:
    import serial
    from serial.tools import list_ports

    HAVE_SERIAL = True
except Exception:
    HAVE_SERIAL = False


def find_pico_port():
    override = os.environ.get("PICO_PORT")
    if override:
        return override
    if not HAVE_SERIAL:
        return None
    candidates = []
    for p in list_ports.comports():
        if getattr(p, "is_bluetooth", False):
            continue
        name = (p.device or "").lower()
        if "ttyacm" in name or "ttyusb" in name or name.startswith("com"):
            candidates.append(p.device)
    return candidates[0] if candidates else None


def get_pico_epoch(timeout=3.0):
    """Ask the connected Pico 2 for the current time over USB serial."""
    if not HAVE_SERIAL:
        return None
    port = find_pico_port()
    if not port:
        return None
    try:
        with serial.Serial(str(port), 115200, timeout=timeout) as ser:
            ser.write((str(int(time.time())) + "\n").encode("ascii"))
            ser.flush()
            line = ser.readline()
            if not line:
                return None
            txt = line.decode("ascii", "replace").strip()
            if txt.isdigit():
                return int(txt)
    except Exception:
        return None
    return None


def send_arduino_command(cmd, timeout=2.0):
    """Send a command line to the Pico 2 over USB serial."""
    port = find_pico_port()
    if not port:
        return False
    try:
        with serial.Serial(str(port), 115200, timeout=timeout) as ser:
            ser.write(cmd.encode("ascii"))
            ser.flush()
            return True
    except Exception:
        return False


def get_processes():
    """Return a simple list of running processes (requires psutil; empty list if unavailable)."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]) or []:
            try:
                info = p.info
                procs.append({
                    "pid": info.get("pid") or 0,
                    "name": info.get("name") or "",
                    "cpu": info.get("cpu_percent") or 0.0,
                    "mem": info.get("memory_percent") or 0.0,
                })
            except Exception:
                continue
        return procs
    except Exception:
        return []


class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, name):
        f = DASHBOARD_DIR / name
        if not f.is_file():
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        data = f.read_bytes()
        ctype = "text/css" if name.endswith(".css") else "text/javascript" if name.endswith(".js") else "text/html"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/time":
            epoch = int(time.time())
            source = "local"
            pico_epoch = get_pico_epoch()
            if pico_epoch is not None:
                epoch = pico_epoch
                source = "pico"
            self._send_json({"epoch": epoch, "source": source})
            return
        if path == "/api/processes":
            self._send_json({"processes": get_processes()})
            return
        if path in ("/", "/index.html"):
            self._serve_file("index.html")
            return
        if path == "/style.css":
            self._serve_file("style.css")
            return
        if path == "/script.js":
            self._serve_file("script.js")
            return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else b"{}"
        path = self.path.split("?")[0]
        if path == "/api/light":
            try:
                data = json.loads(body.decode("utf-8") or "{}")
                state = str(data.get("state") or "off").strip().lower()
                ok = False
                if state == "on":
                    ok = send_arduino_command("LIGHT ON\n")
                elif state == "off":
                    ok = send_arduino_command("LIGHT OFF\n")
                self._send_json({"ok": ok, "state": state})
                return
            except Exception:
                self._send_json({"ok": False, "state": "off"})
                return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"not found")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print("Pico Weather Dashboard running at http://%s:%d/" % (HOST, PORT), flush=True)
    try:
        if os.environ.get("PICO_DASHBOARD_NO_OPEN") != "1":
            import webbrowser

            webbrowser.open("http://%s:%d/" % (HOST, PORT))
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
