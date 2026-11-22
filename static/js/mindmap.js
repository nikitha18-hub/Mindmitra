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
      const patientId = document.querySelector("#mindmap-data")?.dataset.patientId || "1";
      const response = await fetch(`/api/mindmap/${patientId}`);
      const data = await response.json();
      nodes = data.nodes;
      edges = data.edges;
      if (!nodes.length) nodes = [{id: 0, label: "Asha", category: "Family", description: "Asha's memory constellation."}];
      selected = nodes[0];
      resize();
      draw();
      status.textContent = `${nodes.length} memory nodes loaded.`;
      const source = document.querySelector("#edge-source");
      const target = document.querySelector("#edge-target");
      if (source && target) {
        source.innerHTML = nodes.map((node) => `<option value="${node.id}">${node.label}</option>`).join("");
        target.innerHTML = nodes.map((node) => `<option value="${node.id}">${node.label}</option>`).join("");
      }
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

  const editor = document.querySelector("#mindmap-editor");
  if (editor) {
    const editorStatus = document.querySelector("#mindmap-editor-status");
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
    canvas.addEventListener("click", () => {
      if (!selected) return;
      editor.elements.label.value = selected.label || "";
      editor.elements.description.value = selected.description || "";
      editor.elements.category.value = selected.category || "Family";
    });
    editor.addEventListener("submit", async (event) => {
      event.preventDefault();
      const patientId = document.querySelector("#mindmap-data")?.dataset.patientId || "1";
      const body = {
        patient_id: Number(patientId),
        label: editor.elements.label.value.trim(),
        description: editor.elements.description.value.trim(),
        category: editor.elements.category.value,
      };
      if (!body.label) return;
      const response = await fetch("/api/mindmap/nodes", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfToken},
        body: JSON.stringify(body),
      });
      if (response.ok) {
        editorStatus.textContent = "Memory node added.";
        editor.reset();
        load();
      } else {
        editorStatus.textContent = "Caregiver sign-in is required.";
      }
    });

    document.querySelector("#delete-selected-node").addEventListener("click", async () => {
      if (!selected || !selected.id) return;
      if (!window.confirm("Delete this memory node and its connections?")) return;
      const response = await fetch(`/api/mindmap/nodes/${selected.id}`, {
        method: "DELETE",
        headers: {"X-CSRF-Token": csrfToken},
      });
      if (response.ok) {
        editorStatus.textContent = "Memory node deleted.";
        load();
      } else {
        editorStatus.textContent = "Caregiver sign-in is required.";
      }
    });

    document.querySelector("#update-selected-node").addEventListener("click", async () => {
      if (!selected || !selected.id) {
        editorStatus.textContent = "Select a memory node to update.";
        return;
      }
      const body = {
        label: editor.elements.label.value.trim(),
        description: editor.elements.description.value.trim(),
        category: editor.elements.category.value,
      };
      if (!body.label) return;
      const response = await fetch(`/api/mindmap/nodes/${selected.id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfToken},
        body: JSON.stringify(body),
      });
      if (response.ok) {
        editorStatus.textContent = "Memory node updated.";
        load();
      } else {
        editorStatus.textContent = "Caregiver sign-in is required.";
      }
    });

    document.querySelector("#connect-selected-nodes").addEventListener("click", async () => {
      const patientId = document.querySelector("#mindmap-data")?.dataset.patientId || "1";
      const source = document.querySelector("#edge-source").value;
      const target = document.querySelector("#edge-target").value;
      if (!source || !target) return;
      const response = await fetch("/api/mindmap/edges", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfToken},
        body: JSON.stringify({
          patient_id: Number(patientId),
          source: Number(source),
          target: Number(target),
        }),
      });
      editorStatus.textContent = response.ok
        ? "Memory connection added."
        : "Caregiver sign-in is required.";
      if (response.ok) load();
    });
  }
  load();
})();