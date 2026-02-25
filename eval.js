import { API } from "./config.js";

// Handles evaluation flow on eval.html

document.addEventListener("DOMContentLoaded", () => {
  const textBox = document.getElementById("text");
  const statusEl = document.createElement("div");
  statusEl.id = "eval-status";
  statusEl.style.marginTop = "12px";
  statusEl.style.fontSize = "0.9rem";
  statusEl.style.color = "#2b2b2b";
  textBox.parentElement.appendChild(statusEl);

  const setStatus = (msg) => {
    statusEl.textContent = msg;
  };

  const PLACEHOLDER = "리뷰를 드래그해서 선택하세요.";

  const FEEDBACK_URL = API.FEEDBACK;

  // Load previously selected text from storage (set in popup.js)
  chrome.storage.local.get("selectedText", ({ selectedText }) => {
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
      setStatus("텍스트를 먼저 선택해 주세요.");
      return;
    }
    try {
      const res = await fetch(FEEDBACK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText, is_ad: isAdFlag }),
      });
      if (!res.ok) throw new Error(await res.text());
      setStatus(isAdFlag ? "광고로 저장했습니다." : "일반 리뷰로 저장했습니다.");
    } catch (err) {
      console.error("Feedback save failed:", err);
      setStatus("저장에 실패했습니다.");
    }
  };

  const isAdBtn = document.querySelector(".btn.isAd");
  const confirmBtn = document.querySelector(".btn.confirm");
  if (isAdBtn) isAdBtn.addEventListener("click", () => submitFeedback(true));
  if (confirmBtn) confirmBtn.addEventListener("click", () => submitFeedback(false));
});
