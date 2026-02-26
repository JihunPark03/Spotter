import { API } from "./config.js";

// Handles evaluation flow on eval.html with bilingual UI

document.addEventListener("DOMContentLoaded", () => {
  const textBox = document.getElementById("text");
  const statusEl = document.createElement("div");
  statusEl.id = "eval-status";
  statusEl.style.marginTop = "12px";
  statusEl.style.fontSize = "0.9rem";
  statusEl.style.color = "#2b2b2b";
  textBox.parentElement.appendChild(statusEl);

  const tabCheckText = document.getElementById("tabCheckText");
  const tabEvalText = document.getElementById("tabEvalText");
  const reviewTitle = document.getElementById("reviewTitle");
  const isAdBtn = document.getElementById("isAdBtn");
  const confirmBtn = document.getElementById("confirmBtn");
  const langToggle = document.getElementById("langToggle");
  const langToggleLabel = document.getElementById("langToggleLabel");

  const STRINGS = {
    ko: {
      placeholder: "리뷰를 드래그해서 선택하세요.",
      selectFirst: "텍스트를 먼저 선택해 주세요.",
      savedAd: "광고로 저장했습니다.",
      savedReal: "일반 리뷰로 저장했습니다.",
      saveFail: "저장에 실패했습니다.",
      reviewTitle: "인식된 리뷰",
      tabCheck: "리뷰 검사하기",
      tabEval: "리뷰 평가하기",
      isAdBtn: "광고 같아요",
      confirmBtn: "직접 쓴 리뷰같아요",
      langToggleLabel: "언어 변경",
    },
    en: {
      placeholder: "Highlight a review to analyze.",
      selectFirst: "Please select text first.",
      savedAd: "Saved as advertisement.",
      savedReal: "Saved as genuine review.",
      saveFail: "Failed to save.",
      reviewTitle: "Detected Review",
      tabCheck: "Check Review",
      tabEval: "Evaluate Reviews",
      isAdBtn: "Looks like an ad",
      confirmBtn: "Looks genuine",
      langToggleLabel: "Switch language",
    },
  };

  let currentLang = "ko";
  let PLACEHOLDER = STRINGS[currentLang].placeholder;

  const setStatus = (msg) => {
    statusEl.textContent = msg;
  };

  const setPlaceholderIfNeeded = () => {
    if (!textBox.textContent || textBox.classList.contains("placeholder") || textBox.textContent === PLACEHOLDER) {
      textBox.textContent = PLACEHOLDER;
      textBox.classList.add("placeholder");
    }
  };

  const applyLanguage = (lang) => {
    if (!STRINGS[lang]) lang = "ko";
    currentLang = lang;
    PLACEHOLDER = STRINGS[currentLang].placeholder;
    const t = STRINGS[currentLang];

    document.documentElement.lang = currentLang;
    if (tabCheckText) tabCheckText.innerHTML = `📝<b> ${t.tabCheck}</b>`;
    if (tabEvalText) tabEvalText.innerHTML = `📊<b> ${t.tabEval}</b>`;
    if (reviewTitle) reviewTitle.textContent = t.reviewTitle;
    if (isAdBtn) isAdBtn.textContent = t.isAdBtn;
    if (confirmBtn) confirmBtn.textContent = t.confirmBtn;
    if (langToggleLabel) langToggleLabel.textContent = currentLang === "ko" ? "EN" : "KO";
    if (langToggle) langToggle.setAttribute("aria-label", t.langToggleLabel);
    setPlaceholderIfNeeded();
    chrome.storage.local.set({ uiLang: currentLang });
  };

  const FEEDBACK_URL = API.FEEDBACK;

  // Load previously selected text from storage (set in popup.js)
  chrome.storage.local.get(["selectedText", "uiLang"], ({ selectedText, uiLang }) => {
    if (uiLang && STRINGS[uiLang]) currentLang = uiLang;
    PLACEHOLDER = STRINGS[currentLang].placeholder;
    applyLanguage(currentLang);

    const clean = (selectedText || "").trim();
    if (clean) {
      textBox.textContent = clean;
      textBox.classList.remove("placeholder");
    } else {
      textBox.textContent = PLACEHOLDER;
      textBox.classList.add("placeholder");
    }
  });

  const submitFeedback = async (isAdFlag) => {
    const inputText = (textBox.textContent || "").trim();
    if (!inputText || textBox.classList.contains("placeholder")) {
      setStatus(STRINGS[currentLang].selectFirst);
      return;
    }
    try {
      const res = await fetch(FEEDBACK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText, is_ad: isAdFlag }),
      });
      if (!res.ok) throw new Error(await res.text());
      setStatus(isAdFlag ? STRINGS[currentLang].savedAd : STRINGS[currentLang].savedReal);
    } catch (err) {
      console.error("Feedback save failed:", err);
      setStatus(STRINGS[currentLang].saveFail);
    }
  };

  if (isAdBtn) isAdBtn.addEventListener("click", () => submitFeedback(true));
  if (confirmBtn) confirmBtn.addEventListener("click", () => submitFeedback(false));
  if (langToggle) {
    langToggle.addEventListener("click", () => {
      const next = currentLang === "ko" ? "en" : "ko";
      applyLanguage(next);
    });
  }
});
