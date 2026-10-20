import os, sqlite3
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from .claude_client import FakeClient, ClaudeClient
from .processor import classify

app = FastAPI()
client = FakeClient() if os.getenv("USE_FAKE", "1") == "1" else ClaudeClient()
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "dev-token")

db = sqlite3.connect(os.getenv("DB_PATH", "events.db"), check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY, category TEXT, urgency TEXT, summary TEXT,
  input_tokens INT, output_tokens INT, latency_ms INT)""")

class Incoming(BaseModel):
    event_id: str
    text: str

@app.post("/webhook")
def webhook(body: Incoming, x_token: str = Header(default="")):
    if x_token != WEBHOOK_TOKEN:
        raise HTTPException(401, "bad token")
    if db.execute("SELECT 1 FROM events WHERE event_id=?", (body.event_id,)).fetchone():
        return {"status": "duplicate"}          # idempotencia
    ticket, res = classify(client, body.text)
    db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?)",
               (body.event_id, ticket.category, ticket.urgency, ticket.summary,
                res.input_tokens, res.output_tokens, res.latency_ms))
    db.commit()
    return {"status": "ok", "ticket": ticket.model_dump()}