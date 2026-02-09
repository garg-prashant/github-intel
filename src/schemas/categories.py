"""Category list schema."""

from pydantic import BaseModel


class CategoryItem(BaseModel):
    slug: str
    name: str
    description: str | None
    repo_count: int
