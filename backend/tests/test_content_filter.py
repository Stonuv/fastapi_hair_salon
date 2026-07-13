"""contains_profanity()/contains_link() — regression coverage focused on the
false-positive traps of a prefix/substring word filter (see content_filter.py
docstring for why roots are checked as word-prefixes, not raw substrings)."""
from app.utils.content_filter import contains_link, contains_profanity


class TestContainsProfanity:
    def test_clean_text_is_not_flagged(self):
        assert contains_profanity("Отличный мастер, стрижка супер!") is False

    def test_none_and_empty_are_not_flagged(self):
        assert contains_profanity(None) is False
        assert contains_profanity("") is False

    def test_plain_bad_word_is_flagged(self):
        assert contains_profanity("это просто бляха-муха") is True

    def test_evasion_with_dots_is_flagged(self):
        assert contains_profanity("ты х.у.й") is True

    def test_evasion_with_repeated_letters_is_flagged(self):
        assert contains_profanity("сууукаа блин") is True

    def test_latin_lookalike_evasion_is_flagged(self):
        # "cyka" -> "сука" через таблицу латиница->кириллица
        assert contains_profanity("cyka, что за сервис") is True

    def test_english_profanity_is_flagged(self):
        assert contains_profanity("what the fuck is this") is True

    def test_double_letter_english_word_is_still_flagged(self):
        # Regression: до фикса _REPEATED_LETTER схлопывал двойную "ss" внутри
        # обычного написания слова ("asshole" -> "ashole"), из-за чего этот
        # уже существующий корень никогда не совпадал с реальным словом.
        assert contains_profanity("such an asshole") is True

    def test_more_english_profanity_words_are_flagged(self):
        for word in ("dick", "pussy", "whore", "slut", "bastard", "twat", "wanker", "douche"):
            assert contains_profanity(f"you {word}") is True, word

    def test_english_compound_profanity_is_flagged(self):
        # Бранный корень не в начале слова ("motherfucker" не начинается с
        # "fuck") — нужны отдельные составные корни, как для "долбоеб".
        for word in ("motherfucker", "bullshit", "jackass", "dumbass"):
            assert contains_profanity(f"such a {word}") is True, word

    def test_english_words_with_similar_prefixes_are_safe(self):
        # Ложных срабатываний быть не должно: реальные слова, которые не
        # являются бранными, но могли бы задеть новые корни.
        assert contains_profanity("check the dictionary") is False
        assert contains_profanity("douching the sink with soap") is False

    def test_does_not_false_positive_across_word_boundary(self):
        """Regression: "плохую" + начало следующего слова на "й" не должны
        склеиваться в "хую" — фильтр не должен убирать пробелы между словами."""
        assert contains_profanity("не самую плохую йогу видел") is False

    def test_common_words_starting_with_similar_syllables_are_safe(self):
        assert contains_profanity("художник из хутора любит худой хурма") is False

    def test_dog_breeding_term_is_still_flagged_in_this_context(self):
        # "сука" как корень намеренно ловится — в контексте отзывов о
        # барбершопе легитимного использования (собаководство) не бывает.
        assert contains_profanity("наглая сука на ресепшене") is True


class TestContainsLink:
    def test_clean_text_is_not_flagged(self):
        assert contains_link("Приходил в 10 утра, всё отлично") is False

    def test_none_and_empty_are_not_flagged(self):
        assert contains_link(None) is False
        assert contains_link("") is False

    def test_http_link_is_flagged(self):
        assert contains_link("Больше отзывов на http://example.com/reviews") is True

    def test_www_link_is_flagged(self):
        assert contains_link("см. www.example.ru") is True

    def test_bare_domain_is_flagged(self):
        assert contains_link("пишите мне на promo-site.com за скидкой") is True

    def test_ru_domain_is_flagged(self):
        assert contains_link("мой сайт мастер.рф") is True

    def test_decimal_numbers_are_not_flagged(self):
        assert contains_link("отросло на 2.5 см за месяц") is False

    def test_abbreviations_with_dots_are_not_flagged(self):
        assert contains_link("отличный мастер, т.е. рекомендую") is False
