# ──────────────────────────────────────────────────────────────
# main.py
# ──────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging, os
from dotenv import load_dotenv
import google.generativeai as genai

# ──────────────── 1) 기본 설정 ────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY not found in environment variables!")
else:
    genai.configure(api_key=api_key)

# cosine_db 는 genai 초기화 이후 import (순환참조 방지)
import cosine_db  # noqa: E402

app = FastAPI(
    title="Spotter API",
    description="Backend API for the Spotter Chrome Extension",
    version="0.2.0",
)

# CORS (개발용 - 프로덕션에서는 origin 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ──────────────── 2) Pydantic 모델 ────────────────
class TextRequest(BaseModel):
    text: str = Field(..., example="청결하고 저렴한 제주도 맛집 찾아줘")

class RecommendationRequest(TextRequest):
    shop_type: str = Field(
        ...,
        example="식당",
        description="숙박 | 식당 | 미용 중 하나 선택"
    )

# ──────────────── 3) 공통 유틸 ────────────────
def _load_system_prompt() -> str:
    try:
        with open("gemini_prompt.txt", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("gemini_prompt.txt not found - fallback prompt 사용")
        return (
            "You are an extractor that outputs exactly four '-키: 값' lines "
            "(must include location)."
        )

# ──────────────── 4) 엔드포인트 ────────────────
@app.get("/")
async def root():
    return {"status": "online", "message": "Spotter API is running"}

@app.post("/gemini")
async def extract_features(req: TextRequest):
    if not api_key:
        return JSONResponse(status_code=500, content={"reply": "API key not set"})
    if not req.text.strip():
        return JSONResponse(status_code=400, content={"reply": "No input provided."})

    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = _load_system_prompt()

    try:
        rsp = model.generate_content([
            {"role": "user", "parts": [prompt]},
            {"role": "user", "parts": [req.text]},
        ])
        return {"reply": rsp.text}
    except Exception as e:
        logger.exception("Gemini extraction failed")
        return JSONResponse(status_code=500, content={"reply": str(e)})

@app.post("/recommendations")
async def get_recommendations(req: RecommendationRequest):
    if not api_key:
        return JSONResponse(status_code=500, content={"detail": "API key not set"})

    # 1) 사용자 의도 4-feature 추출
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = _load_system_prompt()
    try:
        feat_txt = model.generate_content([
            {"role": "user", "parts": [prompt]},
            {"role": "user", "parts": [req.text]},
        ]).text
        user_feats = cosine_db.parse_feature_output(feat_txt)
    except Exception as e:
        logger.exception("Feature extraction 실패")
        return JSONResponse(status_code=500, content={"detail": str(e)})

    # 2) DB 유사도 기반 추천
    try:
        result = cosine_db.recommend_shops(
            shop_type=req.shop_type,
            user_features=user_feats,
            top_k=3,
        )
        return result
    except Exception as e:
        logger.exception("Recommendation 실패")
        return JSONResponse(status_code=500, content={"detail": str(e)})

# ──────────────── 5) 로컬 실행 ────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
