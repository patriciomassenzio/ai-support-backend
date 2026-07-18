"""Ticket classification and reply drafting.

Uses the OpenAI API when OPENAI_API_KEY is set; otherwise falls back to a
deterministic rule-based engine so the API works out of the box (demo mode).
"""
import json
import re

from app.config import settings

CATEGORIES = ["billing", "technical", "account", "shipping", "general"]
PRIORITIES = ["urgent", "high", "normal"]

_KEYWORDS = {
    "billing": ["invoice", "charge", "payment", "refund", "billing", "price", "credit card"],
    "technical": ["error", "bug", "crash", "not working", "broken", "fail", "exception", "500"],
    "account": ["password", "login", "account", "sign in", "2fa", "locked", "email change"],
    "shipping": ["delivery", "shipping", "package", "tracking", "arrived", "courier"],
}
_URGENT = ["urgent", "asap", "immediately", "critical", "down", "cannot access", "locked out"]
_HIGH = ["today", "important", "frustrated", "second time", "still waiting"]


def _rule_based(subject: str, body: str) -> dict:
    text = f"{subject} {body}".lower()
    category, best = "general", 0
    for cat, words in _KEYWORDS.items():
        hits = sum(1 for w in words if w in text)
        if hits > best:
            category, best = cat, hits
    if any(w in text for w in _URGENT):
        priority = "urgent"
    elif any(w in text for w in _HIGH):
        priority = "high"
    else:
        priority = "normal"
    confidence = min(0.55 + 0.15 * best, 0.95) if best else 0.5
    return {"category": category, "priority": priority, "confidence": round(confidence, 2)}


def _rule_based_reply(subject: str, category: str) -> str:
    openers = {
        "billing": "Thanks for reaching out about your billing question.",
        "technical": "Sorry you ran into a technical issue — let's get it fixed.",
        "account": "Thanks for contacting us about your account.",
        "shipping": "Thanks for your message about your delivery.",
        "general": "Thanks for getting in touch.",
    }
    return (
        f"Hi,\n\n{openers[category]} We've received your request "
        f'("{subject}") and a member of our team is reviewing it now. '
        "We'll get back to you shortly with next steps.\n\n"
        "Best regards,\nSupport Team"
    )


def classify_ticket(subject: str, body: str) -> dict:
    """Return {category, priority, confidence}."""
    if not settings.openai_api_key:
        return _rule_based(subject, body)

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "Classify this support ticket.\n"
        f"Categories: {CATEGORIES}. Priorities: {PRIORITIES}.\n"
        f"Subject: {subject}\nBody: {body}\n\n"
        'Reply with JSON only: {"category": ..., "priority": ..., "confidence": 0.0-1.0}'
    )
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = resp.choices[0].message.content
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(match.group()) if match else {}
    if data.get("category") not in CATEGORIES:
        return _rule_based(subject, body)
    return {
        "category": data["category"],
        "priority": data.get("priority", "normal"),
        "confidence": float(data.get("confidence", 0.7)),
    }


def draft_reply(subject: str, body: str, category: str) -> str:
    """Draft a suggested reply for an agent to review."""
    if not settings.openai_api_key:
        return _rule_based_reply(subject, category)

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You draft short, empathetic customer support replies. "
                    "Never promise refunds or commitments; propose next steps."
                ),
            },
            {"role": "user", "content": f"Category: {category}\nSubject: {subject}\n\n{body}"},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
