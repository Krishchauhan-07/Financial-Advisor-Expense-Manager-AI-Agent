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
