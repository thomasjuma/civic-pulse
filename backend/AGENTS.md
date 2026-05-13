# Backend Agent Guide

## Project overview
- This backend is a FastAPI app for Civic Pulse.
- It stores generated article summaries in SQLite, exposes article/subscriber/ingestion routes, runs scheduled ingestion, uses OpenAI Agents SDK for browser/summarizer agents, and sends WhatsApp Cloud API messages.
- Main code lives in `app/`; tests live in `tests/`.
- Runtime configuration is loaded from `backend/.env` through `app/config.py`.

## Build and test commands
- Create the environment from `backend/`: `python3.12 -m venv .venv`
- Activate it: `source .venv/bin/activate`
- Install dependencies: `pip install -e ".[dev]"`
- Run the API: `uvicorn app.main:app --reload`
- Run all tests: `pytest`
- Run coverage: `pytest --cov=app --cov-report=term-missing`

## Code style guidelines
- Use Python 3.12+ with type hints for new or changed code.
- Keep FastAPI routes thin; put business logic in `services`, persistence in repositories/database helpers, and agent orchestration in `agents`.
- Prefer explicit names, small functions, and simple control flow.
- Use stdlib `logging` for backend logs; keep logs at INFO or ERROR unless requirements change.
- Follow existing Pydantic model and settings patterns instead of introducing new config mechanisms.

## Testing instructions
- Use pytest and pytest-asyncio for async behavior.
- Put focused unit tests near the relevant area: `tests/services`, `tests/routes`, or `tests/agents`.
- Mock external systems: OpenAI, MCP servers, WhatsApp HTTP calls, and network/browser retrieval.
- Use temporary SQLite databases for tests; do not write tests against `backend/civic_pulse.db`.
- Run the narrowest relevant test first, then broader coverage when behavior crosses modules.

## Security considerations
- Never commit `.env`, API keys, WhatsApp tokens, subscriber phone numbers, or real message payloads.
- Do not log secret values; log whether credentials are present only when needed.
- Require explicit WhatsApp consent before sending messages.
- Treat scraped documents and generated summaries as untrusted input; validate and persist through typed models.
- Keep real WhatsApp sending behind configured `WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID`.
