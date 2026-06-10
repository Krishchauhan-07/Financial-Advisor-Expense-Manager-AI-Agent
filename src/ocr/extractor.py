# src/ocr/extractor.py
# Multi-strategy OCR with GPT-4o Vision fallback for high accuracy on UPI screenshots

import os
import io
import base64
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


class OCRExtractor:
    """
    Handles OCR extraction from payment screenshots and financial documents.
    Strategy priority:
      1. Tesseract OCR with gentle preprocessing (multiple PSM modes)
      2. GPT-4o Vision fallback if Tesseract confidence is low
    """

    def __init__(self, tesseract_path: str = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_win_path):
                pytesseract.pytesseract.tesseract_cmd = default_win_path

        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    # ─── Preprocessing ────────────────────────────────────────────────────────

    def _preprocess_gentle(self, image: Image.Image) -> Image.Image:
        """Gentle preprocessing: upscale + mild contrast boost. Good for modern UPI screenshots."""
        # Upscale if small
        w, h = image.size
        if w < 800 or h < 800:
            scale = max(800 / w, 800 / h)
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Mild contrast boost
        enhancer = ImageEnhance.Contrast(image.convert("RGB"))
        return enhancer.enhance(1.4)

    def _preprocess_aggressive(self, image: Image.Image) -> Image.Image:
        """Aggressive preprocessing for scanned docs / low-res images."""
        img_array = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        # Upscale
        if gray.shape[1] < 1000:
            scale = 1000 / gray.shape[1]
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        return Image.fromarray(thresh)

    # ─── Tesseract Extraction ──────────────────────────────────────────────────

    def _tesseract_extract(self, image: Image.Image, psm: int = 6) -> dict:
        """Run Tesseract with a given PSM mode and return text + confidence."""
        config = f"--psm {psm} --oem 3"
        try:
            data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT, config=config
            )
            words, confidences = [], []
            for i, word in enumerate(data["text"]):
                conf = int(data["conf"][i])
                if conf > 20 and word.strip():
                    words.append(word)
                    confidences.append(conf)

            raw_text = pytesseract.image_to_string(image, config=config)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            return {"text": raw_text, "confidence": avg_conf, "word_count": len(words)}
        except Exception as e:
            return {"text": "", "confidence": 0, "word_count": 0, "error": str(e)}

    def _best_tesseract_result(self, image: Image.Image) -> dict:
        """Try multiple PSM modes and return the one with most content."""
        gentle = self._preprocess_gentle(image)
        aggressive = self._preprocess_aggressive(image)

        results = []
        for img in [gentle, aggressive]:
            for psm in [6, 4, 3, 11]:
                r = self._tesseract_extract(img, psm)
                if r["text"].strip():
                    results.append(r)

        if not results:
            return {"text": "", "confidence": 0, "word_count": 0}

        # Pick result with highest word_count * confidence score
        best = max(results, key=lambda r: r["word_count"] * r["confidence"])
        return best

    # ─── GPT-4o Vision Fallback ───────────────────────────────────────────────

    def _gpt_vision_extract(self, image_bytes: bytes) -> dict:
        """Use GPT-4o Vision to extract transaction data from image."""
        if not self.openai_key:
            return {"text": "", "confidence": 0, "success": False, "error": "No API key"}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)

            # Encode image
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Determine mime type
            img = Image.open(io.BytesIO(image_bytes))
            fmt = img.format or "PNG"
            mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(fmt, "image/png")

            prompt = """Extract ALL text visible in this financial/payment screenshot.
Return the raw text exactly as it appears, line by line.
Pay special attention to:
- Transaction amounts (₹ amounts, numbers)
- Merchant/recipient names
- Transaction ID, UTR numbers
- Date and time
- Payment method (UPI, PhonePe, Google Pay, etc.)
- Status (Success, Paid, etc.)

Return ONLY the extracted text, nothing else."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime};base64,{b64_image}",
                            "detail": "high"
                        }}
                    ]
                }],
                max_tokens=1000
            )
            extracted = response.choices[0].message.content.strip()
            return {"text": extracted, "confidence": 92.0, "success": True, "source": "gpt-vision"}

        except Exception as e:
            return {"text": "", "confidence": 0, "success": False, "error": str(e)}

    # ─── Public API ───────────────────────────────────────────────────────────

    def extract_text(self, image_bytes: bytes) -> dict:
        """
        Main extraction. Returns dict with raw_text, confidence, success, source.
        Strategy: Tesseract first → if low confidence → GPT-4o Vision fallback.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return {"raw_text": "", "confidence": 0, "success": False, "error": f"Cannot open image: {e}"}

        # Step 1: Try Tesseract
        tess_result = self._best_tesseract_result(image)
        tess_text = tess_result["text"].strip()
        tess_conf = tess_result["confidence"]

        # Step 2: Decide if GPT Vision fallback needed
        # Use GPT if: tesseract confidence low OR text is too short OR no amount detected
        needs_fallback = (
            tess_conf < 55 or
            len(tess_text) < 30 or
            not any(c in tess_text for c in ["₹", "Rs", "INR", "1,", "2,", "5,", "0,"])
        )

        if needs_fallback and self.openai_key:
            gpt_result = self._gpt_vision_extract(image_bytes)
            if gpt_result["success"] and len(gpt_result["text"]) > len(tess_text):
                return {
                    "raw_text": gpt_result["text"],
                    "confidence": gpt_result["confidence"],
                    "success": True,
                    "source": "gpt-4o-vision",
                    "word_count": len(gpt_result["text"].split())
                }

        # Return Tesseract result (even if not great)
        if tess_text:
            return {
                "raw_text": tess_text,
                "confidence": round(tess_conf, 2),
                "success": True,
                "source": "tesseract",
                "word_count": tess_result.get("word_count", 0)
            }

        # Both failed — try GPT one more time without threshold
        if self.openai_key:
            gpt_result = self._gpt_vision_extract(image_bytes)
            if gpt_result["success"]:
                return {
                    "raw_text": gpt_result["text"],
                    "confidence": gpt_result["confidence"],
                    "success": True,
                    "source": "gpt-4o-vision",
                    "word_count": len(gpt_result["text"].split())
                }

        return {
            "raw_text": tess_text or "",
            "confidence": tess_conf,
            "success": bool(tess_text),
            "source": "tesseract",
            "error": "Low confidence extraction"
        }

    def extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bank statements using pdfplumber."""
        import pdfplumber
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
