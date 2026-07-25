"""Уникальность salons.slug — SalonService.create() генерирует slug и
разруливает коллизию суффиксом (-2, -3, …) через реальный поход в БД на
каждую попытку (SalonRepository.get_by_slug). Юнит-тест utils/slug.py
(test_slug.py) проверяет саму функцию суффиксации как чистую логику; этот
файл проверяет, что SalonService/SalonRepository действительно достаёт
существующие slug'и из настоящей БД и что уникальный индекс их не пропустит,
даже если бы retry-логика была сломана."""
from datetime import time

import pytest
from sqlalchemy import select

from app.models.salon import Salon
from app.schemas.salon import SalonCreate
from app.services.salon_service import SalonService

pytestmark = pytest.mark.integration


def _make_salon_data(name: str) -> SalonCreate:
    return SalonCreate(name=name, address="ул. Тестовая, 1",
                       open_time=time(9, 0), close_time=time(20, 0))


def test_second_salon_with_same_name_gets_suffixed_slug(db_session):
    service = SalonService(db_session)
    first = service.create(_make_salon_data("Сайтама Центр"))
    second = service.create(_make_salon_data("Сайтама Центр"))
    db_session.commit()

    assert first.slug == "saytama-tsentr"
    assert second.slug != first.slug
    assert second.slug.startswith(first.slug)

    slugs = db_session.execute(select(Salon.slug)).scalars().all()
    assert len(slugs) == len(set(slugs)), "slug должен быть уникален физически, не только по коду"


def test_third_collision_increments_past_dash_two(db_session):
    service = SalonService(db_session)
    for _ in range(3):
        service.create(_make_salon_data("Точка"))
    db_session.commit()

    slugs = sorted(db_session.execute(select(Salon.slug)).scalars().all())
    assert slugs == ["tochka", "tochka-2", "tochka-3"]
