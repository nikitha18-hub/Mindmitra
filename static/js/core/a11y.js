(() => {
  const root = document.documentElement;
  const toggle = document.querySelector("[data-calm-toggle]");

  if (!toggle) return;

  const storedPreference = window.localStorage.getItem("mindmitra-calm-mode");
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const shouldStartCalm = storedPreference === "true" || (storedPreference === null && prefersReducedMotion);

  const applyCalmMode = (enabled) => {
    root.dataset.calmMode = String(enabled);
    toggle.setAttribute("aria-pressed", String(enabled));
    toggle.querySelector(".calm-toggle-label").textContent =
      enabled ? "Calm Mode: On" : "Calm Mode: Off";
  };

  applyCalmMode(shouldStartCalm);

  toggle.addEventListener("click", () => {
    const enabled = root.dataset.calmMode !== "true";
    window.localStorage.setItem("mindmitra-calm-mode", String(enabled));
    applyCalmMode(enabled);
  });
})();
