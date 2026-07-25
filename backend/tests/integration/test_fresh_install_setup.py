"""Первичная настройка на пустой БД (ROADMAP.md §4.10 Фаза D).

Regression: до этой фазы /api/setup создавал пользователя с role='admin' и
пустым salon_id, что нарушало ck_users_admin_requires_salon (миграция 0015);
IntegrityError перехватывался обработчиком «дубликат email» — и свежая
установка отвечала 409 «Пользователь с таким email уже существует» на
заведомо пустой БД. Ни один юнит-тест этого не видел: констрейнт живёт
только в реальной схеме Postgres.
"""
import pytest

from app.models.enums import UserRole
from app.repositories.salon_repository import SalonRepository
from app.repositories.user_repository import UserRepository

pytestmark = pytest.mark.integration

SETUP_PAYLOAD = {
    "owner": {
        "email": "founder@example.com",
        "first_name": "Основатель",
        "last_name": "Сети",
        "password": "StrongPass123!",
    },
    "salon": {
        "name": "Сайтама на Тверской",
        "address": "ул. Тверская, 12",
        "open_time": "09:00:00",
        "close_time": "20:00:00",
    },
}


@pytest.mark.anyio
async def test_fresh_install_creates_owner_and_primary_salon(client, db_session):
    status_resp = await client.get("/api/setup/status")
    assert status_resp.status_code == 200, status_resp.text
    assert status_resp.json()["completed"] is False

    resp = await client.post("/api/setup", json=SETUP_PAYLOAD)
    assert resp.status_code == 201, resp.text
    assert resp.json()["user"]["role"] == "owner"

    user = UserRepository(db_session).get_by_email("founder@example.com")
    assert user is not None
    assert user.role == UserRole.owner
    # owner не привязан к точке — он видит всю сеть (ck_users_admin_requires_salon
    # касается только admin).
    assert user.salon_id is None

    # Ровно одна точка: заглушка из миграции 0013 ЗАПОЛНена, а не продублирована.
    salons = SalonRepository(db_session).list_all()
    assert len(salons) == 1
    assert salons[0].name == "Сайтама на Тверской"
    assert salons[0].address == "ул. Тверская, 12"
    assert salons[0].slug == "saytama-na-tverskoy"

    # И визард закрывается навсегда.
    after = await client.get("/api/setup/status")
    assert after.json()["completed"] is True
    repeat = await client.post("/api/setup", json=SETUP_PAYLOAD)
    assert repeat.status_code == 404, repeat.text


@pytest.mark.anyio
async def test_owner_from_setup_can_immediately_run_the_network(client):
    """Смысл фазы — не «201 вернулся», а что созданным аккаунтом реально можно
    работать: owner-only запись настроек и каталога услуг, и заведение мастера
    в точку, созданную тем же запросом setup."""
    setup_resp = await client.post("/api/setup", json=SETUP_PAYLOAD)
    assert setup_resp.status_code == 201, setup_resp.text
    token = setup_resp.json()["access_token"]
    client.cookies.clear()
    auth = {"Authorization": f"Bearer {token}"}

    salons_resp = await client.get("/api/salons")
    assert salons_resp.status_code == 200, salons_resp.text
    salon_id = salons_resp.json()[0]["id"]

    service_resp = await client.post(
        "/api/services",
        json={"name": "Стрижка", "price": "1500.00", "duration_min": 40},
        headers=auth,
    )
    assert service_resp.status_code == 201, service_resp.text

    user_resp = await client.post("/api/admin/users", json={
        "email": "master@example.com", "first_name": "Мастер", "last_name": "Первый",
        "password": "MasterPass123!", "role": "master",
    }, headers=auth)
    assert user_resp.status_code == 201, user_resp.text

    profile_resp = await client.post(
        f"/api/admin/users/{user_resp.json()['id']}/master",
        json={"salon_id": salon_id}, headers=auth,
    )
    assert profile_resp.status_code == 201, profile_resp.text
    assert profile_resp.json()["salon"]["id"] == salon_id
