import re
from collections.abc import Callable

# Практическая транслитерация (веб-конвенция, не ГОСТ) — читаемость URL
# важнее академической точности. ъ/ь отбрасываются, а не подставляются
# апострофом — тот тоже пришлось бы вырезать на следующем шаге.
_CYRILLIC_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """"Сайтама на Тверской" → "sajtama-na-tverskoj". Транслитерация +
    lowercase + небуквенно-цифровые символы схлопываются в один дефис,
    ведущие/хвостовые дефисы обрезаются."""
    lowered = text.lower()
    transliterated = "".join(_CYRILLIC_MAP.get(ch, ch) for ch in lowered)
    return _NON_SLUG_CHARS.sub("-", transliterated).strip("-")


def generate_unique_slug(name: str, *, exists: Callable[[str], bool], fallback: str = "salon") -> str:
    """slug из name + числовой суффикс при коллизии (-2, -3, …). `exists`
    — предикат уникальности (обычно поход в БД), нарочно не завязан на
    конкретный репозиторий, чтобы функцию можно было протестировать без БД.
    `fallback` — на случай названия из одних не-буквенно-цифровых символов
    (пустой slug сам по себе не невалиден для БД, но бессмысленен как URL)."""
    base = slugify(name) or fallback
    if not exists(base):
        return base
    suffix = 2
    while exists(f"{base}-{suffix}"):
        suffix += 1
    return f"{base}-{suffix}"
