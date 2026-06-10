# src/ui/pages/dashboard.py — Stunning glassmorphism dashboard

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from src.advisory.analytics import SpendingAnalytics
from src.database.crud import (
    get_monthly_expenses, get_budgets, get_goals,
    get_category_totals
)
from src.utils.helpers import format_currency, current_month_str, month_display

# ─── Styling Constants ─────────────────────────────────────────────────────
CHART_TEMPLATE = "plotly_dark"
COLOR_PALETTE = ["#7c3aed", "#06b6d4", "#f59e0b", "#10b981", "#f43f5e",
                 "#3b82f6", "#ec4899", "#84cc16", "#ff7c43", "#a78bfa"]


def _kpi_card(title: str, value: str, subtitle: str = "", color: str = "#7c3aed", delta: str = "") -> str:
    delta_html = f'<div style="font-size:0.75rem;color:#10b981;margin-top:4px">{delta}</div>' if delta else ""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(6,182,212,0.08) 100%);
        border: 1px solid rgba(124,58,237,0.3);
        border-left: 4px solid {color};
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 8px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    ">
        <div style="font-size:0.78rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1.2px;font-weight:600">{title}</div>
        <div style="font-size:1.9rem;font-weight:800;color:#f1f5f9;margin-top:6px;letter-spacing:-0.5px">{value}</div>
        <div style="font-size:0.78rem;color:#64748b;margin-top:4px">{subtitle}</div>
        {delta_html}
    </div>"""


def _health_score(savings_rate: float, budget_adherence: float, has_goals: bool) -> int:
    score = 0
    # Savings rate (0–40 points)
    score += min(40, int(savings_rate * 2))
    # Budget adherence (0–40 points)
    score += min(40, int(budget_adherence * 0.4))
    # Has active goals (20 points)
    if has_goals:
        score += 20
    return min(100, max(0, score))


def _health_gauge(score: int) -> go.Figure:
    color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 40 else "#f43f5e")
    label = "Excellent 🚀" if score >= 80 else ("Good 👍" if score >= 60 else ("Fair ⚠️" if score >= 40 else "Needs Work 🔴"))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': f"Financial Health — {label}", 'font': {'color': '#cbd5e1', 'size': 14}},
        number={'font': {'color': color, 'size': 42}, 'suffix': '/100'},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#475569', 'nticks': 6},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': 'rgba(0,0,0,0)',
            'bordercolor': 'rgba(0,0,0,0)',
            'steps': [
                {'range': [0,  40], 'color': 'rgba(244,63,94,0.15)'},
                {'range': [40, 70], 'color': 'rgba(245,158,11,0.15)'},
                {'range': [70,100], 'color': 'rgba(16,185,129,0.15)'},
            ],
            'threshold': {'line': {'color': color, 'width': 3}, 'value': score}
        }
    ))
    fig.update_layout(
        template=CHART_TEMPLATE, paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=50, b=20),
        height=220, font=dict(color='#cbd5e1')
    )
    return fig


def _donut_chart(data: dict, title: str) -> go.Figure:
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=COLOR_PALETTE, line=dict(color='rgba(0,0,0,0.3)', width=2)),
        textinfo='label+percent', textfont=dict(size=11, color='#cbd5e1'),
        hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(
        template=CHART_TEMPLATE, paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', title=dict(text=title, font=dict(color='#cbd5e1', size=14)),
        showlegend=True, legend=dict(font=dict(color='#94a3b8', size=10)),
        margin=dict(l=10, r=10, t=50, b=10), height=340
    )
    return fig


def _trend_bar_chart(monthly_data: list) -> go.Figure:
    """Gradient bar chart for monthly trends."""
    if not monthly_data:
        return None
    months = [m['month'] for m in monthly_data]
    amounts = [m['amount'] for m in monthly_data]
    fig = go.Figure(go.Bar(
        x=months, y=amounts,
        marker=dict(
            color=amounts,
            colorscale=[[0, '#7c3aed'], [0.5, '#06b6d4'], [1, '#10b981']],
            showscale=False,
            line=dict(color='rgba(0,0,0,0.2)', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>',
        text=[f'₹{a:,.0f}' for a in amounts],
        textposition='outside',
        textfont=dict(color='#94a3b8', size=10)
    ))
    fig.update_layout(
        template=CHART_TEMPLATE, paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(text='📈 Monthly Spending Trend', font=dict(color='#cbd5e1', size=14)),
        xaxis=dict(tickangle=-30, tickfont=dict(color='#94a3b8', size=10), gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(tickfont=dict(color='#94a3b8'), gridcolor='rgba(255,255,255,0.05)', tickprefix='₹'),
        margin=dict(l=10, r=10, t=50, b=60), height=340
    )
    return fig


def _budget_progress_html(category, spent, limit):
    pct = min(100, (spent / limit * 100)) if limit > 0 else 0
    remaining = limit - spent
    color = "#10b981" if pct < 60 else ("#f59e0b" if pct < 90 else "#f43f5e")
    overflow = pct >= 100
    return f"""
    <div style="margin-bottom:16px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
        <span style="color:#cbd5e1;font-size:0.85rem;font-weight:600">{category}</span>
        <span style="color:{color};font-size:0.82rem">
          {format_currency(spent)} / {format_currency(limit)}
          {"  🔴 OVER" if overflow else f"  ({remaining:,.0f} left)"}
        </span>
      </div>
      <div style="background:rgba(255,255,255,0.08);border-radius:8px;height:8px;overflow:hidden;">
        <div style="
          width:{pct}%;height:100%;
          background:linear-gradient(90deg,{color}88,{color});
          border-radius:8px;
          transition:width 0.6s ease;
        "></div>
      </div>
    </div>"""


def show():
    current_month = current_month_str()
    month_disp = month_display(current_month)

    # Page header
    st.markdown(f"""
    <div style="margin-bottom:28px;">
      <h1 style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#7c3aed,#06b6d4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        📊 Financial Dashboard
      </h1>
      <p style="color:#64748b;margin:4px 0 0;font-size:0.9rem">
        {datetime.now().strftime('%A, %d %B %Y')} &nbsp;·&nbsp; {month_disp}
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Load Data ──────────────────────────────────────────────────────────
    expenses = get_monthly_expenses(current_month)
    total_debit  = sum(e.amount for e in expenses if e.transaction_type == 'debit')
    total_credit = sum(e.amount for e in expenses if e.transaction_type == 'credit')
    num_tx       = len(expenses)
    goals        = get_goals()
    active_goals = [g for g in goals if not g.is_achieved]
    budgets      = get_budgets(current_month)
    cat_totals   = get_category_totals(current_month)

    # Last month comparison
    last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    last_expenses = get_monthly_expenses(last_month)
    last_debit = sum(e.amount for e in last_expenses if e.transaction_type == 'debit')
    mom_delta = ""
    if last_debit > 0:
        diff_pct = ((total_debit - last_debit) / last_debit) * 100
        arrow = "▲" if diff_pct > 0 else "▼"
        color_cls = "🔴" if diff_pct > 0 else "🟢"
        mom_delta = f"{color_cls} {arrow} {abs(diff_pct):.1f}% vs last month"

    # ─── Health Score ───────────────────────────────────────────────────────
    savings_rate = max(0, ((total_credit - total_debit) / total_credit * 100)) if total_credit > 0 else 0
    budget_adherence = 0
    if budgets:
        on_track = sum(1 for b in budgets if cat_totals.get(b.category, 0) <= b.monthly_limit)
        budget_adherence = (on_track / len(budgets)) * 100
    health = _health_score(savings_rate, budget_adherence, bool(active_goals))

    # ─── KPI Row ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(_kpi_card("💸 Total Spent", format_currency(total_debit), month_disp, "#f43f5e", mom_delta), unsafe_allow_html=True)
    with col2:
        st.markdown(_kpi_card("💰 Income", format_currency(total_credit), "Credited this month", "#10b981"), unsafe_allow_html=True)
    with col3:
        net = total_credit - total_debit
        net_color = "#10b981" if net >= 0 else "#f43f5e"
        st.markdown(_kpi_card("📈 Net Savings", format_currency(abs(net)), "Surplus" if net >= 0 else "Deficit", net_color), unsafe_allow_html=True)
    with col4:
        st.markdown(_kpi_card("🧾 Transactions", str(num_tx), f"{len(active_goals)} active goals", "#7c3aed"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Health Gauge + Category Donut ──────────────────────────────────────
    col_gauge, col_donut = st.columns([1, 2])

    with col_gauge:
        st.plotly_chart(_health_gauge(health), use_container_width=True, config={'displayModeBar': False})

        # Quick Insights
        if expenses:
            cats = {}
            for e in expenses:
                if e.transaction_type == 'debit':
                    cats[e.category] = cats.get(e.category, 0) + e.amount
            if cats:
                top_cat = max(cats, key=cats.get)
                top_pct = (cats[top_cat] / total_debit * 100) if total_debit > 0 else 0
                st.markdown(f"""
                <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.25);
                            border-radius:12px;padding:14px 16px;font-size:0.82rem;color:#94a3b8">
                  💡 <b style="color:#cbd5e1">Top spend:</b> {top_cat} ({top_pct:.0f}% of budget)<br><br>
                  💎 <b style="color:#cbd5e1">Savings rate:</b> {savings_rate:.1f}%<br><br>
                  🎯 <b style="color:#cbd5e1">Goals active:</b> {len(active_goals)}
                </div>""", unsafe_allow_html=True)

    with col_donut:
        cat_data = {}
        for e in expenses:
            if e.transaction_type == 'debit':
                cat_data[e.category] = cat_data.get(e.category, 0) + e.amount
        if cat_data:
            fig = _donut_chart(cat_data, f"🏷️ Spending by Category — {month_disp}")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown("""
            <div style="display:flex;align-items:center;justify-content:center;height:340px;
                        background:rgba(255,255,255,0.03);border-radius:16px;border:1px dashed #334155">
              <span style="color:#475569;font-size:0.9rem">📭 No expense data yet.<br>Upload a screenshot to get started!</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Monthly Trend ───────────────────────────────────────────────────────
    analytics = SpendingAnalytics()
    all_exp = analytics.df
    if not all_exp.empty:
        monthly = (
            all_exp[all_exp['transaction_type'] == 'debit']
            .groupby('month')['amount'].sum()
            .tail(8)
            .reset_index()
            .rename(columns={'month': 'month', 'amount': 'amount'})
        )
        monthly_list = monthly.to_dict('records')
        trend_fig = _trend_bar_chart(monthly_list)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})

    # ─── Budget Status ───────────────────────────────────────────────────────
    st.markdown(f"""
    <h3 style="color:#cbd5e1;font-size:1.1rem;font-weight:700;margin:8px 0 16px">
      📏 Budget Status — {month_disp}
    </h3>""", unsafe_allow_html=True)

    if budgets:
        col_b1, col_b2 = st.columns(2)
        half = len(budgets) // 2 + len(budgets) % 2
        with col_b1:
            for budget in budgets[:half]:
                spent = cat_totals.get(budget.category, 0)
                st.markdown(_budget_progress_html(budget.category, spent, budget.monthly_limit), unsafe_allow_html=True)
        with col_b2:
            for budget in budgets[half:]:
                spent = cat_totals.get(budget.category, 0)
                st.markdown(_budget_progress_html(budget.category, spent, budget.monthly_limit), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px dashed #334155;border-radius:12px;
                    padding:20px;text-align:center;color:#475569;font-size:0.9rem">
          No budgets set. Go to <b style="color:#7c3aed">Goals & Budget</b> to set monthly limits.
        </div>""", unsafe_allow_html=True)

    # ─── Recent Transactions ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<h3 style="color:#cbd5e1;font-size:1.1rem;font-weight:700;margin-bottom:12px">
      🕐 Recent Transactions</h3>""", unsafe_allow_html=True)

    recent = sorted(expenses, key=lambda e: e.date, reverse=True)[:10]
    if recent:
        for e in recent:
            is_debit = e.transaction_type == 'debit'
            icon = "💸" if is_debit else "💰"
            amt_color = "#f43f5e" if is_debit else "#10b981"
            prefix = "-" if is_debit else "+"
            st.markdown(f"""
            <div style="
              display:flex;align-items:center;justify-content:space-between;
              background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
              border-radius:10px;padding:12px 16px;margin-bottom:6px;
              hover:background:rgba(255,255,255,0.06);
            ">
              <div style="display:flex;align-items:center;gap:12px">
                <span style="font-size:1.2rem">{icon}</span>
                <div>
                  <div style="font-size:0.88rem;font-weight:600;color:#e2e8f0">{e.merchant}</div>
                  <div style="font-size:0.75rem;color:#64748b">{e.category} · {e.date.strftime('%d %b %Y')}</div>
                </div>
              </div>
              <div style="font-size:0.95rem;font-weight:700;color:{amt_color}">
                {prefix}{format_currency(e.amount)}
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:32px;color:#475569;font-size:0.9rem">
          No transactions this month yet.
        </div>""", unsafe_allow_html=True)

    # ─── Top Merchants ───────────────────────────────────────────────────────
    merchants_fig = analytics.top_merchants_chart(current_month)
    if merchants_fig:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<h3 style="color:#cbd5e1;font-size:1.1rem;font-weight:700;margin-bottom:12px">
          🏪 Top Merchants This Month</h3>""", unsafe_allow_html=True)
        st.plotly_chart(merchants_fig, use_container_width=True, config={'displayModeBar': False})
