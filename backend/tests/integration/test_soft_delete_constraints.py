"""Partial unique indexes (WHERE deleted_at IS NULL) — email/телефон/vk_user_id
освобождаются при soft-delete. Юнит-тесты покрывают только сервисный
pre-flight-чек (AuthService.register -> email_exists()); этот файл проверяет
сам constraint в БД, defense-in-depth на случай гонки/бага в сервисном слое."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.auth_service import hash_password

from .conftest import TEST_PASSWORD

pytestmark = pytest.mark.integration


def test_email_freed_after_soft_delete(db_session):
    repo = UserRepository(db_session)
    email = "reused@example.com"

    first = repo.create(
        UserCreate(email=email, first_name="Первый", last_name="Юзер", password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD),
        role=UserRole.client,
    )
    db_session.commit()

    repo.soft_delete(first)
    db_session.commit()

    # Тот же email, второй активный пользователь — partial index
    # (WHERE deleted_at IS NULL) должен пропустить это без конфликта, т.к.
    # первая строка больше не попадает под условие индекса.
    second = repo.create(
        UserCreate(email=email, first_name="Второй", last_name="Юзер", password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD),
        role=UserRole.client,
    )
    db_session.commit()

    assert second.id != first.id
    assert repo.get_by_email(email).id == second.id


def test_active_duplicate_email_rejected_at_db_level(db_session):
    """Тот же сценарий, но без soft-delete между созданиями — вызов идёт
    напрямую через репозиторий, в обход сервисной проверки email_exists(),
    чтобы убедиться, что БД сама, а не только код приложения, не допускает
    двух активных пользователей с одним email."""
    repo = UserRepository(db_session)
    email = "duplicate@example.com"

    repo.create(
        UserCreate(email=email, first_name="Первый", last_name="Юзер", password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD),
        role=UserRole.client,
    )
    db_session.commit()

    with pytest.raises(IntegrityError) as exc_info:
        repo.create(
            UserCreate(email=email, first_name="Второй", last_name="Юзер", password=TEST_PASSWORD),
            hash_password(TEST_PASSWORD),
            role=UserRole.client,
        )
    db_session.rollback()

    assert exc_info.value.orig.diag.constraint_name == "uq_users_email_active"
