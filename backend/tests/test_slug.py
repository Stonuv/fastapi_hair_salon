"""slugify()/generate_unique_slug() — генерация URL-слага точки сети из
названия (см. utils/slug.py). Чистые функции, без БД."""
from app.utils.slug import generate_unique_slug, slugify


class TestSlugify:
    def test_transliterates_cyrillic_and_lowercases(self):
        assert slugify("Сайтама на Тверской") == "saytama-na-tverskoy"

    def test_collapses_punctuation_into_single_hyphen(self):
        assert slugify("Салон №1 (центр)") == "salon-1-tsentr"

    def test_strips_leading_and_trailing_hyphens(self):
        assert slugify("  -Салон-  ") == "salon"

    def test_leaves_latin_and_digits_untouched(self):
        assert slugify("Barbershop 42") == "barbershop-42"

    def test_soft_sign_and_hard_sign_are_dropped_not_replaced(self):
        # ь/ъ не несут собственного звука — апостроф выглядел бы в URL
        # неоправданно, а следующий шаг (schlifka non-slug символов) всё
        # равно вырезал бы его же.
        assert slugify("подъезд") == "podezd"


class TestGenerateUniqueSlug:
    def test_returns_base_slug_when_free(self):
        assert generate_unique_slug("Салон Центр", exists=lambda s: False) == "salon-tsentr"

    def test_appends_numeric_suffix_on_single_collision(self):
        taken = {"salon-tsentr"}
        result = generate_unique_slug("Салон Центр", exists=lambda s: s in taken)
        assert result == "salon-tsentr-2"

    def test_keeps_incrementing_suffix_past_multiple_collisions(self):
        taken = {"salon-tsentr", "salon-tsentr-2", "salon-tsentr-3"}
        result = generate_unique_slug("Салон Центр", exists=lambda s: s in taken)
        assert result == "salon-tsentr-4"

    def test_falls_back_to_default_when_name_has_no_slug_chars(self):
        assert generate_unique_slug("!!!", exists=lambda s: False) == "salon"

    def test_custom_fallback_is_honored(self):
        assert generate_unique_slug("!!!", exists=lambda s: False, fallback="tochka") == "tochka"
