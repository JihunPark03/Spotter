document.addEventListener("DOMContentLoaded", () => {
  const textBox = document.getElementById("text");//popup html의 text id에 표시

  // Get selected text from current tab
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tab.id },
        func: () => window.getSelection().toString(),
      },
      ([{ result: selectedText }]) => {
        const cleanText = (selectedText || "").trim();

        if (cleanText) {
          textBox.textContent = cleanText;
          textBox.classList.remove("placeholder");
          chrome.storage.local.set({ selectedText: cleanText });
        } else {
          // Fallback: Use previously saved text or show default message
          chrome.storage.local.get("selectedText", ({ selectedText }) => {
            const fallback = selectedText || "리뷰를 드래그해서 선택하세요.";
            textBox.textContent = fallback;
            textBox.classList.add("placeholder");
          });
        }
      }
    );
  });

  // Handle send button click
  document.getElementById("send").addEventListener("click", async () => {
    const inputText = textBox.textContent.trim();

    if (!inputText || inputText === "리뷰를 드래그해서 선택하세요.") {
      document.getElementById("result").innerText = "텍스트를 먼저 선택해 주세요.";
      return;
    }
    //local
    // const url1 = "http://localhost:8000/gemini";
    // const url2 = "http://localhost:8000/detect-ad";

    //server
    const url1 = "http://34.174.35.119:8000/gemini";
    const url2 = "http://34.174.35.119:8000/detect-ad";

    try {
      const res = await fetch(url1, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });
      const res1 = await fetch(url2, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });

      const gem_data = await res.json();
      document.getElementById("result").innerText = gem_data.reply || "응답이 없습니다.";
      if (gem_data.cached) {
          console.log("Gemini: cache hit");
      }

      const rate_data = await res1.json();
      if (rate_data.cached) {
        console.log("Detect-ad: cache hit");
      }
      const score = Number(rate_data.prob_ad ?? 0);
      // progress.js에 정의된 함수 재사용 → 추가 API 호출 없이 바 업데이트
      if (typeof window.updateProgress === "function") {
        window.updateProgress(score);
      } else {
        document.getElementById("number").innerText = rate_data.prob_ad || "응답이 없습니다.";
      }

    } catch (err) {
      console.error("API Error:", err);
      document.getElementById("result").innerText = "서버 오류가 발생했습니다.";
    }
  });
});
