(() => {
  const canvas = document.querySelector("#landing-galaxy");
  if (!canvas) return;
  const context = canvas.getContext("2d");
  const calm = document.documentElement.dataset.calmMode === "true"
    || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let stars = [];
  let frameId = 0;

  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const count = calm ? 35 : Math.min(120, Math.floor(rect.width / 12));
    stars = Array.from({length: count}, (_, index) => ({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      r: 0.6 + Math.random() * 1.8,
      speed: 0.08 + Math.random() * 0.16,
      phase: index * 0.37,
    }));
  };

  const draw = (time = 0) => {
    const rect = canvas.getBoundingClientRect();
    context.clearRect(0, 0, rect.width, rect.height);
    stars.forEach((star) => {
      if (!calm) star.y -= star.speed;
      if (star.y < 0) star.y = rect.height;
      const alpha = calm ? 0.45 : 0.35 + Math.sin(time * 0.001 + star.phase) * 0.2;
      context.beginPath();
      context.arc(star.x, star.y, star.r, 0, Math.PI * 2);
      context.fillStyle = `rgba(95,242,224,${alpha})`;
      context.fill();
    });
    if (!calm) frameId = requestAnimationFrame(draw);
  };

  resize();
  draw();
  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(frameId);
    else if (!calm) draw();
  });
})();
