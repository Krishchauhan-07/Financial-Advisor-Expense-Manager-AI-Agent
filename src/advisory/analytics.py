# src/advisory/analytics.py — Dark theme charts with custom color palette

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from src.database.crud import get_all_expenses

CHART_TEMPLATE = "plotly_dark"
BRAND_COLORS = ["#7c3aed", "#06b6d4", "#f59e0b", "#10b981", "#f43f5e",
                "#3b82f6", "#ec4899", "#84cc16", "#ff7c43", "#a78bfa"]
_LAYOUT_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8'),
    margin=dict(l=10, r=10, t=50, b=40),
)


class SpendingAnalytics:
    """Generate spending analyses and dark-themed visualizations from expense data."""

    def __init__(self):
        expenses = get_all_expenses()
        self.df = self._to_dataframe(expenses)

    def _to_dataframe(self, expenses) -> pd.DataFrame:
        if not expenses:
            return pd.DataFrame()
        data = [{
            'amount': e.amount,
            'merchant': e.merchant,
            'category': e.category,
            'date': e.date,
            'payment_method': e.payment_method,
            'transaction_type': e.transaction_type,
        } for e in expenses]
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').astype(str)
        return df

    def category_pie_chart(self, month: str = None) -> go.Figure | None:
        """Donut chart: spending by category."""
        if self.df.empty:
            return None
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if month:
            df = df[df['month'] == month]
        if df.empty:
            return None

        cat = df.groupby('category')['amount'].sum().reset_index()
        fig = go.Figure(go.Pie(
            labels=cat['category'], values=cat['amount'],
            hole=0.5,
            marker=dict(colors=BRAND_COLORS, line=dict(color='rgba(0,0,0,0.3)', width=2)),
            textinfo='label+percent',
            textfont=dict(size=11, color='#e2e8f0'),
            hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>'
        ))
        fig.update_layout(
            template=CHART_TEMPLATE, **_LAYOUT_BASE,
            title=dict(text=f'Spending by Category — {month or "All Time"}',
                       font=dict(color='#cbd5e1', size=14)),
            legend=dict(font=dict(color='#94a3b8', size=10)),
            height=340
        )
        return fig

    def monthly_trend_chart(self) -> go.Figure | None:
        """Bar chart: monthly spending trend."""
        if self.df.empty:
            return None
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if df.empty:
            return None
        monthly = df.groupby('month')['amount'].sum().reset_index().sort_values('month')
        vals = monthly['amount'].tolist()
        fig = go.Figure(go.Bar(
            x=monthly['month'], y=monthly['amount'],
            marker=dict(
                color=vals,
                colorscale=[[0, '#7c3aed'], [0.5, '#06b6d4'], [1, '#10b981']],
                showscale=False,
                line=dict(color='rgba(0,0,0,0.2)', width=1)
            ),
            hovertemplate='<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            template=CHART_TEMPLATE, **_LAYOUT_BASE,
            title=dict(text='Monthly Spending Trend', font=dict(color='#cbd5e1', size=14)),
            xaxis=dict(tickangle=-30, tickfont=dict(color='#94a3b8', size=10),
                       gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(tickfont=dict(color='#94a3b8'), gridcolor='rgba(255,255,255,0.05)',
                       tickprefix='₹'),
            height=340
        )
        return fig

    def budget_vs_actual_chart(self, budgets: list, month: str) -> go.Figure | None:
        """Horizontal grouped bar: budget vs actual spend per category."""
        if self.df.empty:
            return None
        df = self.df[(self.df['transaction_type'] == 'debit') & (self.df['month'] == month)].copy()
        cat_totals = df.groupby('category')['amount'].sum().to_dict()

        categories, actuals, limits = [], [], []
        for b in budgets:
            categories.append(b.category)
            actuals.append(cat_totals.get(b.category, 0))
            limits.append(b.monthly_limit)

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Budget Limit', x=limits, y=categories,
                             orientation='h', marker_color='rgba(124,58,237,0.4)',
                             marker_line=dict(color='#7c3aed', width=1)))
        fig.add_trace(go.Bar(name='Actual Spend', x=actuals, y=categories,
                             orientation='h', marker_color='rgba(244,63,94,0.7)',
                             marker_line=dict(color='#f43f5e', width=1)))
        fig.update_layout(
            template=CHART_TEMPLATE, **_LAYOUT_BASE,
            barmode='overlay',
            title=dict(text=f'Budget vs Actual — {month}', font=dict(color='#cbd5e1', size=14)),
            xaxis=dict(title='Amount (₹)', tickfont=dict(color='#94a3b8'),
                       gridcolor='rgba(255,255,255,0.05)', tickprefix='₹'),
            yaxis=dict(tickfont=dict(color='#94a3b8')),
            legend=dict(font=dict(color='#94a3b8')),
            height=350
        )
        return fig

    def top_merchants_chart(self, month: str = None, top_n: int = 10) -> go.Figure | None:
        """Horizontal bar chart: top merchants by spend."""
        if self.df.empty:
            return None
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if month:
            df = df[df['month'] == month]
        if df.empty:
            return None

        top = df.groupby('merchant')['amount'].sum().nlargest(top_n).reset_index()
        vals = top['amount'].tolist()
        fig = go.Figure(go.Bar(
            x=top['amount'], y=top['merchant'],
            orientation='h',
            marker=dict(
                color=vals,
                colorscale=[[0, '#7c3aed'], [1, '#06b6d4']],
                showscale=False,
            ),
            hovertemplate='<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>'
        ))
        fig.update_layout(
            template=CHART_TEMPLATE, **_LAYOUT_BASE,
            title=dict(text=f'Top {top_n} Merchants by Spend', font=dict(color='#cbd5e1', size=14)),
            xaxis=dict(tickfont=dict(color='#94a3b8'), gridcolor='rgba(255,255,255,0.05)', tickprefix='₹'),
            yaxis=dict(categoryorder='total ascending', tickfont=dict(color='#94a3b8')),
            height=min(100 + top_n * 35, 420)
        )
        return fig

    def savings_rate_gauge(self, monthly_income: float, month: str = None) -> go.Figure | None:
        """Gauge chart: savings rate."""
        if self.df.empty:
            return None
        df = self.df[self.df['transaction_type'] == 'debit'].copy()
        if month:
            df = df[df['month'] == month]

        total_spent = df['amount'].sum()
        rate = max(0, ((monthly_income - total_spent) / monthly_income) * 100) if monthly_income > 0 else 0
        color = "#10b981" if rate >= 20 else ("#f59e0b" if rate >= 10 else "#f43f5e")

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=rate,
            title={'text': "Savings Rate (%)", 'font': {'color': '#cbd5e1', 'size': 14}},
            number={'font': {'color': color, 'size': 36}, 'suffix': '%'},
            delta={'reference': 20, 'font': {'color': '#94a3b8'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#475569'},
                'bar': {'color': color, 'thickness': 0.25},
                'bgcolor': 'rgba(0,0,0,0)',
                'bordercolor': 'rgba(0,0,0,0)',
                'steps': [
                    {'range': [0, 10], 'color': 'rgba(244,63,94,0.15)'},
                    {'range': [10, 20], 'color': 'rgba(245,158,11,0.15)'},
                    {'range': [20, 35], 'color': 'rgba(16,185,129,0.15)'},
                    {'range': [35, 100], 'color': 'rgba(16,185,129,0.25)'},
                ],
                'threshold': {'value': 20, 'line': {'color': '#7c3aed', 'width': 3}}
            }
        ))
        fig.update_layout(template=CHART_TEMPLATE, **_LAYOUT_BASE)
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        return fig
