"""AI integration for BookLeaf author support tickets.

Two responsibilities:
1. classify_ticket(subject, description) -> (category, priority)
2. draft_response(ticket) -> str

Design notes (asked about in interview):
- API key is read from settings/env only — never sent to the frontend.
- Knowledge base is split per category. We send only the relevant section to
  keep prompts short (cost-conscious).
- Few-shot examples from the brief calibrate tone and priority.
- Graceful degradation: if OPENAI_API_KEY is missing or the API call fails,
  we fall back to keyword rules and a polite generic draft so the ticket flow
  never breaks.
"""

from __future__ import annotations

import json
import logging
import os
import re

from django.conf import settings

from .knowledge_base import (
    COMPANY_OVERVIEW,
    PRIORITY_RUBRIC,
    TONE_GUIDELINES,
    build_examples_block,
    build_policy_block,
)
from .models import Ticket

logger = logging.getLogger(__name__)


# ---------- Fallback rules (used if no key, or AI call fails) ----------

# Order matters: more specific categories should appear first when ambiguous.
CATEGORY_KEYWORDS = [
    (
        Ticket.Category.ISBN,
        ["isbn", "wrong isbn", "different isbn", "duplicate isbn", "metadata", "barcode"],
    ),
    (
        Ticket.Category.PRINTING,
        [
            "print quality", "misprint", "blurry", "binding", "misaligned",
            "defective", "damaged copy", "reprint",
        ],
    ),
    (
        Ticket.Category.DISTRIBUTION,
        [
            "amazon", "flipkart", "unavailable", "out of stock",
            "distribution", "not available", "stock sync",
        ],
    ),
    (
        Ticket.Category.PRODUCTION,
        [
            "typesetting", "cover design", "proofreading", "in production",
            "still in", "when will it be published",
        ],
    ),
    (
        Ticket.Category.ROYALTY,
        ["royalty", "royalties", "payment", "payout", "haven't received", "low amount"],
    ),
]

CRITICAL_PHRASES = [
    "6 months", "six months", "no royalty", "never received any royalty",
    "wrong isbn on amazon", "duplicate isbn", "different isbn",
]

HIGH_PHRASES = [
    "haven't received", "havent received", "overdue", "delayed payment",
    "print quality", "misaligned", "blurry",
    "currently unavailable", "out of stock", "not showing",
]

LOW_PHRASES = [
    "update my bio", "change description", "update description",
    "how do i", "how does", "general question",
]


def _fallback_category(text: str) -> str:
    lower = text.lower()
    for category, words in CATEGORY_KEYWORDS:
        if any(w in lower for w in words):
            return category
    return Ticket.Category.GENERAL


def _fallback_priority(text: str) -> str:
    lower = text.lower()
    if any(p in lower for p in CRITICAL_PHRASES):
        return Ticket.Priority.CRITICAL
    if any(p in lower for p in HIGH_PHRASES):
        return Ticket.Priority.HIGH
    if any(p in lower for p in LOW_PHRASES):
        return Ticket.Priority.LOW
    return Ticket.Priority.MEDIUM


# ---------- OpenAI helpers ----------

def _openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _parse_json_block(raw: str) -> dict:
    """Extract a JSON object from model output."""
    if not raw:
        return {}
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


# ---------- Public API ----------

def classify_ticket(subject: str, description: str) -> tuple[str, str]:
    """Return (category, priority) for a new ticket."""
    text = f"{subject}\n{description}"
    client = _openai_client()
    if not client:
        logger.info("AI classify: no OpenAI key, using fallback rules")
        return _fallback_category(text), _fallback_priority(text)

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    valid_categories = [c.value for c in Ticket.Category]
    valid_priorities = [p.value for p in Ticket.Priority]

    system_prompt = (
        "You are an experienced BookLeaf Publishing support triage agent.\n"
        "Read the author's ticket and return ONLY a JSON object with two fields: "
        "category and priority.\n\n"
        f"Allowed categories: {valid_categories}\n"
        f"Allowed priorities: {valid_priorities}\n\n"
        "Priority rubric:\n"
        f"{PRIORITY_RUBRIC}\n"
        "Examples to calibrate your judgement:\n"
        f"{build_examples_block(category=None, max_examples=4)}"
    )

    user_prompt = (
        f"Ticket subject: {subject}\n"
        f"Ticket description: {description}\n\n"
        'Reply ONLY as JSON: {"category": "...", "priority": "..."}'
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=80,
            response_format={"type": "json_object"},
        )
        data = _parse_json_block(response.choices[0].message.content or "")
        category = data.get("category")
        priority = data.get("priority")
        if category not in valid_categories:
            category = _fallback_category(text)
        if priority not in valid_priorities:
            priority = _fallback_priority(text)
        return category, priority
    except Exception as exc:
        logger.warning("AI classify failed: %s — using fallback", exc)
        return _fallback_category(text), _fallback_priority(text)


def _book_context(ticket) -> str:
    """Concise book context, only when we have a book linked."""
    if not ticket.book:
        return "No specific book is linked — this is a general/account-level query."
    b = ticket.book
    parts = [
        f"Title: {b.title}",
        f"ISBN: {b.isbn or 'n/a'}",
        f"Status: {b.status}",
    ]
    if b.publication_date:
        parts.append(f"Published: {b.publication_date}")
    if b.mrp is not None:
        parts.append(f"MRP: INR {b.mrp}")
    parts.append(f"Copies sold: {b.total_copies_sold}")
    parts.append(f"Royalty earned: INR {b.total_royalty_earned}")
    parts.append(f"Royalty paid: INR {b.royalty_paid}")
    parts.append(f"Royalty pending: INR {b.royalty_pending}")
    if b.last_royalty_payout_date:
        parts.append(f"Last payout: {b.last_royalty_payout_date}")
    return " | ".join(parts)


def _generic_draft(ticket) -> str:
    """Polite, useful default when AI is unavailable."""
    first_name = ticket.author.user.first_name or "there"
    return (
        f"Hi {first_name},\n\n"
        f"Thanks for reaching out about \"{ticket.subject}\". I've logged your "
        f"query and our team is looking into it. We will get back to you within "
        f"48 hours with a clear next step.\n\n"
        f"If you have any photos, screenshots, or extra details that could help "
        f"us resolve this faster, please reply to this ticket and attach them.\n\n"
        f"Best,\nBookLeaf Support Team"
    )


def draft_response(ticket) -> str:
    """Draft a reply for the admin to review and edit before sending."""
    client = _openai_client()
    if not client:
        logger.info("AI draft: no OpenAI key, using generic template")
        return _generic_draft(ticket)

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    author_name = ticket.author.user.get_full_name() or ticket.author.user.first_name or "Author"

    # Send only the policy section relevant to this category — saves tokens.
    policy_block = build_policy_block(ticket.category)
    examples_block = build_examples_block(ticket.category, max_examples=2)

    system_prompt = (
        "You are a BookLeaf Publishing support representative.\n\n"
        f"{COMPANY_OVERVIEW}\n"
        f"{policy_block}\n\n"
        "Tone and structure:\n"
        f"{TONE_GUIDELINES}\n"
        "Your reply MUST follow this structure:\n"
        "1. One short empathetic acknowledgement of the author's concern.\n"
        "2. Specific explanation grounded in BookLeaf policy (use real numbers / "
        "timelines from the policy section).\n"
        "3. A clear next step or commitment (with a 24/48-hour timeline if it "
        "needs escalation or investigation).\n"
        "4. Sign off as BookLeaf Support.\n\n"
        "Calibration examples:\n"
        f"{examples_block}"
    )

    user_prompt = (
        f"Author: {author_name}\n"
        f"Book context: {_book_context(ticket)}\n"
        f"Detected category: {ticket.category}\n"
        f"Detected priority: {ticket.priority}\n\n"
        f"Subject: {ticket.subject}\n"
        f"Description: {ticket.description}\n\n"
        "Write the reply now (plain text, 2–4 short paragraphs)."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=450,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or _generic_draft(ticket)
    except Exception as exc:
        logger.warning("AI draft failed: %s — using generic template", exc)
        return _generic_draft(ticket)
