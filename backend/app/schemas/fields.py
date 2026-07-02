"""Переиспользуемые Annotated-типы для полей схем (см. claude_hints.md)."""
from typing import Annotated

from pydantic import AfterValidator, Field

# bcrypt хеширует только первые 72 байта и (начиная с bcrypt 5.x) бросает
# ValueError на более длинный ввод — без верхней границы запрос с длинным
# паролем ронял регистрацию/сброс пароля с 500.
_BCRYPT_MAX_BYTES = 72


def _fits_bcrypt(v: str) -> str:
    if len(v.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValueError("Пароль не должен превышать 72 байта")
    return v


NameStr        = Annotated[str, Field(min_length=1, max_length=100)]
PhoneStr       = Annotated[str, Field(max_length=20)]
PasswordStr    = Annotated[str, Field(min_length=8, max_length=_BCRYPT_MAX_BYTES,
                                      description="Пароль (8–72 символа)"),
                           AfterValidator(_fits_bcrypt)]
PositiveMoney  = Annotated[float, Field(gt=0)]
NonNegativeMoney = Annotated[float, Field(ge=0)]
RatingInt      = Annotated[int, Field(ge=1, le=5)]
