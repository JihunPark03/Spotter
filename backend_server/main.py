# ──────────────────────────────────────────────────────────────
# main.py   (Spotter API v0.3.0)
# ──────────────────────────────────────────────────────────────
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging, os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

# [NEW SDK IMPORT]
from google import genai
from services.detect_service import detect_ad as detect_service
from services.gemini_service import extract_features as gemini_service
from services.feedback_service import FeedbackService
from repositories.feedback_repository import FeedbackRepository
from db_init import get_db, create_tables



# ──────────────── Basic Settings ────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    create_tables()
    yield  # Allow FastAPI to start
    print("FastAPI is shutting down...")  # Shutdown logic (optional)
    

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
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ──────────────── Pydantic Models ────────────────
class GeminiRequest(BaseModel):
    text: str

class AdDetectRequest(BaseModel):
    text: str

class AdDetectResponse(BaseModel):
    prob_ad: float
    is_ad: bool
    cached: bool

class FeedbackRequest(BaseModel):
    text: str
    is_ad: bool

# ──────────────── Endpoints ────────────────
@app.get("/")
async def root():
    return {"status": "online", "message": "Spotter API is running (GenAI v2)"}

@app.post("/detect-ad", response_model=AdDetectResponse)
async def detect_ad(req: AdDetectRequest):
    text = req.text.strip()
    if not text:
        return JSONResponse(status_code=400, content={"detail": "Empty text"})

    return detect_service(text)

@app.post("/feedback")
async def save_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    service = FeedbackService(FeedbackRepository(db))
    try:
        fb = service.save_feedback(req.text, req.is_ad)
        return {"status": "ok", "id": fb.id}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"detail": str(ve)})
    except Exception:
        logger.exception("Failed to save feedback")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to save feedback"},
        )

@app.post("/gemini")
async def extract_features(req: GeminiRequest):
    user_text = req.text.strip()
    if not user_text:
        return JSONResponse(status_code=400, content={"reply": "Empty user_text"})

    if not client:
        return JSONResponse(status_code=500, content={"reply": "API key not set"})

    try:
        result = gemini_service(user_text, client)
        return result
    except Exception as e:
        logger.exception("Gemini extraction failed")
        return JSONResponse(status_code=500, content={"reply": str(e)})


@app.post("/recommendations")
async def get_recommendations():
    return JSONResponse(
        status_code=501,
        content={"detail": "Recommendation system disabled in this deployment."}
    )

# ──────────────── Local Run ────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
