# miron's board

A simple, terminal-themed Christmas dashboard that shows the **time**, **weather**, **process
monitor**, and hosts a **snake** game, runs on your PC, and is driven by a **Raspberry Pi Pico 2**
plugged in over USB.

## Features

- **Terminal aesthetic**: monospace font, phosphor-green text, scanline overlay, glowing
  Christmas-red heading, falling snow.
- **Live clock + date** (big, glowing) and **weather card** (temp, condition, hi/lo, humidity,
  wind) from the free [Open-Meteo](https://open-meteo.com) API (no API key needed).
- **Process monitor**: simple live process list (pid, name, cpu, mem) via `GET /api/processes`.
- **Board light control**: toggle the Pico 2's onboard LED from the dashboard
  (`LIGHT ON` / `LIGHT OFF` over USB serial).
- **Games tab**: tiny **snake** game (arrows / WASD to move, space to pause / restart).
- **Customisation**: background picture presets or custom image upload, accent colour picker,
  Celsius/Fahrenheit toggle, custom font picker (TERMINAL / VT323 / SHARETECH / IBM).

## How it works

1. **Firmware** (`firmware/pico2-weather-dashboard/pico2-weather-dashboard.ino`) runs on the
   Pico 2 (RP2350). The Pico has no Wi-Fi/Ethernet and no battery-backed RTC, so it receives the
   current unix time from the host PC over the built-in **USB CDC serial** port and then pushes
   the current time every second.

   Protocol:
   - Host -> Pico: a line with the unix epoch in seconds, e.g. `1762800000\n`
   - Host -> Pico: a command line, e.g. `LIGHT ON\n` / `LIGHT OFF\n`
   - Pico -> Host: once armed, pushes the epoch every second, e.g. `1762800000\n`

2. **PC side** (`run.py`): small Python server that serves the dashboard and exposes
   - `GET /api/time` -> current epoch + source (`pico` or `local`)
   - `POST /api/light` body `{"state": "on"|"off"}` -> sends the light command to the Pico

3. **Dashboard** (`dashboard/`): live clock, weather, board light toggle, snake game, background
   presets / custom upload, accent colour, units.

## Quick start (any platform: Windows / macOS / Linux)

```bash
cd /home/miron/Projects/pico2board
pip install -r requirements.txt   # once: installs pyserial
python3 open_dashboard.py         # starts server, waits for Pico 2, opens dashboard
```

`python3 open_dashboard.py` will:
1. Stop any previous dashboard server instance.
2. Start the dashboard server.
3. Wait for the Raspberry Pi Pico 2 to be detected over USB.
4. Open the dashboard in your browser.

Alternatively, run the server directly:

```bash
python3 run.py    # serves dashboard at http://127.0.0.1:8000/ and opens browser
```

Then:

1. Flash the firmware onto your Raspberry Pi Pico 2 using the Arduino IDE (install the
   *Raspberry Pi Pico/RP2040* board package, which supports the RP2350).
2. Plug the Pico 2 into your PC over USB.
3. Open the dashboard in your browser (auto-opened via `open_dashboard.py` / the watcher).

The dashboard defaults to the Christmas/terminal theme. The browser must allow geolocation for
the weather location (falls back to a default location otherwise).

## Fully automatic setup (no commands needed after the first run)

You can make plugging the Pico 2 into the PC **do everything by itself**:

1. Flash the firmware to the Pico 2.
2. Start the background watcher once:

   ```bash
   python3 watch_dashboard.py          # runs forever in the background
   ```

   (or, on Linux, install & enable the systemd user service instead:

   ```bash
   mkdir -p ~/.config/systemd/user
   cp miron-board-dashboard.service ~/.config/systemd/user/
   systemctl --user enable --now miron-board-dashboard.service
   ```

   )

3. Plug the Pico 2 into the PC.
4. The watcher detects the board, starts the dashboard server, and opens the browser —
   automatically.

You can stop the watcher with `pkill -f watch_dashboard.py` (systemd: `systemctl --user stop miron-board-dashboard`).

## Requirements

- Python 3.7+
- `pyserial` (`pip install -r requirements.txt`)
- A browser
- Internet connection (weather; time comes over USB from the Pico)
- The Arduino IDE, to flash the firmware to the Pico 2

## Hardware notes

- The base Raspberry Pi Pico 2 has no Wi-Fi or Ethernet, so the device itself cannot fetch
  weather or run a network stack. Instead, the PC supplies the time over USB serial and the PC
  fetches the weather.

- To override the auto-detected Pico serial port, set the `PICO_PORT` environment variable
  (e.g. `PICO_PORT=/dev/ttyACM0 python3 run.py` or `PICO_PORT=COM3 python3 run.py`).

## Customisation

- Background: choose a preset (SOLAR / MATRIX / ICE / BURG) or upload your own picture
  (stored in the browser).
- Accent colour: colour picker (stored in the browser).
- Units: C / F toggle.
- All customisations live in `dashboard/` (`style.css`, `script.js`) and are persisted
  client-side where noted.
