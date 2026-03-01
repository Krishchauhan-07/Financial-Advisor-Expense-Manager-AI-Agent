import streamlit as st
import io
import os
from PyPDF2 import PdfReader
import base64
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nexus - AI Financial Advisor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLES (Attempting to keep our awesome dark mode aesthetics) ---
st.markdown("""
<style>
    /* Main Backgrounds & Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background-color: #0f172a;
        background-image: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 40%),
                          radial-gradient(circle at bottom left, rgba(147, 51, 234, 0.05), transparent 40%);
        color: #f8fafc;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    
    .title-gradient {
        background: linear-gradient(135deg, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0;
    }

    /* Buttons */
    .stButton>button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    
    .stButton>button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    }

    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6 !important;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background-color: transparent !important;
    }
    .stChatMessage[data-testid="stChatMessage-bot"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 1rem;
    }
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = ""

# --- SERVICES / LOGIC ---

def extract_text_from_pdf(pdf_file) -> str:
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_image(image_bytes: bytes, api_key: str) -> str:
    if not api_key:
        return "Error: OpenAI API Key is required for Vision OCR."
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a precise OCR tool. Extract all the text and numbers."},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract all financial data and text from this image."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "max_tokens": 1000
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"OCR Error: {response.text}"

def extract_text_from_link(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        text = soup.get_text(separator=' ')
        return text[:15000] # Cap length
    except Exception as e:
        return f"Error reading Link: {e}"

def generate_financial_advice(prompt: str, context: str, api_key: str, message_history: list) -> str:
    if not api_key:
        return "Please connect your OpenAI API Key in the sidebar."
        
    client = OpenAI(api_key=api_key)
    system_prompt = "You are Nexus, a highly knowledgeable, professional, and insightful AI Financial Advisor."
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for msg in message_history[-4:]: # Only keep last 4 for context window
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # Append current msg
    final_content = f"Context from uploaded document:\n{context}\n\nUser Question: {prompt}" if context else prompt
    messages.append({"role": "user", "content": final_content})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: {str(e)}"

# --- UI LAYOUT ---

# Sidebar Navigation/Settings
with st.sidebar:
    st.markdown("### 🤖 Nexus App")
    if st.button("➕ New Analysis"):
        st.session_state.messages = []
        st.session_state.context = ""
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 🔑 API Connections")
    st.caption("Provide your keys to enable LLM access and OCR.")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key:
        st.success("API Key Loaded!")
        
    st.markdown("---")
    st.markdown("### 📎 Upload Documents")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload PDF or Screenshot", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file is not None:
        with st.spinner("Extracting data..."):
            if uploaded_file.name.endswith('.pdf'):
                st.session_state.context = extract_text_from_pdf(uploaded_file)
                st.success(f"Extracted {len(st.session_state.context)} chars from PDF!")
            else:
                bytes_data = uploaded_file.getvalue()
                st.session_state.context = extract_text_from_image(bytes_data, api_key)
                st.success("Image text extracted via Vision OCR!")
                
    st.markdown("---")
    # Link Input
    link_input = st.text_input("Analyze Link (URL)")
    if st.button("Scrape Link"):
        if link_input:
            with st.spinner("Scraping webpage..."):
                st.session_state.context = extract_text_from_link(link_input)
                st.success("Webpage scraped successfully!")

# Main Area
if not st.session_state.messages:
    st.markdown('<p class="title-gradient">Your Personal Finance Guru</p>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8; font-size:1.1rem;'>Upload a screenshot, PDF, or link in the sidebar to get expert insights.</p>", unsafe_allow_html=True)

# Display Chat Messages
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "bot" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask for financial advice..."):
    # Add user msg
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("bot", avatar="🤖"):
        with st.spinner("Analyzing..."):
            response = generate_financial_advice(prompt, st.session_state.context, api_key, st.session_state.messages)
            st.markdown(response)
            
            # Save bot message
            st.session_state.messages.append({"role": "bot", "content": response})
            
            # Clear context if it was used for this turn
            if st.session_state.context:
                st.session_state.context = "" 
