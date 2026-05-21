"""BookLeaf policies and tone guide.

Structured into sections so the AI can retrieve the relevant block per category
instead of mining a long paragraph. Also includes few-shot examples taken from
the assignment brief — these calibrate the model's tone and priority judgement.
"""

COMPANY_OVERVIEW = """\
BookLeaf Publishing is a self-publishing company operating in India and the US.
We offer two packages: Standard Free (no upfront cost) and Bestseller Breakthrough
(premium, paid). We handle cover design, typesetting, ISBN assignment, printing,
distribution, and royalty management. In-house printing and warehouse are in
Delhi. Print partners: Repro India, Epitome Books.
"""

POLICIES = {
    "Royalty & Payments": """\
- Split: 80% net profit to author, 20% to BookLeaf.
- Net profit = MRP minus printing cost, platform commission (Amazon/Flipkart),
  and shipping.
- Calculated quarterly. Paid within 45 days of quarter end.
- Minimum payout threshold: INR 1,000. Below this rolls over to next quarter.
- Payouts via bank transfer to account linked in author dashboard.
- Authors can view a per-platform breakdown in their dashboard.""",

    "ISBN & Metadata Issues": """\
- Every BookLeaf book gets a unique ISBN under BookLeaf's imprint.
- For an author's own imprint, they must obtain ISBN independently.
- ISBN errors (duplicate, wrong book linked) are HIGH PRIORITY: escalate to
  production team. Resolution timeline: 48 hours.
- Metadata updates (description, bio) typically reflect on platforms in
  3–5 business days.""",

    "Printing & Quality": """\
- Most orders printed in-house Delhi. Overflow / specific formats go to Repro
  India or Epitome Books.
- Standard print turnaround: 5–7 business days from order confirmation.
- Quality issues (misprints, binding, color): we arrange a free reprint after
  photo verification of defective copies. Reprint timeline 5–7 business days.""",

    "Distribution & Availability": """\
- Listed on Amazon India, Flipkart, Amazon US, Amazon UK, BookLeaf Store.
- New listings go live within 7–10 business days after publication completes.
- "Currently Unavailable" on a platform usually = stock sync issue. Our team
  triggers a re-sync; expect 24–48 hours to recover.""",

    "Book Status & Production Updates": """\
- Stages: Manuscript Received -> Editing (if opted) -> Cover Design ->
  Typesetting -> Proofreading -> ISBN Assignment -> Printing ->
  Distribution Setup -> Published & Live.
- Authors are notified at each stage by email.
- Common delay points: Cover Design (waiting on author approval) and
  Proofreading (revision rounds).""",

    "General Inquiry": """\
- Catch-all for non-specific questions.
- Account/profile/bio updates can be done from the dashboard.""",
}

TONE_GUIDELINES = """\
- Empathetic and professional. Authors are partners, not customers to manage.
- Acknowledge their concern before jumping to a solution.
- Be specific: real numbers, dates, statuses — never vague.
- Own BookLeaf's mistakes directly when they exist. No corporate deflection.
- For escalations, give a clear timeline (e.g. "team will get back within
  48 hours") instead of open-ended promises.
- End with a clear next step (for the author and/or the BookLeaf team).
- Plain text, 2–4 short paragraphs. No marketing fluff. No emoji.
"""

# Few-shot examples from the assignment brief. These calibrate tone, structure,
# and priority — most important context we can give the model.
SAMPLE_RESPONSES = [
    {
        "category": "Royalty & Payments",
        "priority": "High",
        "query": (
            "I published my book 4 months ago and still haven't received any "
            "royalty. What's going on?"
        ),
        "response": (
            "Thank you for raising this, and I'm sorry for the worry it's "
            "caused. Royalties at BookLeaf are calculated quarterly and paid "
            "within 45 days after the quarter closes, so depending on your "
            "publication date your first cycle may still be in progress.\n\n"
            "I've checked our records and want to confirm a couple of things: "
            "(1) your bank details are linked correctly in your dashboard, and "
            "(2) the next scheduled payout date for your book. If anything is "
            "genuinely overdue, our finance team will resolve it within 48 hours."
        ),
    },
    {
        "category": "Royalty & Payments",
        "priority": "Medium",
        "query": (
            "My royalty amount seems too low. I sold 200 copies but only "
            "received INR 3,000."
        ),
        "response": (
            "Thanks for flagging this — happy to walk through the math.\n\n"
            "Your royalty is 80% of net profit, where net profit = MRP minus "
            "printing cost, platform commission, and shipping. Platform "
            "commissions on Amazon/Flipkart can be 30–55% of MRP, which is "
            "usually why the per-copy amount is lower than expected.\n\n"
            "I can share a per-platform line-by-line breakdown for those 200 "
            "copies so you can see exactly how it adds up. Want me to send it?"
        ),
    },
    {
        "category": "ISBN & Metadata Issues",
        "priority": "Critical",
        "query": (
            "My book is showing a different ISBN on Amazon than what's on the "
            "physical copy."
        ),
        "response": (
            "Thank you for catching this — you're right that it's a serious "
            "data issue, and I'm sorry it's happening on your title.\n\n"
            "I am escalating this to our production team right now. They will "
            "verify which ISBN is correct, fix the listing, and confirm back "
            "to you within 48 hours. In the meantime, please don't change "
            "anything from your end."
        ),
    },
    {
        "category": "Printing & Quality",
        "priority": "High",
        "query": (
            "I received my author copies and the print quality is terrible. "
            "Images are blurry and pages are misaligned."
        ),
        "response": (
            "I'm really sorry — that's not the standard you should be getting "
            "from us, and we'll make it right.\n\n"
            "Could you share a few clear photos of the defective copies "
            "(cover, the misaligned pages, and any blurry images)? Once we "
            "verify, we'll arrange a free reprint and the new copies will "
            "reach you in 5–7 business days from confirmation."
        ),
    },
    {
        "category": "Distribution & Availability",
        "priority": "High",
        "query": (
            'My book is published but it\'s showing as "Currently Unavailable" '
            "on Amazon."
        ),
        "response": (
            "Thank you for letting us know. This is almost always a stock-sync "
            "issue between our warehouse and the platform — not a stock-out.\n\n"
            "I'm triggering a re-sync with our distribution team now. Listings "
            "typically come back live within 24–48 hours. I'll keep an eye on "
            "it and confirm once it's restored."
        ),
    },
    {
        "category": "Book Status & Production Updates",
        "priority": "Medium",
        "query": (
            "It's been 3 weeks and my book is still in typesetting. When will "
            "it be done?"
        ),
        "response": (
            "Thanks for checking in. Let me get you the current status rather "
            "than guess.\n\n"
            "Our typesetting team will send me a precise update by end of "
            "tomorrow, including the updated handover date for proofreading. "
            "If we are waiting on anything from your side (e.g. cover sign-off "
            "or proof revisions), I'll flag exactly what we need so we can "
            "move forward together."
        ),
    },
    {
        "category": "General Inquiry",
        "priority": "Low",
        "query": (
            "Can I update the description of my book on Amazon after it's "
            "already live?"
        ),
        "response": (
            "Yes, absolutely. You can submit metadata updates (description, "
            "keywords, bio, etc.) from your BookLeaf dashboard, or by emailing "
            "the support team with the new copy.\n\n"
            "Once submitted, changes typically reflect on Amazon and other "
            "platforms within 3–5 business days."
        ),
    },
]


# Priority rubric — explicit guide so the model isn't guessing.
PRIORITY_RUBRIC = """\
Critical: Data integrity issues that affect public listings (wrong ISBN on
  Amazon, duplicate ISBN, wrong book linked). Severe financial issues with
  long delay (no royalty for 6+ months despite published book).
High: Royalties significantly delayed (3–5 months, payment overdue), bad
  print quality on author copies, book unavailable on a sales platform.
Medium: Royalty calculation questions, production status questions for an
  in-progress book, regular metadata updates that need action.
Low: Informational / how-to questions (how do I update my bio, can I change
  description, what's the royalty cycle).
"""


def build_policy_block(category: str | None) -> str:
    """Return only the relevant policy section for token efficiency."""
    if category and category in POLICIES:
        return f"Policy section for {category}:\n{POLICIES[category]}"
    return "Policies (all categories):\n" + "\n\n".join(
        f"## {cat}\n{body}" for cat, body in POLICIES.items()
    )


def build_examples_block(category: str | None, max_examples: int = 3) -> str:
    """Pick the most relevant calibration examples — keeps tokens low."""
    if category:
        same = [e for e in SAMPLE_RESPONSES if e["category"] == category]
        others = [e for e in SAMPLE_RESPONSES if e["category"] != category]
        chosen = (same + others)[:max_examples]
    else:
        chosen = SAMPLE_RESPONSES[:max_examples]

    return "\n\n".join(
        f"--- Example ---\n"
        f"Category: {e['category']} | Priority: {e['priority']}\n"
        f"Author query: {e['query']}\n"
        f"Good reply:\n{e['response']}"
        for e in chosen
    )
