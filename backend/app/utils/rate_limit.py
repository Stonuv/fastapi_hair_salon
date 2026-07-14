from slowapi import Limiter

from .client_ip import client_ip

# По IP, не по пользователю — decorator slowapi проверяет лимит ДО того, как
# FastAPI успевает прогнать Depends() эндпоинта (current_user ещё недоступен
# в этот момент), а привязка к IP не требует такого порядка и уже достаточна:
# это защита от спама/автоматизированного перебора (регистрация, запись,
# отзывы), не замена бизнес-ограничений (например
# max_active_appointments_per_client в AppointmentService). В памяти процесса
# (без Redis) — приложение и так рассчитано на один инстанс бэкенда (см.
# ReminderService/scheduler.py), лимиты обнуляются при рестарте, что для
# soft-защиты от спама допустимо. client_ip (а не request.client.host) —
# см. utils/client_ip.py за тем, почему это важно именно за этим прокси.
limiter = Limiter(key_func=client_ip)
