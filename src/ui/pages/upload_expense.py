# src/ui/pages/upload_expense.py

import streamlit as st
import pandas as pd
from datetime import datetime
from src.ocr.extractor import OCRExtractor
from src.parser.transaction_parser import TransactionParser
from src.database.crud import save_expense
from src.utils.helpers import format_currency, ALL_CATEGORIES


def show():
    st.title("📤 Upload Expense")
    st.markdown("Upload a payment screenshot, bank SMS screenshot, PDF statement, or enter expense manually.")

    tab1, tab2, tab3 = st.tabs(["📸 Screenshot Upload", "📄 CSV / PDF Upload", "✏️ Manual Entry"])

    with tab1:
        _screenshot_upload_tab()

    with tab2:
        _csv_pdf_upload_tab()

    with tab3:
        _manual_entry_tab()


def _screenshot_upload_tab():
    uploaded_file = st.file_uploader(
        "Upload payment screenshot",
        type=["jpg", "jpeg", "png", "webp"],
        help="Supported: PhonePe, Google Pay, Paytm, Bank SMS screenshots",
        key="img_uploader"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="Uploaded Screenshot", use_container_width=True)

        with col2:
            with st.spinner("🔍 Extracting text from screenshot..."):
                extractor = OCRExtractor()
                result = extractor.extract_text(uploaded_file.read())

            if result["success"]:
                source = result.get("source", "tesseract")
                source_label = "🤖 GPT-4o Vision" if "gpt" in source else "🔍 Tesseract OCR"
                st.success(f"✅ Text extracted via {source_label} (Confidence: {result['confidence']:.0f}%)")

                with st.expander("📝 Raw Extracted Text"):
                    st.text(result["raw_text"])

                # Parse transaction
                parser = TransactionParser()
                transaction = parser.parse(result["raw_text"], result["confidence"] / 100)

                if transaction:
                    st.markdown("### 🧾 Parsed Transaction")
                    st.markdown(f"**Amount:** {format_currency(transaction.amount)}")
                    st.markdown(f"**Merchant:** {transaction.merchant}")
                    st.markdown(f"**Category:** {transaction.category}")
                    st.markdown(f"**Date:** {transaction.date.strftime('%d %b %Y')}")
                    st.markdown(f"**Payment Method:** {transaction.payment_method}")

                    # Allow user to correct
                    st.markdown("### ✏️ Verify & Correct")
                    corrected_amount = st.number_input("Amount (₹)", value=float(transaction.amount), min_value=0.0, key="ocr_amount")
                    corrected_merchant = st.text_input("Merchant", value=transaction.merchant, key="ocr_merchant")
                    default_idx = ALL_CATEGORIES.index(transaction.category) if transaction.category in ALL_CATEGORIES else 0
                    corrected_category = st.selectbox("Category", ALL_CATEGORIES, index=default_idx, key="ocr_category")

                    if st.button("💾 Save Expense", type="primary", key="ocr_save"):
                        save_expense(
                            amount=corrected_amount,
                            merchant=corrected_merchant,
                            category=corrected_category,
                            date=transaction.date,
                            payment_method=transaction.payment_method,
                            raw_text=result["raw_text"],
                            source="screenshot",
                            confidence=result["confidence"] / 100,
                            is_verified=True
                        )
                        st.success("✅ Expense saved successfully!")
                        st.balloons()
                else:
                    st.warning("⚠️ Could not detect a transaction in this image. Please use manual entry.")
            else:
                st.error(f"❌ OCR failed: {result.get('error', 'Unknown error')}")
                st.info("💡 Make sure Tesseract OCR is installed. See README for setup instructions.")


def _csv_pdf_upload_tab():
    st.markdown("### 📄 Upload Bank Statement (CSV or PDF)")
    uploaded = st.file_uploader(
        "Upload file",
        type=["csv", "pdf"],
        help="Upload a CSV bank statement or PDF bank statement",
        key="csv_pdf_uploader"
    )

    if uploaded:
        if uploaded.name.endswith(".csv"):
            _handle_csv(uploaded)
        elif uploaded.name.endswith(".pdf"):
            _handle_pdf(uploaded)


def _handle_csv(uploaded):
    try:
        df = pd.read_csv(uploaded)
        st.markdown("### 📋 Preview (first 10 rows)")
        st.dataframe(df.head(10))

        st.markdown("### 🔧 Map Columns")
        columns = ["(none)"] + list(df.columns)

        col_amount = st.selectbox("Amount column", columns, key="csv_amount_col")
        col_merchant = st.selectbox("Merchant/Description column", columns, key="csv_merchant_col")
        col_date = st.selectbox("Date column", columns, key="csv_date_col")
        col_type = st.selectbox("Debit/Credit column (optional)", columns, key="csv_type_col")

        if st.button("📥 Import CSV Expenses", type="primary", key="csv_import"):
            count = 0
            errors = 0
            for _, row in df.iterrows():
                try:
                    amount_val = float(str(row[col_amount]).replace(",", "").replace("₹", "").strip())
                    merchant_val = str(row[col_merchant]) if col_merchant != "(none)" else "Unknown"
                    date_val = None
                    if col_date != "(none)":
                        try:
                            date_val = pd.to_datetime(row[col_date]).to_pydatetime()
                        except Exception:
                            date_val = datetime.now()

                    from src.utils.categories import categorize_merchant
                    category_val = categorize_merchant(merchant_val)

                    save_expense(
                        amount=amount_val,
                        merchant=merchant_val,
                        category=category_val,
                        date=date_val,
                        source="csv",
                        is_verified=False
                    )
                    count += 1
                except Exception:
                    errors += 1

            st.success(f"✅ Imported {count} expenses. {errors} rows skipped.")
    except Exception as e:
        st.error(f"❌ Could not read CSV: {str(e)}")


def _handle_pdf(uploaded):
    st.info("📄 PDF bank statement detected. Extracting text...")
    try:
        extractor = OCRExtractor()
        text = extractor.extract_from_pdf(uploaded.read())
        with st.expander("📝 Extracted PDF Text (preview)"):
            st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
        st.warning("For PDF statements, please use the Manual Entry tab to add individual transactions after reviewing the extracted text.")
    except Exception as e:
        st.error(f"❌ Could not extract PDF: {str(e)}")


def _manual_entry_tab():
    st.markdown("### ✏️ Add Expense Manually")

    with st.form("manual_expense_form"):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input("Amount (₹) *", min_value=0.01, value=100.0, step=10.0)
            merchant = st.text_input("Merchant / Payee *", placeholder="e.g. Zomato, DMart, Amazon")
            category = st.selectbox("Category *", ALL_CATEGORIES)

        with col2:
            date = st.date_input("Date *", value=datetime.now())
            payment_method = st.selectbox("Payment Method", [
                "UPI", "PhonePe", "Google Pay", "Paytm", "NEFT", "IMPS", "RTGS",
                "Credit Card", "Debit Card", "Cash", "Unknown"
            ])
            transaction_type = st.radio("Type", ["debit", "credit"], horizontal=True)

        notes = st.text_area("Notes (optional)", placeholder="Any additional notes...")
        submitted = st.form_submit_button("💾 Save Expense", type="primary")

        if submitted:
            if amount > 0 and merchant.strip():
                save_expense(
                    amount=amount,
                    merchant=merchant.strip(),
                    category=category,
                    date=datetime.combine(date, datetime.min.time()),
                    payment_method=payment_method,
                    transaction_type=transaction_type,
                    notes=notes if notes.strip() else None,
                    source="manual",
                    is_verified=True
                )
                st.success(f"✅ Saved: {format_currency(amount)} at {merchant} ({category})")
                st.balloons()
            else:
                st.error("⚠️ Please fill in Amount and Merchant fields.")
