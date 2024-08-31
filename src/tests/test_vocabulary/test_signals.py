import pytest

from model_bakery import baker
from django.db.models.signals import pre_save

from apps.vocabulary.models import Word

pytestmark = [pytest.mark.signals]


class TestSlugFiller:
    @pytest.mark.django_db
    def test_pre_save(self):
        instance = baker.prepare(Word)

        pre_save.send(Word, instance=instance, created=False)

        assert instance.slug != ''

    # word post delete extra objs

    # user pre save set default settings
