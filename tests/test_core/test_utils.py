import pytest

from core.utils import (
    slugify_text_fields,
)

pytestmark = [pytest.mark.utils]


class TestSlugifyFunctions:
    def test_slugify_text(self):
        text_field1 = "TEST -!?.,:'()"
        text_field2 = "text -!?.,:'()"
        expected_slug = 'test-text'

        result = slugify_text_fields(text_field1, text_field2)

        assert result == expected_slug
