// Bridge between the Python assistant and the page (called through ui_bridge.py).
const LABELS = {
  loading: "Загружаюсь…",
  idle: "Готова",
  listening: "Слушаю…",
  thinking: "Думаю…",
  speaking: "Говорю…",
  error: "Ошибка запуска. Подробности в консоли.",
};

const status = document.getElementById("status");
const chat = document.getElementById("chat");

// Loudness: Python sends 0..1 about 20 times a second, the page eases towards it every frame.
const root = document.documentElement;
let levelTarget = 0;
let levelNow = 0;
let levelLoop = false;
window.fridayLevel = () => levelNow;

function stepLevel() {
  levelNow += (levelTarget - levelNow) * 0.12;
  if (Math.abs(levelTarget - levelNow) < 0.002) {
    levelNow = levelTarget;
  }
  root.style.setProperty("--lvl", levelNow.toFixed(3));
  if (levelNow === levelTarget) {
    levelLoop = false;
    return;
  }
  requestAnimationFrame(stepLevel);
}

// Accent colours: Python sends the final values, the page fades to them.
const ACCENT_FADE_MS = 1200;
let accentNow = null; // the values shown right now, so a new fade starts from them
let accentFrame = 0;

function parseAccentValue(value) {
  const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(value);
  if (hex) {
    return { kind: "hex", rgb: [1, 2, 3].map((i) => parseInt(hex[i], 16)) };
  }
  const triplet = /^(\d+), (\d+), (\d+)$/.exec(value);
  if (triplet) {
    return { kind: "triplet", rgb: [1, 2, 3].map((i) => Number(triplet[i])) };
  }
  return null;
}

function formatAccentValue(kind, rgb) {
  const c = rgb.map((v) => Math.round(Math.min(255, Math.max(0, v))));
  if (kind === "hex") {
    return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
  }
  return c.join(", ");
}

function writeAccent(vars) {
  let style = document.getElementById("accent-style");
  if (!style) {
    style = document.createElement("style");
    style.id = "accent-style";
    document.head.appendChild(style);
  }
  const rules = Object.entries(vars).map(([k, v]) => k + ": " + v + ";").join(" ");
  style.textContent = ':root[data-theme="win11"] { ' + rules + " }";
}

function fadeAccent(target) {
  cancelAnimationFrame(accentFrame);
  if (!accentNow) {
    // The first accent is applied at once, there is nothing to fade from.
    accentNow = target;
    writeAccent(target);
    return;
  }
  const from = accentNow;
  const start = performance.now();
  let lastWrite = 0;
  // While the colours fade, the circles must not run their own 1.4 s CSS transition on top.
  root.classList.add("accent-fading");
  function step(now) {
    const t = Math.min(1, (now - start) / ACCENT_FADE_MS);
    if (t < 1 && now - lastWrite < 33) {
      accentFrame = requestAnimationFrame(step);
      return;
    }
    lastWrite = now;
    const eased = t * t * (3 - 2 * t);
    const frame = {};
    for (const [name, to] of Object.entries(target)) {
      const a = parseAccentValue(from[name] !== undefined ? from[name] : to);
      const b = parseAccentValue(to);
      frame[name] = a && b && a.kind === b.kind
        ? formatAccentValue(b.kind, b.rgb.map((v, i) => a.rgb[i] + (v - a.rgb[i]) * eased))
        : to;
    }
    accentNow = frame;
    writeAccent(frame);
    if (t < 1) {
      accentFrame = requestAnimationFrame(step);
    } else {
      root.classList.remove("accent-fading");
    }
  }
  accentFrame = requestAnimationFrame(step);
}

// Wallpaper change: Windows redraws the blur under the window abruptly, about 1.1 s after the
// wallpaper file changes. The page covers the window with a dark veil before that and lifts it
// smoothly once the new accent has arrived. Works in every theme.
const VEIL_FALLBACK_MS = 4000; // lifts by itself if no new accent comes (same accent as before)
const VEIL_RELEASE_DELAY_MS = 500; // after the accent arrives, give Windows time to finish
let veil = null;
let veilTimer = 0;

function releaseVeil() {
  clearTimeout(veilTimer);
  if (veil) {
    veil.classList.remove("on");
  }
}

function coverWallpaperChange() {
  if (!veil) {
    veil = document.createElement("div");
    veil.id = "wallpaper-veil";
    document.body.appendChild(veil);
    void veil.offsetHeight; // so the first fade-in is animated too
  }
  veil.classList.add("on");
  clearTimeout(veilTimer);
  veilTimer = setTimeout(releaseVeil, VEIL_FALLBACK_MS);
}

function releaseVeilSoon() {
  if (!veil || !veil.classList.contains("on")) {
    return;
  }
  clearTimeout(veilTimer);
  veilTimer = setTimeout(releaseVeil, VEIL_RELEASE_DELAY_MS);
}

window.fridayUi = {
  setState(state) {
    document.body.className = "state-" + state;
    status.textContent = LABELS[state] || state;
  },
  addMessage(role, text) {
    const el = document.createElement("div");
    el.className = "msg " + role;
    el.textContent = text;
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
  },
    setLevel(value) {
    levelTarget = Math.min(1, Math.max(0, Number(value) || 0));
    if (!levelLoop) {
      levelLoop = true;
      requestAnimationFrame(stepLevel);
    }
  },
  setCover(image) {
    const orb = document.getElementById("music-orb");
    const cover = document.getElementById("music-cover");
    if (image) {
      cover.src = image;
      orb.classList.remove("hidden");
    } else {
      orb.classList.add("hidden");
    }
  },
  setCirclesStyle(name) {
    window.fridayCircles.use(name);
  },
  setTheme(name) {
    document.documentElement.dataset.theme = name;
  },
  setTransparency(percent) {
    const value = Math.min(100, Math.max(0, Math.round(Number(percent) || 0)));
    root.style.setProperty("--transparency", String(value));
    const slider = document.getElementById("transparency");
    const label = document.getElementById("transparency-value");
    if (slider) {
      slider.value = String(value);
    }
    if (label) {
      label.textContent = value + "%";
    }
  },
  setAccent(vars) {
    fadeAccent(vars);
    releaseVeilSoon();
  },
  wallpaperChanging() {
    coverWallpaperChange();
  },
};

// Text input: the page hands typed text to Python (friday/text_input.py).
// If Python refuses it (busy, still loading), the text stays in the field.
const composer = document.getElementById("composer");
const textInput = document.getElementById("text-input");
const sendButton = document.getElementById("send");

composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = textInput.value.trim();
  if (!text) {
    return;
  }
  const api = window.pywebview && window.pywebview.api;
  if (!api || !api.submit_text) {
    return;
  }
  sendButton.disabled = true;
  try {
    const accepted = await api.submit_text(text);
    if (accepted) {
      textInput.value = "";
      fitInput();
    } else {
      textInput.classList.add("refused");
      setTimeout(() => textInput.classList.remove("refused"), 700);
    }
  } catch (error) {
    console.error(error);
  } finally {
    sendButton.disabled = false;
    textInput.focus();
  }
});

// Own window buttons (the window has no system frame).
function callApi(name) {
  const api = window.pywebview && window.pywebview.api;
  if (api && api[name]) {
    api[name]().catch((error) => console.error(error));
  }
}

document.getElementById("btn-minimize").addEventListener("click", () => callApi("minimize_window"));
document.getElementById("btn-close").addEventListener("click", () => callApi("close_window"));

// Resizing the frameless window: three invisible handles. While one is held, the page
// sends the wanted size to Python, one request at a time (the last wanted size wins).
(function () {
  let drag = null;
  let pending = null;
  let sending = false;

  function flush() {
    if (sending || !pending) {
      return;
    }
    const size = pending;
    pending = null;
    const api = window.pywebview && window.pywebview.api;
    if (!api || !api.resize_window) {
      return;
    }
    sending = true;
    api.resize_window(size.width, size.height)
      .catch((error) => console.error(error))
      .finally(() => {
        sending = false;
        flush();
      });
  }

  function onDown(event) {
    const mode = event.currentTarget.dataset.resize;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    drag = {
      sx: event.screenX,
      sy: event.screenY,
      w: window.outerWidth,
      h: window.outerHeight,
      x: mode.includes("x"),
      y: mode.includes("y"),
    };
  }

  function onMove(event) {
    if (!drag) {
      return;
    }
    pending = {
      width: drag.x ? drag.w + (event.screenX - drag.sx) : drag.w,
      height: drag.y ? drag.h + (event.screenY - drag.sy) : drag.h,
    };
    flush();
  }

  function onUp() {
    drag = null;
  }

  document.querySelectorAll(".resize-handle").forEach((handle) => {
    handle.addEventListener("pointerdown", onDown);
    handle.addEventListener("pointermove", onMove);
    handle.addEventListener("pointerup", onUp);
    handle.addEventListener("pointercancel", onUp);
  });
})();

// Input island, take 2: a growing text area, Enter sends, Shift+Enter makes a new line,
// the placeholder shows what she is doing.
const MAX_INPUT_HEIGHT = 136;

function fitInput() {
  const from = composer.offsetHeight;
  composer.style.height = "auto";
  textInput.style.height = "auto";
  const full = textInput.scrollHeight;
  const to = Math.min(full, MAX_INPUT_HEIGHT);
  // The text area jumps to its final height at once, so the text never scrolls;
  // only the island animates (its bottom edge opens smoothly).
  textInput.style.height = to + "px";
  textInput.style.overflowY = full > MAX_INPUT_HEIGHT ? "auto" : "hidden";
  if (full <= MAX_INPUT_HEIGHT) textInput.scrollTop = 0;
  const target = composer.offsetHeight;
  if (from === target) {
    return;
  }
  composer.style.height = from + "px";
  void composer.offsetHeight; // force reflow so the transition starts from `from`
  composer.style.height = target + "px";
}

composer.addEventListener("transitionend", (event) => {
  if (event.target === composer && event.propertyName === "height") {
    composer.style.height = "";
  }
});

textInput.addEventListener("input", fitInput);
textInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    composer.requestSubmit();
  }
});


// Safety net: if no theme arrives, show the page with the classic one.
setTimeout(() => {
  if (!document.documentElement.dataset.theme) {
    window.fridayUi.setTheme("classic");
  }
}, 3000);


// Settings panel: the page only shows the choices and asks Python to change them.
const THEME_LABELS = { classic: "Синяя", windows: "Серая", black: "Чёрная", win11: "Windows 11" };
const CIRCLES_LABELS = {
  classic: "Классика",
  blobs: "Пятна",
  equalizer: "Эквалайзер",
  dots: "Точки",
};

const settingsPanel = document.getElementById("settings");
const settingsButton = document.getElementById("btn-settings");
let settingsData = null;

function renderOptions(boxId, names, labels, current, apiMethod, key) {
  const box = document.getElementById(boxId);
  box.replaceChildren();
  for (const name of names) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "option" + (name === current ? " on" : "");
    button.textContent = labels[name] || name;
    button.addEventListener("click", async () => {
      const api = window.pywebview && window.pywebview.api;
      if (!api || !api[apiMethod]) {
        return;
      }
      try {
        if (await api[apiMethod](name)) {
          settingsData.current[key] = name;
          renderSettings();
        }
      } catch (error) {
        console.error(error);
      }
    });
    box.appendChild(button);
  }
}

function renderSettings() {
  if (!settingsData || !settingsData.themes) {
    return;
  }
  renderOptions("opt-theme", settingsData.themes, THEME_LABELS,
                settingsData.current.theme, "set_theme", "theme");
  renderOptions("opt-circles", settingsData.circles, CIRCLES_LABELS,
                settingsData.current.circles, "set_circles_style", "circles");
}

async function openSettings() {
  const api = window.pywebview && window.pywebview.api;
  if (api && api.get_settings) {
    try {
      settingsData = await api.get_settings();
      renderSettings();
    } catch (error) {
      console.error(error);
    }
  }
  settingsPanel.classList.remove("closed");
  settingsPanel.setAttribute("aria-hidden", "false");
}

function closeSettings() {
  settingsPanel.classList.add("closed");
  settingsPanel.setAttribute("aria-hidden", "true");
}

settingsButton.addEventListener("click", () => {
  if (settingsPanel.classList.contains("closed")) {
    openSettings();
  } else {
    closeSettings();
  }
});
document.getElementById("settings-close").addEventListener("click", closeSettings);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSettings();
  }
});

// Transparency slider: the page previews at once, Python saves when the slider is released.
const transparencySlider = document.getElementById("transparency");

transparencySlider.addEventListener("input", () => {
  window.fridayUi.setTransparency(transparencySlider.value);
});

transparencySlider.addEventListener("change", async () => {
  const api = window.pywebview && window.pywebview.api;
  if (!api || !api.set_transparency) {
    return;
  }
  try {
    await api.set_transparency(Number(transparencySlider.value));
  } catch (error) {
    console.error(error);
  }
});