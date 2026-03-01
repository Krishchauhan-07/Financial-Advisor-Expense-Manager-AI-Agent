# AI Financial Advisor - Agentic AI

A full-stack, AI-powered financial advisor application. It connects a beautiful frontend UI to a powerful Python backend capable of analyzing text, reading PDFs, extracting data from websites, and leveraging LLMs to provide financial insights.

## Project Structure

- `/frontend` - HTML/CSS/JS files for the UI.
- `/backend` - FastAPI application providing the API endpoints.

## Features

- **Document Reading:** Upload PDF documents or images (via OCR).
- **Link Scraping:** Pass a URL to extract and analyze its contents.
- **Agentic Advice:** Uses LLMs to give personalized financial advice based on your data.
- **Custom API Keys:** Securely manage your API keys via `.env` or the UI.

## Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API Key (or other LLM provider)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your keys.
5. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Open `frontend/index.html` in your browser.
2. Ensure you have the backend running so the frontend can communicate with the APIs.
