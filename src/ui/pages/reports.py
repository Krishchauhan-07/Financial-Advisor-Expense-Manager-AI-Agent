# src/ui/pages/reports.py

import streamlit as st
from datetime import datetime
from src.advisory.analytics import SpendingAnalytics
from src.database.crud import get_monthly_expenses, get_budgets, get_category_totals
from src.utils.helpers import format_currency, current_month_str, month_display


def show():
    st.title("📑 Reports & Export")
    st.markdown("Generate financial reports and export your data.")

    current_month = current_month_str()

    col1, col2 = st.columns(2)
    with col1:
        report_month = st.text_input("Report Month (YYYY-MM)", value=current_month)
        monthly_income_input = st.number_input("Your Monthly Income (₹) for savings analysis",
                                                min_value=0.0, value=50000.0, step=1000.0)
    with col2:
        st.markdown("&nbsp;")

    st.markdown("---")

    # ─── Summary Stats ──────────────────────────────────────────────
    st.markdown(f"### 📊 Monthly Summary — {month_display(report_month)}")
    expenses = get_monthly_expenses(report_month)
    total_debit = sum(e.amount for e in expenses if e.transaction_type == "debit")
    total_credit = sum(e.amount for e in expenses if e.transaction_type == "credit")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💸 Total Spent", format_currency(total_debit))
    m2.metric("💰 Total Income", format_currency(total_credit))
    net = total_credit - total_debit
    m3.metric("📈 Net", format_currency(net))
    savings_rate = max(0, (net / monthly_income_input) * 100) if monthly_income_input > 0 else 0
    m4.metric("💎 Savings Rate", f"{savings_rate:.1f}%")

    # ─── Charts ─────────────────────────────────────────────────────
    analytics = SpendingAnalytics()
    col_l, col_r = st.columns(2)

    pie = analytics.category_pie_chart(report_month)
    if pie:
        col_l.plotly_chart(pie, use_container_width=True)

    trend = analytics.monthly_trend_chart()
    if trend:
        col_r.plotly_chart(trend, use_container_width=True)

    # Savings gauge
    if monthly_income_input > 0:
        gauge = analytics.savings_rate_gauge(monthly_income_input, report_month)
        if gauge:
            st.markdown("### 💎 Savings Rate Gauge")
            st.plotly_chart(gauge, use_container_width=True)

    # Budget comparison
    budgets = get_budgets(report_month)
    if budgets:
        budget_chart = analytics.budget_vs_actual_chart(budgets, report_month)
        if budget_chart:
            st.markdown("### 📏 Budget vs Actual")
            st.plotly_chart(budget_chart, use_container_width=True)

    st.markdown("---")

    # ─── Export ─────────────────────────────────────────────────────
    st.markdown("### 📥 Export Data")

    col_csv, col_pdf = st.columns(2)

    with col_csv:
        st.markdown("#### CSV Export")
        if st.button("📊 Export to CSV", key="export_csv"):
            try:
                from src.utils.export import export_to_csv
                csv_bytes = export_to_csv(report_month)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_bytes,
                    file_name=f"expenses_{report_month}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            except Exception as e:
                st.error(f"CSV export failed: {str(e)}")

    with col_pdf:
        st.markdown("#### PDF Report")
        if st.button("📄 Generate PDF Report", key="generate_pdf"):
            try:
                from src.utils.export import export_budget_report_pdf
                pdf_bytes = export_budget_report_pdf(report_month)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"financial_report_{report_month}.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
            except Exception as e:
                st.error(f"PDF export failed: {str(e)}")
