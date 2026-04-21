from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateUserRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=120)
    user_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    urgency: float = Field(ge=0, le=1000)
    category_weight: float = Field(ge=0, le=1000)


class UpdateUserRequest(BaseModel):
    user_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    urgency: Optional[float] = Field(default=None, ge=0, le=1000)
    category_weight: Optional[float] = Field(default=None, ge=0, le=1000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UpdateUserRequest":
        if self.user_name is None and self.urgency is None and self.category_weight is None:
            raise ValueError("Provide at least one field: user_name, urgency or category_weight")
        return self


class UserView(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str
    user_name: str
    urgency: float
    category_weight: float
    arrival_time_ms: int
    version: int
    score: float


class QueueResponse(BaseModel):
    users: list[UserView]
