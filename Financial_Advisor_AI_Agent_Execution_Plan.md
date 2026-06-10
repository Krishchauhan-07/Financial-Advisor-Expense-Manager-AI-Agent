# 💰 Financial Advisor & Expense Manager AI Agent
## Complete 8-Week Execution Plan — Track A

**Team Size:** 3–4 Students | **Track:** A (Essential) | **Duration:** 8 Weeks  
**Domain:** Personal Finance Assistant + Expense Tracking Agent  
**Stack:** Python · LangChain · Streamlit · OCR · SQLite · OpenAI/Gemini

---

## 📋 Table of Contents

1. [Project Architecture Overview](#project-architecture-overview)
2. [Tech Stack & Setup](#tech-stack--setup)
3. [Week 1–2: Foundation & Quick Win](#week-12-foundation--quick-win)
4. [Week 3–4: Core Financial Advisory Architecture](#week-34-core-financial-advisory-architecture)
5. [Week 5–6: Domain Specialization (Option A1 — Indian Finance Advisor)](#week-56-domain-specialization)
6. [Week 7–8: Polish & Production](#week-78-polish--production)
7. [Database Schema](#database-schema)
8. [Folder Structure](#folder-structure)
9. [API Configuration Guide](#api-configuration-guide)
10. [Testing Checklist](#testing-checklist)
11. [Deployment Instructions](#deployment-instructions)
12. [README Template](#readme-template)

---

## Project Architecture Overview

```
User Interface (Streamlit)
        │
        ▼
   Agent Orchestrator (LangChain)
        │
   ┌────┴──────────────────────────┐
   │                               │
OCR Tool                   Financial Advice Tool
(Tesseract / Google Vision)   (LLM + Financial DB)
   │                               │
Expense Parser              Guru Philosophy Engine
   │                               │
   └──────────┬────────────────────┘
              │
        SQLite Database
        (Expenses, Budgets, Goals)
              │
        Streamlit Dashboard
        (Charts, Reports, Advice)
```

The system follows a pipeline architecture:
1. **Input Layer** — Users upload payment screenshots, CSVs, or enter data manually
2. **Processing Layer** — OCR extracts text; regex + LLM parses transactions
3. **Storage Layer** — SQLite stores categorized expenses, budgets, and goals
4. **Advisory Layer** — LangChain agent queries financial knowledge base and generates personalized advice
5. **Output Layer** — Streamlit displays dashboards, charts, and recommendations

---

## Tech Stack & Setup

### Core Dependencies

```txt
# requirements.txt

# Framework
streamlit==1.32.0
langchain==0.1.16
langchain-openai==0.1.3
langchain-community==0.0.34
openai==1.20.0

# OCR & Image Processing
pytesseract==0.3.10
Pillow==10.3.0
opencv-python==4.9.0.80
google-cloud-vision==3.7.0     # optional (paid)

# Data Processing
pandas==2.2.2
numpy==1.26.4
PyPDF2==3.0.1
pdfplumber==0.11.0

# Visualization
matplotlib==3.8.4
plotly==5.21.0
altair==5.3.0

# Database
sqlalchemy==2.0.30

# Expense & Finance
splitwise==2.0.0               # optional
python-dotenv==1.0.1
requests==2.31.0

# Utilities
regex==2024.4.16
python-dateutil==2.9.0
```

### Environment Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Tesseract OCR (system-level)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

# MacOS:
brew install tesseract

# Windows:
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

# 4. Create .env file
touch .env
```

### .env Configuration

```env
# .env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
GOOGLE_VISION_API_KEY=xxxxxxxxxxxx     # optional
SPLITWISE_CONSUMER_KEY=xxxxxxx         # optional
SPLITWISE_CONSUMER_SECRET=xxxxxxx      # optional
DATABASE_URL=sqlite:///financial_data.db
```

---

## Week 1–2: Foundation & Quick Win

**Goal:** Get basic expense extraction and financial advice working. Deploy a live version by end of Week 2.

---

### Day 1–2: GitHub Repository & Project Structure

**Step 1: Initialize GitHub Repository**

```bash
# Initialize repository
git init financial-advisor-ai
cd financial-advisor-ai
git remote add origin https://github.com/YOUR_USERNAME/financial-advisor-ai.git

# Create .gitignore
cat > .gitignore << EOF
.env
*.db
__pycache__/
.streamlit/secrets.toml
venv/
*.pyc
.DS_Store
EOF
```

**Step 2: Create Project Structure**

```bash
mkdir -p {src,data,assets,tests,docs,notebooks}
mkdir -p src/{ocr,parser,database,advisory,ui,utils}
touch src/__init__.py
touch src/ocr/__init__.py
touch src/parser/__init__.py
touch src/database/__init__.py
touch src/advisory/__init__.py
touch src/ui/__init__.py
touch src/utils/__init__.py
```

Full folder structure is described in the [Folder Structure](#folder-structure) section.

---

### Day 3–4: OCR Module — Screenshot Expense Extraction

**File:** `src/ocr/extractor.py`

This module is the heart of the expense extraction pipeline. It accepts uploaded images (payment screenshots from PhonePe, Google Pay, Paytm, bank SMS, etc.) and extracts raw text using Tesseract OCR.

```python
# src/ocr/extractor.py

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io
from pathlib import Path


class OCRExtractor:
    """
    Handles OCR extraction from payment screenshots and financial documents.
    Supports: JPEG, PNG, WebP image formats.
    Preprocessing improves accuracy on low-resolution phone screenshots.
    """

    def __init__(self, tesseract_path: str = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply image preprocessing to improve OCR accuracy.
        Steps: grayscale → contrast boost → noise removal → thresholding
        """
        # Convert to grayscale
        img_array = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Adaptive thresholding for better contrast
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(thresh, -1, kernel)

        return Image.fromarray(sharpened)

    def extract_text(self, image_bytes: bytes) -> dict:
        """
        Main extraction method. Returns raw text and confidence score.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            processed = self.preprocess_image(image)

            # Extract with confidence data
            data = pytesseract.image_to_data(
                processed,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )

            # Filter low-confidence words
            words = []
            confidences = []
            for i, word in enumerate(data['text']):
                conf = int(data['conf'][i])
                if conf > 30 and word.strip():
                    words.append(word)
                    confidences.append(conf)

            raw_text = pytesseract.image_to_string(
                processed, config='--psm 6'
            )

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "raw_text": raw_text,
                "confidence": round(avg_confidence, 2),
                "success": True,
                "word_count": len(words)
            }

        except Exception as e:
            return {
                "raw_text": "",
                "confidence": 0,
                "success": False,
                "error": str(e)
            }

    def extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bank statements."""
        import pdfplumber
        import io

        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
```

---

### Day 5–7: Transaction Parser — Categorization Engine

**File:** `src/parser/transaction_parser.py`

The parser converts raw OCR text into structured transaction objects. It handles UPI payment formats (PhonePe, Google Pay, Paytm), bank SMS formats (SBI, HDFC, ICICI), and manual entries.

```python
# src/parser/transaction_parser.py

import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from src.utils.categories import categorize_merchant


@dataclass
class Transaction:
    amount: float
    merchant: str
    category: str
    date: datetime
    payment_method: str
    transaction_type: str   # "debit" or "credit"
    raw_text: str
    confidence: float = 1.0


class TransactionParser:
    """
    Parses raw OCR text into structured Transaction objects.
    Supports:
      - UPI payment screenshots (PhonePe, GPay, Paytm)
      - Bank SMS messages (SBI, HDFC, ICICI)
      - Bank statement CSV rows
      - Manual text input
    """

    # Amount patterns: ₹1,234.56 | Rs. 500 | INR 2000
    AMOUNT_PATTERNS = [
        r'₹\s*[\d,]+\.?\d*',
        r'Rs\.?\s*[\d,]+\.?\d*',
        r'INR\s*[\d,]+\.?\d*',
        r'Paid\s+₹\s*[\d,]+\.?\d*',
        r'Debited.*?₹\s*[\d,]+\.?\d*',
        r'Amount[:\s]+₹?\s*[\d,]+\.?\d*',
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
    ]

    # Payment app identifiers
    PAYMENT_APPS = {
        'phonepe': 'PhonePe',
        'google pay': 'Google Pay',
        'gpay': 'Google Pay',
        'paytm': 'Paytm',
        'bhim': 'BHIM UPI',
        'upi': 'UPI',
        'neft': 'NEFT',
        'imps': 'IMPS',
        'rtgs': 'RTGS',
    }

    def parse(self, raw_text: str, confidence: float = 1.0) -> Optional[Transaction]:
        """Parse raw text into a Transaction object."""
        text_lower = raw_text.lower()

        amount = self._extract_amount(raw_text)
        if not amount:
            return None  # No amount = not a transaction

        merchant = self._extract_merchant(raw_text)
        date = self._extract_date(raw_text) or datetime.now()
        payment_method = self._extract_payment_method(text_lower)
        transaction_type = self._detect_transaction_type(text_lower)
        category = categorize_merchant(merchant, raw_text)

        return Transaction(
            amount=amount,
            merchant=merchant,
            category=category,
            date=date,
            payment_method=payment_method,
            transaction_type=transaction_type,
            raw_text=raw_text,
            confidence=confidence
        )

    def _extract_amount(self, text: str) -> Optional[float]:
        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract just the numeric part
                num_str = re.sub(r'[₹RsINRPaidDebitedAmount:\s]', '', match.group())
                num_str = num_str.replace(',', '')
                try:
                    return float(num_str)
                except ValueError:
                    continue
        return None

    def _extract_merchant(self, text: str) -> str:
        # Common patterns: "to [Name]", "paid to [Name]", "UPI-[Name]"
        patterns = [
            r'(?:to|paid to|sent to|transfer to)\s+([A-Z][A-Za-z\s&]+)',
            r'UPI[-/]([A-Za-z\s]+)[@]',
            r'(?:at|@)\s+([A-Z][A-Za-z\s]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]  # Limit length
        return "Unknown Merchant"

    def _extract_date(self, text: str) -> Optional[datetime]:
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group()
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%b %d, %Y', '%d/%m/%y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        return None

    def _extract_payment_method(self, text_lower: str) -> str:
        for key, value in self.PAYMENT_APPS.items():
            if key in text_lower:
                return value
        return "Unknown"

    def _detect_transaction_type(self, text_lower: str) -> str:
        debit_keywords = ['debited', 'paid', 'sent', 'transferred', 'withdrawn', 'purchase']
        credit_keywords = ['credited', 'received', 'refund', 'cashback', 'deposit']
        for word in debit_keywords:
            if word in text_lower:
                return 'debit'
        for word in credit_keywords:
            if word in text_lower:
                return 'credit'
        return 'debit'  # Default assumption
```

**File:** `src/utils/categories.py`

```python
# src/utils/categories.py

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "zomato", "swiggy", "restaurant", "cafe", "coffee", "pizza", "burger",
        "biryani", "dhaba", "hotel", "food", "kitchen", "bakery", "chai",
        "starbucks", "mcdonald", "dominos", "kfc", "subway"
    ],
    "Groceries": [
        "bigbasket", "grofers", "blinkit", "zepto", "grocery", "vegetables",
        "supermarket", "reliance fresh", "dmart", "more", "nature basket",
        "fruits", "milk", "sabji", "kirana"
    ],
    "Transport": [
        "ola", "uber", "rapido", "metro", "bus", "train", "irctc", "redbus",
        "petrol", "fuel", "auto", "taxi", "cab", "indigo", "spicejet",
        "flight", "airways", "parking"
    ],
    "Entertainment": [
        "netflix", "amazon prime", "hotstar", "spotify", "youtube", "movie",
        "pvr", "inox", "cinema", "theatre", "concert", "bookmyshow", "gaming"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "snapdeal",
        "shopping", "clothes", "fashion", "shoes", "accessories"
    ],
    "Healthcare": [
        "pharmacy", "hospital", "clinic", "doctor", "medicine", "apollo",
        "medplus", "1mg", "pharmeasy", "lab", "diagnostic", "health"
    ],
    "Utilities": [
        "electricity", "water", "gas", "internet", "broadband", "airtel",
        "jio", "vodafone", "bsnl", "recharge", "bill", "tata power"
    ],
    "Education": [
        "school", "college", "university", "course", "udemy", "coursera",
        "books", "fees", "tuition", "coaching", "upgrad", "unacademy"
    ],
    "Investment": [
        "zerodha", "groww", "upstox", "mutual fund", "sip", "stock",
        "insurance", "lic", "ppf", "nps", "fd", "rdrd"
    ],
    "Rent & Housing": [
        "rent", "housing", "pg", "maintenance", "society", "apartment"
    ],
}


def categorize_merchant(merchant: str, raw_text: str = "") -> str:
    """
    Categorize a transaction based on merchant name and surrounding text.
    Uses keyword matching against predefined categories.
    Returns 'Others' if no match found.
    """
    search_text = (merchant + " " + raw_text).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in search_text:
                return category

    return "Others"
```

---

### Day 8–10: Database Layer

**File:** `src/database/models.py`

```python
# src/database/models.py

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///financial_data.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    merchant = Column(String(100), default="Unknown")
    category = Column(String(50), default="Others")
    subcategory = Column(String(50), nullable=True)
    date = Column(DateTime, default=datetime.now)
    payment_method = Column(String(50), default="Unknown")
    transaction_type = Column(String(10), default="debit")
    notes = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    source = Column(String(30), default="manual")  # screenshot / csv / manual / splitwise
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.now)
    is_verified = Column(Boolean, default=False)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    month = Column(String(7), nullable=False)   # Format: YYYY-MM
    created_at = Column(DateTime, default=datetime.now)


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True)
    category = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_achieved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class FinancialTip(Base):
    __tablename__ = "financial_tips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guru = Column(String(50), nullable=False)
    principle = Column(String(200), nullable=False)
    advice = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    tags = Column(String(200), nullable=True)


def init_db():
    """Create all tables and seed financial tips."""
    Base.metadata.create_all(engine)
    _seed_financial_tips()


def _seed_financial_tips():
    """Populate initial financial wisdom database."""
    session = SessionLocal()
    existing = session.query(FinancialTip).count()
    if existing > 0:
        session.close()
        return

    tips = [
        FinancialTip(guru="Warren Buffett", principle="Pay Yourself First",
            advice="Save at least 20% of your income before spending on anything else. Invest in index funds for long-term wealth creation.",
            category="Savings", tags="savings,investing,discipline"),
        FinancialTip(guru="Warren Buffett", principle="Never Lose Money",
            advice="Rule #1: Never lose money. Rule #2: Never forget Rule #1. Focus on preserving capital before seeking returns.",
            category="Investment", tags="risk,capital,investment"),
        FinancialTip(guru="Robert Kiyosaki", principle="Assets vs Liabilities",
            advice="Rich people acquire assets (things that put money in your pocket). Poor people acquire liabilities. Focus on building assets through SIP, real estate, or business.",
            category="Investment", tags="assets,cashflow,wealth"),
        FinancialTip(guru="Robert Kiyosaki", principle="Financial Education",
            advice="The most important investment is in yourself. Learn about taxes, investing, and financial planning. Financial literacy is your greatest asset.",
            category="Education", tags="learning,financial literacy"),
        FinancialTip(guru="Ramit Sethi", principle="Automate Your Finances",
            advice="Set up automatic transfers to savings and investments on salary day. Remove the decision from the equation. A good SIP setup in Groww or Zerodha runs itself.",
            category="Automation", tags="automation,sip,savings"),
        FinancialTip(guru="Ramit Sethi", principle="Eliminate Invisible Spending",
            advice="Track every rupee for 30 days. Most people are shocked to find 20-30% of spending goes to forgotten subscriptions, small food orders, and impulse purchases.",
            category="Budgeting", tags="tracking,budgeting,awareness"),
        FinancialTip(guru="Indian Finance", principle="Emergency Fund First",
            advice="Build 3-6 months of expenses in a liquid fund or high-yield savings account before any investment. This is your financial safety net.",
            category="Emergency Fund", tags="emergency,savings,security"),
        FinancialTip(guru="Indian Finance", principle="50-30-20 Rule for India",
            advice="Allocate 50% of income to needs (rent, groceries, utilities), 30% to wants (dining, entertainment), and 20% to savings and investments (SIP, PPF, ELSS).",
            category="Budgeting", tags="budgeting,allocation,50-30-20"),
        FinancialTip(guru="Indian Finance", principle="Tax Saving Under 80C",
            advice="Invest up to ₹1.5 lakh annually in ELSS, PPF, or NPS to save tax under Section 80C. ELSS offers the dual benefit of tax saving and equity returns.",
            category="Tax Planning", tags="tax,80c,elss,ppf"),
    ]

    for tip in tips:
        session.add(tip)
    session.commit()
    session.close()
```

---

### Day 11–14: Basic Streamlit UI & First Deployment

**File:** `app.py`

```python
# app.py — Main Streamlit Application Entry Point

import streamlit as st
from src.database.models import init_db
from src.ui import pages

# Page configuration
st.set_page_config(
    page_title="💰 FinAdvisor AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
init_db()

# Sidebar navigation
st.sidebar.title("💰 FinAdvisor AI")
st.sidebar.markdown("*Your Personal Financial Assistant*")
st.sidebar.markdown("---")

PAGES = {
    "📊 Dashboard": pages.dashboard,
    "📤 Upload Expense": pages.upload_expense,
    "💡 Financial Advice": pages.financial_advice,
    "📁 Expense History": pages.expense_history,
    "🎯 Goals & Budget": pages.goals_budget,
    "📑 Reports": pages.reports,
}

selection = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[selection].show()

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Disclaimer: This tool provides educational financial guidance only. Consult a certified financial advisor for major investment decisions.")
```

**File:** `src/ui/pages/upload_expense.py`

```python
# src/ui/pages/upload_expense.py

import streamlit as st
from src.ocr.extractor import OCRExtractor
from src.parser.transaction_parser import TransactionParser
from src.database.crud import save_expense
from src.utils.helpers import format_currency


def show():
    st.title("📤 Upload Expense")
    st.markdown("Upload a payment screenshot, bank SMS screenshot, or enter expense manually.")

    tab1, tab2, tab3 = st.tabs(["📸 Screenshot Upload", "📄 CSV Upload", "✏️ Manual Entry"])

    with tab1:
        _screenshot_upload_tab()

    with tab2:
        _csv_upload_tab()

    with tab3:
        _manual_entry_tab()


def _screenshot_upload_tab():
    uploaded_file = st.file_uploader(
        "Upload payment screenshot",
        type=["jpg", "jpeg", "png", "webp"],
        help="Supported: PhonePe, Google Pay, Paytm, Bank SMS screenshots"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="Uploaded Screenshot", use_column_width=True)

        with col2:
            with st.spinner("🔍 Extracting text from screenshot..."):
                extractor = OCRExtractor()
                result = extractor.extract_text(uploaded_file.read())

            if result["success"]:
                st.success(f"✅ Text extracted (Confidence: {result['confidence']:.0f}%)")

                with st.expander("📝 Raw Extracted Text"):
                    st.text(result["raw_text"])

                # Parse transaction
                parser = TransactionParser()
                transaction = parser.parse(result["raw_text"], result["confidence"] / 100)

                if transaction:
                    st.markdown("### 🧾 Parsed Transaction")
                    st.markdown(f"**Amount:** {format_currency(transaction.amount)}")
                    st.markdown(f"**Merchant:** {transaction.merchant}")
                    st.markdown(f"**Category:** {transaction.category}")
                    st.markdown(f"**Date:** {transaction.date.strftime('%d %b %Y')}")
                    st.markdown(f"**Payment Method:** {transaction.payment_method}")

                    # Allow user to correct
                    st.markdown("### ✏️ Verify & Correct")
                    corrected_amount = st.number_input("Amount (₹)", value=transaction.amount, min_value=0.0)
                    corrected_merchant = st.text_input("Merchant", value=transaction.merchant)
                    corrected_category = st.selectbox("Category", [
                        "Food & Dining", "Groceries", "Transport", "Entertainment",
                        "Shopping", "Healthcare", "Utilities", "Education",
                        "Investment", "Rent & Housing", "Others"
                    ], index=0)

                    if st.button("💾 Save Expense", type="primary"):
                        save_expense(
                            amount=corrected_amount,
                            merchant=corrected_merchant,
                            category=corrected_category,
                            date=transaction.date,
                            payment_method=transaction.payment_method,
                            raw_text=result["raw_text"],
                            source="screenshot",
                            confidence=result["confidence"] / 100,
                            is_verified=True
                        )
                        st.success("✅ Expense saved successfully!")
                        st.balloons()
                else:
                    st.warning("⚠️ Could not detect a transaction in this image. Please use manual entry.")
            else:
                st.error(f"❌ OCR failed: {result.get('error', 'Unknown error')}")
```

**Deploy to Streamlit Cloud:**

```bash
# 1. Push to GitHub
git add .
git commit -m "Week 1-2: Foundation — OCR + Parser + DB + Streamlit UI"
git push origin main

# 2. Go to share.streamlit.io
# 3. Connect GitHub repo
# 4. Set main file: app.py
# 5. Add secrets in Streamlit Cloud dashboard (from .env)
# 6. Deploy!
```

**Week 1–2 Milestone Checklist:**
- [ ] GitHub repo created with clean project structure
- [ ] OCR extracts text from PhonePe/Google Pay screenshots
- [ ] Transaction parser identifies amount, merchant, category, date
- [ ] SQLite database stores verified expenses
- [ ] Streamlit app runs locally with upload + manual entry
- [ ] Deployed live on Streamlit Cloud
- [ ] 2-minute demo video recorded

---

## Week 3–4: Core Financial Advisory Architecture

**Goal:** Build the LangChain-powered financial advisor. Integrate multi-source content. Add Splitwise data. Create spending visualizations.

---

### Day 15–17: LangChain Financial Advisor Agent

**File:** `src/advisory/financial_agent.py`

```python
# src/advisory/financial_agent.py

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from src.database.crud import (
    get_monthly_expenses,
    get_category_totals,
    get_budgets,
    get_goals
)
from src.database.models import SessionLocal, FinancialTip
from typing import Optional
import json
import os


SYSTEM_PROMPT = """You are FinAdvisor, a personal financial advisor AI assistant for Indian users.
You combine wisdom from top financial gurus (Warren Buffett, Robert Kiyosaki, Ramit Sethi) with 
practical knowledge of the Indian financial ecosystem (UPI payments, SIP, ELSS, PPF, NPS, Indian tax laws).

Your core principles:
1. Always base advice on actual spending data provided to you
2. Be specific, actionable, and empathetic — not preachy
3. Prioritize Indian investment options (SIP, ELSS, PPF, NPS, FD) over generic global advice
4. Always include a disclaimer that you are an educational AI, not a certified financial advisor
5. Use INR (₹) for all currency references

When analyzing expenses:
- Identify the top spending categories
- Compare against 50-30-20 rule (50% needs, 30% wants, 20% savings)
- Find unusual or excessive spending patterns
- Suggest specific actions the user can take this week

Always be warm, conversational, and encouraging. Financial improvement is a journey, not a judgment.

IMPORTANT DISCLAIMER: Always end advice with: "⚠️ This is educational guidance only. Please consult a SEBI-registered financial advisor for investment decisions."
"""


class FinancialAdvisorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Remember last 10 exchanges
        )
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self):
        @tool
        def get_spending_summary(month: str = None) -> str:
            """Get a summary of the user's spending for a given month (YYYY-MM format).
            If no month provided, returns current month's data."""
            expenses = get_monthly_expenses(month)
            if not expenses:
                return "No expense data found for this period."

            category_totals = {}
            total = 0
            for e in expenses:
                category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
                total += e.amount

            result = f"Total spending: ₹{total:,.0f}\n\nBreakdown:\n"
            for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                pct = (amt / total) * 100
                result += f"  {cat}: ₹{amt:,.0f} ({pct:.1f}%)\n"
            return result

        @tool
        def get_financial_guru_advice(topic: str) -> str:
            """Retrieve relevant financial wisdom from the knowledge base.
            Topics: savings, investment, budgeting, tax, emergency fund, debt"""
            session = SessionLocal()
            tips = session.query(FinancialTip).filter(
                FinancialTip.tags.contains(topic.lower())
            ).limit(3).all()
            session.close()

            if not tips:
                return f"No specific guru advice found for '{topic}'."

            result = f"Financial wisdom on '{topic}':\n\n"
            for tip in tips:
                result += f"**{tip.guru} — {tip.principle}**\n{tip.advice}\n\n"
            return result

        @tool
        def get_budget_status() -> str:
            """Check how the user is doing against their set budgets this month."""
            from datetime import datetime
            current_month = datetime.now().strftime("%Y-%m")
            budgets = get_budgets(current_month)
            category_totals = get_category_totals(current_month)

            if not budgets:
                return "No budgets set for this month. I recommend setting category budgets using the Goals & Budget page."

            result = "Budget Status This Month:\n\n"
            for budget in budgets:
                spent = category_totals.get(budget.category, 0)
                remaining = budget.monthly_limit - spent
                pct = (spent / budget.monthly_limit) * 100

                status = "🟢" if pct < 75 else ("🟡" if pct < 100 else "🔴")
                result += f"{status} {budget.category}: ₹{spent:,.0f} / ₹{budget.monthly_limit:,.0f} ({pct:.0f}%)\n"
                if remaining < 0:
                    result += f"   ⚠️ Over budget by ₹{abs(remaining):,.0f}\n"

            return result

        @tool
        def calculate_savings_potential(monthly_income: float) -> str:
            """Calculate savings potential based on income and current spending patterns."""
            from datetime import datetime
            current_month = datetime.now().strftime("%Y-%m")
            expenses = get_monthly_expenses(current_month)
            total_spent = sum(e.amount for e in expenses) if expenses else 0

            savings = monthly_income - total_spent
            savings_rate = (savings / monthly_income) * 100

            target_savings = monthly_income * 0.20  # 20% rule

            result = f"""Savings Analysis:
Monthly Income: ₹{monthly_income:,.0f}
Total Expenses: ₹{total_spent:,.0f}
Current Savings: ₹{savings:,.0f} ({savings_rate:.1f}%)
Target Savings (20% rule): ₹{target_savings:,.0f}

"""
            if savings_rate >= 20:
                result += "✅ Excellent! You're meeting the 20% savings target."
            elif savings_rate >= 10:
                result += f"🟡 Good progress. Cut ₹{target_savings - savings:,.0f}/month to hit 20% target."
            else:
                result += f"🔴 Needs attention. You need to cut ₹{target_savings - savings:,.0f}/month to reach 20% savings."

            return result

        return [get_spending_summary, get_financial_guru_advice, get_budget_status, calculate_savings_potential]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

    def chat(self, user_message: str) -> str:
        try:
            result = self.agent_executor.invoke({"input": user_message})
            return result["output"]
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try rephrasing your question."
```

---

### Day 18–20: Spending Pattern Analysis & Visualizations

**File:** `src/advisory/analytics.py`

```python
# src/advisory/analytics.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.database.crud import get_all_expenses


class SpendingAnalytics:
    """Generate spending analyses and visualizations from expense data."""

    def __init__(self):
        expenses = get_all_expenses()
        self.df = self._to_dataframe(expenses)

    def _to_dataframe(self, expenses) -> pd.DataFrame:
        if not expenses:
            return pd.DataFrame()
        data = [{
            'amount': e.amount,
            'merchant': e.merchant,
            'category': e.category,
            'date': e.date,
            'payment_method': e.payment_method,
            'transaction_type': e.transaction_type,
        } for e in expenses]
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').astype(str)
        df['week'] = df['date'].dt.isocalendar().week
        return df

    def category_pie_chart(self, month: str = None):
        """Donut chart of spending by category."""
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if month:
            df = df[df['month'] == month]
        if df.empty:
            return None

        category_totals = df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(
            category_totals, values='amount', names='category',
            title=f"Spending by Category — {month or 'All Time'}",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(font=dict(size=14))
        return fig

    def monthly_trend_chart(self):
        """Bar chart of monthly spending trends."""
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if df.empty:
            return None

        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly = monthly.sort_values('month')
        fig = px.bar(
            monthly, x='month', y='amount',
            title="Monthly Spending Trend",
            labels={'amount': 'Total Spent (₹)', 'month': 'Month'},
            color='amount',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(xaxis_tickangle=-45)
        return fig

    def budget_vs_actual_chart(self, budgets: list, month: str):
        """Horizontal bar chart comparing budget vs actual spending."""
        df = self.df[(self.df['transaction_type'] == 'debit') & (self.df['month'] == month)].copy()
        category_totals = df.groupby('category')['amount'].sum().to_dict()

        categories, actuals, limits = [], [], []
        for b in budgets:
            categories.append(b.category)
            actuals.append(category_totals.get(b.category, 0))
            limits.append(b.monthly_limit)

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Budget Limit', x=limits, y=categories, orientation='h',
                             marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Actual Spend', x=actuals, y=categories, orientation='h',
                             marker_color='coral'))
        fig.update_layout(
            barmode='overlay', title=f"Budget vs Actual — {month}",
            xaxis_title="Amount (₹)", font=dict(size=13)
        )
        return fig

    def top_merchants_chart(self, month: str = None, top_n: int = 10):
        """Bar chart of top merchants by spend."""
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if month:
            df = df[df['month'] == month]
        if df.empty:
            return None

        top = df.groupby('merchant')['amount'].sum().nlargest(top_n).reset_index()
        fig = px.bar(top, x='amount', y='merchant', orientation='h',
                     title=f"Top {top_n} Merchants by Spend",
                     labels={'amount': 'Total Spent (₹)', 'merchant': 'Merchant'},
                     color='amount', color_continuous_scale='Oranges')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        return fig

    def savings_rate_gauge(self, monthly_income: float, month: str = None):
        """Gauge chart showing savings rate."""
        df = self.df[(self.df['transaction_type'] == 'debit')].copy()
        if month:
            df = df[df['month'] == month]

        total_spent = df['amount'].sum()
        savings_rate = max(0, ((monthly_income - total_spent) / monthly_income) * 100)

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=savings_rate,
            title={'text': "Savings Rate (%)"},
            delta={'reference': 20},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 10], 'color': "red"},
                    {'range': [10, 20], 'color': "orange"},
                    {'range': [20, 35], 'color': "lightgreen"},
                    {'range': [35, 100], 'color': "green"},
                ],
                'threshold': {'value': 20, 'line': {'color': "black", 'width': 4}}
            }
        ))
        return fig
```

---

### Day 21–24: Financial Book Processing (RAG System)

**File:** `src/advisory/book_processor.py`

This module allows users to upload financial books (PDFs) and ask questions based on their content. It uses LangChain's RAG (Retrieval-Augmented Generation) pipeline.

```python
# src/advisory/book_processor.py

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import tempfile
import os


class FinancialBookProcessor:
    """
    Processes uploaded financial books (PDFs) and enables Q&A.
    Built on LangChain RAG: PDF → Chunks → Embeddings → FAISS → Q&A
    """

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.vectorstore = None
        self.qa_chain = None
        self.book_name = None

    def load_book(self, pdf_bytes: bytes, book_name: str) -> dict:
        """
        Load a PDF book, chunk it, embed, and build retrieval chain.
        Returns status and number of chunks created.
        """
        try:
            # Write to temp file (PyPDFLoader needs a file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            # Load and split
            loader = PyPDFLoader(tmp_path)
            documents = loader.load()
            os.unlink(tmp_path)

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            chunks = splitter.split_documents(documents)

            # Build FAISS vector store
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            self.book_name = book_name

            # Build QA chain with custom prompt
            prompt_template = """You are a financial advisor who has studied {book_name} deeply.
Use the following excerpts from the book to answer the question.
Always relate the answer to practical Indian financial context (SIP, UPI, Indian tax laws).
If the answer is not in the context, say "This specific topic isn't covered in the book, but generally..."

Context from book:
{context}

Question: {question}

Answer (practical, specific, actionable):"""

            PROMPT = PromptTemplate(
                template=prompt_template.format(book_name=self.book_name, context="{context}", question="{question}"),
                input_variables=["context", "question"]
            )

            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
                chain_type_kwargs={"prompt": PROMPT}
            )

            return {"success": True, "chunks": len(chunks), "pages": len(documents)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def ask(self, question: str) -> str:
        """Ask a question about the loaded book."""
        if not self.qa_chain:
            return "No book loaded. Please upload a financial PDF first."
        try:
            result = self.qa_chain.invoke({"query": question})
            return result["result"]
        except Exception as e:
            return f"Error answering question: {str(e)}"
```

**Week 3–4 Milestone Checklist:**
- [ ] LangChain agent with 4 financial tools built and tested
- [ ] Agent gives personalized advice based on real spending data
- [ ] Plotly charts: pie, bar, trend, gauge
- [ ] RAG system processes uploaded financial PDFs
- [ ] Splitwise CSV import working (optional)
- [ ] Multi-tab Streamlit UI: Dashboard + Advice + History

---

## Week 5–6: Domain Specialization

**Chosen Option: A1 — Indian Personal Finance Advisor**

**Goal:** Add deep Indian financial context — tax saving, UPI analysis, SIP recommendations, Indian spending categories.

---

### Day 29–32: Indian Tax Planning Module

**File:** `src/advisory/indian_tax.py`

```python
# src/advisory/indian_tax.py

from dataclasses import dataclass
from typing import List


@dataclass
class TaxSlabOldRegime:
    """Income Tax Slabs — Old Regime FY 2024-25"""
    slabs = [
        (250000, 0.0),
        (500000, 0.05),
        (750000, 0.10),   # After standard deduction
        (1000000, 0.20),
        (float('inf'), 0.30)
    ]


@dataclass
class TaxSlabNewRegime:
    """Income Tax Slabs — New Regime FY 2024-25 (Default from FY 2023-24)"""
    slabs = [
        (300000, 0.0),
        (600000, 0.05),
        (900000, 0.10),
        (1200000, 0.15),
        (1500000, 0.20),
        (float('inf'), 0.30)
    ]


DEDUCTIONS = {
    "Section 80C": {
        "limit": 150000,
        "options": ["ELSS Mutual Fund", "PPF", "NSC", "5-Year FD", "Life Insurance Premium", "Home Loan Principal", "Sukanya Samriddhi"],
        "description": "Most popular deduction. Invest in ELSS for best returns with tax saving."
    },
    "Section 80D": {
        "limit": 25000,   # 50000 for senior citizens
        "options": ["Health Insurance Premium"],
        "description": "Health insurance premium for self/family. Must-have for everyone."
    },
    "Section 80CCD(1B)": {
        "limit": 50000,
        "options": ["NPS (National Pension System)"],
        "description": "Additional ₹50,000 deduction over 80C limit for NPS contributions."
    },
    "Section 24(b)": {
        "limit": 200000,
        "options": ["Home Loan Interest"],
        "description": "Interest on home loan for self-occupied property."
    },
    "HRA": {
        "limit": None,  # Calculated based on salary and rent
        "options": ["House Rent Allowance"],
        "description": "If you pay rent, claim HRA exemption. Save significantly on tax."
    }
}


class IndianTaxPlanner:
    def __init__(self, annual_income: float, investments: dict = None):
        self.annual_income = annual_income
        self.investments = investments or {}

    def calculate_tax_old_regime(self) -> dict:
        """Calculate tax under old regime with deductions."""
        gross = self.annual_income
        standard_deduction = 50000  # FY 2024-25

        # Apply declared deductions
        total_deductions = standard_deduction
        for section, amount in self.investments.items():
            if section in DEDUCTIONS:
                limit = DEDUCTIONS[section].get('limit', 0)
                if limit:
                    total_deductions += min(amount, limit)

        taxable_income = max(0, gross - total_deductions)
        tax = self._compute_tax(taxable_income, TaxSlabOldRegime.slabs)
        cess = tax * 0.04  # 4% health & education cess

        return {
            "regime": "Old Regime",
            "gross_income": gross,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "base_tax": tax,
            "cess": cess,
            "total_tax": tax + cess,
            "effective_rate": ((tax + cess) / gross) * 100 if gross > 0 else 0
        }

    def calculate_tax_new_regime(self) -> dict:
        """Calculate tax under new regime (lower rates, fewer deductions)."""
        standard_deduction = 75000  # Enhanced for FY 2024-25
        taxable_income = max(0, self.annual_income - standard_deduction)
        tax = self._compute_tax(taxable_income, TaxSlabNewRegime.slabs)
        cess = tax * 0.04

        return {
            "regime": "New Regime",
            "gross_income": self.annual_income,
            "total_deductions": standard_deduction,
            "taxable_income": taxable_income,
            "base_tax": tax,
            "cess": cess,
            "total_tax": tax + cess,
            "effective_rate": ((tax + cess) / self.annual_income) * 100 if self.annual_income > 0 else 0
        }

    def recommend_regime(self) -> str:
        """Compare regimes and recommend the better one."""
        old = self.calculate_tax_old_regime()
        new = self.calculate_tax_new_regime()

        savings = new['total_tax'] - old['total_tax']
        if old['total_tax'] < new['total_tax']:
            return f"✅ **Old Regime is better for you.** You save ₹{savings:,.0f} by choosing Old Regime and claiming deductions under 80C, 80D, NPS, etc."
        else:
            return f"✅ **New Regime is better for you.** You save ₹{abs(savings):,.0f} by switching to New Regime. Consider this if you don't have large deductions."

    def get_tax_saving_recommendations(self) -> List[dict]:
        """Suggest specific investment actions to reduce tax."""
        recommendations = []
        total_80c = self.investments.get("Section 80C", 0)
        remaining_80c = max(0, 150000 - total_80c)

        if remaining_80c > 0:
            recommendations.append({
                "action": f"Invest ₹{remaining_80c:,.0f} more in ELSS or PPF",
                "section": "80C",
                "potential_tax_saving": remaining_80c * 0.20,  # approx at 20% slab
                "priority": "HIGH"
            })

        if self.investments.get("Section 80D", 0) == 0:
            recommendations.append({
                "action": "Buy health insurance (minimum ₹5,000/year premium) for self + family",
                "section": "80D",
                "potential_tax_saving": 5000 * 0.20,
                "priority": "HIGH"
            })

        if self.investments.get("Section 80CCD(1B)", 0) == 0:
            recommendations.append({
                "action": "Invest ₹50,000 in NPS for additional deduction over 80C limit",
                "section": "80CCD(1B)",
                "potential_tax_saving": 50000 * 0.20,
                "priority": "MEDIUM"
            })

        return sorted(recommendations, key=lambda x: x['potential_tax_saving'], reverse=True)

    def _compute_tax(self, income: float, slabs: list) -> float:
        tax = 0.0
        prev_limit = 0
        for limit, rate in slabs:
            if income <= prev_limit:
                break
            taxable_in_slab = min(income, limit) - prev_limit
            tax += taxable_in_slab * rate
            prev_limit = limit
        return tax
```

---

### Day 33–36: UPI Transaction Analysis & SIP Recommender

**File:** `src/advisory/sip_recommender.py`

```python
# src/advisory/sip_recommender.py

from dataclasses import dataclass
from typing import List


@dataclass
class MutualFund:
    name: str
    category: str
    risk_level: str
    expected_return: float   # CAGR %
    min_sip: float
    platform: str
    use_case: str


RECOMMENDED_FUNDS = [
    MutualFund("Mirae Asset Large Cap Fund", "Large Cap", "Low-Medium", 12.0, 500, "Groww/Zerodha",
               "Core portfolio, stable long-term wealth"),
    MutualFund("Parag Parikh Flexi Cap Fund", "Flexi Cap", "Medium", 13.5, 1000, "Groww/Zerodha",
               "Diversified domestic + international exposure"),
    MutualFund("Axis Small Cap Fund", "Small Cap", "High", 17.0, 500, "Groww/Zerodha",
               "High growth potential, 7+ year horizon"),
    MutualFund("HDFC Short Duration Fund", "Debt", "Low", 7.0, 500, "HDFC AMC",
               "Emergency fund alternative, stable returns"),
    MutualFund("Quant ELSS Tax Saver Fund", "ELSS", "Medium-High", 15.0, 500, "Groww",
               "Tax saving under 80C + equity returns"),
    MutualFund("SBI Nifty Index Fund", "Index Fund", "Low-Medium", 12.0, 500, "Groww/Zerodha",
               "Passive investing, low cost, market returns"),
]


class SIPRecommender:
    """
    Recommends SIP investments based on user's financial profile:
    monthly income, expenses, risk tolerance, and goals.
    """

    def __init__(self, monthly_income: float, monthly_expenses: float,
                 risk_tolerance: str = "medium", investment_horizon: int = 5):
        self.monthly_income = monthly_income
        self.monthly_expenses = monthly_expenses
        self.risk_tolerance = risk_tolerance.lower()
        self.investment_horizon = investment_horizon  # years
        self.investable_surplus = monthly_income - monthly_expenses

    def get_sip_allocation(self) -> dict:
        """
        Recommend SIP allocation based on risk profile.
        Follows standard asset allocation principles adapted for Indian market.
        """
        if self.investable_surplus <= 0:
            return {"error": "No investable surplus. Focus on reducing expenses first."}

        sip_amount = self.investable_surplus * 0.70  # 70% of surplus to SIP, 30% liquid

        if self.risk_tolerance == "low":
            allocation = {
                "Large Cap Fund": 0.50,
                "Debt/Liquid Fund": 0.30,
                "ELSS (80C)": 0.20
            }
        elif self.risk_tolerance == "medium":
            allocation = {
                "Large Cap Fund": 0.30,
                "Flexi Cap Fund": 0.25,
                "Small Cap Fund": 0.15,
                "ELSS (80C)": 0.20,
                "Debt Fund": 0.10
            }
        else:  # high
            allocation = {
                "Flexi Cap Fund": 0.30,
                "Small Cap Fund": 0.30,
                "Mid Cap Fund": 0.20,
                "ELSS (80C)": 0.20
            }

        return {
            "total_monthly_sip": round(sip_amount, -2),  # round to nearest 100
            "allocation": {
                fund: round(sip_amount * pct, -2)
                for fund, pct in allocation.items()
            },
            "liquid_reserve": round(self.investable_surplus * 0.30, -2)
        }

    def calculate_sip_returns(self, monthly_sip: float, years: int,
                               annual_return: float = 12.0) -> dict:
        """
        Calculate SIP maturity value using compound interest formula.
        FV = P × [((1 + r)^n - 1) / r] × (1 + r)
        """
        monthly_rate = annual_return / 100 / 12
        n = years * 12
        invested = monthly_sip * n
        maturity = monthly_sip * ((((1 + monthly_rate)**n - 1) / monthly_rate) * (1 + monthly_rate))
        gains = maturity - invested

        return {
            "monthly_sip": monthly_sip,
            "years": years,
            "total_invested": round(invested, 2),
            "maturity_value": round(maturity, 2),
            "total_gains": round(gains, 2),
            "return_rate": round((gains / invested) * 100, 1)
        }
```

**Week 5–6 Milestone Checklist:**
- [ ] Indian tax calculator (old vs new regime comparison)
- [ ] 80C, 80D, NPS deduction tracking in UI
- [ ] SIP recommender with amount + fund suggestions
- [ ] UPI spending analysis (PhonePe, GPay, Paytm category breakdown)
- [ ] Indian expense categories in use (dmart, swiggy, jio, etc.)
- [ ] Tax saving recommendations with specific actions
- [ ] SIP return projection calculator in UI

---

## Week 7–8: Polish & Production

**Goal:** Professional UI, error handling, export, documentation, final deployment.

---

### Day 43–46: Dashboard & Complete UI

**File:** `src/ui/pages/dashboard.py`

```python
# src/ui/pages/dashboard.py

import streamlit as st
from datetime import datetime
from src.advisory.analytics import SpendingAnalytics
from src.database.crud import (
    get_monthly_expenses, get_budgets, get_goals,
    get_category_totals
)
from src.utils.helpers import format_currency


def show():
    st.title("📊 Financial Dashboard")
    current_month = datetime.now().strftime("%Y-%m")
    month_display = datetime.now().strftime("%B %Y")

    # ─── KPI Row ───────────────────────────────────────────────────
    expenses = get_monthly_expenses(current_month)
    total_debit = sum(e.amount for e in expenses if e.transaction_type == 'debit')
    total_credit = sum(e.amount for e in expenses if e.transaction_type == 'credit')
    num_transactions = len(expenses)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💸 Total Spent", format_currency(total_debit), f"{month_display}")
    col2.metric("💰 Income Received", format_currency(total_credit))
    col3.metric("🧾 Transactions", num_transactions)
    goals = get_goals()
    active_goals = len([g for g in goals if not g.is_achieved])
    col4.metric("🎯 Active Goals", active_goals)

    st.markdown("---")

    # ─── Charts ────────────────────────────────────────────────────
    analytics = SpendingAnalytics()

    col_left, col_right = st.columns(2)

    with col_left:
        pie_fig = analytics.category_pie_chart(current_month)
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("📭 No expense data yet. Upload a screenshot to get started!")

    with col_right:
        trend_fig = analytics.monthly_trend_chart()
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)

    # ─── Budget Status ─────────────────────────────────────────────
    st.markdown("### 📏 Budget Status — " + month_display)
    budgets = get_budgets(current_month)
    category_totals = get_category_totals(current_month)

    if budgets:
        for budget in budgets:
            spent = category_totals.get(budget.category, 0)
            pct = min(100, (spent / budget.monthly_limit) * 100)
            color = "normal" if pct < 75 else ("off" if pct >= 100 else "inverse")
            st.progress(
                pct / 100,
                text=f"{budget.category}: {format_currency(spent)} / {format_currency(budget.monthly_limit)} ({pct:.0f}%)"
            )
    else:
        st.info("No budgets set. Go to **Goals & Budget** to set monthly limits.")

    # ─── Recent Transactions ───────────────────────────────────────
    st.markdown("### 🕐 Recent Transactions")
    recent = sorted(expenses, key=lambda e: e.date, reverse=True)[:8]
    if recent:
        for e in recent:
            icon = "💸" if e.transaction_type == 'debit' else "💰"
            col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 1])
            col_a.write(f"{icon} {e.merchant}")
            col_b.write(e.category)
            col_c.write(format_currency(e.amount))
            col_d.write(e.date.strftime("%d %b"))
    else:
        st.info("No transactions this month.")
```

---

### Day 47–50: Export, Error Handling & Validation

**File:** `src/utils/export.py`

```python
# src/utils/export.py

import pandas as pd
import io
from fpdf import FPDF
from datetime import datetime
from src.database.crud import get_all_expenses, get_monthly_expenses


def export_to_csv(month: str = None) -> bytes:
    """Export expense data to CSV."""
    expenses = get_monthly_expenses(month) if month else get_all_expenses()
    data = [{
        'Date': e.date.strftime('%d-%m-%Y'),
        'Merchant': e.merchant,
        'Category': e.category,
        'Amount (INR)': e.amount,
        'Type': e.transaction_type,
        'Payment Method': e.payment_method,
        'Source': e.source
    } for e in expenses]

    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def export_budget_report_pdf(month: str) -> bytes:
    """Generate a PDF financial summary report."""
    expenses = get_monthly_expenses(month)
    total = sum(e.amount for e in expenses if e.transaction_type == 'debit')

    category_totals = {}
    for e in expenses:
        if e.transaction_type == 'debit':
            category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 12, "FinAdvisor AI — Financial Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Period: {month}", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %B %Y')}", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Total Spent: INR {total:,.0f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Category", border=1)
    pdf.cell(50, 8, "Amount (INR)", border=1)
    pdf.cell(40, 8, "% of Total", border=1, ln=True)

    pdf.set_font("Arial", "", 11)
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (amt / total) * 100 if total > 0 else 0
        pdf.cell(100, 7, cat, border=1)
        pdf.cell(50, 7, f"{amt:,.0f}", border=1)
        pdf.cell(40, 7, f"{pct:.1f}%", border=1, ln=True)

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
```

---

### Day 51–54: Final Testing, README & Demo Video

**Testing Checklist (before final deployment):**

Refer to the [Testing Checklist](#testing-checklist) section for the complete list.

**Final deployment commands:**

```bash
# Final git push
git add .
git commit -m "Week 7-8: Production ready — Full UI, Export, Error Handling"
git push origin main

# Redeploy on Streamlit Cloud (auto-deploys on push)
# Verify at: https://your-app-name.streamlit.app
```

**Week 7–8 Milestone Checklist:**
- [ ] Dashboard with KPIs, charts, budget progress bars, recent transactions
- [ ] Financial advice chat with conversational memory (last 10 messages)
- [ ] Indian tax calculator with old vs new regime comparison
- [ ] SIP recommender with return projection
- [ ] CSV + PDF export working
- [ ] Input validation and error messages on all forms
- [ ] Comprehensive README written
- [ ] 5–7 minute demo video recorded and uploaded

---

## Database Schema

```sql
-- expenses table
CREATE TABLE expenses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amount          REAL NOT NULL,
    merchant        VARCHAR(100) DEFAULT 'Unknown',
    category        VARCHAR(50) DEFAULT 'Others',
    subcategory     VARCHAR(50),
    date            DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method  VARCHAR(50) DEFAULT 'Unknown',
    transaction_type VARCHAR(10) DEFAULT 'debit',
    notes           TEXT,
    raw_text        TEXT,
    source          VARCHAR(30) DEFAULT 'manual',
    confidence      REAL DEFAULT 1.0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_verified     BOOLEAN DEFAULT FALSE
);

-- budgets table
CREATE TABLE budgets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category        VARCHAR(50) NOT NULL,
    monthly_limit   REAL NOT NULL,
    month           VARCHAR(7) NOT NULL,   -- YYYY-MM
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- financial_goals table
CREATE TABLE financial_goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name       VARCHAR(100) NOT NULL,
    target_amount   REAL NOT NULL,
    current_amount  REAL DEFAULT 0.0,
    target_date     DATETIME,
    category        VARCHAR(50),
    notes           TEXT,
    is_achieved     BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- financial_tips table (pre-seeded)
CREATE TABLE financial_tips (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guru            VARCHAR(50) NOT NULL,
    principle       VARCHAR(200) NOT NULL,
    advice          TEXT NOT NULL,
    category        VARCHAR(50),
    tags            VARCHAR(200)
);
```

---

## Folder Structure

```
financial-advisor-ai/
├── app.py                          # Streamlit entry point
├── requirements.txt                # Python dependencies
├── .env                            # API keys (never commit this)
├── .gitignore
├── README.md
├── financial_data.db               # SQLite database (auto-created)
│
├── src/
│   ├── __init__.py
│   ├── ocr/
│   │   ├── __init__.py
│   │   └── extractor.py            # OCR + image preprocessing
│   ├── parser/
│   │   ├── __init__.py
│   │   └── transaction_parser.py   # Text → Transaction object
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models + init_db()
│   │   └── crud.py                 # Create/Read/Update/Delete functions
│   ├── advisory/
│   │   ├── __init__.py
│   │   ├── financial_agent.py      # LangChain agent + tools
│   │   ├── analytics.py            # Plotly charts
│   │   ├── book_processor.py       # PDF RAG pipeline
│   │   ├── indian_tax.py           # Tax calculator
│   │   └── sip_recommender.py      # SIP + returns calculator
│   ├── ui/
│   │   ├── __init__.py
│   │   └── pages/
│   │       ├── __init__.py
│   │       ├── dashboard.py        # Main dashboard
│   │       ├── upload_expense.py   # Screenshot/CSV/manual upload
│   │       ├── financial_advice.py # Chat with financial agent
│   │       ├── expense_history.py  # Table view + filters
│   │       ├── goals_budget.py     # Set/track budgets & goals
│   │       └── reports.py          # Export + summary reports
│   └── utils/
│       ├── __init__.py
│       ├── categories.py           # Expense category keywords
│       ├── helpers.py              # format_currency, date helpers
│       └── export.py               # CSV + PDF export
│
├── data/
│   ├── sample_screenshots/         # Test images for demo
│   └── sample_bank_statements/     # Test CSVs
│
├── assets/
│   └── logo.png
│
├── tests/
│   ├── test_ocr.py
│   ├── test_parser.py
│   ├── test_analytics.py
│   └── test_tax.py
│
└── docs/
    ├── architecture.md
    └── api_config.md
```

---

## API Configuration Guide

### OpenAI (LLM & Embeddings)
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account → API Keys → Create new secret key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`
4. Cost estimate: ~$2–5/month for light use with GPT-3.5-turbo

### Google Vision API (OCR — Optional)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Enable "Cloud Vision API"
3. Create credentials → Service Account → Download JSON key
4. Add to `.env`: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`
5. Free tier: 1,000 units/month

### Tesseract OCR (Free — Recommended for Track A)
```bash
# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-hin  # Hindi support
# Verify
tesseract --version
```

### Splitwise API (Optional)
1. Register at [secure.splitwise.com/oauth_clients](https://secure.splitwise.com/oauth_clients)
2. Create app → get Consumer Key + Secret
3. Add to `.env`: `SPLITWISE_CONSUMER_KEY=...` and `SPLITWISE_CONSUMER_SECRET=...`

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → Select `app.py` as main file
4. In "Advanced settings" → Secrets, add all `.env` contents in TOML format:
```toml
OPENAI_API_KEY = "sk-..."
GOOGLE_VISION_API_KEY = "..."
DATABASE_URL = "sqlite:///financial_data.db"
```

---

## Testing Checklist

### OCR & Parser
- [ ] PhonePe screenshot → amount extracted correctly
- [ ] Google Pay screenshot → merchant name extracted
- [ ] Bank SMS screenshot → date parsed correctly
- [ ] Low-quality image → graceful error message shown
- [ ] PDF bank statement → text extracted from all pages

### Database
- [ ] New expense saves correctly
- [ ] Duplicate expense not created on re-upload
- [ ] Budget CRUD works for all categories
- [ ] Goal progress updates correctly
- [ ] Financial tips seeded on first run

### Financial Agent
- [ ] "What did I spend this month?" → returns accurate breakdown
- [ ] "How can I save more?" → gives actionable advice
- [ ] "Compare Warren Buffett and Ramit Sethi advice" → presents both perspectives
- [ ] "Set a budget for food" → correct tool called
- [ ] Conversation memory persists across messages

### UI / UX
- [ ] Dashboard loads without errors on empty database
- [ ] Charts render correctly with sample data
- [ ] Budget progress bars update in real time
- [ ] File uploader accepts jpg, png, pdf
- [ ] CSV export downloads with correct data
- [ ] PDF report generates without errors
- [ ] All pages navigate correctly from sidebar

### Indian Features
- [ ] Old vs New regime tax comparison accurate for ₹8 lakh income
- [ ] SIP calculator correct (verify manually with a known input)
- [ ] 80C deduction capped at ₹1.5 lakh
- [ ] Indian payment app names recognized (PhonePe, GPay, Paytm)
- [ ] INR formatting throughout (₹1,23,456 style)

---

## Deployment Instructions

### Local Development
```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/financial-advisor-ai.git
cd financial-advisor-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run app.py
# Open: http://localhost:8501
```

### Streamlit Cloud (Production)
```bash
# Ensure app.py is in root
# Ensure requirements.txt is in root
# Push to GitHub main branch
git push origin main

# On share.streamlit.io:
# 1. "New app" → Select repo → Set main file: app.py
# 2. Add secrets in Settings > Secrets
# 3. Click Deploy
```

---

## README Template

```markdown
# 💰 FinAdvisor AI — Personal Financial Advisor & Expense Manager

An AI-powered financial assistant that extracts expenses from payment screenshots,
provides personalized advice inspired by top financial gurus, and offers
India-specific planning tools including tax calculators and SIP recommenders.

## Features
- 📸 **OCR Expense Extraction** — Upload PhonePe/GPay/Paytm screenshots
- 💡 **AI Financial Advisor** — Chat-based advice powered by LangChain + GPT
- 📊 **Spending Analytics** — Category breakdown, trends, budget tracking
- 📚 **Book Q&A** — Upload financial books (PDFs) and ask questions
- 🇮🇳 **India-Specific Tools** — Tax calculator, SIP recommender, 80C planner
- 📑 **Export** — Download CSV and PDF financial reports

## Tech Stack
- Frontend: Streamlit
- Backend: Python, LangChain, SQLite
- OCR: Tesseract + OpenCV
- LLM: OpenAI GPT-3.5-turbo
- Charts: Plotly

## Setup
\`\`\`bash
git clone https://github.com/YOUR_USERNAME/financial-advisor-ai.git
cd financial-advisor-ai
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
streamlit run app.py
\`\`\`

## Configuration
See `docs/api_config.md` for full API setup instructions.

## Live Demo
[https://your-app-name.streamlit.app](https://your-app-name.streamlit.app)

## Disclaimer
This tool provides educational financial guidance only. It is not a SEBI-registered
financial advisor. Please consult a certified professional for investment decisions.
```

---

## Summary: Weekly Milestones at a Glance

| Week | Focus | Key Deliverable |
|------|-------|-----------------|
| 1–2 | Foundation | OCR module, transaction parser, SQLite DB, Streamlit UI, first deployment |
| 3–4 | Advisory Core | LangChain agent, 4 financial tools, Plotly charts, PDF book RAG |
| 5–6 | Indian Specialization | Tax calculator, SIP recommender, Indian expense categories |
| 7–8 | Polish & Ship | Full UI polish, export (CSV+PDF), error handling, README, demo video |

---

*Built with ❤️ as part of Capabl AI Agent Development Project*  
*Track A — Essential | 8 Weeks | Financial Technology Domain*
```
