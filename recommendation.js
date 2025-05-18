document.addEventListener("DOMContentLoaded", () => {
  const resultDiv = document.getElementById("result");
  const sendBtn = document.getElementById("send");
  const textArea = document.getElementById("text");

  sendBtn.addEventListener("click", async () => {
    console.log("버튼 눌림");
    resultDiv.innerHTML = ""; // 결과 초기화

    // --- [1] 사용자 입력 확인 및 JSON 저장 ---
    const userInput = textArea.value.trim();
    if (!userInput) {
      alert("내용을 입력해주세요.");
      return;
    }

    const jsonData = {
      입력내용: userInput,
      timestamp: new Date().toISOString()
    };

    const jsonString = JSON.stringify(jsonData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "user_input.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    resultDiv.innerHTML = `<p><strong>입력한 내용이 JSON 파일로 저장되었습니다.</strong></p>`;

    // --- [2] 5초 대기 후 추천 요청 ---
    await new Promise((resolve) => setTimeout(resolve, 5000));

    try {
      const response = await fetch("/recommendations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({}) // shop_type 생략 가능
      });

      if (!response.ok) {
        resultDiv.innerHTML += "<p>추천 생성 실패</p>";
        return;
      }

      resultDiv.innerHTML += "<p><strong>추천 요청 전송 완료. 결과를 기다리는 중...</strong></p>";
    } catch (error) {
      console.error("추천 생성 에러:", error);
      resultDiv.innerHTML += "<p>추천 생성 중 에러 발생</p>";
      return;
    }

    // --- [3] 추가로 5초 대기 후 결과 불러오기 ---
    await new Promise((resolve) => setTimeout(resolve, 5000));

    try {
      const response = await fetch("output/recommendations.json");
      const data = await response.json();

      if (!Array.isArray(data)) {
        resultDiv.innerHTML += "<p>잘못된 결과 형식입니다.</p>";
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

      resultDiv.appendChild(list);
    } catch (error) {
      console.error("Error loading result.json:", error);
      resultDiv.innerHTML += "<p>결과를 불러오는 데 실패했습니다.</p>";
    }
  });
});
