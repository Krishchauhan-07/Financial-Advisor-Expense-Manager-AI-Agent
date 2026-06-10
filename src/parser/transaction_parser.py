# src/parser/transaction_parser.py
# Improved parser with better regex, GPT-assisted parsing, and Indian UPI format support.

import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import os
from src.utils.categories import categorize_merchant


@dataclass
class Transaction:
    amount: float
    merchant: str
    category: str
    date: datetime
    payment_method: str
    transaction_type: str   # "debit" or "credit"
    raw_text: str
    confidence: float = 1.0


class TransactionParser:
    """
    Parses raw OCR text into structured Transaction objects.
    Supports:
      - PhonePe/Google Pay/Paytm "Money Paid" screens
      - Bank SMS messages (SBI, HDFC, ICICI, Axis)
      - UPI transaction receipts
      - Manual text input
    Falls back to GPT-4o-mini for structured extraction when regex fails.
    """

    # ─── Compiled Patterns ─────────────────────────────────────────────────────

    # Amount: captures the numeric value separately
    AMOUNT_PATTERNS = [
        # ₹1,300 or ₹ 1300.50
        r'₹\s*([\d,]+(?:\.\d{1,2})?)',
        # Rs. 1,300 or Rs 500
        r'Rs\.?\s*([\d,]+(?:\.\d{1,2})?)',
        # INR 1300
        r'INR\s+([\d,]+(?:\.\d{1,2})?)',
        # "Amount: 1,300" or "Amount ₹1300"
        r'[Aa]mount[:\s]+₹?\s*([\d,]+(?:\.\d{1,2})?)',
        # "Paid ₹1,300" or "Paid Rs 500"
        r'[Pp]aid\s+(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)',
        # "Debited ₹500" (bank SMS)
        r'[Dd]ebited\s+(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)',
        # "Credited ₹500"
        r'[Cc]redited\s+(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)',
        # Money Paid\n\nAmount\n₹1,300  (multiline PhonePe)
        r'[Aa]mount\s*\n+₹?\s*([\d,]+(?:\.\d{1,2})?)',
        # Standalone large number that looks like a price (last resort)
        r'(?<!\d)([\d]{1,2},[\d]{3}(?:\.\d{1,2})?)(?!\d)',
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
        r'\d{4}-\d{2}-\d{2}',       # ISO format
        r'\d{1,2}\s+\w+\s+\d{4}',  # "16 Apr 2026"
    ]

    # Merchant extraction patterns (ordered by specificity)
    MERCHANT_PATTERNS = [
        # "To\nMerchant Name" (PhonePe style)
        r'[Tt]o\s*\n+\s*([A-Za-z][A-Za-z0-9\s&.\-]{2,49})',
        # "Paid to Merchant"
        r'[Pp]aid\s+to\s+([A-Z][A-Za-z0-9\s&.\-]{2,49})',
        # "Sent to Merchant"
        r'[Ss]ent\s+to\s+([A-Z][A-Za-z0-9\s&.\-]{2,49})',
        # "Transfer to Merchant"
        r'[Tt]ransfer(?:red)?\s+to\s+([A-Z][A-Za-z0-9\s&.\-]{2,49})',
        # UPI ID style: merchantname@upi or merchant@bank
        r'([A-Za-z][A-Za-z0-9.\-_]{2,30})@(?:upi|oksbi|okaxis|okhdfcbank|okicici|paytm|ybl|ibl|apl)',
        # "at [MERCHANT NAME]" (credit card style)
        r'\bat\s+([A-Z][A-Z0-9\s&.\-]{2,40})',
        # "UPI/merchant-name" or "UPI-Merchant"
        r'UPI[-/]([A-Za-z][A-Za-z0-9\s.\-]{2,40})',
        # After "To:" label
        r'[Tt]o[:\s]+([A-Z][A-Za-z][A-Za-z0-9\s&.\-]{1,48})',
    ]

    PAYMENT_APPS = {
        'phonepe': 'PhonePe',
        'phone pe': 'PhonePe',
        'google pay': 'Google Pay',
        'gpay': 'Google Pay',
        'paytm': 'Paytm',
        'bhim': 'BHIM UPI',
        'neft': 'NEFT',
        'imps': 'IMPS',
        'rtgs': 'RTGS',
        'upi': 'UPI',
        'debit card': 'Debit Card',
        'credit card': 'Credit Card',
        'net banking': 'Net Banking',
        'online': 'Online',
    }

    def parse(self, raw_text: str, confidence: float = 1.0) -> Optional[Transaction]:
        """Parse raw text into a Transaction object. Returns None if no transaction detected."""
        if not raw_text or not raw_text.strip():
            return None

        amount = self._extract_amount(raw_text)
        if not amount:
            # Last resort: try GPT parsing
            return self._gpt_parse(raw_text, confidence)

        merchant = self._extract_merchant(raw_text)
        date = self._extract_date(raw_text) or datetime.now()
        payment_method = self._extract_payment_method(raw_text.lower())
        transaction_type = self._detect_transaction_type(raw_text.lower())
        category = categorize_merchant(merchant, raw_text)

        return Transaction(
            amount=amount,
            merchant=merchant,
            category=category,
            date=date,
            payment_method=payment_method,
            transaction_type=transaction_type,
            raw_text=raw_text,
            confidence=confidence
        )

    # ─── Amount Extraction ────────────────────────────────────────────────────

    def _extract_amount(self, text: str) -> Optional[float]:
        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # All patterns now capture the numeric group(s)
                groups = [g for g in match.groups() if g is not None]
                if not groups:
                    continue
                num_str = groups[0].replace(",", "").strip()
                try:
                    val = float(num_str)
                    if 0.5 <= val <= 10_000_000:  # Sanity range
                        return val
                except ValueError:
                    continue
        return None

    # ─── Merchant Extraction ──────────────────────────────────────────────────

    def _extract_merchant(self, text: str) -> str:
        for pattern in self.MERCHANT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up: remove trailing punctuation / extra whitespace
                name = re.sub(r'[.\s]+$', '', name)
                name = re.sub(r'\s+', ' ', name)
                if len(name) >= 2:
                    return name[:60]
        return "Unknown Merchant"

    # ─── Date Extraction ──────────────────────────────────────────────────────

    def _extract_date(self, text: str) -> Optional[datetime]:
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group().strip()
                formats = [
                    '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%b %d, %Y',
                    '%d/%m/%y', '%Y-%m-%d', '%d %B %Y', '%B %d, %Y',
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        return None

    # ─── Support Methods ──────────────────────────────────────────────────────

    def _extract_payment_method(self, text_lower: str) -> str:
        for key, value in self.PAYMENT_APPS.items():
            if key in text_lower:
                return value
        return "UPI"  # Most Indian transactions are UPI

    def _detect_transaction_type(self, text_lower: str) -> str:
        credit_keywords = ['credited', 'received', 'refund', 'cashback', 'deposit', 'credit']
        debit_keywords = ['debited', 'paid', 'sent', 'transferred', 'withdrawn', 'purchase', 'payment']
        for word in credit_keywords:
            if word in text_lower:
                return 'credit'
        for word in debit_keywords:
            if word in text_lower:
                return 'debit'
        return 'debit'

    # ─── GPT Fallback ─────────────────────────────────────────────────────────

    def _gpt_parse(self, raw_text: str, confidence: float) -> Optional[Transaction]:
        """Use GPT-4o-mini to extract transaction fields when regex fails."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return None
        try:
            from openai import OpenAI
            import json
            client = OpenAI(api_key=api_key)
            prompt = f"""Extract transaction details from this text. Reply ONLY with valid JSON.
If this is not a financial transaction, return {{"is_transaction": false}}.

Text:
{raw_text[:1500]}

Return JSON with these fields:
{{
  "is_transaction": true,
  "amount": <number in INR>,
  "merchant": "<merchant or recipient name>",
  "date": "<DD/MM/YYYY or null>",
  "payment_method": "<UPI/PhonePe/Google Pay/Paytm/NEFT/Debit Card/etc>",
  "transaction_type": "<debit or credit>"
}}"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0
            )
            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            data = json.loads(content)

            if not data.get("is_transaction"):
                return None

            amount = float(data.get("amount", 0))
            if amount <= 0:
                return None

            merchant = str(data.get("merchant", "Unknown Merchant"))
            payment_method = str(data.get("payment_method", "UPI"))
            transaction_type = str(data.get("transaction_type", "debit"))
            category = categorize_merchant(merchant, raw_text)

            date = datetime.now()
            date_str = data.get("date")
            if date_str:
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

            return Transaction(
                amount=amount,
                merchant=merchant,
                category=category,
                date=date,
                payment_method=payment_method,
                transaction_type=transaction_type,
                raw_text=raw_text,
                confidence=confidence
            )
        except Exception:
            return None
