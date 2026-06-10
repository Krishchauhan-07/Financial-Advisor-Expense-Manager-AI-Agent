# src/advisory/indian_tax.py

from dataclasses import dataclass
from typing import List


@dataclass
class TaxSlabOldRegime:
    """Income Tax Slabs — Old Regime FY 2024-25"""
    slabs = [
        (250000, 0.0),
        (500000, 0.05),
        (750000, 0.10),   # After standard deduction
        (1000000, 0.20),
        (float('inf'), 0.30)
    ]


@dataclass
class TaxSlabNewRegime:
    """Income Tax Slabs — New Regime FY 2024-25 (Default from FY 2023-24)"""
    slabs = [
        (300000, 0.0),
        (600000, 0.05),
        (900000, 0.10),
        (1200000, 0.15),
        (1500000, 0.20),
        (float('inf'), 0.30)
    ]


DEDUCTIONS = {
    "Section 80C": {
        "limit": 150000,
        "options": ["ELSS Mutual Fund", "PPF", "NSC", "5-Year FD", "Life Insurance Premium", "Home Loan Principal", "Sukanya Samriddhi"],
        "description": "Most popular deduction. Invest in ELSS for best returns with tax saving."
    },
    "Section 80D": {
        "limit": 25000,   # 50000 for senior citizens
        "options": ["Health Insurance Premium"],
        "description": "Health insurance premium for self/family. Must-have for everyone."
    },
    "Section 80CCD(1B)": {
        "limit": 50000,
        "options": ["NPS (National Pension System)"],
        "description": "Additional ₹50,000 deduction over 80C limit for NPS contributions."
    },
    "Section 24(b)": {
        "limit": 200000,
        "options": ["Home Loan Interest"],
        "description": "Interest on home loan for self-occupied property."
    },
    "HRA": {
        "limit": None,  # Calculated based on salary and rent
        "options": ["House Rent Allowance"],
        "description": "If you pay rent, claim HRA exemption. Save significantly on tax."
    }
}


class IndianTaxPlanner:
    def __init__(self, annual_income: float, investments: dict = None):
        self.annual_income = annual_income
        self.investments = investments or {}

    def calculate_tax_old_regime(self) -> dict:
        """Calculate tax under old regime with deductions."""
        gross = self.annual_income
        standard_deduction = 50000  # FY 2024-25

        # Apply declared deductions
        total_deductions = standard_deduction
        for section, amount in self.investments.items():
            if section in DEDUCTIONS:
                limit = DEDUCTIONS[section].get('limit', 0)
                if limit:
                    total_deductions += min(amount, limit)

        taxable_income = max(0, gross - total_deductions)
        tax = self._compute_tax(taxable_income, TaxSlabOldRegime.slabs)
        cess = tax * 0.04  # 4% health & education cess

        return {
            "regime": "Old Regime",
            "gross_income": gross,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "base_tax": tax,
            "cess": cess,
            "total_tax": tax + cess,
            "effective_rate": ((tax + cess) / gross) * 100 if gross > 0 else 0
        }

    def calculate_tax_new_regime(self) -> dict:
        """Calculate tax under new regime (lower rates, fewer deductions)."""
        standard_deduction = 75000  # Enhanced for FY 2024-25
        taxable_income = max(0, self.annual_income - standard_deduction)
        tax = self._compute_tax(taxable_income, TaxSlabNewRegime.slabs)
        cess = tax * 0.04

        return {
            "regime": "New Regime",
            "gross_income": self.annual_income,
            "total_deductions": standard_deduction,
            "taxable_income": taxable_income,
            "base_tax": tax,
            "cess": cess,
            "total_tax": tax + cess,
            "effective_rate": ((tax + cess) / self.annual_income) * 100 if self.annual_income > 0 else 0
        }

    def recommend_regime(self) -> str:
        """Compare regimes and recommend the better one."""
        old = self.calculate_tax_old_regime()
        new = self.calculate_tax_new_regime()

        savings = new['total_tax'] - old['total_tax']
        if old['total_tax'] < new['total_tax']:
            return f"✅ **Old Regime is better for you.** You save ₹{savings:,.0f} by choosing Old Regime and claiming deductions under 80C, 80D, NPS, etc."
        else:
            return f"✅ **New Regime is better for you.** You save ₹{abs(savings):,.0f} by switching to New Regime. Consider this if you don't have large deductions."

    def get_tax_saving_recommendations(self) -> List[dict]:
        """Suggest specific investment actions to reduce tax."""
        recommendations = []
        total_80c = self.investments.get("Section 80C", 0)
        remaining_80c = max(0, 150000 - total_80c)

        if remaining_80c > 0:
            recommendations.append({
                "action": f"Invest ₹{remaining_80c:,.0f} more in ELSS or PPF",
                "section": "80C",
                "potential_tax_saving": remaining_80c * 0.20,  # approx at 20% slab
                "priority": "HIGH"
            })

        if self.investments.get("Section 80D", 0) == 0:
            recommendations.append({
                "action": "Buy health insurance (minimum ₹5,000/year premium) for self + family",
                "section": "80D",
                "potential_tax_saving": 5000 * 0.20,
                "priority": "HIGH"
            })

        if self.investments.get("Section 80CCD(1B)", 0) == 0:
            recommendations.append({
                "action": "Invest ₹50,000 in NPS for additional deduction over 80C limit",
                "section": "80CCD(1B)",
                "potential_tax_saving": 50000 * 0.20,
                "priority": "MEDIUM"
            })

        return sorted(recommendations, key=lambda x: x['potential_tax_saving'], reverse=True)

    def _compute_tax(self, income: float, slabs: list) -> float:
        tax = 0.0
        prev_limit = 0
        for limit, rate in slabs:
            if income <= prev_limit:
                break
            taxable_in_slab = min(income, limit) - prev_limit
            tax += taxable_in_slab * rate
            prev_limit = limit
        return tax
