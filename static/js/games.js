(() => {
  const feedback = document.querySelector("#game-feedback");
  const difficulty = document.querySelector("#difficulty");
  if (!feedback || !difficulty) return;
  const roundStatus = document.createElement("p");
  roundStatus.setAttribute("aria-live", "polite");
  feedback.insertAdjacentElement("afterend", roundStatus);

  const loadRound = async (game) => {
    const response = await fetch(`/api/games/${game}/round?difficulty=${difficulty.value}`);
    if (!response.ok) return;
    const round = await response.json();
    if (game === "pattern") {
      roundStatus.textContent = `Pattern: ${round.sequence.join(" → ")}`;
    } else if (game === "attention") {
      roundStatus.textContent = `${round.stars} stars are shown. Notice the glowing star.`;
    } else {
      roundStatus.textContent = `Memory target: ${round.target}`;
    }
  };

  let activeGame = "picture-match";
  document.querySelectorAll("[data-game]").forEach((card) => {
    card.addEventListener("click", () => {
      activeGame = card.dataset.game;
      document.querySelector("#game-console-title").textContent =
        card.querySelector("h2").textContent;
      feedback.textContent = activeGame === "picture-match"
        ? "Choose the picture that feels familiar."
        : "Choose the gentle action that comes next.";
      loadRound(activeGame);
    });
  });

  document.querySelectorAll("[data-answer]").forEach((button) => {
    button.addEventListener("click", async () => {
      const correct = activeGame === "picture-match"
        ? button.dataset.answer === "Garden"
        : button.dataset.answer === "Family";
      feedback.textContent = correct
        ? "Lovely work. You found the familiar place."
        : "No problem. Let's try another gentle look.";
      await fetch(`/api/games/${activeGame}/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]')?.content || "",
        },
        body: JSON.stringify({score: correct ? 100 : 50, difficulty: Number(difficulty.value)}),
      });
    });
  });
})();