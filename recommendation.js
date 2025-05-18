document.addEventListener("DOMContentLoaded", () => {
  const resultDiv = document.getElementById("result");
  const sendBtn = document.getElementById("send");

  sendBtn.addEventListener("click", async () => {
    console.log("버튼 눌림");
    resultDiv.innerHTML = "<p>5초 후 추천 결과를 가져옵니다...</p>";

    // 5초 대기 후 fetch 실행
    setTimeout(async () => {
      try {
        const response = await fetch("result.json");
        const data = await response.json();

        if (!Array.isArray(data)) {
          resultDiv.innerHTML = "<p>잘못된 결과 형식입니다.</p>";
          return;
        }

        const list = document.createElement("ol");
        list.style.paddingLeft = "1.2em";

        data.forEach((item) => {
          const li = document.createElement("li");
          li.innerHTML = `<strong>가게: ${item["가게"]}</strong><br/>
                          이유: ${item["이유"]}<br/>
                          리뷰: ${item["리뷰"]}`;
          li.style.marginBottom = "1em";
          list.appendChild(li);
        });

        resultDiv.innerHTML = ""; // 이전 메시지 제거
        resultDiv.appendChild(list);

        // ✅ 삭제 요청 보내기
        await fetch("/delete-result", {
          method: "DELETE",
        });
        console.log("result.json 삭제 요청 보냄");
      } catch (error) {
        console.error("Error loading result.json:", error);
        resultDiv.innerHTML = "<p>결과를 불러오는 데 실패했습니다.</p>";
      }
    }, 5000); // 5초 (5000ms) 지연
  });
});
