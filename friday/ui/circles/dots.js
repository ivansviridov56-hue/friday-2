// Style "dots": a ring of particles that fly apart with the voice.
(function () {
  let canvas = null;
  let raf = 0;
  const particles = Array.from({ length: 220 }, () => ({
    angle: Math.random() * Math.PI * 2,
    speed: (Math.random() * 0.5 + 0.2) * (Math.random() < 0.5 ? -1 : 1) * 0.00018,
    phase: Math.random() * Math.PI * 2,
    size: Math.random() * 2 + 1.2,
    weight: Math.random(),
  }));

  function frame(t) {
    const [ctx, w, h] = window.fridayCircles.prepare(canvas);
    const { c1 } = window.fridayCircles.colors();
    const lvl = window.fridayCircles.level();
    const cx = w - 30;
    const cy = h / 2;
    const radius = 150;

    ctx.shadowColor = c1;
    ctx.shadowBlur = 8;
    for (const p of particles) {
      const a = p.angle + t * p.speed;
      const r = radius + 9 * Math.sin(t * 0.0017 + p.phase) + lvl * 90 * (0.3 + 0.7 * p.weight);
      ctx.globalAlpha = 0.45 + 0.55 * p.weight;
      ctx.fillStyle = p.weight > 0.5 ? c1 : "#ffffff";
      ctx.beginPath();
      ctx.arc(cx + Math.cos(a) * r, cy + Math.sin(a) * r, p.size + lvl * 2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    raf = requestAnimationFrame(frame);
  }

  window.fridayCircles.register("dots", {
    mount(box) {
      canvas = document.createElement("canvas");
      box.appendChild(canvas);
      raf = requestAnimationFrame(frame);
    },
    unmount() {
      cancelAnimationFrame(raf);
      canvas = null;
    },
  });
})();