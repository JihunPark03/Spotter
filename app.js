// app.js
async function init() {
    try {
      // 백엔드에서 숫자를 가져온다. (예: /api/score 가 { "value": 73 } 반환)
    //   const res   = await fetch("/api/score");
    //   const data  = await res.json();
    //   const value = data.value;
    value = 19; // 테스트용
  
      // 요소 선택
      const numberEl  = document.getElementById("number");
      const messageEl = document.getElementById("message");
  
      // 숫자 자체 출력

      numberEl.textContent = value;
  
      /* 값에 따라 분기 */
      if (value >= 80) {
        messageEl.textContent = "스스로 작성한 리뷰예요";
        messageEl.className   = "80";
      } else if (value >= 60) {
        messageEl.textContent = "어느 정도 직접 작성했어요";
        messageEl.className   = "60";
      } else if (value >= 40) {
        messageEl.textContent = "부분적으로 직접 작성했어요";
        messageEl.className   = "40";
      } else if (value >= 20) {
        messageEl.textContent = "광고로 의심되는 문구가 있어요"
        messageEl.className   = "20";
      } else {
        messageEl.textContent = "직접 작성하지 않은 광고 리뷰예요";
        messageEl.className   = "0";
      }
  
    } catch (err) {
      console.error(err);
    }
  }
  
  document.addEventListener("DOMContentLoaded", init);
  