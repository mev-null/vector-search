from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from uuid import UUID


def get_now_utc():
    return datetime.now(timezone.utc)


class ApodUrls(SQLModel, table=True):
    """schema of APOD URLs"""
    __tablename__ = "apod_url"

    id: UUID = Field(default=None, primary_key=True)
    title: str
    url: str
    date: str
    embedding: list[float] = Field(
        sa_column=Column(Vector(384))
    )
    created_at: datetime = Field(default_factory=get_now_utc)
    updated_at: datetime = Field(
        default_factory=get_now_utc,
        sa_column_kwargs={"onupdate": get_now_utc}
    )


class NasaApodInput(SQLModel):
    """model class of json from APOD API"""
    title: str | None = None
    explanation: str | None = None
    url: str | None = None
    date: str | None = None
