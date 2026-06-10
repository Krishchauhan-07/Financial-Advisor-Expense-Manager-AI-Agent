# src/utils/export.py

import pandas as pd
import io
from datetime import datetime
from src.database.crud import get_all_expenses, get_monthly_expenses


def export_to_csv(month: str = None) -> bytes:
    """Export expense data to CSV."""
    expenses = get_monthly_expenses(month) if month else get_all_expenses()
    data = [{
        'Date': e.date.strftime('%d-%m-%Y') if e.date else '',
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
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 not installed. Run: pip install fpdf2")

    expenses = get_monthly_expenses(month)
    total = sum(e.amount for e in expenses if e.transaction_type == 'debit')
    income = sum(e.amount for e in expenses if e.transaction_type == 'credit')

    category_totals = {}
    for e in expenses:
        if e.transaction_type == 'debit':
            category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "FinAdvisor AI - Financial Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Period: {month}", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %B %Y')}", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Total Spent: INR {total:,.0f}", ln=True)
    pdf.cell(0, 10, f"Total Income: INR {income:,.0f}", ln=True)
    pdf.cell(0, 10, f"Net: INR {income - total:,.0f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(100, 8, "Category", border=1)
    pdf.cell(50, 8, "Amount (INR)", border=1)
    pdf.cell(40, 8, "% of Total", border=1, ln=True)

    pdf.set_font("Helvetica", "", 11)
    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (amt / total) * 100 if total > 0 else 0
        pdf.cell(100, 7, cat, border=1)
        pdf.cell(50, 7, f"{amt:,.0f}", border=1)
        pdf.cell(40, 7, f"{pct:.1f}%", border=1, ln=True)

    buffer = io.BytesIO()
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
