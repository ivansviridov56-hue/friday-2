// Style "equalizer": rays around a circle that jump with the voice.
(function () {
  let canvas = null;
  let raf = 0;
  const RAYS = 84;

  function frame(t) {
    const [ctx, w, h] = window.fridayCircles.prepare(canvas);
    const { c1, c2 } = window.fridayCircles.colors();
    const lvl = window.fridayCircles.level();
    const cx = w - 30;
    const cy = h / 2;
    const radius = 130;

    ctx.lineCap = "round";
    ctx.strokeStyle = c2;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius - 12, 0, Math.PI * 2);
    ctx.stroke();

    ctx.lineWidth = 3.4;
    ctx.strokeStyle = c1;
    ctx.shadowColor = c1;
    ctx.shadowBlur = 10;
    for (let i = 0; i < RAYS; i++) {
      const a = (i / RAYS) * Math.PI * 2 - Math.PI / 2;
      const v = 0.5 + 0.5 * Math.sin(i * 0.9 + t * 0.004) * Math.sin(i * 0.37 - t * 0.0027);
      const len = 6 + 8 * v + lvl * 95 * (0.25 + 0.75 * v);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a) * radius, cy + Math.sin(a) * radius);
      ctx.lineTo(cx + Math.cos(a) * (radius + len), cy + Math.sin(a) * (radius + len));
      ctx.stroke();
    }
    ctx.shadowBlur = 0;
    raf = requestAnimationFrame(frame);
  }

  window.fridayCircles.register("equalizer", {
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