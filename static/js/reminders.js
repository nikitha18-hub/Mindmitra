(() => {
  document.querySelectorAll("[data-complete]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = button.closest(".reminder-item");
      item.classList.toggle("completed");
      button.textContent = item.classList.contains("completed") ? "Completed" : "Mark complete";
    });
  });
})();