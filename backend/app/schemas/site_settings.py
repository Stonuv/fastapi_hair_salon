from datetime import time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .fields import HexColorStr

# ── Контент сайта — редактируется администратором (CMS) ───────────
# Каждый раздел соответствует блоку на главной странице / шапке / футере.
# Значения по умолчанию повторяют текущие захардкоженные тексты —
# если админ ничего не сохранял, сайт выглядит как сейчас.


class HeaderContent(BaseModel):
    brand_name:    Annotated[str, Field(min_length=1, max_length=60)] = "Сайтама"
    brand_tagline: Annotated[str, Field(min_length=1, max_length=60)] = "Барбершоп"


HeroVariant = Literal["split", "poster", "dark"]
# Медиа в правом/верхнем блоке главного экрана: статичное фото или
# интерактивная 3D-модель зала (вращается за курсором на фронтенде).
HeroMediaType = Literal["photo", "3d"]


class HeroContent(BaseModel):
    variant:          HeroVariant = "split"
    eyebrow:          Annotated[str, Field(max_length=200)] = "С 2019 года — современное барберство"
    title:            Annotated[str, Field(min_length=1, max_length=200)] = "Чёткий\nсрез.\nТихий\nзал."
    subtitle:         Annotated[str, Field(max_length=500)] = (
        "Без навязанных услуг и спешки. Точная стрижка и чистый финиш — запись с точностью до минуты."
    )
    primary_button:   Annotated[str, Field(min_length=1, max_length=60)] = "Записаться"
    secondary_button: Annotated[str, Field(min_length=1, max_length=60)] = "Услуги и цены"
    media_type:       HeroMediaType = "photo"
    photo_url:        Annotated[str | None, Field(default=None, max_length=2048)]


class FeatureItem(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=100)]
    text:  Annotated[str, Field(min_length=1, max_length=400)]


def _default_feature_items() -> list[FeatureItem]:
    return [
        FeatureItem(title="Точная стрижка",
                   text="Каждый мастер начинает с консультации, а не с догадок. Вы уходите ровно с тем образом, который просили."),
        FeatureItem(title="Без спешки",
                   text="Между записями достаточно времени на каждого клиента. Никакого двойного бронирования и поторапливания."),
        FeatureItem(title="Чистый финиш",
                   text="Каждая стрижка заканчивается аккуратным оформлением линии шеи — это стандарт, а не платная опция."),
    ]


class FeaturesContent(BaseModel):
    eyebrow: Annotated[str, Field(max_length=200)] = "Почему «Сайтама»"
    title:   Annotated[str, Field(min_length=1, max_length=200)] = "Барбершоп без лишнего."
    items:   Annotated[list[FeatureItem], Field(min_length=1, max_length=6)] = Field(default_factory=_default_feature_items)


class ServicesContent(BaseModel):
    eyebrow: Annotated[str, Field(max_length=200)] = "Услуги и цены"
    title:   Annotated[str, Field(min_length=1, max_length=200)] = "Меню."
    note:    Annotated[str, Field(max_length=300)] = "Цены в рублях\nОплата картой и наличными"


class MastersContent(BaseModel):
    eyebrow: Annotated[str, Field(max_length=200)] = "Наши мастера"
    title:   Annotated[str, Field(min_length=1, max_length=200)] = "Мастера, которым доверяют."


class CtaContent(BaseModel):
    eyebrow:      Annotated[str, Field(max_length=200)] = "Готовы, когда будете вы"
    title:        Annotated[str, Field(min_length=1, max_length=200)] = "Займите место."
    subtitle:     Annotated[str, Field(max_length=500)] = "Выберите мастера, дату и время. Подтверждение приходит сразу после записи."
    button_label: Annotated[str, Field(min_length=1, max_length=60)] = "Записаться"


class SocialLink(BaseModel):
    label: Annotated[str, Field(min_length=1, max_length=60)]
    url:   Annotated[str, Field(min_length=1, max_length=500)]


def _default_social_links() -> list[SocialLink]:
    return [
        SocialLink(label="Instagram ↗", url="#"),
        SocialLink(label="Google Карты ↗", url="#"),
        SocialLink(label="Сертификаты ↗", url="#"),
    ]


class FooterContent(BaseModel):
    tagline:     Annotated[str, Field(max_length=300)] = "Чёткий срез, тихий зал. Современное барберство с точностью до минуты."
    address:     Annotated[str, Field(max_length=300)] = "ул. Тверская, 12\nМосква\n+7 (495) 123-45-67"
    hours:       Annotated[str, Field(max_length=300)] = "Пн–Пт 9:00–20:00\nСб 10:00–18:00\nВс — выходной"
    social_links: Annotated[list[SocialLink], Field(max_length=8)] = Field(default_factory=_default_social_links)
    bottom_note: Annotated[str, Field(max_length=200)] = "Запись онлайн · Оплата картой и наличными"


# ── Время работы салона (ISSUES #36) ──────────────────────────────
# В отличие от footer.hours (просто текст для отображения в футере — может
# написать что угодно) — это машиночитаемая жёсткая граница: расписание
# любого мастера (MasterService.set_schedule/update_schedule) и любая
# запись (AppointmentService._validate_within_schedule) не могут выходить
# за эти рамки, даже если конкретный мастер хочет "работать допоздна".
class BusinessHoursContent(BaseModel):
    open_time:  Annotated[time, Field(description="Открытие салона")] = time(9, 0)
    close_time: Annotated[time, Field(description="Закрытие салона")] = time(20, 0)

    @model_validator(mode="after")
    def close_after_open(self) -> "BusinessHoursContent":
        if self.close_time <= self.open_time:
            raise ValueError("Время закрытия должно быть позже времени открытия")
        return self


# ── Тема оформления — применяется сайт-целиком (Tailwind-токены как
# CSS-переменные, см. frontend/tailwind.config.js). `preset` — чисто для
# UI в админке (какая пресет-кнопка подсвечена); фактически применяются
# всегда значения `colors`, "custom" ставится фронтендом при ручной правке.
ThemePreset = Literal["default", "coffee", "slate", "custom"]
# Пары шрифтов (осн. текст+заголовки / моно-надписи вроде eyebrow) — только
# готовые пары, без произвольного ввода (см. frontend/src/theme/fonts.js
# — там же Google Fonts URL и CSS-фолбэки для каждой пары).
FontPreset = Literal["golos", "archivo", "manrope", "grotesk", "inter"]


class ThemeColors(BaseModel):
    brand_900:  HexColorStr = "#111111"
    brand_800:  HexColorStr = "#3A3A3A"
    brand_700:  HexColorStr = "#5C5C5C"
    accent_400: HexColorStr = "#FBBF24"
    accent_100: HexColorStr = "#ECEAE5"
    ink_900:    HexColorStr = "#111111"
    ink_600:    HexColorStr = "#5C5955"
    stone_50:   HexColorStr = "#F4F3F0"
    stone_200:  HexColorStr = "#E3E1DC"


class ThemeContent(BaseModel):
    preset: ThemePreset = "default"
    colors: ThemeColors = Field(default_factory=ThemeColors)
    font:   FontPreset = "golos"


class SiteContent(BaseModel):
    """Полный редактируемый контент сайта. Используется и как тело
    PATCH-запроса, и как тело ответа — форма в админке всегда
    отправляет/получает объект целиком."""

    model_config = ConfigDict(from_attributes=True)

    header:   HeaderContent   = Field(default_factory=HeaderContent)
    hero:     HeroContent     = Field(default_factory=HeroContent)
    features: FeaturesContent = Field(default_factory=FeaturesContent)
    services: ServicesContent = Field(default_factory=ServicesContent)
    theme:    ThemeContent    = Field(default_factory=ThemeContent)
    masters:  MastersContent  = Field(default_factory=MastersContent)
    cta:      CtaContent      = Field(default_factory=CtaContent)
    footer:   FooterContent   = Field(default_factory=FooterContent)
    business_hours: BusinessHoursContent = Field(default_factory=BusinessHoursContent)
