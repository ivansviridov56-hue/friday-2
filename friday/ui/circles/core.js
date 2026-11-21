// Switchable look of the background circles.
// A style file registers itself:  fridayCircles.register("name", { mount(box) {...}, unmount() {...} })
(function () {
  const styles = {};
  let current = null;
  let currentName = null;
  const eased = { c1: null, c2: null };

  function parseColor(text) {
    const m = /^#?([0-9a-f]{6})$/i.exec((text || "").trim());
    if (!m) {
      return [47, 94, 241];
    }
    const n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function easeTo(from, to) {
    if (!from) {
      return to.slice();
    }
    return from.map((v, i) => v + (to[i] - v) * 0.05);
  }

  function rgb(c) {
    return "rgb(" + c.map(Math.round).join(",") + ")";
  }

  window.fridayCircles = {
    register(name, style) {
      styles[name] = style;
    },
    use(name) {
      const wanted = styles[name] ? name : "classic";
      if (!styles[name]) {
        console.warn("unknown circles style: " + name);
      }
      if (wanted === currentName) {
        return;
      }
      if (current && current.unmount) {
        current.unmount();
      }
      const box = document.getElementById("circles-custom");
      box.replaceChildren();
      currentName = wanted;
      current = styles[wanted];
      document.body.dataset.circles = wanted;
      if (current.mount) {
        current.mount(box);
      }
    },
    // Current state colours, eased so they fade like the CSS circles do.
    colors() {
      const cs = getComputedStyle(document.body);
      eased.c1 = easeTo(eased.c1, parseColor(cs.getPropertyValue("--c1")));
      eased.c2 = easeTo(eased.c2, parseColor(cs.getPropertyValue("--c2")));
      return { c1: rgb(eased.c1), c2: rgb(eased.c2) };
    },
    // Microphone loudness 0..1 (app.js provides window.fridayLevel).
    level() {
      return typeof window.fridayLevel === "function" ? window.fridayLevel() : 0;
    },
    // Sizes a full-layer canvas to its CSS size and returns [ctx, width, height].
    prepare(canvas) {
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
      }
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      return [ctx, w, h];
    },
  };

  // The old look lives in index.html and styles.css; CSS only shows or hides it.
  window.fridayCircles.register("classic", {});
})();