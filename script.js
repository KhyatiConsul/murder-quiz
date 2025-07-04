document.getElementById('quizForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const motive = quizForm.motive.value;
  const weapon = quizForm.weapon.value;
  const emotion = quizForm.emotion.value;

  let result = "";

  if (motive === "abandonment" && weapon === "hands") {
    result = "🩸 The Devourer in Disguise — You touch to hold, but you destroy to feel.";
  } else if (motive === "envy" && weapon === "knife") {
    result = "🕷️ The Silk-Wrapped Monster — Beauty and pain wrapped in a single gesture.";
  } else if (emotion === "nothing" && weapon === "gun") {
    result = "🧊 The Surgical Ghost — You don’t kill for rage. You kill to remind the world you’re real.";
  } else if (motive === "boundary" && weapon === "poison") {
    result = "🕯️ The Ritualist — You make violence an art, each drop a spell.";
  } else {
    result = "🔮 The Quiet God — You watch from shadows, pulling strings you never admit exist.";
  }

  const resultDiv = document.getElementById('result');
  resultDiv.innerText = result;
  resultDiv.classList.remove('hidden');
});
