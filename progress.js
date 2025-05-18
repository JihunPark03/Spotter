// progress.js (가독성 겸 오류 방지용 개선본)
document.addEventListener("DOMContentLoaded", updateProgress);

async function updateProgress() {
    const barEl   = document.getElementById("progressBar");
    const labelEl = document.getElementById("number");
    const MAX = 100;
  
    /* 실제 API → let { value } = await (await fetch("/api/score")).json(); */
    let value = 19;                       // 테스트용
  
    const pct = Math.min(Math.max(value, 0), MAX) / MAX * 100;
  
    /* 길이 변경 */
    barEl.style.width = `${pct}%`;
    labelEl.textContent = `${pct.toFixed(0)}%`;
  
    /* ❶ 이전 단계(class) 제거 */
    barEl.classList.remove("a", "b", "c", "d", "e");
  
    /* ❷ 새 단계(class) 부여 */
    if      (pct < 20) barEl.classList.add("a");
    else if (pct < 40) barEl.classList.add("b");
    else if (pct < 60) barEl.classList.add("c");
    else if (pct < 80) barEl.classList.add("d");
    else               barEl.classList.add("e");
  }
  
  document.addEventListener("DOMContentLoaded", updateProgress);
  
