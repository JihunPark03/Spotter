# Spotter: Review Verification Platform

**A Chrome Extension to detect advertising reviews and show only reliable reviews**  
Based on the GDGoC Korea X Japan The Bridge Hackathon presentation. citeturn0file0

---

## Background

- Travelers rely heavily on online reviews for travel planning:
  - 95% of travelers refer to online reviews before booking.
  - On average, tourists read 6–7 reviews and spend about 30 minutes doing so.  
- However, review credibility has declined due to:
  - **Sponsored and misleading blog posts** – influencers failing to clearly label paid content.
  - **AI-generated and paid reviews** – apps like “Misik” create reviews for rewards.
  - **Review-swapping and paid search manipulation**.  
- Generation Z especially blocks ads and seeks authentic, honest reviews.  
  **Insight:** Gen Z consumers need services to help them identify honest reviews and avoid advertisements.

---

## Key Features

1. **Chrome Extension**  
   - Validate reviews anywhere on the web with a simple drag-and-drop.  
2. **Explainable AI**  
   - **Model Choice 1:** Pre-trained KO-BERT  
     - F1-Score: 98% (2,080 Naver review texts)  
   - **Model Choice 2:** LSTM + Attention  
     - F1-Score: 99%  
     - Attention mechanism highlights keywords for interpretability.  
3. **Gemini API Integration**  
   - Query filtering, feature extraction, and similarity analysis with Gemini.  
   - Recommend shops and restaurants based on authenticated reviews.  

---

## Architecture Overview

1. **User Query**  
2. **Query Filtering / Feature Extraction** via Spotter & Gemini  
3. **Similarity Analysis** against backend database  
4. **Recommendations** of shops/restaurants with reliable reviews  

---

## Getting Started

### Installation

1. Install the Spotter Chrome Extension.  
2. Pin the extension to your browser toolbar.

### Usage

1. **Step 1:** Open any page with user reviews.  
2. **Step 2:** Drag the text of a review into the Spotter popup to analyze it.  
3. **Step 3:** View the binary classification and AI-generated summary:  
   - Icons and colors indicate review authenticity and confidence.  
4. **Step 4:** Search for places by type and location; read only verified, reliable reviews.

---

## Expansion & Community Contributions

- **Validate Others' Reviews:**  
  - Contribute by verifying and uploading results to improve service reliability.  
- **More Accurate Reviews:**  
  - View reviews from the **same place**, **nearby restaurants**, or **similar restaurants**.  
- **Multilingual Support:**  
  - Offer Korean, English, and Japanese interfaces to expand overseas tourist users.  

---

## Team Members

- **GEONWOO KIM (Yonsei U.)** – AI/ML/DL Engineer  
- **Sungwon Jeon (Korea U.)** – UX/UI Designer  
- **Jaeseung Lee (Korea U.)** – Project Manager / Web Frontend  
- **Jihun Park (Waseda U.)** – Web Frontend / Backend Engineer  

---

## Acknowledgements

Thank you for trying out Spotter!  
감사합니다. ありがとうございます。

---

_Source: GDGoC.pdf – Spotter presentation_ citeturn0file0
