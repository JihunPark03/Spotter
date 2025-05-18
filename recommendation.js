// recommendation.js

document.addEventListener("DOMContentLoaded", () => {
    const resultDiv = document.getElementById("result");
    const sendBtn = document.getElementById("send");
  
    sendBtn.addEventListener("click", async () => {
      console.log("버튼 눌림"); 
      resultDiv.innerHTML = ""; // 결과 초기화
  
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
  
        resultDiv.appendChild(list);
      } catch (error) {
        console.error("Error loading result.json:", error);
        resultDiv.innerHTML = "<p>결과를 불러오는 데 실패했습니다.</p>";
      }
    });
  });
  