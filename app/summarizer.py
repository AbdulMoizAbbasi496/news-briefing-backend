from __future__ import annotations

import re
from app.config import settings


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def local_summary(title: str, raw_summary: str = "") -> tuple[str, str]:
    """Free fallback summary. No LLM needed."""
    text = clean_text(raw_summary)
    if not text or len(text) < 30:
        text = clean_text(title)

    words = text.split()
    short = " ".join(words[:32])
    if len(words) > 32:
        short += "..."

    summary = f"• {short}"
    why = "Why it matters: Ye update current affairs aur daily awareness ke liye relevant hai."
    return summary, why


def ai_summary(title: str, raw_summary: str = "") -> tuple[str, str]:
    if not settings.USE_AI_SUMMARY or not settings.GEMINI_API_KEY:
        return local_summary(title, raw_summary)

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
You are making a concise daily news briefing for Pakistani students.
Return exactly this format:
Summary: one clear sentence under 25 words.
Why it matters: one clear sentence under 20 words.

Title: {title}
Text: {raw_summary}
"""
        response = model.generate_content(prompt)
        out = clean_text(response.text)

        summary = ""
        why = ""
        for part in out.split("Why it matters:"):
            if part.lower().startswith("summary:"):
                summary = part.replace("Summary:", "").strip()
            else:
                why = part.strip()
        if not summary:
            return local_summary(title, raw_summary)
        return f"• {summary}", f"Why it matters: {why or 'Important daily update.'}"
    except Exception:
        return local_summary(title, raw_summary)
