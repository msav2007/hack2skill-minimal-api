import pytest
from fastapi.testclient import TestClient

from main import DEFAULT_API_KEY, app, reset_topic_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_topic_store()


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_topics_endpoint() -> None:
    response = client.get("/topics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 4
    assert payload["topics"][0]["title"] == "Voting Process"


def test_invalid_topic_returns_404() -> None:
    response = client.get("/topics/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Topic not found."}


def test_recommendation_endpoint() -> None:
    response = client.get("/recommend-topic?level=advanced")

    assert response.status_code == 200
    assert response.json()["recommended_topic"] == "Election Security"


def test_google_insight_endpoint() -> None:
    response = client.get("/google-insight?query=security")

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_result"] == "Election Security"
    assert "security basics" in payload["related_searches"]


def test_accessible_topics_endpoint() -> None:
    response = client.get("/accessible-topics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["accessibility_mode"] == "screen-reader-friendly"
    assert payload["topics"][0]["screen_reader_hint"].startswith("Topic 1")


def test_async_topics_endpoint() -> None:
    response = client.get("/async-topics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["count"] == 4


def test_secure_topics_requires_api_key() -> None:
    response = client.get("/secure-topics")

    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized access."}


def test_secure_topics_with_api_key() -> None:
    response = client.get(
        "/secure-topics",
        headers={"X-API-Key": DEFAULT_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 4
