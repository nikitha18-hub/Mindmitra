(() => {
  const orb = document.querySelector("#voice-orb");
  const status = document.querySelector("#voice-status");
  const form = document.querySelector("#voice-text-form");
  if (!orb || !status || !form) return;

  orb.addEventListener("click", () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      status.textContent = "Voice recognition is not available here. Please type below.";
      document.querySelector("#voice-text").focus();
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "en-IN";
    recognition.onstart = () => {
      orb.classList.add("listening");
      status.textContent = "Listening...";
    };
    recognition.onresult = (event) => {
      document.querySelector("#voice-text").value = event.results[0][0].transcript;
      status.textContent = "Voice question added.";
    };
    recognition.onend = () => orb.classList.remove("listening");
    recognition.onerror = () => {
      orb.classList.remove("listening");
      status.textContent = "Voice was not available. Please type instead.";
    };
    recognition.start();
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = form.querySelector("input");
    status.textContent = input.value.trim()
      ? "MindMitra received your question."
      : "Please type a question first.";
  });
})();