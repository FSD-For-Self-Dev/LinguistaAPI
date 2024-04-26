"""Core constants."""

from django.utils.translation import gettext_lazy as _

GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
)


class AmountLimits:
    """Ограничения кол-ва объектов."""

    @staticmethod
    def get_error_message(limit, attr_name=None):
        if attr_name:
            return _(f'{attr_name}: достигнуто максимальное кол-во ({limit}).')
        return _(f'Достигнуто максимальное кол-во ({limit}).')
