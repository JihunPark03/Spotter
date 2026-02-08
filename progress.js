// progress.js (가독성 겸 오류 방지용 개선본)
function updateProgress(value) {
    const barEl   = document.getElementById("progressBar");
    const labelEl = document.getElementById("number");
    const MAX = 100;

    // 값이 전달되지 않았다면 현재 라벨 텍스트를 숫자로 재사용
    const safeValue = Number(value ?? labelEl?.textContent ?? 0);
    const pct = Math.min(Math.max(safeValue, 0), MAX);
  
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
  
  // 초기 로드 시 현재 표시된 숫자를 이용해 그리기
  document.addEventListener("DOMContentLoaded", () => updateProgress());
  
  // popup.js에서 재호출할 수 있도록 전역에 노출
  window.updateProgress = updateProgress;
  
