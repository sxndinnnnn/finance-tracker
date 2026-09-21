import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.category import Category, CategoryKind
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    kind: CategoryKind | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Category).where(
        or_(Category.user_id.is_(None), Category.user_id == current_user.id)
    )
    if kind is not None:
        stmt = stmt.where(Category.kind == kind)
    stmt = stmt.order_by(Category.kind, Category.name)
    result = await db.execute(stmt)
    return [CategoryRead.from_model(c) for c in result.scalars().all()]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = Category(user_id=current_user.id, **payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryRead.from_model(category)


async def _get_own_category(category_id: uuid.UUID, current_user: User, db: AsyncSession) -> Category:
    category = await db.get(Category, category_id)
    if category is None or category.user_id != current_user.id:
        # System defaults (user_id=None) are shared read-only rows — not
        # directly editable/deletable, since that would affect every user.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await _get_own_category(category_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return CategoryRead.from_model(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await _get_own_category(category_id, current_user, db)
    await db.delete(category)
    await db.commit()
