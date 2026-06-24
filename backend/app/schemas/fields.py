"""Переиспользуемые Annotated-типы для полей схем (см. claude_hints.md)."""
from typing import Annotated

from pydantic import Field

NameStr        = Annotated[str, Field(min_length=1, max_length=100)]
PhoneStr       = Annotated[str, Field(max_length=20)]
PositiveMoney  = Annotated[float, Field(gt=0)]
NonNegativeMoney = Annotated[float, Field(ge=0)]
RatingInt      = Annotated[int, Field(ge=1, le=5)]
