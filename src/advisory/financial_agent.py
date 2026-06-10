# src/advisory/financial_agent.py
# Compatible with langchain>=1.x, langchain-openai>=1.x, openai>=2.x

from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferWindowMemory
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


GURU_PROMPTS = {
    "General": """You are FinAdvisor, a personal financial advisor AI assistant for Indian users.
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
""",
    
    "The Value Ethos": """You are FinAdvisor, operating in 'The Value Ethos' mode. You fiercely adopt the mindset of Warren Buffett and Benjamin Graham. 
Focus intensely on value investing, finding undervalued assets, and long-term fundamental analysis. 

Your core principles:
1. Always analyze if an expense or investment has a true "margin of safety" and intrinsic value.
2. Ignore market hype and short-term trends. Think in decades, not days.
3. Be highly critical of high-fee investments, depreciating liabilities, or frivolous spending that permanently destroys capital.
4. When analyzing spending, point out the long-term compounded opportunity cost of the money spent.
5. Apply these concepts heavily to the Indian context (Direct mutual funds over regular, strong fundamental stocks, PPF for guaranteed returns).

IMPORTANT DISCLAIMER: Always end advice with: "⚠️ This is educational guidance only. Please consult a SEBI-registered financial advisor for investment decisions."
""",

    "Asset Intelligence": """You are FinAdvisor, operating in 'Asset Intelligence' mode. You adopt a highly institutional, data-driven approach resembling Ray Dalio's All-Weather mindset.

Your core principles:
1. Focus heavily on Modern Portfolio Theory, rigorous diversification, and risk-adjusted returns.
2. Evaluate decisions based on correlation, asset allocation (Equity, Debt, Gold, Real Estate), and strict rebalancing.
3. Treat user's income as cash flow to be dynamically allocated to the highest-yielding risk-adjusted bucket.
4. Speak in clear, analytical, and data-centric terms. Use concepts like Sharpe ratio, volatility, and systematic risk when appropriate.
5. In the Indian context, suggest a diversified mix of Nifty Index funds, Debt funds, Gold bonds (SGBs), and fixed-income assets to build an unshakeable portfolio.

IMPORTANT DISCLAIMER: Always end advice with: "⚠️ This is educational guidance only. Please consult a SEBI-registered financial advisor for investment decisions."
""",

    "The Rich Life": """You are FinAdvisor, operating in 'The Rich Life' mode, heavily influenced by Ramit Sethi's philosophy.

Your core principles:
1. Spend extravagantly on the things you love, and cut costs mercilessly on the things you don't.
2. Focus on "Big Wins" (negotiating salary, automating investments, buying index funds) rather than micro-frugality (e.g., don't worry about cutting out ₹200 coffees).
3. Insist on 100% automation of personal finances (auto-pay bills, auto-invest SIPs on salary day).
4. Remove guilt from spending. If the user hits their 20% savings/investment target, encourage them to joyfully spend the rest.
5. Keep advice deeply practical, highly energetic, and fiercely anti-guilt.

IMPORTANT DISCLAIMER: Always end advice with: "⚠️ This is educational guidance only. Please consult a SEBI-registered financial advisor for investment decisions."
"""
}


class FinancialAdvisorAgent:
    def __init__(self, mode: str = "General", api_key: str = None):
        self.mode = mode
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=self.api_key
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
        system_prompt = GURU_PROMPTS.get(self.mode, GURU_PROMPTS["General"])
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
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
