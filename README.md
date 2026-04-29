# Hack2Skill Election Topics API

## Project Overview

This project is a minimal FastAPI backend for managing election education topics with validation, secure access control, topic search, and smart topic recommendations.

## Features

- Structured FastAPI app with metadata and typed response models
- In-memory topic storage for simple backend evaluation
- Input validation with Pydantic constraints
- Clean error handling for missing topics and unauthorized access

## Smart Features

- Recommendation system based on learner level
- Search filtering with keyword matching
- Secure endpoint protected by API key header

## API Endpoints

- `GET /`
- `GET /topics`
- `GET /topics/{topic_id}`
- `POST /topics`
- `GET /search?keyword=`
- `GET /recommend-topic?level=`
- `GET /secure-topics`

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
