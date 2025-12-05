import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --- Always load .env manually from project root ---
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- Fallback in case .env still doesn’t load ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "❌ OPENAI_API_KEY not found. Please check your .env file or environment variables."
    )

# --- Initialize the client explicitly with key ---
client = OpenAI(api_key=api_key)


def explain_choice_llm(df_ranked, family_desc: str) -> str:
    """Uses prompt-engineered LLM for human-like explanation."""
    if df_ranked.empty:
        return "I couldn’t find any valid quote data to compare."

    top_plans = df_ranked.head(3).to_dict(orient="records")
    system_prompt = (
        "You are an insurance advisor. Given multiple quotes, "
        "explain which plan is best for the described family. "
        "Use clear, friendly, non-technical language."
    )

    user_prompt = (
        f"Family details: {family_desc}\n"
        f"Quotes: {top_plans}\n\n"
        "Compare these plans and explain which one is best, why, "
        "and the trade-offs between them in simple language."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=300,
    )

    return response.choices[0].message.content
