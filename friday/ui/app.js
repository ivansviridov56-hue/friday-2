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
};