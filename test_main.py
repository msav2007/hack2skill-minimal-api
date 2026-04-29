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
    assert len(payload["topics"]) == 4


def test_invalid_topic_returns_404() -> None:
    response = client.get("/topics/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Topic not found."}


def test_recommendation_endpoint() -> None:
    response = client.get("/recommend-topic?level=advanced")

    assert response.status_code == 200
    assert response.json() == {
        "level": "advanced",
        "recommended_topic": "Election Security",
    }


def test_secure_endpoint_fails_without_api_key() -> None:
    response = client.get("/secure-topics")

    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized access."}


def test_secure_endpoint_succeeds_with_api_key() -> None:
    response = client.get(
        "/secure-topics",
        headers={"X-API-Key": DEFAULT_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 4
