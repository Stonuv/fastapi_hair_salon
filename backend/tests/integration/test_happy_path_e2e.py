"""Happy path целиком через реальный HTTP-стек поверх реальной БД: клиент
регистрируется, видит свободный слот, бронирует, мастер подтверждает и
завершает запись. Юнит-тесты проверяют этот сценарий по кускам с фейковыми
репозиториями (см. test_appointment_create_guards.py, test_state_machine.py);
здесь — что все куски реально работают вместе поверх настоящего Postgres."""
from datetime import datetime

import pytest

from .conftest import TEST_PASSWORD, next_weekday_at

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_client_registers_books_and_master_completes_appointment(client, bookable_setup):
    start = next_weekday_at(weekday=0, hour=11)
    master_id = str(bookable_setup.master.id)
    service_id = str(bookable_setup.service.id)

    # 1. Регистрация клиента
    register_resp = await client.post("/api/auth/register", json={
        "email": "happy-client@example.com",
        "first_name": "Клиент", "last_name": "Довольный",
        "password": TEST_PASSWORD,
    })
    assert register_resp.status_code == 201, register_resp.text
    client_auth = {"Authorization": f"Bearer {register_resp.json()['access_token']}"}

    # 2. Свободные слоты на этот день включают выбранное время
    slots_resp = await client.get(
        f"/api/masters/{master_id}/slots",
        params={"service_id": service_id, "target_date": start.date().isoformat()},
    )
    assert slots_resp.status_code == 200, slots_resp.text
    slot_starts = {datetime.fromisoformat(s["start_time"]) for s in slots_resp.json()["slots"]}
    assert start in slot_starts

    # 3. Бронирование
    create_resp = await client.post(
        "/api/appointments",
        json={"master_id": master_id, "service_id": service_id, "start_time": start.isoformat()},
        headers=client_auth,
    )
    assert create_resp.status_code == 201, create_resp.text
    appointment = create_resp.json()
    assert appointment["status"] == "pending"
    appointment_id = appointment["id"]

    # 4. Клиент видит свою запись
    get_resp = await client.get(f"/api/appointments/{appointment_id}", headers=client_auth)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "pending"

    # 5. Мастер логинится (тем же паролем, что задан в bookable_setup)
    master_login = await client.post("/api/auth/login", json={
        "email": bookable_setup.master_user.email,
        "password": bookable_setup.master_password,
    })
    assert master_login.status_code == 200, master_login.text
    master_auth = {"Authorization": f"Bearer {master_login.json()['access_token']}"}

    # 6. Мастер подтверждает запись (pending -> confirmed)
    confirm_resp = await client.patch(
        f"/api/appointments/{appointment_id}/status",
        json={"status": "confirmed"},
        headers=master_auth,
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    assert confirm_resp.json()["status"] == "confirmed"

    # 7. Мастер завершает запись (confirmed -> done)
    done_resp = await client.patch(
        f"/api/appointments/{appointment_id}/status",
        json={"status": "done"},
        headers=master_auth,
    )
    assert done_resp.status_code == 200, done_resp.text
    assert done_resp.json()["status"] == "done"

    # 8. Финальное состояние видно клиенту
    final_resp = await client.get(f"/api/appointments/{appointment_id}", headers=client_auth)
    assert final_resp.status_code == 200
    assert final_resp.json()["status"] == "done"
