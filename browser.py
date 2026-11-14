"""Open the dashboard in the platform's preferred browser.

Windows -> Microsoft Edge
Linux   -> Firefox
macOS   -> Safari

Each platform is launched directly (no reliance on xdg-open / webbrowser
detection) with graceful fallbacks, so it also works from a systemd user
service or a background process.
"""

import os
import platform
import shutil
import subprocess
import webbrowser


def _spawn(cmd):
    """Start a command detached from this process. Return True on success."""
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


def _windows(url):
    candidates = []
    exe = shutil.which("msedge")
    if exe:
        candidates.append([exe, url])
    for path in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.isfile(path):
            candidates.append([path, url])
    candidates.append(["cmd", "/c", "start", "", "msedge", url])
    for c in candidates:
        if _spawn(c):
            return True
    return False


def _linux(url):
    for name in ("firefox", "firefox-esr"):
        exe = shutil.which(name)
        if exe and _spawn([exe, url]):
            return True
    for name in ("xdg-open", "gio"):
        exe = shutil.which(name)
        if not exe:
            continue
        cmd = [exe, url] if name == "xdg-open" else [exe, "open", url]
        if _spawn(cmd):
            return True
    return False


def _macos(url):
    if _spawn(["open", "-a", "Safari", url]):
        return True
    if _spawn(["open", url]):
        return True
    return False


def open_url(url):
    """Open ``url`` in the preferred browser. Returns True if a launch was attempted."""
    system = platform.system()
    if system == "Windows":
        ok = _windows(url)
    elif system == "Darwin":
        ok = _macos(url)
    else:
        ok = _linux(url)
    if ok:
        return True
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False
