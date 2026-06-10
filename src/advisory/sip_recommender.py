# src/advisory/sip_recommender.py

from dataclasses import dataclass
from typing import List


@dataclass
class MutualFund:
    name: str
    category: str
    risk_level: str
    expected_return: float   # CAGR %
    min_sip: float
    platform: str
    use_case: str


RECOMMENDED_FUNDS = [
    MutualFund("Mirae Asset Large Cap Fund", "Large Cap", "Low-Medium", 12.0, 500, "Groww/Zerodha",
               "Core portfolio, stable long-term wealth"),
    MutualFund("Parag Parikh Flexi Cap Fund", "Flexi Cap", "Medium", 13.5, 1000, "Groww/Zerodha",
               "Diversified domestic + international exposure"),
    MutualFund("Axis Small Cap Fund", "Small Cap", "High", 17.0, 500, "Groww/Zerodha",
               "High growth potential, 7+ year horizon"),
    MutualFund("HDFC Short Duration Fund", "Debt", "Low", 7.0, 500, "HDFC AMC",
               "Emergency fund alternative, stable returns"),
    MutualFund("Quant ELSS Tax Saver Fund", "ELSS", "Medium-High", 15.0, 500, "Groww",
               "Tax saving under 80C + equity returns"),
    MutualFund("SBI Nifty Index Fund", "Index Fund", "Low-Medium", 12.0, 500, "Groww/Zerodha",
               "Passive investing, low cost, market returns"),
]


class SIPRecommender:
    """
    Recommends SIP investments based on user's financial profile:
    monthly income, expenses, risk tolerance, and goals.
    """

    def __init__(self, monthly_income: float, monthly_expenses: float,
                 risk_tolerance: str = "medium", investment_horizon: int = 5):
        self.monthly_income = monthly_income
        self.monthly_expenses = monthly_expenses
        self.risk_tolerance = risk_tolerance.lower()
        self.investment_horizon = investment_horizon  # years
        self.investable_surplus = monthly_income - monthly_expenses

    def get_sip_allocation(self) -> dict:
        """
        Recommend SIP allocation based on risk profile.
        Follows standard asset allocation principles adapted for Indian market.
        """
        if self.investable_surplus <= 0:
            return {"error": "No investable surplus. Focus on reducing expenses first."}

        sip_amount = self.investable_surplus * 0.70  # 70% of surplus to SIP, 30% liquid

        if self.risk_tolerance == "low":
            allocation = {
                "Large Cap Fund": 0.50,
                "Debt/Liquid Fund": 0.30,
                "ELSS (80C)": 0.20
            }
        elif self.risk_tolerance == "medium":
            allocation = {
                "Large Cap Fund": 0.30,
                "Flexi Cap Fund": 0.25,
                "Small Cap Fund": 0.15,
                "ELSS (80C)": 0.20,
                "Debt Fund": 0.10
            }
        else:  # high
            allocation = {
                "Flexi Cap Fund": 0.30,
                "Small Cap Fund": 0.30,
                "Mid Cap Fund": 0.20,
                "ELSS (80C)": 0.20
            }

        return {
            "total_monthly_sip": round(sip_amount, -2),  # round to nearest 100
            "allocation": {
                fund: round(sip_amount * pct, -2)
                for fund, pct in allocation.items()
            },
            "liquid_reserve": round(self.investable_surplus * 0.30, -2)
        }

    def calculate_sip_returns(self, monthly_sip: float, years: int,
                               annual_return: float = 12.0) -> dict:
        """
        Calculate SIP maturity value using compound interest formula.
        FV = P × [((1 + r)^n - 1) / r] × (1 + r)
        """
        monthly_rate = annual_return / 100 / 12
        n = years * 12
        invested = monthly_sip * n
        maturity = monthly_sip * ((((1 + monthly_rate)**n - 1) / monthly_rate) * (1 + monthly_rate))
        gains = maturity - invested

        return {
            "monthly_sip": monthly_sip,
            "years": years,
            "total_invested": round(invested, 2),
            "maturity_value": round(maturity, 2),
            "total_gains": round(gains, 2),
            "return_rate": round((gains / invested) * 100, 1)
        }
