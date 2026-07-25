"""Salon-scoping сквозь реальный HTTP-стек и Postgres (ROADMAP.md §4.8, Фаза C).
Юнит-тесты (test_salon_scoping.py) проверяют ветвления сервисов на фейковых
репозиториях; этот файл — что repository-level join'ы (особенно
UserRepository.list_paginated — outerjoin на Master + OR по ролям) реально
дают верный SQL, а не только "выглядит правильно на бумаге"."""
from datetime import time

import pytest

from app.models.enums import UserRole
from app.repositories.master_repository import MasterRepository
from app.repositories.salon_repository import SalonRepository
from app.repositories.user_repository import UserRepository
from app.schemas.salon import SalonCreate
from app.schemas.user import UserCreate
from app.services.auth_service import hash_password

from .conftest import TEST_PASSWORD, next_weekday_at

pytestmark = pytest.mark.integration


async def _login(client, email: str, password: str = TEST_PASSWORD) -> dict:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    client.cookies.clear()  # см. test_admin_role_assignment_flow.py — общий cookie jar
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_salon(db_session, name: str):
    salon = SalonRepository(db_session).create(
        SalonCreate(name=name, address=f"ул. {name}, 1", open_time=time(9, 0), close_time=time(20, 0)),
        slug=f"salon-{name.lower()}",
    )
    db_session.commit()
    return salon


def _make_user(db_session, *, email: str, role: UserRole, salon_id=None,
               first_name="Тест", last_name="Тестов"):
    # ck_users_admin_requires_salon требует salon_id уже в момент, когда role
    # становится 'admin' — тот же порядок, что и в реальном двухшаговом флоу
    # (PATCH .../salon, затем PATCH .../role), см. test_admin_role_assignment_flow.py.
    repo = UserRepository(db_session)
    create_role = UserRole.client if role == UserRole.admin else role
    user = repo.create(
        UserCreate(email=email, first_name=first_name, last_name=last_name, password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD), role=create_role,
    )
    if salon_id is not None:
        user = repo.set_salon(user, salon_id)
    if role == UserRole.admin:
        user = repo.set_role(user, role)
    db_session.commit()
    return user


def _make_master(db_session, *, email: str, salon_id, is_active=True, first_name="Мастер"):
    user = _make_user(db_session, email=email, role=UserRole.master, first_name=first_name)
    master = MasterRepository(db_session).create(user.id, salon_id)
    if not is_active:
        MasterRepository(db_session).deactivate(master)
    db_session.commit()
    return master


@pytest.fixture
def two_salons(db_session):
    salon_a = _make_salon(db_session, "Альфа")
    salon_b = _make_salon(db_session, "Бета")
    return salon_a, salon_b


@pytest.mark.anyio
async def test_admin_users_list_scoped_to_own_salon_masters_and_admins(client, db_session, two_salons):
    """Клиенты видны admin'у без ограничений (один аккаунт на всю сеть),
    master/admin — только своей точки (ROADMAP.md §4.5/§4.8)."""
    salon_a, salon_b = two_salons
    _make_user(db_session, email="owner@example.com", role=UserRole.owner)
    _make_user(db_session, email="admin-a@example.com", role=UserRole.admin, salon_id=salon_a.id)
    _make_user(db_session, email="admin-b@example.com", role=UserRole.admin, salon_id=salon_b.id)
    _make_master(db_session, email="master-a@example.com", salon_id=salon_a.id)
    _make_master(db_session, email="master-b@example.com", salon_id=salon_b.id)
    _make_user(db_session, email="client@example.com", role=UserRole.client)

    admin_a_auth = await _login(client, "admin-a@example.com")
    resp = await client.get("/api/admin/users", params={"page_size": 20}, headers=admin_a_auth)
    assert resp.status_code == 200, resp.text
    emails = {u["email"] for u in resp.json()["items"]}

    assert "client@example.com" in emails          # клиент виден без ограничений
    assert "admin-a@example.com" in emails         # свой salon
    assert "master-a@example.com" in emails        # свой salon
    assert "admin-b@example.com" not in emails     # чужой salon — скрыт
    assert "master-b@example.com" not in emails    # чужой salon — скрыт


@pytest.mark.anyio
async def test_owner_users_list_defaults_to_whole_network(client, db_session, two_salons):
    salon_a, salon_b = two_salons
    _make_user(db_session, email="owner@example.com", role=UserRole.owner)
    _make_master(db_session, email="master-a@example.com", salon_id=salon_a.id)
    _make_master(db_session, email="master-b@example.com", salon_id=salon_b.id)

    owner_auth = await _login(client, "owner@example.com")
    resp = await client.get("/api/admin/users", params={"page_size": 20}, headers=owner_auth)
    assert resp.status_code == 200, resp.text
    emails = {u["email"] for u in resp.json()["items"]}
    assert {"master-a@example.com", "master-b@example.com"} <= emails


@pytest.mark.anyio
async def test_masters_catalog_salon_filter_and_inactive_visibility(client, db_session, two_salons):
    salon_a, salon_b = two_salons
    _make_user(db_session, email="owner@example.com", role=UserRole.owner)
    _make_master(db_session, email="active-a@example.com", salon_id=salon_a.id, first_name="Активный")
    _make_master(db_session, email="inactive-a@example.com", salon_id=salon_a.id,
                is_active=False, first_name="Скрытый")
    _make_master(db_session, email="active-b@example.com", salon_id=salon_b.id, first_name="Чужой")

    # Публичный вызов: только активные, только своей точки при фильтре.
    public_resp = await client.get("/api/masters", params={"salon_id": str(salon_a.id), "page_size": 20})
    assert public_resp.status_code == 200, public_resp.text
    public_names = {m["first_name"] for m in public_resp.json()["items"]}
    assert public_names == {"Активный"}

    # owner видит и деактивированных.
    owner_auth = await _login(client, "owner@example.com")
    owner_resp = await client.get(
        "/api/masters", params={"salon_id": str(salon_a.id), "page_size": 20}, headers=owner_auth,
    )
    assert owner_resp.status_code == 200, owner_resp.text
    owner_names = {m["first_name"] for m in owner_resp.json()["items"]}
    assert owner_names == {"Активный", "Скрытый"}


@pytest.mark.anyio
async def test_admin_cannot_view_appointment_of_other_salon(client, db_session, bookable_setup, two_salons):
    """Regression (ROADMAP.md §4.8 Фаза C): раньше admin видел любую запись сети."""
    salon_a, _ = two_salons
    _make_user(db_session, email="owner@example.com", role=UserRole.owner)
    _make_user(db_session, email="admin-a@example.com", role=UserRole.admin, salon_id=salon_a.id)

    # bookable_setup создаёт салон/мастера в СВОЕЙ (третьей) точке — не salon_a/salon_b.
    await client.post("/api/auth/register", json={
        "email": "booker@example.com", "first_name": "Клиент", "last_name": "Букер",
        "password": TEST_PASSWORD,
    })
    client.cookies.clear()
    booker_auth = await _login(client, "booker@example.com")

    start = next_weekday_at(0, 10)
    create_resp = await client.post("/api/appointments", json={
        "master_id": str(bookable_setup.master.id), "service_id": str(bookable_setup.service.id),
        "start_time": start.isoformat(),
    }, headers=booker_auth)
    assert create_resp.status_code == 201, create_resp.text
    appointment_id = create_resp.json()["id"]

    admin_a_auth = await _login(client, "admin-a@example.com")
    resp = await client.get(f"/api/appointments/{appointment_id}", headers=admin_a_auth)
    assert resp.status_code == 403, resp.text


@pytest.mark.anyio
async def test_settings_and_services_writes_are_owner_only(client, db_session, two_salons):
    salon_a, _ = two_salons
    _make_user(db_session, email="owner@example.com", role=UserRole.owner)
    _make_user(db_session, email="admin-a@example.com", role=UserRole.admin, salon_id=salon_a.id)

    admin_auth = await _login(client, "admin-a@example.com")
    owner_auth = await _login(client, "owner@example.com")

    settings_get = await client.get("/api/settings")
    admin_settings_resp = await client.patch("/api/settings", json=settings_get.json(), headers=admin_auth)
    assert admin_settings_resp.status_code == 403, admin_settings_resp.text
    owner_settings_resp = await client.patch("/api/settings", json=settings_get.json(), headers=owner_auth)
    assert owner_settings_resp.status_code == 200, owner_settings_resp.text

    service_payload = {"name": "Тестовая услуга", "price": "500.00", "duration_min": 30}
    admin_service_resp = await client.post("/api/services", json=service_payload, headers=admin_auth)
    assert admin_service_resp.status_code == 403, admin_service_resp.text
    owner_service_resp = await client.post("/api/services", json=service_payload, headers=owner_auth)
    assert owner_service_resp.status_code == 201, owner_service_resp.text
