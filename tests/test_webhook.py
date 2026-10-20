import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rejects_bad_token():
    r = client.post("/webhook", json={"event_id": "t1", "text": "hola"},
                    headers={"x-token": "mal"})
    assert r.status_code == 401

def test_duplicate_event_is_ignored():
    payload = {"event_id": "dup-test-1", "text": "Necesito ayuda"}
    h = {"x-token": "dev-token"}
    first = client.post("/webhook", json=payload, headers=h)
    second = client.post("/webhook", json=payload, headers=h)
    assert first.status_code == 200
    assert second.json()["status"] == "duplicate"