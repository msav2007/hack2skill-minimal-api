import pytest
from fastapi.testclient import TestClient

from main import DEFAULT_API_KEY, app, reset_topic_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_topic_store()


def test_read_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Hack2Skill Topics API.",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


def test_list_topics() -> None:
    response = client.get("/topics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 3


def test_filter_topics() -> None:
    response = client.get("/topics?category=security&published=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "API Security Basics"


def test_get_invalid_topic_id() -> None:
    response = client.get("/topics/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Topic not found."}


def test_create_topic() -> None:
    response = client.post(
        "/topics",
        json={
            "title": "Performance Tuning",
            "description": "Explore lightweight API optimization strategies for Python.",
            "category": "efficiency",
            "difficulty": "advanced",
            "published": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 4
    assert payload["title"] == "Performance Tuning"


def test_create_topic_validation_error() -> None:
    response = client.post(
        "/topics",
        json={
            "title": "AI",
            "description": "Short",
            "category": "ml",
            "difficulty": "advanced",
            "published": True,
        },
    )

    assert response.status_code == 422


def test_secure_endpoint_requires_api_key() -> None:
    response = client.get("/topics/secure-stats")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_secure_endpoint_with_api_key() -> None:
    response = client.get(
        "/topics/secure-stats",
        headers={"X-API-Key": DEFAULT_API_KEY},
    )

    assert response.status_code == 200
    assert response.json()["authorized"] is True
