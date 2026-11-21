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