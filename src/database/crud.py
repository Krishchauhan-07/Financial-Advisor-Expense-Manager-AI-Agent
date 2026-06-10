# src/database/crud.py

from sqlalchemy import func
from src.database.models import SessionLocal, Expense, Budget, FinancialGoal, FinancialTip
from datetime import datetime
from typing import Optional, List, Dict


# ─── Expenses ────────────────────────────────────────────────────────────────

def save_expense(
    amount: float,
    merchant: str,
    category: str,
    date: datetime = None,
    payment_method: str = "Unknown",
    transaction_type: str = "debit",
    notes: str = None,
    raw_text: str = None,
    source: str = "manual",
    confidence: float = 1.0,
    is_verified: bool = False,
) -> Expense:
    """Save a new expense to the database."""
    session = SessionLocal()
    try:
        expense = Expense(
            amount=amount,
            merchant=merchant,
            category=category,
            date=date or datetime.now(),
            payment_method=payment_method,
            transaction_type=transaction_type,
            notes=notes,
            raw_text=raw_text,
            source=source,
            confidence=confidence,
            is_verified=is_verified,
        )
        session.add(expense)
        session.commit()
        session.refresh(expense)
        return expense
    finally:
        session.close()


def get_all_expenses() -> List[Expense]:
    """Return all expenses ordered by date descending."""
    session = SessionLocal()
    try:
        return session.query(Expense).order_by(Expense.date.desc()).all()
    finally:
        session.close()


def get_monthly_expenses(month: str = None) -> List[Expense]:
    """Return expenses for a given YYYY-MM month (defaults to current month)."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    session = SessionLocal()
    try:
        year, mon = map(int, month.split("-"))
        return (
            session.query(Expense)
            .filter(
                func.strftime("%Y", Expense.date) == str(year),
                func.strftime("%m", Expense.date) == f"{mon:02d}",
            )
            .order_by(Expense.date.desc())
            .all()
        )
    finally:
        session.close()


def get_category_totals(month: str = None) -> Dict[str, float]:
    """Return {category: total_amount} for debit transactions in the given month."""
    expenses = get_monthly_expenses(month)
    totals: Dict[str, float] = {}
    for e in expenses:
        if e.transaction_type == "debit":
            totals[e.category] = totals.get(e.category, 0.0) + e.amount
    return totals


def delete_expense(expense_id: int) -> bool:
    """Delete an expense by ID."""
    session = SessionLocal()
    try:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            session.delete(expense)
            session.commit()
            return True
        return False
    finally:
        session.close()


def update_expense_verification(expense_id: int, is_verified: bool) -> bool:
    """Mark expense as verified or not."""
    session = SessionLocal()
    try:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            expense.is_verified = is_verified
            session.commit()
            return True
        return False
    finally:
        session.close()


# ─── Budgets ─────────────────────────────────────────────────────────────────

def save_budget(category: str, monthly_limit: float, month: str) -> Budget:
    """Upsert a budget for a category + month."""
    session = SessionLocal()
    try:
        existing = (
            session.query(Budget)
            .filter(Budget.category == category, Budget.month == month)
            .first()
        )
        if existing:
            existing.monthly_limit = monthly_limit
            session.commit()
            return existing
        budget = Budget(category=category, monthly_limit=monthly_limit, month=month)
        session.add(budget)
        session.commit()
        session.refresh(budget)
        return budget
    finally:
        session.close()


def get_budgets(month: str = None) -> List[Budget]:
    """Return all budgets for the given month."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    session = SessionLocal()
    try:
        return session.query(Budget).filter(Budget.month == month).all()
    finally:
        session.close()


def delete_budget(budget_id: int) -> bool:
    session = SessionLocal()
    try:
        b = session.query(Budget).filter(Budget.id == budget_id).first()
        if b:
            session.delete(b)
            session.commit()
            return True
        return False
    finally:
        session.close()


# ─── Goals ───────────────────────────────────────────────────────────────────

def save_goal(
    goal_name: str,
    target_amount: float,
    current_amount: float = 0.0,
    target_date: datetime = None,
    category: str = None,
    notes: str = None,
) -> FinancialGoal:
    session = SessionLocal()
    try:
        goal = FinancialGoal(
            goal_name=goal_name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            category=category,
            notes=notes,
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return goal
    finally:
        session.close()


def get_goals() -> List[FinancialGoal]:
    session = SessionLocal()
    try:
        return session.query(FinancialGoal).order_by(FinancialGoal.created_at.desc()).all()
    finally:
        session.close()


def update_goal_progress(goal_id: int, current_amount: float) -> bool:
    session = SessionLocal()
    try:
        goal = session.query(FinancialGoal).filter(FinancialGoal.id == goal_id).first()
        if goal:
            goal.current_amount = current_amount
            if current_amount >= goal.target_amount:
                goal.is_achieved = True
            session.commit()
            return True
        return False
    finally:
        session.close()


def delete_goal(goal_id: int) -> bool:
    session = SessionLocal()
    try:
        g = session.query(FinancialGoal).filter(FinancialGoal.id == goal_id).first()
        if g:
            session.delete(g)
            session.commit()
            return True
        return False
    finally:
        session.close()
