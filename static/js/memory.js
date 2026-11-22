(() => {
  const button = document.querySelector("#memory-film");
  if (!button) return;
  button.addEventListener("click", () => {
    const cards = [...document.querySelectorAll(".memory-photo")];
    let index = 0;
    cards.forEach((card) => card.classList.remove("is-playing"));
    const play = () => {
      cards.forEach((card) => card.classList.remove("is-playing"));
      cards[index].classList.add("is-playing");
      cards[index].scrollIntoView({behavior: "smooth", block: "center"});
      index = (index + 1) % cards.length;
    };
    play();
    const interval = window.setInterval(play, 3000);
    button.textContent = "Pause Memory Film";
    button.onclick = () => {
      window.clearInterval(interval);
      button.textContent = "Play Memory Film";
    };
  });
})();