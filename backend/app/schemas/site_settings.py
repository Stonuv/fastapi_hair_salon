from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# ── Контент сайта — редактируется администратором (CMS) ───────────
# Каждый раздел соответствует блоку на главной странице / шапке / футере.
# Значения по умолчанию повторяют текущие захардкоженные тексты —
# если админ ничего не сохранял, сайт выглядит как сейчас.


class HeaderContent(BaseModel):
    brand_name:    Annotated[str, Field(min_length=1, max_length=60)] = "Сайтама"
    brand_tagline: Annotated[str, Field(min_length=1, max_length=60)] = "Барбершоп"


class HeroContent(BaseModel):
    eyebrow:          Annotated[str, Field(max_length=200)] = "С 2019 года — современное барберство"
    title:            Annotated[str, Field(min_length=1, max_length=200)] = "Чёткий\nсрез.\nТихий\nзал."
    subtitle:         Annotated[str, Field(max_length=500)] = (
        "Без навязанных услуг и спешки. Точная стрижка и чистый финиш — запись с точностью до минуты."
    )
    primary_button:   Annotated[str, Field(min_length=1, max_length=60)] = "Записаться"
    secondary_button: Annotated[str, Field(min_length=1, max_length=60)] = "Услуги и цены"
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


class SiteContent(BaseModel):
    """Полный редактируемый контент сайта. Используется и как тело
    PATCH-запроса, и как тело ответа — форма в админке всегда
    отправляет/получает объект целиком."""

    model_config = ConfigDict(from_attributes=True)

    header:   HeaderContent   = Field(default_factory=HeaderContent)
    hero:     HeroContent     = Field(default_factory=HeroContent)
    features: FeaturesContent = Field(default_factory=FeaturesContent)
    services: ServicesContent = Field(default_factory=ServicesContent)
    masters:  MastersContent  = Field(default_factory=MastersContent)
    cta:      CtaContent      = Field(default_factory=CtaContent)
    footer:   FooterContent   = Field(default_factory=FooterContent)
