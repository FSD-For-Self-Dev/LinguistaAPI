""" Core abstract models """

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CreatedModel(models.Model):
    """ Abstract base class to add date created field """

    created = models.DateTimeField(
        _("date created"),
        editable=False,
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True


class ModifiedModel(models.Model):
    """ Abstract base class to add date modified field """

    modified = models.DateTimeField(
        _("date modified"),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """ On save, update timestamps """
        self.modified = timezone.now()
        return super().save(*args, **kwargs)
