(() => {
  const canvas = document.querySelector("#progress-chart");
  if (!canvas) return;
  const context = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * 2;
  canvas.height = rect.height * 2;
  context.scale(2, 2);
  context.strokeStyle = "#5ff2e0";
  context.lineWidth = 3;
  context.beginPath();
  [35, 52, 48, 70, 64, 82].forEach((value, index, values) => {
    const x = (rect.width / (values.length - 1)) * index;
    const y = rect.height - value;
    index ? context.lineTo(x, y) : context.moveTo(x, y);
  });
  context.stroke();
})();