const DEFAULT_COORDS = { lat: 40.7128, lon: -74.006 }; // fallback location if geolocation is unavailable

const BG_PRESETS = [
  { name: "SOLAR", css: "linear-gradient(135deg, #0b0033 0%, #5b0b0b 55%, #b3001b 100%)" },
  { name: "MATRIX", css: "linear-gradient(135deg, #02120a 0%, #03351d 60%, #061f0f 100%)" },
  { name: "ICE", css: "linear-gradient(135deg, #030712 0%, #164e63 60%, #0e7490 100%)" },
  { name: "BURG", css: "linear-gradient(135deg, #1a0202 0%, #7f1d1d 55%, #b45309 100%)" }
];

const FONT_PRESETS = [
  { name: "TERMINAL", css: 'ui-monospace, "Cascadia Mono", "Courier New", Menlo, Consolas, monospace' },
  { name: "VT323", css: '"VT323", ui-monospace, monospace' },
  { name: "SHARETECH", css: '"Share Tech Mono", ui-monospace, monospace' },
  { name: "IBM", css: '"IBM Plex Mono", ui-monospace, monospace' }
];

let currentEpoch = Math.floor(Date.now() / 1000);
let timeSource = "local";
let coords = null;
let useF = false;
let lastWeather = null;
const body = document.body;

/* ---------------- background ---------------- */

function applyBg(css) {
  body.style.backgroundImage = "none";
  body.style.background = css;
}

function applyBgImage(dataUrl) {
  body.style.backgroundImage = "url(" + dataUrl + ")";
  body.style.backgroundColor = "#000000";
}

function initBackground() {
  const accent = localStorage.getItem("pico-accent");
  if (accent) {
    document.documentElement.style.setProperty("--accent", accent);
  }
  const saved = localStorage.getItem("pico-bg");
  if (saved && saved.startsWith("data:image")) {
    applyBgImage(saved);
  } else {
    const idx = parseInt(localStorage.getItem("pico-bg-preset") || "0", 10) % BG_PRESETS.length;
    applyBg(BG_PRESETS[idx].css);
  }
}

function initBgPresets() {
  document.querySelectorAll(".preset").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const idx = parseInt(btn.getAttribute("data-bg"), 10);
      const preset = BG_PRESETS[idx];
      if (!preset) return;
      applyBg(preset.css);
      localStorage.setItem("pico-bg-preset", String(idx));
      localStorage.removeItem("pico-bg");
    });
  });
  const upload = document.getElementById("bgUpload");
  upload.addEventListener("change", function (e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function () {
      const dataUrl = String(reader.result);
      applyBgImage(dataUrl);
      try {
        localStorage.setItem("pico-bg", dataUrl);
        localStorage.removeItem("pico-bg-preset");
      } catch (err) {}
    };
    reader.readAsDataURL(file);
  });
}

function initFonts() {
  document.querySelectorAll(".font-preset").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const idx = parseInt(btn.getAttribute("data-font"), 10);
      const preset = FONT_PRESETS[idx];
      if (!preset) return;
      document.body.style.fontFamily = preset.css;
      localStorage.setItem("pico-font", String(idx));
    });
  });
  const savedFont = localStorage.getItem("pico-font");
  if (savedFont) {
    const idx = parseInt(savedFont, 10);
    const preset = FONT_PRESETS[idx];
    if (preset) {
      document.body.style.fontFamily = preset.css;
    }
  }
}

function initSystem() {
  const listEl = document.getElementById("processList");
  const countEl = document.getElementById("procCount");
  async function refresh() {
    try {
      const res = await fetch("/api/processes");
      const j = await res.json();
      const procs = j.processes || [];
      if (countEl) countEl.textContent = "(" + procs.length + ")";
      let html = "";
      for (let i = 0; i < procs.length; i++) {
        const p = procs[i];
        html += "<div class='proc-row'><span class='p-pid'>" + p.pid + "</span> <span>" + (p.name || "") + "</span> <span>" + p.cpu + "% cpu</span> <span>" + p.mem + "% mem</span></div>";
      }
      if (listEl) listEl.innerHTML = html || "<div class='proc-empty'>no processes found</div>";
    } catch (e) {
      if (listEl) listEl.innerHTML = "<div class='proc-empty'>process monitor unavailable</div>";
    }
  }
  refresh();
  setInterval(refresh, 2000);
}

function initNotes() {
  const area = document.getElementById("notesArea");
  const saveBtn = document.getElementById("notesSave");
  if (area) {
    const saved = localStorage.getItem("pico-notes");
    if (saved) area.value = saved;
  }
  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      localStorage.setItem("pico-notes", area.value);
    });
  }
}

function initGameImport() {
  const fileInput = document.getElementById("gameImport");
  const codeArea = document.getElementById("gameCode");
  if (fileInput) {
    fileInput.addEventListener("change", function (e) {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function () {
        if (codeArea) codeArea.value = String(reader.result);
      };
      reader.readAsText(file);
    });
  }
}

/* ---------------- snowflakes ---------------- */

let snowHost = null;
let snowOn = true;
let snowColor = "#ffffff";
let snowAmount = 30;

function renderSnow() {
  if (!snowHost) return;
  snowHost.innerHTML = "";
  if (!snowOn) return;
  for (let i = 0; i < snowAmount; i++) {
    const s = document.createElement("div");
    s.className = "flake";
    const size = 2 + Math.random() * 4;
    s.style.width = size + "px";
    s.style.height = size + "px";
    s.style.left = Math.random() * 100 + "%";
    s.style.top = -10 - Math.random() * 110 + "%";
    s.style.background = snowColor;
    s.style.opacity = 0.4 + Math.random() * 0.6;
    s.style.animationDuration = (8 + Math.random() * 12) + "s";
    s.style.animationDelay = (Math.random() * 10) + "s";
    snowHost.appendChild(s);
  }
}

function initSnow() {
  const host = document.createElement("div");
  host.className = "snow";
  document.body.appendChild(host);
  snowHost = host;
  const savedOn = localStorage.getItem("pico-snow-on");
  const savedColor = localStorage.getItem("pico-snow-color");
  const savedAmount = localStorage.getItem("pico-snow-amount");
  snowOn = savedOn ? savedOn === "1" : true;
  snowColor = savedColor || "#ffffff";
  snowAmount = parseInt(savedAmount || "30", 10);
  if (isNaN(snowAmount) || snowAmount < 0) snowAmount = 0;
  if (snowAmount > 80) snowAmount = 80;
  renderSnow();
  const snowToggle = document.getElementById("snowToggle");
  const snowColorPicker = document.getElementById("snowColorPicker");
  const snowAmountInput = document.getElementById("snowAmount");
  if (snowToggle) {
    snowToggle.addEventListener("click", function () {
      snowOn = !snowOn;
      snowToggle.textContent = "[ SNOW: " + (snowOn ? "ON" : "OFF") + " ]";
      localStorage.setItem("pico-snow-on", snowOn ? "1" : "0");
      renderSnow();
    });
  }
  if (snowColorPicker) {
    snowColorPicker.addEventListener("input", function () {
      snowColor = snowColorPicker.value;
      localStorage.setItem("pico-snow-color", snowColor);
      renderSnow();
    });
  }
  if (snowAmountInput) {
    snowAmountInput.addEventListener("input", function () {
      snowAmount = parseInt(snowAmountInput.value, 10) || 0;
      localStorage.setItem("pico-snow-amount", String(snowAmount));
      renderSnow();
    });
  }
}

/* ---------------- clock ---------------- */

function pad(n) {
  return String(n).padStart(2, "0");
}

function renderTime() {
  const d = new Date(currentEpoch * 1000);
  const hh = pad(d.getHours());
  const mm = pad(d.getMinutes());
  const ss = pad(d.getSeconds());
  document.getElementById("clock").textContent = hh + ":" + mm + ":" + ss;
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  document.getElementById("date").textContent =
    days[d.getDay()] + ", " + (d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear();
}

async function refreshTime() {
  try {
    const res = await fetch("/api/time", { cache: "no-store" });
    const data = await res.json();
    currentEpoch = data.epoch;
    timeSource = data.source || "local";
    document.getElementById("timeSource").textContent =
      timeSource === "pico" ? "Time source: Pico 2 (via USB)" : "Time source: This device";
    renderTime();
  } catch (e) {
    document.getElementById("timeSource").textContent = "Time source: This device";
  }
}

setInterval(function () {
  currentEpoch = Math.floor(Date.now() / 1000);
  renderTime();
}, 1000);
setInterval(refreshTime, 5000);
refreshTime();

/* ---------------- weather ---------------- */

function conditionInfo(code) {
  const map = {
    0: ["\u2600\uFE0F", "Clear sky"],
    1: ["\uD83C\uDF4B", "Partly cloudy"],
    2: ["\u26D4", "Scattered clouds"],
    3: ["\u2601\uFE0F", "Overcast"],
    45: ["\uD83C\uDFE0\uFE0F", "Fog"],
    48: ["\uD83C\uDFE0\uFE0F", "Rime fog"],
    51: ["\uD83C\uDF27\uFE0F", "Light drizzle"],
    53: ["\uD83C\uDF27\uFE0F", "Drizzle"],
    55: ["\uD83C\uDF27\uFE0F", "Dense drizzle"],
    56: ["\uD83C\uDF27\uFE0F", "Freezing drizzle"],
    57: ["\uD83C\uDF27\uFE0F", "Freezing drizzle"],
    61: ["\uD83C\uDF27\uFE0F", "Light rain"],
    63: ["\uD83C\uDF27\uFE0F", "Rain"],
    65: ["\uD83C\uDF27\uFE0F", "Heavy rain"],
    66: ["\u2744\uFE0F", "Freezing rain"],
    67: ["\u2744\uFE0F", "Heavy freezing rain"],
    71: ["\uD83C\uDF28\uFE0F", "Light snow"],
    73: ["\u2744\uFE0F", "Snow"],
    75: ["\u2744\uFE0F", "Heavy snow"],
    77: ["\u2744\uFE0F", "Snow grains"],
    80: ["\uD83C\uDF27\uFE0F", "Light showers"],
    81: ["\uD83C\uDF27\uFE0F", "Showers"],
    82: ["\uD83C\uDF27\uFE0F", "Violent showers"],
    85: ["\uD83C\uDF28\uFE0F", "Snow showers"],
    86: ["\u2744\uFE0F", "Snow showers"],
    95: ["\u26D4\uFE0F", "Thunderstorm"],
    96: ["\u26D4\uFE0F", "Thunderstorm"],
    99: ["\u26D4\uFE0F", "Thunderstorm"]
  };
  return map[code] || ["\uD83C\uDF21\uFE0F", "Unknown"];
}

function getCoords() {
  if (coords) {
    return Promise.resolve([coords.lat, coords.lon]);
  }
  const fallback = Promise.resolve([DEFAULT_COORDS.lat, DEFAULT_COORDS.lon]);
  if (!navigator.geolocation) {
    return fallback;
  }
  return new Promise(function (resolve) {
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        coords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        resolve([coords.lat, coords.lon]);
      },
      function () {
        coords = DEFAULT_COORDS;
        resolve([DEFAULT_COORDS.lat, DEFAULT_COORDS.lon]);
      },
      { timeout: 8000 }
    );
  });
}

function toDisplayTemp(c) {
  const t = useF ? c * 9 / 5 + 32 : c;
  return Math.round(t);
}

function renderWeather() {
  if (!lastWeather) {
    document.getElementById("weatherIcon").textContent = "\u274C";
    document.getElementById("weatherTemp").textContent = "--\u00B0C";
    document.getElementById("weatherCondition").textContent = "Fetching\u2026";
    document.getElementById("weatherHiLo").textContent = "H: --\u00B0  L: --\u00B0";
    document.getElementById("weatherMeta").textContent = "Waiting for weather\u2026";
    return;
  }
  const cur = lastWeather.current;
  const daily = lastWeather.daily;
  const info = conditionInfo(cur.weather_code);
  const temp = toDisplayTemp(cur.temperature_2m);
  document.getElementById("weatherIcon").textContent = info[0];
  document.getElementById("weatherCondition").textContent = info[1];
  document.getElementById("weatherTemp").textContent = temp + "\u00B0" + (useF ? "F" : "C");
  const hi = toDisplayTemp(daily.temperature_2m_max[0]);
  const lo = toDisplayTemp(daily.temperature_2m_min[0]);
  document.getElementById("weatherHiLo").textContent = "H: " + hi + "\u00B0  L: " + lo + "\u00B0";
  document.getElementById("weatherMeta").textContent =
    "Humidity: " + Math.round(cur.relative_humidity_2m) +
    "%  \u00B7  Wind: " + Math.round(cur.wind_speed_10m) + " km/h";
}

async function refreshWeather() {
  try {
    const [la, lo] = await getCoords();
    const url =
      "https://api.open-meteo.com/v1/forecast?latitude=" + la +
      "&longitude=" + lo +
      "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m" +
      "&daily=weather_code,temperature_2m_max,temperature_2m_min" +
      "&timezone=auto";
    const res = await fetch(url);
    if (!res.ok) throw new Error("weather request failed");
    const j = await res.json();
    lastWeather = { current: j.current, daily: j.daily };
    renderWeather();
  } catch (e) {
    document.getElementById("weatherIcon").textContent = "\u274C";
    document.getElementById("weatherTemp").textContent = "--\u00B0C";
    document.getElementById("weatherCondition").textContent = "Weather unavailable";
    document.getElementById("weatherHiLo").textContent = "";
    document.getElementById("weatherMeta").textContent = "Check your connection";
  }
}

refreshWeather();
setInterval(refreshWeather, 30 * 60 * 1000);

/* ---------------- board light control ---------------- */

const unitToggle = document.getElementById("unitToggle");
const accentPicker = document.getElementById("accentPicker");
const bgUpload = document.getElementById("bgUpload");

unitToggle.addEventListener("click", function () {
  useF = !useF;
  unitToggle.textContent = "[ UNITS: " + (useF ? "F" : "C") + " ]";
  renderWeather();
});

accentPicker.addEventListener("input", function () {
  const v = accentPicker.value;
  document.documentElement.style.setProperty("--accent", v);
  localStorage.setItem("pico-accent", v);
});

/* ---------------- tabs ---------------- */

function initTabs() {
  document.querySelectorAll(".tabs .tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".tabs .tab").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      document.querySelectorAll("#tab-time, #tab-games, #tab-system, #tab-notes, #tab-settings").forEach(function (p) { p.classList.remove("active"); });
      const panel = document.getElementById("tab-" + btn.getAttribute("data-tab"));
      if (panel) panel.classList.add("active");
      if (btn.getAttribute("data-tab") === "games") { startGame(); }
    });
  });
  document.querySelectorAll("#settingsTabs .tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("#settingsTabs .tab").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      document.querySelectorAll(".sub-panel").forEach(function (p) { p.classList.remove("active"); });
      const panel = document.getElementById("settings-" + btn.getAttribute("data-sub"));
      if (panel) panel.classList.add("active");
    });
  });
}

/* ---------------- snake game ---------------- */

const GRID = 20;
const CELL = 24;
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("gameScore");
const statusEl = document.getElementById("gameStatus");

let snake, dir, food, score, gameState = "ready", gameTimer = null;

function resetSnake() {
  snake = [{ x: 10, y: 10 }];
  dir = { x: 1, y: 0 };
  score = 0;
  gameState = "running";
  placeFood();
  scoreEl.textContent = "score: 0";
  statusEl.textContent = "snake: running - arrows/WASD to move, space to pause";
  drawSnake();
}

function placeFood() {
  const occupied = new Set();
  for (let i = 0; i < snake.length; i++) {
    occupied.add(snake[i].x + "," + snake[i].y);
  }
  const free = [];
  for (let x = 0; x < GRID; x++) {
    for (let y = 0; y < GRID; y++) {
      if (!occupied.has(x + "," + y)) free.push({ x: x, y: y });
    }
  }
  if (free.length === 0) return;
  food = free[Math.floor(Math.random() * free.length)];
}

function tick() {
  if (gameState !== "running") return;
  stepSnake();
  drawSnake();
}

function stopGameLoop() {
  if (gameTimer) { clearInterval(gameTimer); gameTimer = null; }
}

function startGame() {
  resetSnake();
  stopGameLoop();
  gameTimer = setInterval(tick, 140);
}

function stepSnake() {
  const head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };
  const hitWall = head.x < 0 || head.y < 0 || head.x >= GRID || head.y >= GRID;
  let hitSelf = false;
  for (let i = 0; i < snake.length; i++) {
    if (snake[i].x === head.x && snake[i].y === head.y) hitSelf = true;
  }
  if (hitWall || hitSelf) {
    gameState = "over";
    stopGameLoop();
    statusEl.textContent = "game over - score: " + score + " - press space to restart";
    return;
  }
  snake.unshift(head);
  if (head.x === food.x && head.y === food.y) {
    score = score + 1;
    scoreEl.textContent = "score: " + score;
    placeFood();
  } else {
    snake.pop();
  }
}

function drawSnake() {
  ctx.fillStyle = "#020a04";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ff3b5c";
  ctx.fillRect(food.x * CELL + 1, food.y * CELL + 1, CELL - 2, CELL - 2);
  for (let i = snake.length - 1; i >= 0; i--) {
    ctx.fillStyle = i === 0 ? "#4ade80" : "#22c55e";
    const s = snake[i];
    ctx.fillRect(s.x * CELL + 1, s.y * CELL + 1, CELL - 2, CELL - 2);
  }
}

function onKeyDown(e) {
  const k = e.key;
  if (!document.getElementById("tab-games").classList.contains("active")) {
    return;
  }
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].indexOf(k) >= 0) {
    e.preventDefault();
  }
  if (k === " " || k === "Enter") {
    if (gameState === "ready" || gameState === "over") {
      startGame();
    } else if (gameState === "running") {
      gameState = "paused";
      stopGameLoop();
      statusEl.textContent = "snake: paused";
    } else if (gameState === "paused") {
      startGame();
    }
    return;
  }
  if (gameState === "ready") {
    startGame();
  }
  const map = {
    ArrowUp: { x: 0, y: -1 },
    ArrowDown: { x: 0, y: 1 },
    ArrowLeft: { x: -1, y: 0 },
    ArrowRight: { x: 1, y: 0 },
    w: { x: 0, y: -1 },
    s: { x: 0, y: 1 },
    a: { x: -1, y: 0 },
    d: { x: 1, y: 0 }
  };
  const d = map[k];
  if (d) {
    if (!(d.x === -dir.x && d.y === -dir.y)) {
      dir = d;
    }
  }
}

document.addEventListener("keydown", onKeyDown);

const snakeToggle = document.getElementById("snakeToggle");
const snakeStatusEl = document.getElementById("snakeStatus");
if (snakeToggle) {
  snakeToggle.addEventListener("click", function () {
    if (gameState === "running") {
      gameState = "paused";
      stopGameLoop();
      if (snakeStatusEl) snakeStatusEl.textContent = "snake: paused";
    } else {
      startGame();
    }
  });
}

const boardNameInput = document.getElementById("boardNameInput");
function applyBoardName() {
  const name = boardNameInput && boardNameInput.value ? boardNameInput.value : "miron's board";
  document.querySelector("h1").textContent = name;
  localStorage.setItem("pico-board-name", name);
}

const timeSyncBtn = document.getElementById("timeSyncBtn");
if (timeSyncBtn) {
  timeSyncBtn.addEventListener("click", function () { refreshTime(); });
}

/* ---------------- init ---------------- */

initBackground();
initBgPresets();
initFonts();
initSnow();
initSystem();
initNotes();
initGameImport();
initTabs();
applyBoardName();
