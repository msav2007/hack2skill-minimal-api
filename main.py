"""
Hack2Skill election education API.

This FastAPI backend manages election learning topics with validation,
intelligent recommendations, accessible content output, secure data access,
Google-like insight simulation, and async-ready topic retrieval. The service is
kept intentionally lightweight for evaluation while still showing professional
API design, structured response models, logging, and practical decision logic.
"""

import asyncio
import logging
from os import getenv
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field

APP_TITLE = "Hack2Skill Election Topics API"
APP_DESCRIPTION = "A structured FastAPI backend for election education workflows."
APP_VERSION = "3.0.0"
API_KEY_NAME = "X-API-Key"
DEFAULT_API_KEY = "hack2skill-secure-key"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("hack2skill_api")


class ErrorResponse(BaseModel):
    detail: str


class RootResponse(BaseModel):
    status: str
    service: str
    version: str


class TopicBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=10, max_length=320)
    category: str = Field(..., min_length=3, max_length=30)
    audience_level: str = Field(..., min_length=3, max_length=20)


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int = Field(..., ge=1)


class TopicListResponse(BaseModel):
    topics: list[TopicResponse]
    count: int = Field(..., ge=0)


class SearchResponse(BaseModel):
    keyword: str
    matches: list[TopicResponse]
    total_matches: int = Field(..., ge=0)


class RecommendationResponse(BaseModel):
    level: str
    recommended_topic: str
    reason: str


class GoogleInsightResponse(BaseModel):
    query: str
    top_result: str
    summary: str
    related_searches: list[str]


class AccessibleTopic(BaseModel):
    id: int = Field(..., ge=1)
    title: str
    plain_language_summary: str
    screen_reader_hint: str


class AccessibleTopicsResponse(BaseModel):
    topics: list[AccessibleTopic]
    accessibility_mode: str


class AsyncTopicsResponse(BaseModel):
    status: str
    topics: list[TopicResponse]
    count: int = Field(..., ge=0)


def create_seed_topics() -> list[TopicResponse]:
    return [
        TopicResponse(
            id=1,
            title="Voting Process",
            description="Understand each step from voter registration to final result counting.",
            category="basics",
            audience_level="beginner",
        ),
        TopicResponse(
            id=2,
            title="EVM",
            description="Learn how electronic voting machines operate during real elections.",
            category="technology",
            audience_level="intermediate",
        ),
        TopicResponse(
            id=3,
            title="Election Security",
            description="Explore how audits, monitoring, and controls protect elections.",
            category="security",
            audience_level="advanced",
        ),
        TopicResponse(
            id=4,
            title="General Overview",
            description="Review the complete election process in a simple end-to-end format.",
            category="overview",
            audience_level="beginner",
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
        logger.warning("Rejected secure endpoint request due to invalid API key.")
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
        logger.warning("Topic lookup failed for id=%s", topic_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found.",
        )
    return topic


def recommend_title(level: str | None) -> tuple[str, str]:
    normalized_level = (level or "").strip().lower()
    recommendations = {
        "beginner": (
            "Voting Process",
            "Beginner learners benefit from a simple step-by-step election flow.",
        ),
        "intermediate": (
            "EVM",
            "Intermediate learners are ready for machine-based election concepts.",
        ),
        "advanced": (
            "Election Security",
            "Advanced learners should focus on protection, auditing, and trust.",
        ),
    }
    return recommendations.get(
        normalized_level,
        (
            "General Overview",
            "A broad overview works best when a learner level is not specified.",
        ),
    )


def build_related_searches(query: str) -> list[str]:
    normalized_query = query.strip().lower() or "election"
    return [
        f"{normalized_query} basics",
        f"{normalized_query} checklist",
        f"{normalized_query} security",
    ]


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    logger.info("Health check requested.")
    return RootResponse(
        status="ok",
        service=APP_TITLE,
        version=APP_VERSION,
    )


@app.get("/topics", response_model=TopicListResponse)
def list_topics(request: Request) -> TopicListResponse:
    logger.info("Listing all topics.")
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
    logger.info("Reading topic with id=%s", topic_id)
    return get_topic_or_404(topic_id=topic_id, request=request)


@app.post(
    "/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
def create_topic(topic: TopicCreate, request: Request) -> TopicResponse:
    topics = get_topics(request)
    logger.info("Creating topic with title=%s", topic.title)

    if any(existing.title.lower() == topic.title.lower() for existing in topics):
        logger.warning("Duplicate topic title rejected: %s", topic.title)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic title already exists.",
        )

    new_topic = TopicResponse(id=request.app.state.next_topic_id, **topic.model_dump())
    topics.append(new_topic)
    request.app.state.next_topic_id += 1
    return new_topic


@app.get("/search", response_model=SearchResponse)
def search_topics(
    request: Request,
    keyword: Annotated[str, Query(min_length=2, max_length=50)],
) -> SearchResponse:
    logger.info("Searching topics with keyword=%s", keyword)
    normalized_keyword = keyword.strip().lower()
    filtered_topics = [
        topic
        for topic in get_topics(request)
        if normalized_keyword in topic.title.lower()
        or normalized_keyword in topic.description.lower()
        or normalized_keyword in topic.category.lower()
        or normalized_keyword in topic.audience_level.lower()
    ]
    return SearchResponse(
        keyword=keyword,
        matches=filtered_topics,
        total_matches=len(filtered_topics),
    )


@app.get("/recommend-topic", response_model=RecommendationResponse)
def recommend_topic(
    level: Annotated[str | None, Query(max_length=20)] = None,
) -> RecommendationResponse:
    logger.info("Generating recommendation for level=%s", level)
    recommended_topic, reason = recommend_title(level)
    normalized_level = (level or "default").strip().lower() or "default"
    return RecommendationResponse(
        level=normalized_level,
        recommended_topic=recommended_topic,
        reason=reason,
    )


@app.get("/secure-topics", response_model=TopicListResponse)
def read_secure_topics(
    request: Request,
    _: None = Depends(verify_api_key),
) -> TopicListResponse:
    logger.info("Secure topics requested.")
    return build_topic_list_response(get_topics(request))


@app.get("/google-insight", response_model=GoogleInsightResponse)
def google_insight(
    request: Request,
    query: Annotated[str, Query(min_length=2, max_length=50)] = "election",
) -> GoogleInsightResponse:
    logger.info("Generating Google-like insight for query=%s", query)
    normalized_query = query.strip().lower()
    topics = get_topics(request)
    ranked_topic = next(
        (
            topic
            for topic in topics
            if normalized_query in topic.title.lower()
            or normalized_query in topic.description.lower()
            or normalized_query in topic.category.lower()
        ),
        topics[-1],
    )
    return GoogleInsightResponse(
        query=query,
        top_result=ranked_topic.title,
        summary=f"Top simulated search insight: {ranked_topic.description}",
        related_searches=build_related_searches(query),
    )


@app.get("/accessible-topics", response_model=AccessibleTopicsResponse)
def accessible_topics(request: Request) -> AccessibleTopicsResponse:
    logger.info("Accessible topics requested.")
    accessible_items = [
        AccessibleTopic(
            id=topic.id,
            title=topic.title,
            plain_language_summary=f"{topic.title}: {topic.description}",
            screen_reader_hint=f"Topic {topic.id}, category {topic.category}, level {topic.audience_level}.",
        )
        for topic in get_topics(request)
    ]
    return AccessibleTopicsResponse(
        topics=accessible_items,
        accessibility_mode="screen-reader-friendly",
    )


@app.get("/async-topics", response_model=AsyncTopicsResponse)
async def async_topics(request: Request) -> AsyncTopicsResponse:
    logger.info("Async topics endpoint requested.")
    await asyncio.sleep(0)
    topics = get_topics(request)
    return AsyncTopicsResponse(
        status="ready",
        topics=topics,
        count=len(topics),
    )
