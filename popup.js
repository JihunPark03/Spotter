document.addEventListener("DOMContentLoaded", () => {
  const textBox = document.getElementById("text");

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
    const url = "http://3.106.143.90:8000/gemini";

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await res.json();
      document.getElementById("result").innerText = data.reply || "응답이 없습니다.";
    } catch (err) {
      console.error("API Error:", err);
      document.getElementById("result").innerText = "서버 오류가 발생했습니다.";
    }
  });
});
