// Handles language toggle and strings for eval_home.html

const STRINGS = {
  ko: {
    tabCheck: "리뷰 검사하기",
    tabEval: "리뷰 평가하기",
    hero: "더 정확한 판단을 할 수 있도록<br>리뷰를 평가해주세요!",
    startBtn: "시작하기",
    langToggleLabel: "언어 변경",
  },
  en: {
    tabCheck: "Check Review",
    tabEval: "Evaluate Reviews",
    hero: "Help us improve accuracy by<br>rating reviews!",
    startBtn: "Start",
    langToggleLabel: "Switch language",
  },
};

let currentLang = "ko";

const tabCheckText = document.getElementById("tabCheckText");
const tabEvalText = document.getElementById("tabEvalText");
const heroTitle = document.getElementById("heroTitle");
const startBtn = document.getElementById("startBtn");
const langToggle = document.getElementById("langToggle");
const langToggleLabel = document.getElementById("langToggleLabel");

const applyLanguage = (lang) => {
  if (!STRINGS[lang]) lang = "ko";
  currentLang = lang;
  const t = STRINGS[currentLang];
  document.documentElement.lang = currentLang;
  if (tabCheckText) tabCheckText.innerHTML = `📝<b> ${t.tabCheck}</b>`;
  if (tabEvalText) tabEvalText.innerHTML = `📊<b> ${t.tabEval}</b>`;
  if (heroTitle) heroTitle.innerHTML = t.hero;
  if (startBtn) startBtn.textContent = t.startBtn;
  if (langToggleLabel) langToggleLabel.textContent = currentLang === "ko" ? "EN" : "KO";
  if (langToggle) langToggle.setAttribute("aria-label", t.langToggleLabel);
  chrome.storage.local.set({ uiLang: currentLang });
};

chrome.storage.local.get("uiLang", ({ uiLang }) => {
  if (uiLang && STRINGS[uiLang]) currentLang = uiLang;
  applyLanguage(currentLang);
});

if (langToggle) {
  langToggle.addEventListener("click", () => {
    const next = currentLang === "ko" ? "en" : "ko";
    applyLanguage(next);
  });
}
