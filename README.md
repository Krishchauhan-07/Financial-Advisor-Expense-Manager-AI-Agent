# 💰 FinAdvisor AI — Personal Financial Advisor & Expense Manager

An AI-powered financial assistant that extracts expenses from payment screenshots, provides personalized advice inspired by top financial gurus, and offers India-specific planning tools including tax calculators and SIP recommenders.

## Features
- 📸 **OCR Expense Extraction** — Upload PhonePe/GPay/Paytm screenshots
- 💡 **AI Financial Advisor** — Chat-based advice powered by LangChain + GPT (modern v0.2+ API)
- 📊 **Spending Analytics** — Category breakdown, trends, budget tracking
- 📚 **Book Q&A** — Upload financial books (PDFs) and ask questions
- 🇮🇳 **India-Specific Tools** — Tax calculator, SIP recommender, 80C planner
- 📑 **Export** — Download CSV and PDF financial reports

## Tech Stack
- Frontend: Streamlit
- Backend: Python, LangChain, SQLite & SQLAlchemy
- OCR: Tesseract + OpenCV
- LLM: OpenAI GPT-4o-mini
- Charts: Plotly

## Setup
```bash
git clone https://github.com/YOUR_USERNAME/financial-advisor-ai.git
cd financial-advisor-ai
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
streamlit run app.py
```

## Running Locally

Once configured, run the following command to start the app:

```bash
python -m streamlit run app.py
```

## Configuration

If using OCR, you need to install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) on your system.
By default, the path is expected to be `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows.
You can configure this in your `.env` file if it's placed differently.

Set your `OPENAI_API_KEY` in the `.env` file for AI advice and RAG Q&A functionalities to work.

## Disclaimer
This tool provides educational financial guidance only. It is not a SEBI-registered
financial advisor. Please consult a certified professional for investment decisions.

---

*Built with ❤️ as part of Capabl AI Agent Development Project*  
*Track A — Essential | 8 Weeks | Financial Technology Domain*
