# src/ui/pages/expense_history.py

import streamlit as st
import pandas as pd
from src.database.crud import get_all_expenses, get_monthly_expenses, delete_expense
from src.utils.helpers import format_currency, ALL_CATEGORIES
from datetime import datetime


def show():
    st.title("📁 Expense History")
    st.markdown("View, filter, and manage all your recorded expenses.")

    # ─── Filters ───────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_mode = st.radio("Date Filter", ["This Month", "All Time", "Custom Month"], horizontal=True)

    with col2:
        filter_category = st.selectbox("Category", ["All"] + ALL_CATEGORIES)

    with col3:
        filter_type = st.selectbox("Type", ["All", "debit", "credit"])

    # Determine month
    if filter_mode == "This Month":
        month = datetime.now().strftime("%Y-%m")
        expenses = get_monthly_expenses(month)
    elif filter_mode == "Custom Month":
        month_input = st.text_input("Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
        expenses = get_monthly_expenses(month_input)
    else:
        expenses = get_all_expenses()

    # Apply category + type filters
    if filter_category != "All":
        expenses = [e for e in expenses if e.category == filter_category]
    if filter_type != "All":
        expenses = [e for e in expenses if e.transaction_type == filter_type]

    # ─── Summary Row ───────────────────────────────────────────────
    total = sum(e.amount for e in expenses)
    debits = sum(e.amount for e in expenses if e.transaction_type == "debit")
    credits_total = sum(e.amount for e in expenses if e.transaction_type == "credit")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📊 Total Records", len(expenses))
    m2.metric("💸 Total Debits", format_currency(debits))
    m3.metric("💰 Total Credits", format_currency(credits_total))
    m4.metric("📈 Net", format_currency(credits_total - debits))

    st.markdown("---")

    # ─── Table ─────────────────────────────────────────────────────
    if not expenses:
        st.info("📭 No expenses found for the selected filters.")
        return

    data = [{
        "ID": e.id,
        "Date": e.date.strftime("%d %b %Y") if e.date else "—",
        "Merchant": e.merchant,
        "Category": e.category,
        "Amount (₹)": e.amount,
        "Type": e.transaction_type,
        "Payment": e.payment_method,
        "Source": e.source,
        "Verified": "✅" if e.is_verified else "❌",
    } for e in expenses]

    df = pd.DataFrame(data)
    st.dataframe(df.drop(columns=["ID"]), use_container_width=True, height=400)

    # ─── Delete Expense ────────────────────────────────────────────
    st.markdown("### 🗑️ Delete an Expense")
    with st.form("delete_form"):
        delete_id = st.number_input("Enter Expense ID to delete", min_value=1, step=1)
        if st.form_submit_button("🗑️ Delete", type="secondary"):
            if delete_expense(int(delete_id)):
                st.success(f"✅ Expense #{delete_id} deleted.")
                st.rerun()
            else:
                st.error(f"❌ Expense #{delete_id} not found.")
