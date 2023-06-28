from django.db import models


class DateAddedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    date_added = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
