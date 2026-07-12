import re

# Корни нецензурной лексики — сознательно небольшой список конкретных
# корней (не общих слогов вроде "ху"/"пи", которые ловили бы обычные слова
# типа "художник"/"хутор"/"пирог"), а не словарь всех словоформ. Каждый
# элемент проверяется как ПРЕФИКС отдельного слова после нормализации —
# расширяйте список при необходимости.
_PROFANITY_ROOTS = (
    "хуй", "хуе", "хуё", "хую", "хуя",
    "пизд",
    "еба", "ебу", "ебн", "ёб",
    "бля",
    "муда", "мудо", "мудак",
    "сука", "суки",
    "гандон",
    "долбоеб", "долбоёб",
    "пидор", "пидар",
    "залуп",
    "шлюх",
    "fuck", "shit", "bitch", "asshole", "cunt",
)

_LATIN_TO_CYRILLIC = str.maketrans({
    "a": "а", "e": "е", "o": "о", "p": "р", "c": "с",
    "x": "х", "y": "у", "k": "к", "m": "м", "t": "т", "h": "н", "b": "в",
})

_NON_LETTER = re.compile(r"[^a-zа-яёA-ZА-ЯЁ]+")
_REPEATED_LETTER = re.compile(r"(.)\1{1,}")


def _clean_word(word: str) -> str:
    """Схлопывает типичный обход фильтра внутри одного "слова": разделители
    (х.у.й, х-у-й), повтор букв (хууй -> хуй) — но НЕ склеивает разные слова
    между собой (иначе "плохую йогу" превратилось бы в ложное срабатывание
    на "хую"), и не трогает латиницу/кириллицу — это отдельный шаг
    (см. contains_profanity), иначе английские корни вроде "fuck" ломаются
    переводом c/k в кириллические с/к."""
    word = word.lower()
    word = _NON_LETTER.sub("", word)
    return _REPEATED_LETTER.sub(r"\1", word)


def contains_profanity(text: str | None) -> bool:
    if not text:
        return False
    for raw_word in text.split():
        cleaned = _clean_word(raw_word)
        # Два варианта: как есть (ловит английские корни: "fuck") и с
        # переводом латинских двойников в кириллицу (ловит "cyka" -> "сука").
        # Перевод не трогает уже кириллические слова, так что для них оба
        # варианта совпадают.
        translated = cleaned.translate(_LATIN_TO_CYRILLIC)
        if any(cleaned.startswith(root) or translated.startswith(root)
              for root in _PROFANITY_ROOTS):
            return True
    return False


# http(s)://..., www...., или домен с частой зоной (мастер.рф, site.com) —
# запрет ссылок в отзывах (ISSUES #29а), не только "http" в лоб.
_LINK_PATTERN = re.compile(
    r"(https?://|www\.)\S+"
    r"|\b[a-zа-яёA-ZА-ЯЁ0-9-]{2,63}\.(ru|com|net|org|io|me|su|biz|info|xyz|top|site|online|store|shop|рф)\b",
    re.IGNORECASE,
)


def contains_link(text: str | None) -> bool:
    if not text:
        return False
    return bool(_LINK_PATTERN.search(text))
