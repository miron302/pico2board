/*
 * Pico 2 (RP2350) weather dashboard firmware
 * ----------------------------------------
 * The Pico 2 has no Wi-Fi / Ethernet and no battery-backed RTC, so it gets the
 * current time from the host PC over the built-in USB CDC serial port ("Serial"
 * in the Arduino API) and then pushes the current epoch every second.
 *
 * Host -> Pico : a single line containing the unix epoch in seconds,
 *               terminated by '\n'. e.g. "1762800000\n"
 * Pico -> Host : once armed, pushes the epoch every second, one per line.
 *               e.g. "1762800000\n"
 */

#include <Arduino.h>

static const int RX_BUF_SIZE = 40;
static char rxBuf[RX_BUF_SIZE];
static int rxIdx = 0;
static bool armed = false;
static unsigned long epoch = 0;
static unsigned long lastPushMs = 0;

static void handleLine() {
  rxBuf[rxIdx] = '\0';
  // Command lines start with "LIGHT " (e.g. "LIGHT ON" / "LIGHT OFF")
  if (rxIdx > 4 && rxBuf[0] == 'L' && rxBuf[1] == 'I' && rxBuf[2] == 'G' && rxBuf[3] == 'H' && rxBuf[4] == 'T' && rxBuf[5] == ' ') {
    bool on = false;
    if (rxIdx >= 8 && rxBuf[6] == 'O') {
      on = (rxBuf[7] == 'N');
    }
    digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
    rxIdx = 0;
    return;
  }
  unsigned long val = 0;
  bool valid = true;
  for (int i = 0; rxBuf[i] != '\0'; i++) {
    char c = rxBuf[i];
    if (c < '0' || c > '9') { valid = false; break; }
    val = val * 10 + (c - '0');
  }
  if (valid && val > 0) { armed = true; epoch = val; }
  rxIdx = 0;
}

static void pushTime() {
  Serial.print(epoch);
  Serial.println();
}

void setup() {
  Serial.begin(115200); // USB CDC serial
  lastPushMs = millis();
}

void loop() {
  while (Serial.available() > 0) {
    int c = Serial.read();
    if (c == '\n' || c == '\r') {
      handleLine();
    } else if (rxIdx < RX_BUF_SIZE - 1) {
      rxBuf[rxIdx++] = (char)c;
    }
  }
  if (armed) {
    unsigned long nowMs = millis();
    if ((nowMs - lastPushMs) >= 1000) {
      lastPushMs = nowMs;
      pushTime();
    }
  }
}
