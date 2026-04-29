"""
Hack2Skill election education API.

This FastAPI service provides a small backend for managing election topics,
searching content, protecting sensitive data with an API key, and returning
smart topic recommendations based on learner level. The intelligent logic maps
beginner users to Voting Process, intermediate users to EVM, advanced users to
Election Security, and falls back to General Overview for any other request.
"""

from os import getenv
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field

APP_TITLE = "Hack2Skill Election Topics API"
APP_DESCRIPTION = "A minimal yet structured FastAPI backend for election learning topics."
APP_VERSION = "2.0.0"
API_KEY_NAME = "X-API-Key"
DEFAULT_API_KEY = "hack2skill-secure-key"


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


class TopicBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=10, max_length=300)
    category: str = Field(..., min_length=3, max_length=30)


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int = Field(..., ge=1)


class TopicListResponse(BaseModel):
    topics: list[TopicResponse]
    count: int = Field(..., ge=0)


class RecommendationResponse(BaseModel):
    level: str
    recommended_topic: str


def create_seed_topics() -> list[TopicResponse]:
    return [
        TopicResponse(
            id=1,
            title="Voting Process",
            description="Understand each step of voting from registration to final counting.",
            category="basics",
        ),
        TopicResponse(
            id=2,
            title="EVM",
            description="Learn how electronic voting machines work in real election flows.",
            category="technology",
        ),
        TopicResponse(
            id=3,
            title="Election Security",
            description="Explore methods that protect election systems and voter trust.",
            category="security",
        ),
        TopicResponse(
            id=4,
            title="General Overview",
            description="Review the full election process at a high level for any audience.",
            category="overview",
        ),
    ]


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)


def reset_topic_store() -> None:
    app.state.topics = create_seed_topics()
    app.state.next_topic_id = len(app.state.topics) + 1


reset_topic_store()


def get_expected_api_key() -> str:
    return getenv("TOPICS_API_KEY", DEFAULT_API_KEY)


def verify_api_key(
    x_api_key: Annotated[str | None, Header(alias=API_KEY_NAME)] = None,
) -> None:
    if x_api_key is None or not compare_digest(x_api_key, get_expected_api_key()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access.",
        )


def get_topics(request: Request) -> list[TopicResponse]:
    return request.app.state.topics


def build_topic_list_response(topics: list[TopicResponse]) -> TopicListResponse:
    return TopicListResponse(topics=topics, count=len(topics))


def get_topic_or_404(topic_id: int, request: Request) -> TopicResponse:
    topic = next((item for item in get_topics(request) if item.id == topic_id), None)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )
    return topic


def recommend_title(level: str | None) -> str:
    normalized_level = (level or "").strip().lower()
    recommendations = {
        "beginner": "Voting Process",
        "intermediate": "EVM",
        "advanced": "Election Security",
    }
    return recommendations.get(normalized_level, "General Overview")


@app.get("/", response_model=HealthResponse)
def read_root() -> HealthResponse:
    return HealthResponse(
        status="ok",
        message="Hack2Skill election topics API is running.",
        version=APP_VERSION,
    )


@app.get("/topics", response_model=TopicListResponse)
def list_topics(request: Request) -> TopicListResponse:
    return build_topic_list_response(get_topics(request))


@app.get(
    "/topics/{topic_id}",
    response_model=TopicResponse,
    responses={404: {"model": ErrorResponse}},
)
def read_topic(
    topic_id: Annotated[int, Path(ge=1)],
    request: Request,
) -> TopicResponse:
    return get_topic_or_404(topic_id=topic_id, request=request)


@app.post("/topics", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(topic: TopicCreate, request: Request) -> TopicResponse:
    topics = get_topics(request)

    if any(existing.title.lower() == topic.title.lower() for existing in topics):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic title already exists.",
        )

    new_topic = TopicResponse(id=request.app.state.next_topic_id, **topic.model_dump())
    topics.append(new_topic)
    request.app.state.next_topic_id += 1
    return new_topic


@app.get("/search", response_model=TopicListResponse)
def search_topics(
    request: Request,
    keyword: Annotated[str, Query(min_length=2, max_length=50)],
) -> TopicListResponse:
    normalized_keyword = keyword.strip().lower()
    filtered_topics = [
        topic
        for topic in get_topics(request)
        if normalized_keyword in topic.title.lower()
        or normalized_keyword in topic.description.lower()
        or normalized_keyword in topic.category.lower()
    ]
    return build_topic_list_response(filtered_topics)


@app.get("/recommend-topic", response_model=RecommendationResponse)
def recommend_topic(level: Annotated[str | None, Query(max_length=20)] = None) -> RecommendationResponse:
    return RecommendationResponse(
        level=(level or "default").strip().lower() or "default",
        recommended_topic=recommend_title(level),
    )


@app.get(
    "/secure-topics",
    response_model=TopicListResponse,
    responses={403: {"model": ErrorResponse}},
)
def read_secure_topics(
    request: Request,
    _: None = Depends(verify_api_key),
) -> TopicListResponse:
    return build_topic_list_response(get_topics(request))
