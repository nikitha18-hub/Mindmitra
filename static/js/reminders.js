(() => {
  document.querySelectorAll("[data-complete]").forEach((button) => {
    button.addEventListener("click", async () => {
      const item = button.closest(".reminder-item");
      const completed = !item.classList.contains("completed");
      const response = await fetch(`/api/reminders/${button.dataset.id}/complete`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]')?.content || "",
        },
        body: JSON.stringify({complete: completed}),
      });
      if (!response.ok) return;
      item.classList.toggle("completed", completed);
      button.textContent = completed ? "Completed" : "Mark complete";
    });
  });
})();