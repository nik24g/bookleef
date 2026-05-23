# Approach, Notes & Assumptions

## Tech Stack Rationale

- **Django + DRF** for the backend: built-in user model + admin, mature auth, permissions, serializers, and OpenAPI schema. Lets a single dev cover author portal, admin portal, and AI integration in 5 days without a microservices distraction.
- **React + Vite** for the frontend: lightweight, fast hot reload, no SSR overhead since this is an internal-style portal (no SEO need).
- **JWT (SimpleJWT)** for auth: stateless, easy to use across browser + future mobile clients, no session affinity required behind a load balancer.
- **SQLite locally, Postgres-ready in prod:** SQLite keeps onboarding to a single command, and Django's ORM means swapping to Postgres is a settings change.

## AI Design

### Two responsibilities, two endpoints internally
- `classify_ticket(subject, description) -> (category, priority)` — fired once, on ticket creation.
- `draft_response(ticket) -> str` — fired once on first admin view of a ticket; cached in `Ticket.ai_draft_response`. Re-fired only when admin clicks "Regenerate".

Splitting these means each call has a tight, task-specific prompt — not a kitchen-sink "do everything" prompt.

### Knowledge base is structured, not a blob
`core/knowledge_base.py` holds:
- `COMPANY_OVERVIEW` (short, sent only on draft).
- `POLICIES` — a dict keyed by category, each ~5–10 lines.
- `TONE_GUIDELINES` (sent only on draft).
- `SAMPLE_RESPONSES` — 7 few-shot examples taken directly from the assignment brief, tagged with category + priority. Used to calibrate both classification and drafting.
- `PRIORITY_RUBRIC` — explicit Critical/High/Medium/Low criteria so the model isn't guessing.

`build_policy_block(category)` and `build_examples_block(category, max_examples)` retrieve only the relevant slice on each call.

### Provider-agnostic LLM client
`core/ai_service.py:_llm_client()` uses the OpenAI Python SDK pointed at any OpenAI-compatible base URL. Default is OpenRouter free tier (`deepseek/deepseek-chat-v3.1:free`), but the same code works for OpenAI, DeepSeek direct, Groq, etc. by changing 3 env vars.

### Graceful degradation
- Missing `LLM_API_KEY` → keyword-rule classifier + polite template draft.
- API exception (rate limit, network) → caught, logged, fallback used.
- Hard 20-second client timeout → defends against the gunicorn worker timeout (free LLM tiers occasionally queue requests beyond 30s).
- The ticket flow never returns a 500 because of an AI failure.

## Cost Awareness

Reviewers asked for evidence we thought about token usage. Concrete measures in the code:

| # | Technique | Where | Effect |
| --- | --- | --- | --- |
| 1 | Per-category policy retrieval (poor-man's RAG) | `knowledge_base.build_policy_block` | Send ~8 lines of relevant policy instead of all 6 sections. ~80% saving on policy tokens. |
| 2 | Category-biased few-shot selection | `knowledge_base.build_examples_block` | Drafts use 2 same-category examples (not all 7). |
| 3 | Different `max_tokens` per task | `ai_service.classify_ticket` (80) vs `draft_response` (450) | Classification doesn't pay for unused output budget. |
| 4 | No conversation history sent to LLM | `draft_response` | We never serialize `ticket.messages` into the prompt. Each call is stateless on history. |
| 5 | Compact book context | `_book_context` | Pipe-delimited single line, not pretty JSON. |
| 6 | Skip book context when not relevant | `_book_context` | Returns one sentence for general queries; no empty-field padding. |
| 7 | AI draft cached in DB | `Ticket.ai_draft_response` field | Admin viewing a ticket 50 times = 1 LLM call, not 50. |
| 8 | Classification fires once on create | `AuthorTicketListCreateView.perform_create` | Stored on the row; not regenerated on list/detail reads. |
| 9 | Cheap-by-default model | `LLM_MODEL` default | Free tier on OpenRouter; if migrating to OpenAI, default would be `gpt-4o-mini`, not `gpt-4o`. |
| 10 | Lazy LLM client | `_llm_client()` | Returns `None` if no key — never opens a connection if AI is disabled. |
| 11 | Bounded fallback on errors | `try/except` in both AI functions | No retry storms; fail fast and serve a fallback response. |

Rough estimate per ticket lifecycle (1 classify + 1 draft):

| | Naive (full KB + all examples every call) | This impl | Saving |
| --- | --- | --- | --- |
| Classification | ~1100 tok | ~680 tok | -38% |
| Draft | ~2300 tok | ~900 tok | -61% |

Things we did **not** do (honest list, future work):
- No prompt caching (OpenAI/Anthropic feature) — would help if traffic scales.
- No semantic deduplication of similar tickets.
- No two-stage "rules first, LLM only on uncertainty" classifier — current keyword rules could pre-filter trivial cases.
- No per-call usage logging (`prompt_tokens` / `completion_tokens`) for spend dashboards.

## Real-Time Updates

Implemented as **client-side polling** (`setInterval` on author Tickets and admin Queue/Detail). Trade-off: simple, works behind any proxy, no extra infra. WebSockets / SSE would be lower-latency and scale better but require Channels + Redis or an SSE-aware proxy — overkill for an evaluation project.

## Security & Privacy

- API keys read from environment only. Never sent to the frontend, never committed.
- `.env` is git-ignored. `.env.example` carries only placeholders.
- JWT tokens carry `role`; permission classes (`IsAuthor`, `IsAdmin`) gate each endpoint.
- Authors can only access their own books and tickets (querysets filter on `request.user.author_profile`).
- Internal notes are never serialized in the author-facing endpoint.
- CORS is restricted to the frontend origin.

## Trade-offs Made on Purpose

| Decision | Why | Acceptable because |
| --- | --- | --- |
| SQLite in default config | Single-command onboarding | Postgres swap is a `DATABASES` change; ORM does the rest. |
| Polling instead of WebSockets | Time-boxed scope | Latency of 5s acceptable for support-ticket UX. |
| Synchronous AI on ticket create | Simplest path to a working demo | Mitigated by 20s SDK timeout + fallback; future work is a Celery/RQ background task. |
| Single Django app `core` | Project size doesn't warrant split | Easy to refactor later if `tickets`, `books`, `users` grow. |
| Plain CSS, no UI library | Avoid heavy bundle for a small UI | Layout is intentionally simple and readable. |

## Assumptions

- Authors authenticate with the email present in `bookleaf_sample_data.json`. Default seeded password is `password123`.
- A single seeded admin (`admin@bookleaf.com` / `admin123`) is enough — multi-admin assignment workflows are supported by the model (`Ticket.assigned_to`) but only one admin is created by `seed_data`.
- "Priority" is system-assigned at creation but admin can override; we record `priority_overridden` so future analytics can measure AI accuracy.
- Royalty/payment policy values (45-day window, 80/20 split, INR 1,000 threshold) are taken verbatim from the assignment brief.
- "AI must be visible in the admin UI" is interpreted as: the draft is shown above the reply box, plus a Regenerate button.

## Future Improvements (out of scope, but I'd do these next)

1. **Background AI:** move `classify_ticket` + `draft_response` into a Celery/RQ task. Ticket creation returns 201 instantly; AI fields populate seconds later. Frontend already polls.
2. **Usage telemetry:** persist `prompt_tokens`, `completion_tokens`, model, and latency per AI call → admin dashboard for spend monitoring.
3. **Confidence-based escalation:** when LLM classification confidence is low (e.g. self-evaluated via a follow-up cheap call), keep the keyword fallback's answer.
4. **WebSockets** via Channels for true push updates instead of polling.
5. **Postgres + Alembic-equivalent migration discipline** in production.
6. **Rate limiting + auth throttling** (DRF throttle classes) on the public API.
7. **Audit log** of admin overrides (category/priority/status) — useful both for accountability and for retraining the AI.
