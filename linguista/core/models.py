''' Core abstract models '''

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CreatedModel(models.Model):
    '''
    Abstract base class to add date created field
    '''

    created = models.DateTimeField(
        _('Date created'),
        editable=False,
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True


class ModifiedModel(models.Model):
    '''
    Abstract base class to add date modified field
    '''

    modified = models.DateTimeField(
        _('Date modified'),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.modified = timezone.now()
        return super().save(*args, **kwargs)


class UserRelatedModel(CreatedModel):
    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
