(() => {
  const canvas = document.querySelector("#memory-canvas");
  if (!canvas) return;
  const context = canvas.getContext("2d");
  const status = document.querySelector("#mindmap-status");
  let nodes = [];
  let edges = [];
  let selected = null;
  const colors = {
    Family: "#ff9fb2",
    Places: "#1fb5a8",
    Events: "#ffd98a",
    Interests: "#4aa8ff",
    Friends: "#5ff2e0",
  };

  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * Math.min(window.devicePixelRatio || 1, 2);
    canvas.height = rect.height * Math.min(window.devicePixelRatio || 1, 2);
    context.setTransform(canvas.width / rect.width, 0, 0, canvas.height / rect.height, 0, 0);
  };

  const draw = () => {
    const rect = canvas.getBoundingClientRect();
    context.clearRect(0, 0, rect.width, rect.height);
    const radius = Math.min(rect.width, rect.height) * 0.32;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    nodes.forEach((node, index) => {
      const angle = nodes.length === 1 ? 0 : (Math.PI * 2 * index) / nodes.length;
      node.x = nodes.length === 1 ? cx : cx + Math.cos(angle) * radius;
      node.y = nodes.length === 1 ? cy : cy + Math.sin(angle) * radius;
    });

    edges.forEach((edge) => {
      const source = nodes.find((node) => node.id === edge.source);
      const target = nodes.find((node) => node.id === edge.target);
      if (!source || !target) return;
      context.beginPath();
      context.moveTo(source.x, source.y);
      context.quadraticCurveTo(cx, cy, target.x, target.y);
      context.strokeStyle = "rgba(95,242,224,.28)";
      context.lineWidth = 2;
      context.stroke();
    });

    nodes.forEach((node) => {
      context.beginPath();
      context.arc(node.x, node.y, selected && selected.id === node.id ? 30 : 22, 0, Math.PI * 2);
      context.fillStyle = colors[node.category] || "#5ff2e0";
      context.shadowBlur = selected && selected.id === node.id ? 24 : 12;
      context.shadowColor = context.fillStyle;
      context.fill();
      context.shadowBlur = 0;
      context.fillStyle = "#04111d";
      context.font = "700 12px Inter, sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(node.label.slice(0, 10), node.x, node.y);
    });
  };

  const load = async () => {
    try {
      const response = await fetch("/api/mindmap/1");
      const data = await response.json();
      nodes = data.nodes;
      edges = data.edges;
      if (!nodes.length) nodes = [{id: 0, label: "Asha", category: "Family", description: "Asha's memory constellation."}];
      selected = nodes[0];
      resize();
      draw();
      status.textContent = `${nodes.length} memory nodes loaded.`;
    } catch (error) {
      status.textContent = "The memory map could not load.";
    }
  };

  canvas.addEventListener("click", (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const hit = nodes.find((node) => Math.hypot(node.x - x, node.y - y) <= 34);
    if (!hit) return;
    selected = hit;
    document.querySelector("#memory-label").textContent = hit.label;
    document.querySelector("#memory-description").textContent = hit.description;
    draw();
  });

  document.querySelector("#node-search").addEventListener("input", (event) => {
    const term = event.target.value.toLowerCase();
    const hit = nodes.find((node) => node.label.toLowerCase().includes(term));
    if (hit) selected = hit;
    draw();
  });
  document.querySelector("#fit-map").addEventListener("click", () => {
    resize();
    draw();
  });
  document.querySelector("#read-memory").addEventListener("click", () => {
    if (!selected || !("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(`${selected.label}. ${selected.description}`));
  });
  window.addEventListener("resize", () => {
    resize();
    draw();
  });
  load();
})();