# ==============================================================
# Quote Comparison Chatbot – Final Polished Version (with clean AI output)
# ==============================================================

import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import List
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from core.models import Quote
from core.parser import read_uploaded_file, read_quotes_from_df
from core.pdf_extractor import extract_quotes_from_pdfs
from core.scoring import score_quotes
from utils.logger import get_logger

# ==============================================================
# Initialization
# ==============================================================
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
logger = get_logger("quote_app")

st.set_page_config(page_title="Quote Comparison Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Smart Quote Comparison Chatbot")

client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# ==============================================================
# Sidebar: Family Profile + Weights + Context
# ==============================================================
with st.sidebar:
    st.header("Family & Financial Profile")
    fam_size = st.number_input("Family size", min_value=1, max_value=10, value=4)
    region = st.selectbox("Region / Country", ["United States", "India", "Other"])
    income_level = st.selectbox("Income level", ["Low", "Middle", "High / Rich"])
    ages = st.text_input("Ages (comma-separated)", value="40, 38, 10, 8")
    expected_claims = st.number_input("Expected claims/year", min_value=0, max_value=10, value=1)
    avg_claim = st.number_input("Avg claim amount", min_value=0.0, value=50000.0, step=1000.0)

    st.divider()
    st.caption("Adjust scoring weights (optional):")
    w_cost = st.slider("Cost importance", 0.0, 1.0, 0.6, 0.05)
    w_cov = st.slider("Coverage importance", 0.0, 1.0, 0.3, 0.05)
    w_net = st.slider("Network importance", 0.0, 1.0, 0.1, 0.05)
    total = max(1e-9, w_cost + w_cov + w_net)
    weights = {
        "cost": w_cost / total,
        "coverage": w_cov / total,
        "network": w_net / total,
    }

# ==============================================================
# Upload Section
# ==============================================================
st.markdown("### 📄 Upload Insurance Quote PDFs or CSVs")
uploaded_files = st.file_uploader("Upload files", type=["pdf", "csv", "xlsx", "json"], accept_multiple_files=True)

quotes: List[Quote] = []
if uploaded_files:
    pdfs = [f for f in uploaded_files if f.name.lower().endswith(".pdf")]
    others = [f for f in uploaded_files if not f.name.lower().endswith(".pdf")]

    if pdfs:
        with st.spinner("🔍 Extracting data from PDFs..."):
            pdf_quotes = extract_quotes_from_pdfs(pdfs)
            if pdf_quotes:
                quotes.extend(pdf_quotes)
                st.success(f"Extracted {len(pdf_quotes)} quote(s) from PDFs.")
            else:
                st.warning("No structured data could be extracted from PDFs.")

    for f in others:
        try:
            quotes.extend(read_uploaded_file(f))
        except Exception as e:
            st.error(f"Error reading {f.name}: {e}")

# ==============================================================
# Display Loaded Quotes
# ==============================================================
if quotes:
    st.subheader("📋 Quotes Loaded")
    st.dataframe(pd.DataFrame([asdict(q) for q in quotes]), use_container_width=True)
else:
    st.info("Upload or enter at least one quote to begin.")

# ==============================================================
# Question Input
# ==============================================================
st.divider()
st.subheader("💬 Ask Your Question")
user_question = st.text_input("Example: 'Which plan is best for a rich family of 8 in the US?'")

# ==============================================================
# Local Reasoning Fallback
# ==============================================================
def build_local_summary(df: pd.DataFrame, region: str, income: str, family_size: int) -> str:
    """Fallback structured summary when OpenAI is unavailable."""
    if df.empty:
        return "No quotes available for analysis."

    df = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    best = df.iloc[0]

    bullets = [
        f"- **Best Plan:** {best['plan_name']}",
        f"- **Coverage Score:** {best.get('coverage_score', 'N/A')}",
        f"- **Deductible:** ${best.get('deductible', 0):,}",
        f"- **Coinsurance:** {best.get('coinsurance', 0)*100:.0f}%",
        f"- **Out-of-Pocket Max:** ${best.get('out_of_pocket_max', 0):,}",
    ]

    summary = "### 🧠 Analysis\n" + "\n".join(bullets)
    summary += "\n\n### 🏆 Recommended Plan\n"
    summary += f"**{best['plan_name']}** is the most suitable option for a {income.lower()} income family of {family_size}. "
    summary += "It balances coverage, deductible, and coinsurance most effectively."
    return summary

# ==============================================================
# Ask OpenAI with Structured Markdown Output
# ==============================================================
def ask_openai_context(df: pd.DataFrame, question: str, region: str, income_level: str, family_size: int) -> str:
    """Ask OpenAI model with structured reasoning and consistent formatting."""
    if not client:
        return build_local_summary(df, region, income_level, family_size)

    try:
        context = df.to_dict(orient="records")
        prompt = f"""
You are a senior health insurance advisor. Analyze the following insurance quotes and recommend ONE best plan.

### CONTEXT
Region: {region}
Family size: {family_size}
Income level: {income_level}

### PLANS DATA
{context}

### INSTRUCTIONS
1. Interpret coinsurance correctly:
   - "100%" or 1.0 = insurer pays all after deductible.
   - "0.03" or 3% = user pays 3% after deductible.
2. If the family is 4+ members or income is high, prefer **comprehensive ACA or long-term plans** like Moda Beacon Gold.
3. Short-term or limited plans (e.g. Security Health Advisors) are unsuitable for families.
4. Format the output exactly like this:

### 🧠 Analysis
- 3–5 concise bullet points comparing cost, deductible, and coverage
- Mention trade-offs clearly

### 🏆 Recommended Plan
**Plan Name:** (Best Plan)
**Reasons:**
- Reason 1
- Reason 2
- Reason 3
- Reason 4

### 💡 Summary
One short paragraph summarizing why this plan is ideal for this family context.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=750,
        )

        text = response.choices[0].message.content.strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    except OpenAIError as e:
        print(f"⚠️ API Error: {e}")
        return build_local_summary(df, region, income_level, family_size)

# ==============================================================
# Run Analysis and Display
# ==============================================================
if user_question and quotes:
    ranked = score_quotes(quotes, int(expected_claims), float(avg_claim), weights)
    with st.spinner("Analyzing with context awareness..."):
        answer = ask_openai_context(ranked, user_question, region, income_level, fam_size)

    # Markdown formatting fix for long outputs
    st.markdown(
        """
        <style>
        div[data-testid="stMarkdownContainer"] p {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(answer)

elif user_question and not quotes:
    st.warning("Please upload or enter at least one quote before asking a question.")

# ==============================================================
# Footer
# ==============================================================
st.divider()
st.caption("🧠 OCR via Tesseract • Context-Aware AI Reasoning • Structured Markdown Output • Smart Plan Selection")
