"""ReviewCreate.comment — цензура/запрет ссылок применяются на входе схемы,
до создания отзыва (отзывы публикуются сразу, без модерации)."""
import uuid

import pytest
from pydantic import ValidationError

from app.schemas.review import ReviewCreate


def make_review(comment):
    return ReviewCreate(appointment_id=uuid.uuid4(), rating=5, comment=comment)


class TestReviewCreateContentValidation:
    def test_clean_comment_is_accepted(self):
        review = make_review("Отличная стрижка, всё понравилось!")
        assert review.comment == "Отличная стрижка, всё понравилось!"

    def test_none_comment_is_accepted(self):
        review = make_review(None)
        assert review.comment is None

    def test_profanity_is_rejected_with_friendly_message(self):
        with pytest.raises(ValidationError) as exc:
            make_review("это просто бляха-муха, а не стрижка")
        errors = exc.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error"
        assert "недопустимые слова" in str(errors[0]["ctx"]["error"])

    def test_link_is_rejected_with_friendly_message(self):
        with pytest.raises(ValidationError) as exc:
            make_review("подробнее на promo-site.com")
        errors = exc.value.errors()
        assert len(errors) == 1
        assert "Ссылки" in str(errors[0]["ctx"]["error"])
