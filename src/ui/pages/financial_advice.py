# src/ui/pages/financial_advice.py — Real-time AI chat (no predefined questions)

import streamlit as st
import os


# ─── Cached agent initializer (persists across reruns based on args) ────────
@st.cache_resource(show_spinner=False)
def _load_agent(mode: str, api_key: str):
    from src.advisory.financial_agent import FinancialAdvisorAgent
    return FinancialAdvisorAgent(mode=mode, api_key=api_key)


def show():
    # ── Page header ───────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:24px;">
      <h1 style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#06b6d4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        💡 FinAdvisor AI Chat
      </h1>
      <p style="color:#64748b;margin:6px 0 0;font-size:0.9rem">
        Ask me anything about personal finance, investments, tax saving, budgeting, and more.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Initialize Session State ───────────────────────────────────────────
    if "api_keys" not in st.session_state:
        st.session_state.api_keys = {}
        
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hi! I'm **FinAdvisor AI** — your personal financial assistant.\n\n"
                    "I can help you with:\n"
                    "- 📊 Analyzing your spending & budget\n"
                    "- 📈 SIP, mutual fund & investment advice\n"
                    "- 🏦 Indian tax planning (80C, NPS, ELSS, PPF)\n"
                    "- 💡 Wealth-building strategies\n"
                    "- 🧾 Understanding your expense patterns\n\n"
                    "Just select a **Guru Mode** in the sidebar and ask me anything! 🚀"
                )
            }
        ]

    # ── Sidebar: Chat Controls & Personas ──────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Guru Mode & Setup")
        
        mode = st.selectbox(
            "Select Persona",
            ["General", "The Value Ethos", "Asset Intelligence", "The Rich Life"],
            index=0,
            help="Change the AI's core financial philosophy."
        )
        
        # Hide the API key input from the webapp UI. Just use the environment variable.
        active_key = os.getenv("OPENAI_API_KEY", "")

        st.markdown("---")
        st.markdown("### 💬 Chat Controls")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_messages = [st.session_state.chat_messages[0]]  # keep welcome msg
            st.rerun()
        st.markdown(f"**{len(st.session_state.chat_messages) - 1}** messages in this session")

        st.markdown("---")
        st.markdown("### 💡 Try asking...")
        
        # Provide mode-specific suggestions
        mode_suggestions = {
            "General": [
                "What did I spend this month?",
                "Am I over budget anywhere?",
                "Best SIP funds for 2024?",
                "How can I save tax under 80C?",
                "Should I invest in NPS?"
            ],
            "The Value Ethos": [
                "How do I determine intrinsic value?",
                "What is a good margin of safety?",
                "Should I hold cash during a downturn?",
                "How does compound interest work?"
            ],
            "Asset Intelligence": [
                "What is the best asset allocation for me?",
                "How should I balance equity and debt?",
                "Explain the risk of different asset classes.",
                "How can I rebalance my portfolio?"
            ],
            "The Rich Life": [
                "How do I create a Conscious Spending Plan?",
                "What's the best way to automate my finances?",
                "How to spend guilt-free on things I love?",
                "How can I negotiate a higher salary?"
            ]
        }
        
        suggestions = mode_suggestions.get(mode, mode_suggestions["General"])
        for s in suggestions:
            # Use a unique key for each button to avoid Streamlit DuplicateWidgetID errors
            if st.button(s, key=f"sug_{mode[:5]}_{s[:15]}", use_container_width=True):
                _send_message(s, mode, active_key)

    # ── API Key Check ──────────────────────────────────────────────────────
    if not active_key or "xxxx" in active_key:
        st.warning(f"⚠️ **API Key missing for {mode} mode.** Please set a valid OPENAI_API_KEY environment variable.")
        _show_demo_tips()
        return

    # ── Load Agent ─────────────────────────────────────────────────────────
    try:
        with st.spinner("🤖 Loading FinAdvisor AI..."):
            # Caches the agent based on exact mode and api_key
            agent = _load_agent(mode, active_key)
    except Exception as e:
        st.error(f"❌ Could not initialize AI agent: {str(e)}")
        st.info("Make sure your OpenAI API key is valid and has credits.")
        return

    # ── Chat Display ───────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # ── Chat Input ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if prompt := st.chat_input(f"Ask in '{mode}' mode...", key="main_chat_input"):
        _send_message(prompt, mode, active_key)


def _send_message(prompt: str, mode: str, api_key: str):
    """Send a message to the AI agent and stream the response."""
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Get agent response
    agent = _load_agent(mode, api_key)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(f"🤔 {mode} is thinking..."):
            try:
                response = agent.chat(prompt)
            except Exception as e:
                err_str = str(e)
                if "insufficient_quota" in err_str or "429" in err_str:
                    response = "⚠️ **API Quota Exceeded:** The key used for this mode is out of credits. Please update it in the sidebar."
                else:
                    response = f"⚠️ I encountered an issue: {err_str}\n\nPlease try rephrasing your question."
        st.markdown(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()


def _show_demo_tips():
    """Show demo content when no API key is available."""
    st.markdown("### 💡 Sample Financial Wisdom")
    tips = [
        ("🧠", "Warren Buffett", "investing", "Invest in index funds for long-term wealth. Time in the market beats timing the market. A low-cost Nifty 50 index fund SIP beats most actively managed funds over 10+ years."),
        ("🤖", "Ramit Sethi", "automation", "Automate your SIP on salary day. Set up automatic transfers to savings before you can spend. Remove willpower from the equation completely."),
        ("🛡️", "Indian Finance", "emergency fund", "Build a 3-6 month emergency fund in a liquid mutual fund or high-yield savings account before any equity investment. This is non-negotiable."),
        ("📈", "Robert Kiyosaki", "assets", "Rich people acquire assets (things that pay you). Poor people acquire liabilities (things that cost you). Your SIP portfolio is an asset. Your fancy car is a liability."),
        ("🏦", "Tax Planning", "tax", "Invest ₹1.5L in ELSS/PPF/NPS under Section 80C to save up to ₹46,800 in taxes annually. Don't leave this money on the table."),
        ("💰", "50-30-20 Rule", "budgeting", "50% of income → Needs (rent, groceries, EMI). 30% → Wants (dining, entertainment, travel). 20% → Savings & Investments (SIP, PPF, emergency fund)."),
    ]
    cols = st.columns(2)
    for i, (icon, guru, tag, tip) in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);
                        border-radius:12px;padding:16px;margin-bottom:12px">
              <div style="font-size:1.4rem;margin-bottom:8px">{icon} <b style="color:#a78bfa">{guru}</b></div>
              <div style="color:#94a3b8;font-size:0.85rem;line-height:1.6">{tip}</div>
            </div>""", unsafe_allow_html=True)

