# Hack2Skill Election Topics API

## Project Overview

This project is a lightweight FastAPI backend for election education topics with intelligent recommendation logic, secure access, accessibility-focused responses, async support, and simulated search insights.

## Features

- Structured FastAPI application with typed request and response models
- In-memory topic storage for fast evaluation and simple deployment
- Pydantic validation with field constraints
- API key protection for restricted topic access
- Built-in logging across endpoints

## Smart Features

- `recommend-topic` decision logic based on learner level
- `search` filtering for dynamic topic lookup
- `google-insight` simulation for search-style insight generation
- `accessible-topics` output for screen-reader-friendly summaries
- `async-topics` endpoint for async-ready responses

## API Endpoints

- `GET /`
- `GET /topics`
- `GET /topics/{topic_id}`
- `POST /topics`
- `GET /search?keyword=`
- `GET /recommend-topic?level=`
- `GET /secure-topics`
- `GET /google-insight?query=`
- `GET /accessible-topics`
- `GET /async-topics`

## How to Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Run tests with:

```bash
pytest test_main.py
```

## Deployment Link

[Add deployment URL here](https://example.com)
