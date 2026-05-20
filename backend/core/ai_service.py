import json
import os
import re

from django.conf import settings

from .knowledge_base import KNOWLEDGE_BASE
from .models import Ticket

# Simple keyword fallback when OpenAI is not configured or fails
CATEGORY_KEYWORDS = {
    Ticket.Category.ROYALTY: ["royalty", "payment", "payout", "paid", "earn"],
    Ticket.Category.ISBN: ["isbn", "metadata", "barcode"],
    Ticket.Category.PRINTING: ["print", "quality", "binding", "misprint", "blurry"],
    Ticket.Category.DISTRIBUTION: ["amazon", "flipkart", "unavailable", "listing", "distribution"],
    Ticket.Category.PRODUCTION: ["production", "typesetting", "cover", "status", "published"],
}

PRIORITY_RULES = [
    (Ticket.Priority.CRITICAL, ["6 months", "never received", "no royalty", "urgent", "critical"]),
    (Ticket.Priority.HIGH, ["isbn", "wrong isbn", "duplicate isbn", "haven't received"]),
    (Ticket.Priority.LOW, ["bio", "update description", "general question"]),
]


def _openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _fallback_category(text: str) -> str:
    lower = text.lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(w in lower for w in words):
            return category
    return Ticket.Category.GENERAL


def _fallback_priority(text: str) -> str:
    lower = text.lower()
    for priority, words in PRIORITY_RULES:
        if any(w in lower for w in words):
            return priority
    return Ticket.Priority.MEDIUM


def _parse_json_block(raw: str) -> dict:
    """Extract JSON object from model text."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def classify_ticket(subject: str, description: str) -> tuple[str, str]:
    """
    Return (category, priority).
    Uses OpenAI if available; otherwise simple rules.
    """
    text = f"{subject}\n{description}"
    client = _openai_client()
    if not client:
        return _fallback_category(text), _fallback_priority(text)

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    prompt = f"""Classify this author support ticket.

Categories: {", ".join(c.value for c in Ticket.Category)}
Priorities: {", ".join(p.value for p in Ticket.Priority)}

Ticket:
Subject: {subject}
Description: {description}

Reply with JSON only: {{"category": "...", "priority": "..."}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120,
        )
        data = _parse_json_block(response.choices[0].message.content or "")
        category = data.get("category", _fallback_category(text))
        priority = data.get("priority", _fallback_priority(text))
        # Validate values
        valid_cats = {c.value for c in Ticket.Category}
        valid_pri = {p.value for p in Ticket.Priority}
        if category not in valid_cats:
            category = _fallback_category(text)
        if priority not in valid_pri:
            priority = _fallback_priority(text)
        return category, priority
    except Exception:
        return _fallback_category(text), _fallback_priority(text)


def draft_response(ticket) -> str:
    """Draft a reply for admins to edit before sending."""
    client = _openai_client()
    book_line = ""
    if ticket.book:
        book_line = (
            f"Book: {ticket.book.title} | Status: {ticket.book.status} | "
            f"Sold: {ticket.book.total_copies_sold} | Pending royalty: ₹{ticket.book.royalty_pending}"
        )

    if not client:
        return (
            f"Dear {ticket.author.user.first_name or 'Author'},\n\n"
            f"Thank you for reaching out about \"{ticket.subject}\". "
            f"We have received your query and our team is reviewing it. "
            f"We will get back to you within 48 hours.\n\n"
            f"Warm regards,\nBookLeaf Support Team"
        )

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    prompt = f"""You are a BookLeaf Publishing support representative.

{KNOWLEDGE_BASE}

Author: {ticket.author.user.get_full_name() or ticket.author.user.email}
{book_line}
Category: {ticket.category}
Priority: {ticket.priority}

Ticket subject: {ticket.subject}
Ticket description: {ticket.description}

Write a helpful, empathetic reply (plain text, 2-4 short paragraphs). Use specific policy details where relevant."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return (
            "Thank you for your message. Our team will review and respond within 48 hours.\n\n"
            "— BookLeaf Support"
        )
