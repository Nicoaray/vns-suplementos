from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewAuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: str | None
    created_at: datetime
    user: ReviewAuthorRead
