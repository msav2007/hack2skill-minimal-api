# Hack2Skill Topics API

## Project Overview

Hack2Skill Topics API is a production-style FastAPI backend that manages learning topics with validation, filtering, typed responses, and API key protection.

## Features

- Structured FastAPI application with metadata and clear response models
- Input validation using Pydantic field constraints
- In-memory topic storage for lightweight execution
- Query-based filtering for search, category, difficulty, and published status
- Protected endpoint secured with an `X-API-Key` header
- Automated tests with `pytest` and `TestClient`

## API Endpoints

- `GET /` - API summary and version details
- `GET /health` - health check endpoint
- `GET /topics` - list topics with optional filters: `search`, `category`, `difficulty`, `published`, and `limit`
- `GET /topics/{topic_id}` - fetch a single topic by ID
- `POST /topics` - create a new topic with validation
- `GET /topics/secure-stats` - protected topic statistics endpoint

## How to Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Run tests with:

```bash
pytest
```

Set an API key before calling the protected endpoint:

```bash
set TOPICS_API_KEY=hack2skill-local-key
```

## Deployment Link

[Add your live deployment URL here](https://example.com)
