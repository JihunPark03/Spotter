from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for API key and log warning if missing
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY not found in environment variables!")

# Configure Google AI with API key if available
if api_key:
    genai.configure(api_key=api_key)

app = FastAPI(title="Spotter API", 
              description="Backend API for the Spotter Chrome Extension")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your extension's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.get("/")
async def root():
    """Health check endpoint to verify the API is running."""
    return {"status": "online", "message": "Spotter API is running"}

@app.post("/gemini")
async def send_to_gemini(request: TextRequest):
    """Send text to Gemini API for processing."""
    user_input = request.text

    if not user_input:
        return JSONResponse(
            status_code=400,
            content={"reply": "No input provided."}
        )

    # Check if API key is configured
    if not api_key:
        return JSONResponse(
            status_code=500, 
            content={"reply": "API key not configured. Please set the GOOGLE_API_KEY environment variable."}
        )

    try:
        # Load system prompt from file
        try:
            with open("gemini_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.warning("gemini_prompt.txt not found, using default prompt")
            system_prompt = "You are a helpful assistant that analyzes reviews."

        # Initialize the model
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Generate content
        logger.info(f"Sending request to Gemini API with text: {user_input[:50]}...")
        response = model.generate_content(
            [
                {"role": "user", "parts": [system_prompt]},
                {"role": "user", "parts": [user_input]}
            ]
        )
        
        logger.info(f"Successfully received response from Gemini API: {response.text}")
        return {"reply": response.text}
    
    except Exception as e:
        logger.error(f"Error while processing Gemini request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"reply": f"Error: {str(e)}"}
        )

# Add this to make the app runnable with uvicorn directly from this file
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
