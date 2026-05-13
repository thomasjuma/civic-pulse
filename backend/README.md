# Civic Pulse Backend

FastAPI backend for article storage, scheduled source ingestion, OpenAI Agents SDK summarization, and WhatsApp Cloud API delivery.

## Run locally

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The SQLite database defaults to `backend/civic_pulse.db`.

## Environment

Copy `.env.example` to `.env` and set:

- `OPENAI_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`

The scheduled ingestion job runs every `SUMMARY_JOB_INTERVAL_MINUTES`. Set `SUMMARY_JOB_RUN_ON_STARTUP=true` to run it once when the API starts.

