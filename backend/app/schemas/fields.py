"""Переиспользуемые Annotated-типы для полей схем (см. claude_hints.md)."""
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field, PlainSerializer

# bcrypt хеширует только первые 72 байта и (начиная с bcrypt 5.x) бросает
# ValueError на более длинный ввод — без верхней границы запрос с длинным
# паролем ронял регистрацию/сброс пароля с 500.
_BCRYPT_MAX_BYTES = 72


def _fits_bcrypt(v: str) -> str:
    if len(v.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValueError("Пароль не должен превышать 72 байта")
    return v


NameStr        = Annotated[str, Field(min_length=1, max_length=100)]
# Цвет темы оформления: строго #RRGGBB (то, что отдаёт <input type="color">)
HexColorStr    = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]
# Телефон: цифры, необязательный +, скобки/пробелы/дефисы; 5–20 символов
PhoneStr       = Annotated[str, Field(max_length=20,
                                      pattern=r"^\+?[0-9()\- ]{5,20}$")]
PasswordStr    = Annotated[str, Field(min_length=8, max_length=_BCRYPT_MAX_BYTES,
                                      description="Пароль (8–72 символа)"),
                           AfterValidator(_fits_bcrypt)]
# Деньги: в БД Numeric(10,2), валидация и арифметика — в Decimal (float
# теряет точность), но в JSON отдаём числом, а не строкой, чтобы не менять
# контракт API для фронтенда.
_money_as_number = PlainSerializer(float, return_type=float, when_used="json")

PositiveMoney  = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2),
                           _money_as_number]
NonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2),
                             _money_as_number]
# Для response-схем: без ограничений ввода, только Decimal + сериализация числом
MoneyOut       = Annotated[Decimal, _money_as_number]
RatingInt      = Annotated[int, Field(ge=1, le=5)]
