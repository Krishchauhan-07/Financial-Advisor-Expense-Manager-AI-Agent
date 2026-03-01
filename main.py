from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Import our modular services (we will create these next)
from services.pdf_service import extract_text_from_pdf
from services.ocr_service import extract_text_from_image
from services.link_service import extract_text_from_link
from services.llm_service import generate_financial_advice

load_dotenv()

app = FastAPI(title="AI Financial Advisor API")

# Setup CORS to allow the frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    context: str = ""
    api_key: str = None  # Optional field if user passes key from UI

class LinkRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Nexus Financial Advisor Backend is running!"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Handles chat messages and uses LLM to generate advice."""
    try:
        # User can pass API key directly from UI, otherwise we use .env
        api_key = request.api_key if request.api_key else os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="API Key not provided. Set it in .env or the UI.")

        # Construct prompt adding context if any document was parsed
        combined_prompt = request.message
        if request.context:
            combined_prompt = f"Context from uploaded document/link:\n{request.context}\n\nUser query: {request.message}"

        advice = generate_financial_advice(combined_prompt, api_key)
        return {"response": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Extract text from uploaded PDF."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    try:
        content = await file.read()
        text = extract_text_from_pdf(content)
        return {"filename": file.filename, "extracted_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Extract text from uploaded Image (OCR)."""
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG)")
    try:
        content = await file.read()
        text = extract_text_from_image(content)
        return {"filename": file.filename, "extracted_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/link")
async def parse_link(request: LinkRequest):
    """Extract text from a URL."""
    try:
        text = extract_text_from_link(request.url)
        return {"url": request.url, "extracted_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
