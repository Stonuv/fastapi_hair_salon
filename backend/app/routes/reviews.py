from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.pagination import PageParams, PageResponse
from ..schemas.review import ReviewCreate, ReviewModerate, ReviewResponse
from ..services.auth_service import get_current_admin, get_current_client
from ..services.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """Оставить отзыв на свою завершённую запись."""
    return ReviewService(db).create(current_user.id, data)


@router.get("/master/{master_id}", response_model=PageResponse[ReviewResponse])
def get_master_reviews(
    master_id: UUID,
    *,
    db: Session = Depends(get_db),
    page_params: Annotated[PageParams, Depends()],
    min_rating: int | None = None,
):
    """Опубликованные отзывы мастера. Публичный эндпоинт."""
    return ReviewService(db).list_for_master(
        master_id, page=page_params.page, page_size=page_params.page_size,
        min_rating=min_rating,
    )


@router.get("", response_model=PageResponse[ReviewResponse])
def get_all_reviews(
    *,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
    page_params: Annotated[PageParams, Depends()],
    master_id: UUID | None = None,
    is_published: bool | None = None,
    min_rating: int | None = None,
):
    """Все отзывы, включая скрытые — для модерации администратором."""
    return ReviewService(db).list_all_admin(
        page=page_params.page, page_size=page_params.page_size,
        master_id=master_id, is_published=is_published, min_rating=min_rating,
    )


@router.patch("/{review_id}/publish", response_model=ReviewResponse)
def moderate_review(
    review_id: UUID,
    data: ReviewModerate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Опубликовать / снять с публикации — быстрое действие администратора (4.3)."""
    return ReviewService(db).moderate(review_id, data.is_published)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """Удалить свой отзыв."""
    ReviewService(db).delete_own(review_id, current_user.id)
