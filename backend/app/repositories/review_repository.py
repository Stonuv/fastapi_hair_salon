import uuid
from typing import Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models.master import Master
from ..models.review import Review
from ._query_utils import paginated


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, review_id: uuid.UUID) -> Optional[Review]:
        return self.db.execute(
            select(Review).where(Review.id == review_id)
        ).scalar_one_or_none()

    def get_by_appointment(self, appointment_id: uuid.UUID) -> Optional[Review]:
        return self.db.execute(
            select(Review).where(Review.appointment_id == appointment_id)
        ).scalar_one_or_none()

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        master_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
        min_rating: int | None = None,
        is_published: bool | None = True,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[Review], int]:
        """Отзывы — фильтр по мастеру/услуге/минимальной оценке, с пагинацией.
        is_published=True (по умолчанию) — для публичной выдачи;
        is_published=None — для модерации админом (видно всё)."""
        stmt = select(Review).options(
            joinedload(Review.client),
            joinedload(Review.master).joinedload(Master.user),
            joinedload(Review.service),
        )
        if is_published is not None:
            stmt = stmt.where(Review.is_published.is_(is_published))
        if master_id is not None:
            stmt = stmt.where(Review.master_id == master_id)
        if service_id is not None:
            stmt = stmt.where(Review.service_id == service_id)
        if min_rating is not None:
            stmt = stmt.where(Review.rating >= min_rating)

        order = Review.created_at.asc() if sort_order == "asc" else Review.created_at.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    def rating_summary(self, master_id: uuid.UUID) -> tuple[float | None, int]:
        """(средний рейтинг, всего опубликованных отзывов) мастера — среднее
        считается по всем отзывам в SQL, а не по одной странице выдачи."""
        stmt = select(func.avg(Review.rating), func.count()).where(
            Review.master_id == master_id,
            Review.is_published.is_(True),
        )
        avg, count = self.db.execute(stmt).one()
        return (round(float(avg), 1) if avg is not None else None), count

    # ── Создание / изменение ──────────────────────────────────────

    def create(self, *, appointment_id: uuid.UUID, client_id: uuid.UUID,
               master_id: uuid.UUID, service_id: uuid.UUID,
               rating: int, comment: str | None) -> Review:
        review = Review(
            appointment_id=appointment_id,
            client_id=client_id,
            master_id=master_id,
            service_id=service_id,
            rating=rating,
            comment=comment,
        )
        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)
        return review

    def set_published(self, review: Review, is_published: bool) -> Review:
        review.is_published = is_published
        self.db.flush()
        self.db.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.db.delete(review)
        self.db.flush()
