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

  const reminderForm = document.querySelector("#caregiver-reminder-form");
  if (reminderForm) {
    reminderForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = document.querySelector("#caregiver-form-status");
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
      const response = await fetch("/api/reminders", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfToken},
        body: JSON.stringify({
          title: reminderForm.elements.title.value.trim(),
          time_label: reminderForm.elements.time_label.value,
        }),
      });
      const result = await response.json();
      status.textContent = response.ok ? "Reminder added." : (result.error || "Could not add reminder.");
      if (response.ok) reminderForm.reset();
    });
  }
})();