(() => {
  const feedback = document.querySelector("#game-feedback");
  const difficulty = document.querySelector("#difficulty");
  if (!feedback || !difficulty) return;

  document.querySelectorAll("[data-answer]").forEach((button) => {
    button.addEventListener("click", async () => {
      const correct = button.dataset.answer === "Garden";
      feedback.textContent = correct
        ? "Lovely work. You found the familiar place."
        : "No problem. Let's try another gentle look.";
      await fetch("/api/games/picture-match/session", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({score: correct ? 100 : 50, difficulty: Number(difficulty.value)}),
      });
    });
  });
})();