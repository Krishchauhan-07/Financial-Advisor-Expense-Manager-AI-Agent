# src/ui/pages/goals_budget.py

import streamlit as st
from datetime import datetime
from src.database.crud import (
    save_budget, get_budgets, delete_budget,
    save_goal, get_goals, update_goal_progress, delete_goal,
    get_category_totals
)
from src.utils.helpers import format_currency, ALL_CATEGORIES, current_month_str, month_display
from src.advisory.sip_recommender import SIPRecommender
from src.advisory.indian_tax import IndianTaxPlanner, DEDUCTIONS


def show():
    st.title("🎯 Goals & Budget")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📏 Monthly Budgets",
        "🏆 Financial Goals",
        "📈 SIP Calculator",
        "🇮🇳 Tax Planner",
    ])

    with tab1:
        _budgets_tab()

    with tab2:
        _goals_tab()

    with tab3:
        _sip_tab()

    with tab4:
        _tax_tab()


def _budgets_tab():
    st.markdown("### 📏 Monthly Budget Manager")
    current_month = current_month_str()
    month_disp = month_display(current_month)
    category_totals = get_category_totals(current_month)

    st.markdown(f"**Setting budgets for: {month_disp}**")

    with st.form("budget_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            bcat = st.selectbox("Category", ALL_CATEGORIES[:-1], key="bcat")  # exclude "Others"
        with col2:
            blimit = st.number_input("Monthly Limit (₹)", min_value=100.0, value=5000.0, step=500.0)
        with col3:
            bmonth = st.text_input("Month (YYYY-MM)", value=current_month)

        if st.form_submit_button("💾 Set Budget", type="primary"):
            save_budget(bcat, blimit, bmonth)
            st.success(f"✅ Budget set: {bcat} = {format_currency(blimit)} for {bmonth}")
            st.rerun()

    # Show existing budgets
    budgets = get_budgets(current_month)
    if budgets:
        st.markdown(f"### Current Budgets — {month_disp}")
        for b in budgets:
            spent = category_totals.get(b.category, 0)
            pct = min(100, (spent / b.monthly_limit) * 100) if b.monthly_limit > 0 else 0
            remaining = b.monthly_limit - spent
            status = "🟢" if pct < 75 else ("🟡" if pct < 100 else "🔴")

            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.progress(pct / 100, text=f"{status} {b.category}: {format_currency(spent)} / {format_currency(b.monthly_limit)} — remaining {format_currency(remaining)}")
            with col_b:
                if st.button("🗑️", key=f"del_budget_{b.id}", help="Delete budget"):
                    delete_budget(b.id)
                    st.rerun()
    else:
        st.info("No budgets set for this month.")


def _goals_tab():
    st.markdown("### 🏆 Financial Goals")

    with st.form("goal_form"):
        col1, col2 = st.columns(2)
        with col1:
            gname = st.text_input("Goal Name *", placeholder="e.g. Emergency Fund, Vacation, Laptop")
            gtarget = st.number_input("Target Amount (₹) *", min_value=100.0, value=50000.0, step=1000.0)
            gcurrent = st.number_input("Current Amount Saved (₹)", min_value=0.0, value=0.0, step=500.0)
        with col2:
            gcat = st.selectbox("Category", ALL_CATEGORIES)
            gtarget_date = st.date_input("Target Date (optional)", value=None)
            gnotes = st.text_area("Notes", placeholder="Any details about this goal...")

        if st.form_submit_button("🎯 Add Goal", type="primary"):
            if gname.strip() and gtarget > 0:
                td = datetime.combine(gtarget_date, datetime.min.time()) if gtarget_date else None
                save_goal(gname.strip(), gtarget, gcurrent, td, gcat, gnotes or None)
                st.success(f"✅ Goal added: {gname}")
                st.rerun()
            else:
                st.error("Please fill in Goal Name and Target Amount.")

    # Show goals
    goals = get_goals()
    if goals:
        st.markdown("### Your Goals")
        for g in goals:
            pct = min(100, (g.current_amount / g.target_amount) * 100) if g.target_amount > 0 else 0
            status = "🏅" if g.is_achieved else ("🔥" if pct >= 75 else "🎯")

            col_a, col_b, col_c = st.columns([4, 1, 1])
            with col_a:
                st.progress(
                    pct / 100,
                    text=f"{status} {g.goal_name}: {format_currency(g.current_amount)} / {format_currency(g.target_amount)} ({pct:.0f}%)"
                )

            with col_b:
                new_amount = st.number_input(
                    "Update ₹", value=float(g.current_amount), step=500.0,
                    key=f"goal_update_{g.id}", label_visibility="collapsed"
                )
                if st.button("📝", key=f"upd_goal_{g.id}", help="Update progress"):
                    update_goal_progress(g.id, new_amount)
                    st.rerun()

            with col_c:
                if st.button("🗑️", key=f"del_goal_{g.id}", help="Delete goal"):
                    delete_goal(g.id)
                    st.rerun()
    else:
        st.info("No goals set yet. Add your first financial goal above!")


def _sip_tab():
    st.markdown("### 📈 SIP Calculator & Recommender")

    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input("Monthly Income (₹)", min_value=1000.0, value=50000.0, step=1000.0)
        monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0.0, value=35000.0, step=1000.0)
        risk = st.select_slider("Risk Tolerance", options=["low", "medium", "high"], value="medium")

    with col2:
        sip_amount = st.number_input("SIP Amount (₹) for projection", min_value=500.0, value=5000.0, step=500.0)
        years = st.slider("Investment Period (years)", 1, 30, 10)
        expected_return = st.slider("Expected Annual Return (%)", 6.0, 20.0, 12.0, step=0.5)

    if st.button("📊 Calculate", type="primary"):
        recommender = SIPRecommender(monthly_income, monthly_expenses, risk, years)
        allocation = recommender.get_sip_allocation()
        returns = recommender.calculate_sip_returns(sip_amount, years, expected_return)

        if "error" in allocation:
            st.error(f"❌ {allocation['error']}")
        else:
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("#### 💼 Recommended SIP Allocation")
                st.metric("Total Monthly SIP", format_currency(allocation['total_monthly_sip']))
                st.metric("Liquid Reserve", format_currency(allocation['liquid_reserve']))
                for fund_type, amount in allocation['allocation'].items():
                    st.write(f"• **{fund_type}:** {format_currency(amount)}/month")

            with col_r:
                st.markdown("#### 📈 SIP Return Projection")
                st.metric("Total Invested", format_currency(returns['total_invested']))
                st.metric("Maturity Value", format_currency(returns['maturity_value']))
                st.metric("Total Gains", format_currency(returns['total_gains']))
                st.metric("Return on Investment", f"{returns['return_rate']}%")


def _tax_tab():
    st.markdown("### 🇮🇳 Indian Tax Planner (FY 2024-25)")

    annual_income = st.number_input("Annual Income (₹)", min_value=0.0, value=800000.0, step=10000.0)

    st.markdown("#### 🧾 Declare Your Investments & Deductions")
    investments = {}
    col1, col2 = st.columns(2)
    for i, (section, details) in enumerate(DEDUCTIONS.items()):
        if details.get("limit"):
            col = col1 if i % 2 == 0 else col2
            investments[section] = col.number_input(
                f"{section} (max ₹{details['limit']:,})",
                min_value=0.0,
                max_value=float(details['limit']),
                value=0.0,
                step=1000.0,
                help=details['description'],
                key=f"tax_{section}"
            )

    if st.button("🧮 Calculate Tax", type="primary"):
        planner = IndianTaxPlanner(annual_income, investments)
        old = planner.calculate_tax_old_regime()
        new = planner.calculate_tax_new_regime()
        recommendation = planner.recommend_regime()
        recs = planner.get_tax_saving_recommendations()

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### 📋 Old Regime")
            st.metric("Taxable Income", format_currency(old['taxable_income']))
            st.metric("Total Tax", format_currency(old['total_tax']))
            st.metric("Effective Rate", f"{old['effective_rate']:.1f}%")

        with col_r:
            st.markdown("#### 📋 New Regime")
            st.metric("Taxable Income", format_currency(new['taxable_income']))
            st.metric("Total Tax", format_currency(new['total_tax']))
            st.metric("Effective Rate", f"{new['effective_rate']:.1f}%")

        st.markdown("#### 🎯 Recommendation")
        st.markdown(recommendation)

        if recs:
            st.markdown("#### 💡 Tax Saving Actions")
            for rec in recs:
                priority_color = "🔴" if rec['priority'] == "HIGH" else "🟡"
                st.write(f"{priority_color} **{rec['action']}** — Save approx. {format_currency(rec['potential_tax_saving'])} (Section {rec['section']})")
