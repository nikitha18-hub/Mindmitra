(() => {
  const root = document.documentElement;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    root.dataset.calmMode = "true";
  }
})();
