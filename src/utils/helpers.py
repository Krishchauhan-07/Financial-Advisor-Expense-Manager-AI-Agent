# src/utils/helpers.py

from datetime import datetime


def format_currency(amount: float) -> str:
    """Format a number as Indian Rupee currency string."""
    if amount is None:
        return "₹0"
    try:
        # Indian number format: ₹1,23,456.78
        amount = float(amount)
        if amount >= 0:
            return f"₹{amount:,.0f}"
        else:
            return f"-₹{abs(amount):,.0f}"
    except (ValueError, TypeError):
        return "₹0"


def format_date(dt: datetime) -> str:
    """Format datetime to readable Indian date string."""
    if dt is None:
        return "—"
    try:
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(dt)


def current_month_str() -> str:
    """Return current month in YYYY-MM format."""
    return datetime.now().strftime("%Y-%m")


def month_display(month_str: str) -> str:
    """Convert YYYY-MM to Month Year string."""
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        return dt.strftime("%B %Y")
    except Exception:
        return month_str


ALL_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transport",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Utilities",
    "Education",
    "Investment",
    "Rent & Housing",
    "Others",
]
