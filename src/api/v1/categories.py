"""GET /categories — list categories with repo count."""

from sqlalchemy import func, select
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.models.category import Category, RepositoryCategory
from src.schemas.categories import CategoryItem

router = APIRouter()


@router.get("/categories", response_model=list[CategoryItem])
async def get_categories(session: AsyncSession = Depends(get_db)) -> list[CategoryItem]:
    cnt = select(Category.id, func.count(RepositoryCategory.id).label("cnt")).select_from(Category).outerjoin(
        RepositoryCategory, Category.id == RepositoryCategory.category_id
    ).group_by(Category.id).subquery()
    result = await session.execute(
        select(Category, cnt.c.cnt).join(cnt, Category.id == cnt.c.id).order_by(Category.id)
    )
    return [
        CategoryItem(slug=c.slug, name=c.name, description=c.description, repo_count=rc or 0)
        for c, rc in result.all()
    ]
