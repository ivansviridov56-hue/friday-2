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
