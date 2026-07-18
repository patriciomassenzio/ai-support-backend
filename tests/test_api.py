import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_support.db"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_classify_ticket():
    r = client.post(
        "/tickets",
        json={
            "customer_email": "jane@example.com",
            "subject": "Payment charged twice",
            "body": "My credit card shows a duplicate charge on the last invoice. Please refund.",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["category"] == "billing"
    assert data["suggested_reply"]
    assert 0 <= data["confidence"] <= 1


def test_urgent_priority():
    r = client.post(
        "/tickets",
        json={
            "customer_email": "sam@example.com",
            "subject": "URGENT: cannot access my account",
            "body": "I am locked out and this is critical for my business.",
        },
    )
    assert r.json()["priority"] == "urgent"


def test_list_filter_and_status():
    r = client.get("/tickets", params={"category": "billing"})
    assert r.status_code == 200
    assert all(t["category"] == "billing" for t in r.json())

    tid = r.json()[0]["id"]
    r2 = client.patch(f"/tickets/{tid}", json={"status": "resolved"})
    assert r2.json()["status"] == "resolved"


def test_stats():
    data = client.get("/tickets/stats").json()
    assert data["total"] >= 2
