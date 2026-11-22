(() => {
  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!window.confirm(button.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      document.documentElement.dataset.pageVisible = "false";
    } else {
      document.documentElement.dataset.pageVisible = "true";
    }
  });
})();