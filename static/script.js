// script.js — Trait-based psychological profiler with backend POST

function nextSection(current) {
  const currentSection = document.getElementById(`section-${current}`);
  const nextSection = document.getElementById(`section-${current + 1}`);

  const selects = currentSection.querySelectorAll('select');
  for (let select of selects) {
    if (!select.value) {
      alert("Please answer all questions in this section before moving on.");
      return;
    }
  }

  currentSection.classList.add("hidden");
  nextSection.classList.remove("hidden");
}

const form = document.getElementById("quizForm");
form.addEventListener("submit", function (e) {
  e.preventDefault();

  const data = new FormData(form);
  const answers = Object.fromEntries(data.entries());

  let traits = {
    grief: 0,
    rage: 0,
    control: 0,
    numb: 0,
    secrecy: 0,
    obsession: 0,
    compassion: 0,
    trauma: 0,
    envy: 0,
    chaos: 0,
    revenge: 0
  };

  const { motive, timing, weapon, emotion, echo, body, texted } = answers;

  if (motive === "abandonment") traits.grief++, traits.trauma++;
  if (motive === "envy") traits.envy++;
  if (motive === "boundary") traits.rage++;
  if (motive === "identity") traits.trauma++;

  if (timing === "planned") traits.control++;
  if (timing === "snapped") traits.rage++, traits.chaos++;
  if (timing === "conversation") traits.control++;
  if (timing === "public") traits.chaos++;

  if (weapon === "gun") traits.numb++, traits.control++;
  if (weapon === "knife") traits.rage++, traits.envy++;
  if (weapon === "hands") traits.rage++, traits.trauma++;
  if (weapon === "poison") traits.control++;

  if (emotion === "nothing") traits.numb++;
  if (emotion === "power") traits.rage++;
  if (emotion === "disgust") traits.trauma++;
  if (emotion === "relief") traits.grief++;

  if (echo === "silence") traits.numb++;
  if (echo === "laughter") traits.envy++;
  if (echo === "heartbeat") traits.control++;
  if (echo === "screams") traits.trauma++;

  if (body === "burned") traits.rage++;
  if (body === "buried") traits.control++;
  if (body === "message") traits.chaos++;
  if (body === "hidden") traits.secrecy++;

  if (texted === "burner") traits.secrecy++, traits.control++;
  if (texted === "victim") traits.obsession++;
  if (texted === "normal") traits.control++;

  let result = "🔮 The Quiet God — You watch from shadows, pulling strings you never admit exist.";

  if (traits.numb >= 3 && traits.control >= 2) {
    result = "🧊 The Surgical Ghost — You don’t scream. You execute. You’re the absence of chaos, and that’s what terrifies them.";
  } else if (traits.grief >= 2 && traits.trauma >= 2) {
    result = "🩸 The Devourer in Disguise — You touch to hold, but you destroy to feel.";
  } else if (traits.envy >= 2 && traits.rage >= 1) {
    result = "🕷️ The Silk-Wrapped Monster — Beauty and pain wrapped in a single gesture.";
  } else if (traits.control >= 3 && traits.secrecy >= 2) {
    result = "🔮 The Quiet God — You never speak your plans. You only let them unfold.";
  } else if (traits.obsession >= 1 && traits.rage >= 2) {
    result = "🧨 The Lover Who Snapped — You couldn’t have them. So no one would.";
  } else if (traits.trauma >= 2 && traits.rage === 0 && traits.numb === 0) {
    result = "🧬 The Wound-Mirror — You didn’t just kill them. You killed the echo of your past.";
  } else if (traits.grief >= 2 && traits.rage === 0) {
    result = "🔪 The Empathic Butcher — You felt it all too deeply. So you lit the memory on fire.";
  } else if (traits.chaos >= 3 && traits.rage >= 2) {
    result = "🦴 The Ritual Breaker — Rules are cages. Your blood sings only in chaos.";
  } else if (traits.revenge >= 2 || (traits.rage >= 2 && traits.control >= 2)) {
    result = "🦂 The Collector of Sins — Every pain they gave you... you returned in silence.";
  } else {
    result = "🕯️ The Ritualist — You make violence an art, each drop a spell.";
  }

  // Full profile object

const archetypeTraits = {
  "🧊 The Surgical Ghost — You don’t scream. You execute. You’re the absence of chaos, and that’s what terrifies them.": [
    "emotionally detached",
    "highly analytical",
    "avoids intimacy",
    "needs control",
    "suppresses feelings",
    "cold to other",
    "trusts logic not emotion",
    "avoids vulnerability",
    "fears connection",
    "uses silence as power"
  ],
  "🩸 The Devourer in Disguise — You touch to hold, but you destroy to feel.": [
    "obsessed with love",
    "fears being left",
    "needs constant closeness",
    "gets jealous fast",
    "controls through affection",
    "needy but hides it",
    "hurts others emotionally",
    "can't be alone",
    "intense in relationships",
    "blends love with pain"
  ],
  "🕷️ The Silk-Wrapped Monster — Beauty and pain wrapped in a single gesture.": [
    "wants to be admired",
    "hides anger",
    "uses beauty to control",
    "manipulates emotions",
    "feels easily rejected",
    "holds grudges",
    "acts superior",
    "afraid of being ignored",
    "punishes with silence",
    "attention-seeking through charm"
  ],
  "🦂 The Collector of Sins — Every pain they gave you... you returned in silence.": [
    "remembers every hurt",
    "doesn’t forgive",
    "avoids talking about emotions",
    "waits for revenge",
    "feels used",
    "hides feelings",
    "keeps emotional distance",
    "cold toward others",
    "takes everything personally",
    "fears being powerless"
  ],
  "🧨 The Lover Who Snapped — You couldn’t have them. So no one would.": [
    "gets obsessed with people",
    "can’t handle rejection",
    "extreme emotions",
    "loves too hard too fast",
    "loses control when hurt",
    "needs to feel wanted",
    "angry when ignored",
    "confused love with pain", 
    "emotional outbursts", 
    "jealous and possessive"
  ],
  "🧬 The Wound-Mirror — You didn’t just kill them. You killed the echo of your past.": [
    "connects through pain", 
    "puts others first", 
    "avoids conflict", 
    "carries old hurt", 
    "helps others but forgets self",
    "feels invisible", 
    "drawn to broken people", 
    "doesn’t ask for help", 
    "holds sadness quietly",
    "scared of being a burden"
  ],
  "🧒 The Hollowed Child — You buried yourself before they could bury you.": [
    "emotionally numb",
    "avoids growing up",
    "fears responsibility",
    "stuck in the past",
    "doesn’t trust anyone",
    "feels abandoned",
    "lost identity",
    "depends on others",
    "hides true feelings",
    "scared of being alone"
  ],
  "👁 The Oracle of Rot — You turned pain into prophecy, but forgot how to live.": [
    "sees meaning in pain",
    "trusts instincts over logic",
    "paranoid thoughts",
    "feels cursed",
    "drawn to darkness",
    "isolates often",
    "can’t let go of trauma",
    "sees betrayal everywhere",
    "speaks in symbols",
    "avoids reality"
  ],
  "🪞 The Puppet with Sharp Strings — You followed the script so long, you forgot how to speak.": [
    "controlled by others",
    "seeks approval",
    "hides real thoughts",
    "blames self for everything",
    "easily manipulated",
    "scared to disobey",
    "angry deep down",
    "feels used",
    "acts polite but resents it",
    "wants to escape expectations"
  ],
  "🎭 The Painted Cage — You smiled too long, and no one noticed you were drowning.": [
    "acts perfect in public",
    "hides breakdowns",
    "follows rules to be loved",
    "fears being exposed",
    "performs happiness",
    "depends on image",
    "feels trapped in life",
    "fears judgment",
    "covers pain with smiles",
    "hides true self"
  ]
};

  const profile = {
    name:        answers.name,
    city:        answers.city,
    archetype:   archetype,
    traits:      traits,        // {grief:1, rage:2, control:3 ...} — stored as columns
    raw_answers: answers        // full answers kept for reference
  };
 
  fetch('/api/save', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile)
  })
  .then(r => r.json())
  .then(data => console.log("Saved:", data))
  .catch(err => console.error("Error saving:", err));
 
  // Show result to user
  document.getElementById("quizForm").classList.add("hidden");
  const resultDiv = document.getElementById("result");
  resultDiv.innerHTML = `<h2>Your Archetype:</h2><p><strong>${archetype}</strong></p>`;
  resultDiv.classList.remove("hidden");
});