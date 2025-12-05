# core/pdf_extractor.py
import io
import re
from typing import List, Dict
import pdfplumber
import pytesseract
from PIL import Image
from .models import Quote


def clean_number(value: str) -> float:
    """Clean numeric strings like '6,500' or '6\n500' -> 6500.0"""
    if not value:
        return 0.0
    value = re.sub(r"[^0-9]", "", value)
    try:
        return float(value)
    except ValueError:
        return 0.0


def extract_text_from_pdf(file_bytes: bytes, file_name: str) -> str:
    """Extract text from every page using text + OCR fallback."""
    all_text = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    all_text.append(text)
                else:
                    try:
                        img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(img)
                        all_text.append(ocr_text)
                    except Exception as e:
                        print(f"OCR failed on {file_name} (page {i+1}): {e}")
    except Exception as e:
        print(f"PDF read error in {file_name}: {e}")
    return "\n".join(all_text)


def parse_quote_from_text(text: str) -> Dict[str, float]:
    """Parse key insurance fields from text."""
    fields = {}

    # More flexible regex that tolerates line breaks and commas
    patterns = {
        "premium": r"(?:annual\s+premium|premium)[^\d]*(\d[\d,\n ]+)",
        "deductible": r"(?:deductible)[^\d]*(\d[\d,\n ]+)",
        "coinsurance": r"(?:coinsurance)[^\d]*(\d+)%?",
        "out_of_pocket_max": r"(?:out[- ]?of[- ]?pocket(?:\s*maximum|\s*max)?)[^\d]*(\d[\d,\n ]+)",
        "coverage_limit": r"(?:coverage\s*limit|sum\s*insured)[^\d]*(\d[\d,\n ]+)",
        "network_size": r"(?:network\s*size)[^\d]*(\d[\d,\n ]+)"
    }

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            # Combine multi-line fragments like '6\n500'
            combined = "".join(matches[0].split())
            fields[key] = clean_number(combined)

    # Normalize coinsurance
    if "coinsurance" in fields and fields["coinsurance"] > 1:
        fields["coinsurance"] /= 100.0

    return fields


def extract_quotes_from_pdfs(uploaded_files) -> List[Quote]:
    """Extract data from all uploaded PDFs."""
    quotes = []
    for f in uploaded_files:
        try:
            print(f"📘 Processing: {f.name}")
            text = extract_text_from_pdf(f.getvalue(), f.name)
            parsed = parse_quote_from_text(text)
            print(f"🧾 Extracted Fields from {f.name}: {parsed}")

            if not parsed:
                print(f"⚠️ No valid fields found in {f.name}")
                continue

            quotes.append(
                Quote(
                    plan_name=f.name.replace(".pdf", ""),
                    premium=parsed.get("premium", 0.0),
                    deductible=parsed.get("deductible", 0.0),
                    coinsurance=parsed.get("coinsurance", 0.2),
                    out_of_pocket_max=parsed.get("out_of_pocket_max", 0.0),
                    coverage_limit=parsed.get("coverage_limit"),
                    network_size=parsed.get("network_size"),
                )
            )

        except Exception as e:
            print(f"❌ Error processing {f.name}: {e}")
            continue

    print(f"✅ Total quotes extracted: {len(quotes)}")
    return quotes
