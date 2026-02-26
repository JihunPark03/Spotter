import { API } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
  // ===== DOM cache =====
  const textBox = document.getElementById("text");
  const sendBtn = document.getElementById("send");
  const resultEl = document.getElementById("result");
  const numberEl = document.getElementById("number");

  const PLACEHOLDER = "리뷰를 드래그해서 선택하세요.";

  // ===== In-memory cache (popup session) =====
  // key: text string
  // val: { gemReply: string, gemCached?: boolean, score?: number, detectCached?: boolean, ts: number }
  const memCache = new Map();

  // ===== Request de-dupe (same text -> share promise) =====
  // key: text string
  // val: { gemP: Promise<any>, detP: Promise<any> }
  const inflightByText = new Map();

  // AbortController for the *current* click (if user clicks multiple times quickly)
  let currentAbort = null;

  // ===== Small helpers =====
  const setStatus = (msg) => {
    // Optional: if you have a status element, you can use it
    // For now, we reuse resultEl when empty
    if (!resultEl.textContent || resultEl.textContent === PLACEHOLDER) {
      resultEl.textContent = msg;
    }
  };

  const setLoadingUI = () => {
    // show fast feedback immediately
    resultEl.textContent = "처리 중...";
    if (numberEl) numberEl.textContent = "";
    // if you have progress bar, you can also reset it here:
    if (typeof window.updateProgress === "function") {
      window.updateProgress(0);
    }
  };

  const showGemini = (reply) => {
    resultEl.textContent = reply || "응답이 없습니다.";
  };

  const showScore = (score) => {
    const safeScore = Number.isFinite(score) ? score : 0;

    if (typeof window.updateProgress === "function") {
      window.updateProgress(safeScore);
      return;
    }
    if (numberEl) numberEl.textContent = String(safeScore);
  };

  const normalizeSelectedText = (t) => (t || "").trim();

  const sameAsPlaceholder = (t) => !t || t === PLACEHOLDER;

  // Cache policy: keep only recent (avoid memory blow-up if user selects tons of text)
  const CACHE_TTL_MS = 2 * 60 * 1000; // 2 min
  const CACHE_MAX = 20;

  const cleanupCache = () => {
    const now = Date.now();
    for (const [k, v] of memCache.entries()) {
      if (!v?.ts || now - v.ts > CACHE_TTL_MS) memCache.delete(k);
    }
    // if still too big, drop oldest
    if (memCache.size > CACHE_MAX) {
      const entries = [...memCache.entries()].sort((a, b) => a[1].ts - b[1].ts);
      const toRemove = memCache.size - CACHE_MAX;
      for (let i = 0; i < toRemove; i++) memCache.delete(entries[i][0]);
    }
  };

  const cachePut = (text, patch) => {
    const prev = memCache.get(text) || { ts: Date.now() };
    const merged = { ...prev, ...patch, ts: Date.now() };
    memCache.set(text, merged);
    cleanupCache();
    return merged;
  };

  // ===== Selection loading =====
  const loadSelectionIntoTextBox = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (!tab?.id) {
        textBox.textContent = PLACEHOLDER;
        textBox.classList.add("placeholder");
        return;
      }

      chrome.scripting.executeScript(
        {
          target: { tabId: tab.id },
          func: () => window.getSelection().toString(),
        },
        (results) => {
          const selectedText = results?.[0]?.result ?? "";
          const cleanText = normalizeSelectedText(selectedText);

          if (cleanText) {
            textBox.textContent = cleanText;
            textBox.classList.remove("placeholder");
            chrome.storage.local.set({ selectedText: cleanText });
          } else {
            chrome.storage.local.get("selectedText", ({ selectedText }) => {
              const fallback = normalizeSelectedText(selectedText) || PLACEHOLDER;
              textBox.textContent = fallback;
              textBox.classList.toggle("placeholder", fallback === PLACEHOLDER);
            });
          }
        }
      );
    });
  };

  loadSelectionIntoTextBox();

  // ===== Networking =====
  const postJSON = async (url, bodyStr, signal) => {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: bodyStr,
      signal,
      // keepalive can help if popup closes quickly (limited support for POST)
      // keepalive: true,
    });

    // Try to parse error body too
    if (!res.ok) {
      let detail = "";
      try {
        const t = await res.text();
        detail = t ? ` (${t.slice(0, 200)})` : "";
      } catch (_) {}
      throw new Error(`HTTP ${res.status}${detail}`);
    }
    return res.json();
  };

  const getOrStartInflight = (text, signal) => {
    // De-dupe: if same text is already being processed, reuse promises.
    const existing = inflightByText.get(text);
    if (existing) return existing;

    const payload = JSON.stringify({ text });

    const gemP = postJSON(API.GEMINI, payload, signal);
    const detP = postJSON(API.DETECT_AD, payload, signal);

    const pair = { gemP, detP };
    inflightByText.set(text, pair);

    // Cleanup inflight entry after both settle
    Promise.allSettled([gemP, detP]).then(() => {
      // only delete if still the same pair (avoid race with new request for same text)
      const cur = inflightByText.get(text);
      if (cur === pair) inflightByText.delete(text);
    });

    return pair;
  };

  // ===== Click handler =====
  const onSend = async () => {
    const inputText = normalizeSelectedText(textBox.textContent);

    if (sameAsPlaceholder(inputText)) {
      resultEl.innerText = "텍스트를 먼저 선택해 주세요.";
      return;
    }

    // Abort previous in-flight request for this popup session
    if (currentAbort) currentAbort.abort();
    currentAbort = new AbortController();

    setLoadingUI();

    // Instant response if cached
    const cached = memCache.get(inputText);
    if (cached && Date.now() - cached.ts <= CACHE_TTL_MS) {
      if (cached.gemReply) showGemini(cached.gemReply);
      if (typeof cached.score === "number") showScore(cached.score);
      // Still optionally refresh in background? (Popup code can't truly background-run reliably)
      // We'll just return for max speed.
      return;
    }

    try {
      const { gemP, detP } = getOrStartInflight(inputText, currentAbort.signal);

      // Render Gemini as soon as ready
      gemP
        .then((gem) => {
          const reply = gem?.reply || "응답이 없습니다.";
          cachePut(inputText, { gemReply: reply, gemCached: !!gem?.cached });
          showGemini(reply);
          if (gem?.cached) console.log("Gemini: cache hit");
        })
        .catch((e) => {
          // If aborted, do nothing
          if (e?.name === "AbortError") return;
          console.error("Gemini Error:", e);
          // Don't overwrite if user already got a reply from another run
          resultEl.textContent = "서버 오류가 발생했습니다.";
        });

      // Render score as soon as ready
      detP
        .then((rate) => {
          const score = Number(rate?.prob_ad ?? 0);
          cachePut(inputText, { score, detectCached: !!rate?.cached });
          showScore(score);
          if (rate?.cached) console.log("Detect-ad: cache hit");
        })
        .catch((e) => {
          if (e?.name === "AbortError") return;
          console.error("Detect-ad Error:", e);
          // Score failing shouldn't kill Gemini result; just show a small hint
          if (numberEl) numberEl.textContent = "점수 오류";
        });

      // Optionally wait for both if you need to coordinate (not required for speed)
      // await Promise.allSettled([gemP, detP]);

    } catch (err) {
      if (err?.name === "AbortError") return;
      console.error("API Error:", err);
      resultEl.textContent = "서버 오류가 발생했습니다.";
    }
  };

  sendBtn.addEventListener("click", onSend);

  // Bonus: allow Enter key to send (if your popup supports it)
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") onSend();
  });

  // Abort when popup is closing (best effort)
  window.addEventListener("beforeunload", () => {
    if (currentAbort) currentAbort.abort();
  });
});
