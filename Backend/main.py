# ──────────────────────────────────────────────────────────────
# main.py   (Spotter API v0.3.0)
# ──────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging, os
from pathlib import Path
from dotenv import load_dotenv

# [NEW SDK IMPORT]
from google import genai
from google.genai import types
from ad_model.inference import predict_prob
import hashlib
from typing import Dict, Any
import cosine_db
import time



# ──────────────── Basic Settings ────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# [NEW SDK CLIENT INIT]
# The client is reusable. We initialize it once if the key exists.
client = None
if not api_key:
    logger.warning("GOOGLE_API_KEY not found in environment variables!")
else:
    client = genai.Client(api_key=api_key)

app = FastAPI(
    title="Spotter API",
    description="Backend API for the Spotter Chrome Extension",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ──────────────── Pydantic Models ────────────────
class RecommendationRequest(BaseModel):
    shop_type: str = Field(..., example="식당", description="숙박 | 식당 | 미용")
    user_text: str

class GeminiRequest(BaseModel):
    text: str

class AdDetectRequest(BaseModel):
    text: str

class AdDetectResponse(BaseModel):
    prob_ad: float
    is_ad: bool
    cached: bool

# ──────────────── Utils ────────────────
PROMPT_PATH = Path("gemini_prompt.txt")

def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("gemini_prompt.txt not found - fallback prompt used")
        return (
            "You are an extractor that outputs exactly four '-키: 값' lines "
            "(must include location)."
        )
    
# ──────────────── Utils: Cache ────────────────
CACHE_TTL = 60 * 60 
CACHE: Dict[str, Dict[str, Any]] = {}

def make_cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

def get_cache(key: str):
    entry = CACHE.get(key)
    if not entry:
        return None

    if time.time() > entry["expires_at"]:
        del CACHE[key]
        return None

    return entry["data"]

def set_cache(key: str, data: dict):
    CACHE[key] = {
        "data": data,
        "expires_at": time.time() + CACHE_TTL
    }

# ──────────────── Endpoints ────────────────
@app.get("/")
async def root():
    return {"status": "online", "message": "Spotter API is running (GenAI v2)"}

@app.post("/detect-ad", response_model=AdDetectResponse)
async def detect_ad(req: AdDetectRequest):
    text = req.text.strip()
    if not text:
        return JSONResponse(status_code=400, content={"detail": "Empty text"})
    
    key = make_cache_key(text)
    cached = get_cache(key)
    if cached and "prob_ad" in cached:
        return {
            **cached,
            "cached": True
        }

    prob = predict_prob(text)
    result = {
        "prob_ad": round(prob, 4) * 100,
        "is_ad": prob >= 0.5
    }

    set_cache(key, result)

    return {
        **result,
        "cached": False
    }

@app.post("/gemini")
async def extract_features(req: GeminiRequest):
    user_text = req.text.strip()
    if not user_text:
        return JSONResponse(status_code=400, content={"reply": "Empty user_text"})

    if not client:
        return JSONResponse(status_code=500, content={"reply": "API key not set"})

    key = make_cache_key(user_text)

    cached = get_cache(key)
    if cached and "reply" in cached:
        return {
            "reply": cached["reply"],
            "cached": True
        }

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=_load_system_prompt(),
                temperature=0.0
            )
        )

        result = {"reply": response.text}
        set_cache(key, result)

        return {
            **result,
            "cached": False
        }

    except Exception as e:
        logger.exception("Gemini extraction failed")
        return JSONResponse(status_code=500, content={"reply": str(e)})


@app.post("/recommendations")
async def get_recommendations(req: RecommendationRequest):
    user_text = req.user_text.strip()
    if not client:
        return JSONResponse(status_code=500, content={"detail": "API key not set"})

    # 1) User Intent Extraction
    try:
        # [NEW SDK USAGE]
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=_load_system_prompt()
            )
        )
        feat_txt = response.text
        
        user_feats = cosine_db.parse_feature_output(feat_txt)
    except Exception as e:
        logger.exception("Feature extraction failed")
        return JSONResponse(status_code=500, content={"detail": str(e)})

    # 2) DB Similarity Recommendation
    try:
        result = cosine_db.recommend_shops(
            shop_type = req.shop_type,
            user_features = user_feats,
            top_k = 3,
            save_path = Path("output/recommendations.json"),
        )
        return result
    except Exception as e:
        logger.exception("Recommendation failed")
        return JSONResponse(status_code=500, content={"detail": str(e)})

# ──────────────── Local Run ────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
