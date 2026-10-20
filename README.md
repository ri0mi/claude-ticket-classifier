# claude-ticket-classifier

Webhook-driven ticket classification pipeline built around Claude's Messages API.
Incoming customer messages are classified into a category and urgency level, returned
as schema-validated JSON, and stored with token and latency metrics.

## How it works

```
POST /webhook
   │  1. Authenticate (x-token header)            → 401 if invalid
   │  2. Idempotency check on event_id            → {"status": "duplicate"} if seen
   │  3. Send text to the LLM client (system prompt asks for JSON only)
   │  4. Validate the reply with Pydantic         → retry with the error fed back
   │  5. Retry transient failures with exponential backoff
   ▼
SQLite: category, urgency, summary, input/output tokens, latency (ms)
```

## Design decisions

- **Swappable LLM client.** `FakeClient` and `ClaudeClient` share one interface
  (`complete(text) -> LLMResult`). The whole pipeline, including failure paths, is
  tested offline, at no cost and without network access.
- **Structured output.** The model is instructed to reply with JSON only; the reply is
  validated against a Pydantic schema. Invalid output triggers a retry that includes
  the validation error.
- **Idempotent webhooks.** `event_id` is the primary key, so redelivered events are
  not processed (or billed) twice.
- **Observability.** Tokens and latency are recorded per event, so cost and
  performance can be tracked.
- **CI.** GitHub Actions runs the tests and builds the Docker image on every push.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

```bash
curl -X POST localhost:8000/webhook \
  -H "Content-Type: application/json" -H "x-token: dev-token" \
  -d '{"event_id":"1","text":"I was charged twice this month"}'
```

With Docker:

```bash
docker build -t claude-ticket-classifier .
docker run --rm -p 8000:8000 claude-ticket-classifier
```

## Configuration

| Variable            | Default       | Purpose                                      |
|---------------------|---------------|----------------------------------------------|
| `USE_FAKE`          | `1`           | `1` = simulated client, `0` = Claude API     |
| `ANTHROPIC_API_KEY` | –             | Required when `USE_FAKE=0`                   |
| `WEBHOOK_TOKEN`     | `dev-token`   | Token expected in the `x-token` header       |
| `DB_PATH`           | `events.db`   | SQLite file location                         |

## Status

The pipeline runs end to end against the simulated client. `ClaudeClient` is
implemented but has not yet been exercised against the live API.

## Roadmap

- Run against the live API and compare cost/latency across models
- Tool use (e.g. customer lookup in a CRM) for an agentic flow
- `/stats` endpoint for token and cost reporting
- Queue-based processing (SQS) with a dead-letter queue
