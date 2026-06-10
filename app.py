# app.py — Main Streamlit Application Entry Point

import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

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

# ─── Premium Dark Theme CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Global ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
  }
  .main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #12122b 50%, #0c1426 100%) !important;
    border-right: 1px solid rgba(124,58,237,0.2) !important;
  }
  [data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
  }
  [data-testid="stSidebar"] .stRadio label {
    color: #cbd5e1 !important;
    font-size: 0.88rem !important;
    padding: 6px 0 !important;
  }
  [data-testid="stSidebar"] .stRadio > div {
    gap: 4px !important;
  }
  /* Active nav item */
  [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
    background: rgba(124,58,237,0.2) !important;
    border-radius: 8px;
  }

  /* ── Main Background ── */
  .stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 50%, #0a1628 100%) !important;
  }

  /* ── Headings ── */
  h1 { background: linear-gradient(135deg, #7c3aed, #06b6d4);
       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
       font-weight: 800 !important; }
  h2, h3 { color: #cbd5e1 !important; font-weight: 700 !important; }

  /* ── Metric Cards ── */
  [data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(6,182,212,0.07)) !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    border-radius: 16px !important;
    padding: 18px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35) !important;
    backdrop-filter: blur(10px) !important;
  }
  [data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 1px; }
  [data-testid="metric-container"] [data-testid="metric-value"] { color: #f1f5f9 !important; font-weight: 800 !important; }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 8px 20px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.35) !important;
  }
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.5) !important;
    background: linear-gradient(135deg, #6d28d9, #5b21b6) !important;
  }
  .stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    box-shadow: none !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
  }

  /* ── Inputs & Selects ── */
  .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
  }
  .stTextInput input:focus, .stNumberInput input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.25) !important;
  }

  /* ── Expanders ── */
  [data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.3) !important;
    color: #a78bfa !important;
  }

  /* ── Progress Bars ── */
  .stProgress > div > div {
    background: linear-gradient(90deg, #7c3aed, #06b6d4) !important;
    border-radius: 6px !important;
  }

  /* ── Chat Messages ── */
  [data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    margin-bottom: 8px !important;
  }

  /* ── Dataframes ── */
  .stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
  }

  /* ── Alerts / Info boxes ── */
  .stAlert {
    border-radius: 12px !important;
    border-left-width: 4px !important;
  }

  /* ── Divider ── */
  hr { border-color: rgba(255,255,255,0.08) !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a1a; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center;padding:16px 0 8px">
  <div style="font-size:2.2rem">💰</div>
  <div style="font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#06b6d4);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent">
    FinAdvisor AI
  </div>
  <div style="font-size:0.75rem;color:#64748b;margin-top:4px">Your Personal Financial Assistant</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="color:#64748b;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Navigate</p>', unsafe_allow_html=True)

PAGES = {
    "📊 Dashboard":        pages.dashboard,
    "📤 Upload Expense":   pages.upload_expense,
    "💡 Financial Advice": pages.financial_advice,
    "📁 Expense History":  pages.expense_history,
    "🎯 Goals & Budget":   pages.goals_budget,
    "📑 Reports":          pages.reports,
}

selection = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
PAGES[selection].show()

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Educational guidance only. Consult a SEBI-registered advisor for investment decisions.")
st.sidebar.markdown("---")
st.sidebar.caption("Built with ❤️ | Capabl AI Project")
