from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.enums import AppointmentStatus, UserRole
from ..models.review import Review
from ..models.user import User
from ..repositories.appointment_repository import AppointmentRepository
from ..repositories.master_repository import MasterRepository
from ..repositories.review_repository import ReviewRepository
from ..schemas.pagination import PageResponse
from ..schemas.review import ReviewCreate, ReviewResponse


class ReviewService:
    def __init__(self, db: Session):
        self.review_repo = ReviewRepository(db)
        self.appointment_repo = AppointmentRepository(db)
        self.master_repo = MasterRepository(db)

    # ── Создание (клиентом, по завершённой записи) ────────────────

    def create(self, client_id: UUID, data: ReviewCreate) -> ReviewResponse:
        appointment = self.appointment_repo.get_by_id(data.appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")
        if appointment.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Можно оставить отзыв только на свою запись")
        if appointment.status != AppointmentStatus.done:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Отзыв можно оставить только на завершённую запись")
        if self.review_repo.get_by_appointment(data.appointment_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Отзыв на эту запись уже оставлен")

        review = self.review_repo.create(
            appointment_id=data.appointment_id,
            client_id=client_id,
            master_id=appointment.master_id,
            service_id=appointment.service_id,
            rating=data.rating,
            comment=data.comment,
        )
        return ReviewResponse.model_validate(review)

    # ── Списки ───────────────────────────────────────────────────

    def list_for_master(self, master_id: UUID, *, page: int, page_size: int,
                        min_rating: int | None = None) -> PageResponse[ReviewResponse]:
        """Опубликованные отзывы мастера — публичный эндпоинт."""
        reviews, total = self.review_repo.list_paginated(
            page=page, page_size=page_size, master_id=master_id,
            min_rating=min_rating, is_published=True,
        )
        return PageResponse[ReviewResponse](
            items=[ReviewResponse.model_validate(r) for r in reviews],
            total=total, page=page, page_size=page_size,
        )

    def list_all_admin(self, *, page: int, page_size: int,
                       master_id: UUID | None = None,
                       is_published: bool | None = None,
                       min_rating: int | None = None,
                       salon_id: UUID | None = None) -> PageResponse[ReviewResponse]:
        """Все отзывы (включая скрытые) — для модерации. salon_id
        (ROADMAP.md §4.8, Фаза C) — None означает всю сеть (owner)."""
        reviews, total = self.review_repo.list_paginated(
            page=page, page_size=page_size, master_id=master_id,
            min_rating=min_rating, is_published=is_published, salon_id=salon_id,
        )
        return PageResponse[ReviewResponse](
            items=[ReviewResponse.model_validate(r) for r in reviews],
            total=total, page=page, page_size=page_size,
        )

    # ── Модерация / удаление ──────────────────────────────────────

    def moderate(self, review_id: UUID, is_published: bool,
                requesting_user: User) -> ReviewResponse:
        """Быстрое действие админа «опубликовать / снять с публикации» (4.3)."""
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
        self._ensure_can_moderate(review, requesting_user)
        review = self.review_repo.set_published(review, is_published)
        return ReviewResponse.model_validate(review)

    def delete(self, review_id: UUID, requesting_user: User) -> None:
        """Клиент удаляет свой отзыв; owner — любой; admin — только своей
        точки (модерация спама, ROADMAP.md §4.8 Фаза C)."""
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
        if requesting_user.role in (UserRole.admin, UserRole.owner):
            self._ensure_can_moderate(review, requesting_user)
        elif review.client_id != requesting_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Можно удалить только свой отзыв")
        self.review_repo.delete(review)

    def _ensure_can_moderate(self, review: Review, requesting_user: User) -> None:
        """owner модерирует все отзывы сети; admin — только своей точки
        (скоуп через мастера отзыва, у Review нет своего salon_id)."""
        if requesting_user.role == UserRole.owner:
            return
        master = self.master_repo.get_by_id(review.master_id)
        if not master or master.salon_id != requesting_user.salon_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Доступ только к отзывам своей точки")
