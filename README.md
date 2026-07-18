# AI Customer Support Backend

REST API that ingests customer support tickets, classifies them by **category** and **priority** using an LLM, and drafts a suggested reply for the support agent — all persisted and queryable.

Built with **FastAPI · SQLAlchemy · OpenAI API · PostgreSQL/SQLite**.

## Features

- 🎯 **Auto-classification** — every new ticket gets a category (`billing`, `technical`, `account`, `shipping`, `general`), a priority (`urgent`, `high`, `normal`) and a confidence score.
- ✍️ **AI reply drafting** — a suggested response is generated for agents to review and send.
- 🧪 **Demo mode** — no API key? The service falls back to a deterministic rule-based classifier, so you can run and test it in 30 seconds.
- 📊 **Stats endpoint** — ticket counts by category/priority/status for dashboards.
- 🐳 **Dockerized** — one command to run anywhere. SQLite by default, PostgreSQL via `DATABASE_URL`.

## Quickstart

```bash
git clone <this-repo> && cd ai-support-backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # add OPENAI_API_KEY for real AI mode
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tickets` | Create ticket → auto-classify + draft reply |
| GET | `/tickets` | List, filter by `category`/`priority`/`status` |
| GET | `/tickets/{id}` | Ticket detail |
| PATCH | `/tickets/{id}` | Update status (`open→resolved`, etc.) |
| POST | `/tickets/{id}/reclassify` | Re-run AI classification |
| GET | `/tickets/stats` | Aggregated counts |

### Example

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"jane@example.com","subject":"Payment charged twice","body":"My card shows a duplicate charge. Please refund."}'
```

```json
{
  "id": 1,
  "category": "billing",
  "priority": "normal",
  "confidence": 0.85,
  "suggested_reply": "Hi, thanks for reaching out about your billing question..."
}
```

## Tests

```bash
pytest -v
```

## Architecture notes

- `app/services/ai.py` isolates all LLM logic behind two functions (`classify_ticket`, `draft_reply`) — swapping providers (OpenAI → Claude → local model) touches one file.
- Rule-based fallback keeps the API deterministic in tests and demos.
- SQLAlchemy 2.0 typed models; `DATABASE_URL` swaps SQLite → PostgreSQL with zero code changes.

## Roadmap

- [ ] Webhook ingestion (email → ticket)
- [ ] Agent auth (JWT)
- [ ] Semantic duplicate detection with embeddings

## License

Patricio Massenzio
