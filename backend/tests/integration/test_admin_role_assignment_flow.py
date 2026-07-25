"""Полный HTTP-флоу назначения salon-scoped admin (ROADMAP.md §4.10 Фаза B):
создать пользователя → назначить точку → повысить роль. Юнит-тесты
(test_admin_role_assignment.py) проверяют ветвления AdminService с фейковыми
репозиториями; этот файл — что это реально работает вместе поверх настоящего
Postgres, включая CHECK CONSTRAINT ck_users_admin_requires_salon, который и
вынуждает двухшаговый флоу (роль меняется отдельным запросом от назначения
точки — единая транзакция тут недостижима через два HTTP-вызова)."""
from datetime import time

import pytest

from app.models.enums import UserRole
from app.repositories.salon_repository import SalonRepository
from app.repositories.user_repository import UserRepository
from app.schemas.salon import SalonCreate
from app.schemas.user import UserCreate
from app.services.auth_service import hash_password

from .conftest import TEST_PASSWORD

pytestmark = pytest.mark.integration


async def _login(client, email: str, password: str = TEST_PASSWORD) -> dict:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    # _token_from_request (auth_service.py) читает cookie раньше заголовка —
    # httpx.AsyncClient держит общий cookie jar на все запросы, так что без
    # явной очистки cookie login/register ЛЮБОГО другого пользователя внутри
    # того же теста тихо перебивал бы это Authorization-заголовок его же
    # cookie'й (см. ROADMAP.md — не баг прод-кода, артефакт теста с
    # несколькими "личностями" в одном AsyncClient).
    client.cookies.clear()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _register(client, *, email: str, first_name: str, last_name: str) -> str:
    resp = await client.post("/api/auth/register", json={
        "email": email, "first_name": first_name, "last_name": last_name, "password": TEST_PASSWORD,
    })
    assert resp.status_code == 201, resp.text
    client.cookies.clear()
    return resp.json()["user"]["id"]


def _make_owner(db_session):
    owner = UserRepository(db_session).create(
        UserCreate(email="owner@example.com", first_name="Влад", last_name="Владелец",
                  password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD), role=UserRole.owner,
    )
    db_session.commit()
    return owner


def _make_salon(db_session, name="Вторая точка"):
    salon = SalonRepository(db_session).create(
        SalonCreate(name=name, address="ул. Вторая, 2", open_time=time(9, 0), close_time=time(20, 0)),
        slug=f"salon-{name.lower()}",
    )
    db_session.commit()
    return salon


@pytest.mark.anyio
async def test_two_step_flow_promotes_user_to_scoped_admin(client, db_session):
    _make_owner(db_session)
    salon = _make_salon(db_session)
    owner_auth = await _login(client, "owner@example.com")

    user_id = await _register(client, email="future-admin@example.com",
                              first_name="Света", last_name="Светова")

    # Повышение до admin без точки — CHECK CONSTRAINT (через понятную 400,
    # не сырой 500 от IntegrityError).
    premature_resp = await client.patch(
        f"/api/admin/users/{user_id}/role", json={"role": "admin"}, headers=owner_auth,
    )
    assert premature_resp.status_code == 400, premature_resp.text

    salon_resp = await client.patch(
        f"/api/admin/users/{user_id}/salon", json={"salon_id": str(salon.id)}, headers=owner_auth,
    )
    assert salon_resp.status_code == 200, salon_resp.text

    role_resp = await client.patch(
        f"/api/admin/users/{user_id}/role", json={"role": "admin"}, headers=owner_auth,
    )
    assert role_resp.status_code == 200, role_resp.text
    assert role_resp.json()["role"] == "admin"

    # Новый admin реально логинится и получает доступ к /api/admin/*.
    admin_auth = await _login(client, "future-admin@example.com")
    stats_resp = await client.get("/api/admin/stats", headers=admin_auth)
    assert stats_resp.status_code == 200, stats_resp.text


@pytest.mark.anyio
async def test_non_owner_admin_cannot_assign_salon_or_promote(client, db_session):
    _make_owner(db_session)
    salon = _make_salon(db_session)
    owner_auth = await _login(client, "owner@example.com")

    # Владелец сам готовит salon-admin'а, чтобы проверить его права отдельно.
    scoped_admin_id = await _register(client, email="scoped-admin@example.com",
                                      first_name="Игорь", last_name="Игорев")
    salon_setup_resp = await client.patch(f"/api/admin/users/{scoped_admin_id}/salon",
                                          json={"salon_id": str(salon.id)}, headers=owner_auth)
    assert salon_setup_resp.status_code == 200, salon_setup_resp.text
    promote_setup_resp = await client.patch(f"/api/admin/users/{scoped_admin_id}/role",
                                            json={"role": "admin"}, headers=owner_auth)
    assert promote_setup_resp.status_code == 200, promote_setup_resp.text
    scoped_admin_auth = await _login(client, "scoped-admin@example.com")

    victim_id = await _register(client, email="victim@example.com",
                                first_name="Клиент", last_name="Обычный")

    salon_resp = await client.patch(
        f"/api/admin/users/{victim_id}/salon", json={"salon_id": str(salon.id)},
        headers=scoped_admin_auth,
    )
    assert salon_resp.status_code == 403, salon_resp.text

    promote_resp = await client.patch(
        f"/api/admin/users/{victim_id}/role", json={"role": "admin"}, headers=scoped_admin_auth,
    )
    assert promote_resp.status_code == 403, promote_resp.text

    self_promote_resp = await client.patch(
        f"/api/admin/users/{scoped_admin_id}/role", json={"role": "owner"}, headers=scoped_admin_auth,
    )
    assert self_promote_resp.status_code == 403, self_promote_resp.text
