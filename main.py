from os import getenv
from secrets import compare_digest
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field

APP_TITLE = "Hack2Skill Topics API"
APP_VERSION = "1.0.0"
API_KEY_HEADER = "X-API-Key"
DEFAULT_API_KEY = "hack2skill-local-key"


class RootResponse(BaseModel):
    message: str
    version: str
    docs_url: str


class HealthResponse(BaseModel):
    status: str


class TopicBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=10, max_length=500)
    category: str = Field(..., min_length=3, max_length=30)
    difficulty: Literal["beginner", "intermediate", "advanced"]
    published: bool = True


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int = Field(..., ge=1)


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    total: int = Field(..., ge=0)


class SecureStatsResponse(BaseModel):
    authorized: bool
    total_topics: int = Field(..., ge=0)
    api_version: str


def create_seed_topics() -> list[TopicResponse]:
    return [
        TopicResponse(
            id=1,
            title="FastAPI Fundamentals",
            description="Learn how to design clean REST endpoints with FastAPI.",
            category="backend",
            difficulty="beginner",
            published=True,
        ),
        TopicResponse(
            id=2,
            title="API Security Basics",
            description="Protect services with API keys, validation, and safe defaults.",
            category="security",
            difficulty="intermediate",
            published=True,
        ),
        TopicResponse(
            id=3,
            title="Efficient Testing",
            description="Write lightweight automated tests for backend reliability.",
            category="testing",
            difficulty="beginner",
            published=False,
        ),
    ]


app = FastAPI(
    title=APP_TITLE,
    description="A structured FastAPI backend for managing learning topics.",
    version=APP_VERSION,
)


def reset_topic_store() -> None:
    app.state.topics = create_seed_topics()
    app.state.next_topic_id = len(app.state.topics) + 1


reset_topic_store()


def get_expected_api_key() -> str:
    return getenv("TOPICS_API_KEY", DEFAULT_API_KEY)


def require_api_key(
    x_api_key: Annotated[str | None, Header(alias=API_KEY_HEADER)] = None,
) -> None:
    if x_api_key is None or not compare_digest(x_api_key, get_expected_api_key()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def get_topic_store(request: Request) -> list[TopicResponse]:
    return request.app.state.topics


def get_topic_or_404(topic_id: int, request: Request) -> TopicResponse:
    for topic in get_topic_store(request):
        if topic.id == topic_id:
            return topic

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    return RootResponse(
        message="Welcome to the Hack2Skill Topics API.",
        version=APP_VERSION,
        docs_url="/docs",
    )


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/topics", response_model=TopicListResponse)
def list_topics(
    request: Request,
    search: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    category: Annotated[str | None, Query(min_length=3, max_length=30)] = None,
    difficulty: Annotated[
        Literal["beginner", "intermediate", "advanced"] | None,
        Query(),
    ] = None,
    published: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> TopicListResponse:
    topics: list[TopicResponse] = get_topic_store(request)
    filtered_topics: list[TopicResponse] = topics

    if search:
        search_lower = search.lower()
        filtered_topics = [
            topic
            for topic in filtered_topics
            if search_lower in topic.title.lower()
            or search_lower in topic.description.lower()
        ]

    if category:
        category_lower = category.lower()
        filtered_topics = [
            topic for topic in filtered_topics if topic.category.lower() == category_lower
        ]

    if difficulty:
        filtered_topics = [
            topic for topic in filtered_topics if topic.difficulty == difficulty
        ]

    if published is not None:
        filtered_topics = [
            topic for topic in filtered_topics if topic.published == published
        ]

    limited_topics = filtered_topics[:limit]
    return TopicListResponse(items=limited_topics, total=len(filtered_topics))


@app.get("/topics/secure-stats", response_model=SecureStatsResponse)
def get_secure_stats(
    request: Request,
    _: None = Depends(require_api_key),
) -> SecureStatsResponse:
    return SecureStatsResponse(
        authorized=True,
        total_topics=len(get_topic_store(request)),
        api_version=APP_VERSION,
    )


@app.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: Annotated[int, Path(ge=1)],
    request: Request,
) -> TopicResponse:
    return get_topic_or_404(topic_id=topic_id, request=request)


@app.post(
    "/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(topic: TopicCreate, request: Request) -> TopicResponse:
    topics = get_topic_store(request)

    if any(existing_topic.title.lower() == topic.title.lower() for existing_topic in topics):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A topic with this title already exists.",
        )

    new_topic = TopicResponse(id=request.app.state.next_topic_id, **topic.model_dump())
    topics.append(new_topic)
    request.app.state.next_topic_id += 1
    return new_topic
