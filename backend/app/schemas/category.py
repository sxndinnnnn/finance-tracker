import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.category import CategoryKind


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    kind: CategoryKind
    icon: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    icon: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    kind: CategoryKind
    icon: str | None
    color: str | None
    is_default: bool = False

    @staticmethod
    def from_model(category) -> "CategoryRead":
        return CategoryRead(
            id=category.id,
            user_id=category.user_id,
            name=category.name,
            kind=category.kind,
            icon=category.icon,
            color=category.color,
            is_default=category.user_id is None,
        )
