# BookLeaf Author Support & Communication Portal

A full-stack support portal for BookLeaf Publishing authors and the internal support team, with AI-assisted ticket classification and reply drafting.

## Tech Stack

- **Backend:** Python 3.11+, Django 5, Django REST Framework, JWT (SimpleJWT), drf-spectacular (Swagger).
- **Frontend:** React 18 + Vite, React Router, plain CSS.
- **Database:** SQLite (local), can be swapped to PostgreSQL via `DATABASES` env config.
- **AI:** OpenAI-compatible API (default: OpenRouter free tier with `deepseek/deepseek-chat-v3.1:free`). Drop-in for OpenAI / DeepSeek / Groq by changing 3 env vars.
- **Auth:** Email + password, JWT access/refresh, RBAC (`author` / `admin`).

## Live Demo

- **Live URL:** `https://bookleef.voltrify.in/`
- **API docs (Swagger):** `https://bookleef.voltrify.in/api/docs/`

## Test Credentials

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@bookleaf.com` | `admin123` |
| Author | `priya.sharma@email.com` | `password123` |
| Author | `rohit.kapoor@email.com` | `password123` |
| Author | `ananya.reddy@email.com` | `password123` |

All seeded authors use the password `password123`.

## Local Setup

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set LLM_API_KEY (free key at https://openrouter.ai/keys)

python manage.py migrate
python manage.py seed_data
python manage.py runserver 8000
```

Backend runs at `http://127.0.0.1:8000` and Swagger docs at `http://127.0.0.1:8000/api/docs/`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env       # default points at http://127.0.0.1:8000
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

## Environment Variables (backend)

See `backend/.env.example`. Key variables:

| Var | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | (dev value) | Set a long random string in prod. |
| `DEBUG` | `True` | Set to `False` in prod. |
| `LLM_API_KEY` | (empty) | If empty, AI gracefully falls back to keyword rules. |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint. |
| `LLM_MODEL` | `deepseek/deepseek-chat-v3.1:free` | Free OpenRouter tier. |

Switch providers by changing only `LLM_*` vars (no code change needed):

```bash
# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# DeepSeek (direct)
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## Features

### Author Portal
- Login (email + password).
- View own books with key fields (status, royalty earned/paid/pending, copies sold, etc.).
- Create new support ticket (subject, description, optional book link).
- See AI-assigned category and priority on submission.
- View list of own tickets with admin reply preview.
- View ticket detail with full conversation thread.

### Admin Portal
- Login as admin.
- Ticket queue with filters: status, category, priority, date range.
- Ordering: priority (Critical → Low) then oldest first — surfaces urgent old tickets.
- Ticket detail: full thread, AI draft (cached, regenerable), category/priority override, status change, internal notes (not visible to author).
- Reply to author — flips status to In Progress automatically.
- Assign-to-me action.

### AI Assistance
- **Classification** on ticket creation: assigns one of 6 categories and a priority (Low / Medium / High / Critical) based on a structured knowledge base, priority rubric, and few-shot examples taken from the assignment brief.
- **Draft response** generation grounded in BookLeaf policy (per-category policy block — not the whole KB — to keep prompts cheap).
- **Graceful fallback:** if the LLM key is missing, the API returns an error, or the call times out, classification falls back to keyword rules and drafting falls back to a polite template. The ticket flow never breaks.

## API Summary

Full schema at `/api/docs/`. Highlights:

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/login/` | any | Email + password → JWT pair |
| GET | `/api/me/` | any auth | Current user |
| GET | `/api/books/` | author | Own books |
| GET/POST | `/api/tickets/` | author | List / create own tickets |
| GET | `/api/tickets/<id>/` | author | Own ticket detail + thread |
| GET | `/api/admin/tickets/` | admin | Ticket queue (filters: status/category/priority/date_from/date_to) |
| GET/PATCH | `/api/admin/tickets/<id>/` | admin | Ticket detail / update status, category, priority |
| POST | `/api/admin/tickets/<id>/reply/` | admin | Reply to author |
| POST | `/api/admin/tickets/<id>/note/` | admin | Add internal note |
| POST | `/api/admin/tickets/<id>/assign-me/` | admin | Self-assign |
| POST | `/api/admin/tickets/<id>/regenerate-draft/` | admin | Re-run AI draft |

## Project Structure

```
bookleaf-portal/
  backend/
    config/         # Django project (settings, urls, wsgi)
    core/           # Single app: models, serializers, views, AI, permissions
      knowledge_base.py   # Policies, tone, few-shot examples
      ai_service.py       # classify_ticket, draft_response, fallback rules
      management/commands/seed_data.py
    data/bookleaf_sample_data.json
    requirements.txt
  frontend/
    src/
      pages/author/
      pages/admin/
      api/client.js
      context/AuthContext.jsx
    package.json
  README.md
  APPROACH.md       # Design notes, trade-offs, cost awareness
```

## Notes & Assumptions

See [`APPROACH.md`](./APPROACH.md) for design rationale, cost-awareness measures, trade-offs, and future improvements.
