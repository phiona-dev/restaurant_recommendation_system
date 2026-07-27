/**
 * Kahoot-style preference quiz (ported from Epimetheus PlayerQuizViewController flow).
 * One question at a time → collect prefs → POST to /quiz/submit.
 */

const OPTION_COLORS = [
  { bg: "bg-red-500 hover:bg-red-600", ring: "ring-red-300" },
  { bg: "bg-blue-500 hover:bg-blue-600", ring: "ring-blue-300" },
  { bg: "bg-amber-400 hover:bg-amber-500", ring: "ring-amber-200" },
  { bg: "bg-emerald-500 hover:bg-emerald-600", ring: "ring-emerald-300" },
];

let currentIndex = 0;
let collectedPrefs = {};
let hasAnswered = false;
let timerInterval = null;

const segmentEl = document.getElementById("segment-label");
const categoryEl = document.getElementById("category-label");
const questionEl = document.getElementById("question-text");
const timerEl = document.getElementById("timer-label");
const progressEl = document.getElementById("progress-bar");
const optionsEl = document.getElementById("answer-container");
const statusEl = document.getElementById("status-label");
const quizCardEl = document.getElementById("quiz-card");

function updateProgress() {
  const total = QUESTIONS.length;
  const pct = ((currentIndex) / total) * 100;
  progressEl.style.width = `${pct}%`;
}

function clearTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function startTimer(seconds) {
  clearTimer();
  let remaining = seconds;
  timerEl.textContent = remaining;
  timerEl.classList.remove("text-red-500", "animate-pulse");
  timerEl.classList.add("text-white");

  timerInterval = setInterval(() => {
    remaining -= 1;
    timerEl.textContent = remaining;

    if (remaining <= 5) {
      timerEl.classList.remove("text-white");
      timerEl.classList.add("text-red-500", "animate-pulse");
    }

    if (remaining <= 0) {
      clearTimer();
      handleTimeout();
    }
  }, 1000);
}

function handleTimeout() {
  if (hasAnswered) return;
  const q = QUESTIONS[currentIndex];
  const firstOption = q.options[0];
  handleAnswer(firstOption.prefs, true);
}

function showLockedFeedback() {
  statusEl.textContent = "Locked in!";
  statusEl.classList.remove("hidden", "text-gray-400");
  statusEl.classList.add("text-emerald-400");
}

function loadQuestion() {
  if (currentIndex >= QUESTIONS.length) {
    submitQuiz();
    return;
  }

  const q = QUESTIONS[currentIndex];
  hasAnswered = false;

  segmentEl.textContent = `Question ${currentIndex + 1} / ${QUESTIONS.length}`;
  categoryEl.textContent = q.category || "Preferences";
  questionEl.textContent = q.questionText;
  statusEl.textContent = "LIVE";
  statusEl.classList.remove("hidden", "text-emerald-400", "text-red-400");
  statusEl.classList.add("text-amber-400");

  optionsEl.innerHTML = "";
  optionsEl.classList.remove("pointer-events-none", "opacity-60");

  q.options.forEach((opt, i) => {
    const colors = OPTION_COLORS[i % OPTION_COLORS.length];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `quiz-option w-full text-left text-white font-bold text-lg px-6 py-5 rounded-2xl shadow-lg transition-all duration-150 transform hover:scale-[1.02] active:scale-[0.98] ring-2 ring-transparent hover:${colors.ring} ${colors.bg}`;
    btn.innerHTML = `<span class="opacity-80 mr-2">${String.fromCharCode(65 + i)}</span>${opt.label}`;
    btn.addEventListener("click", () => handleAnswer(opt.prefs, false));
    optionsEl.appendChild(btn);
  });

  updateProgress();
  startTimer(q.timeLimitSeconds || 15);
}

function handleAnswer(prefs, timedOut) {
  if (hasAnswered) return;
  hasAnswered = true;
  clearTimer();

  Object.assign(collectedPrefs, prefs);
  optionsEl.classList.add("pointer-events-none", "opacity-60");

  if (timedOut) {
    statusEl.textContent = "Time's up — default saved";
    statusEl.classList.remove("text-amber-400");
    statusEl.classList.add("text-red-400");
  } else {
    showLockedFeedback();
  }

  currentIndex += 1;

  setTimeout(() => {
    if (currentIndex >= QUESTIONS.length) {
      submitQuiz();
    } else {
      loadQuestion();
    }
  }, timedOut ? 800 : 500);
}

async function submitQuiz() {
  clearTimer();
  quizCardEl.classList.add("opacity-50", "pointer-events-none");
  statusEl.textContent = "Finding your matches...";
  statusEl.classList.remove("text-amber-400", "text-emerald-400");
  statusEl.classList.add("text-orange-400");

  try {
    const response = await fetch("/quiz/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectedPrefs),
    });

    if (!response.ok) {
      throw new Error("Submit failed");
    }

    const html = await response.text();
    document.open();
    document.write(html);
    document.close();
  } catch (err) {
    quizCardEl.classList.remove("opacity-50", "pointer-events-none");
    statusEl.textContent = "Something went wrong. Please try again.";
    statusEl.classList.add("text-red-400");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (typeof QUESTIONS !== "undefined" && QUESTIONS.length > 0) {
    loadQuestion();
  }
});
