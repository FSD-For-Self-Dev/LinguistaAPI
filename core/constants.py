"""Core constants."""
import os

from django.utils.translation import gettext_lazy as _

from .exceptions import AmountLimitExceeded

GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
)

ADMIN_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', default='admin')


class AmountLimits:
    """
    Amount limit base class to set some objects amount limits and get detail message
    when AmountLimitExceeded custom exception is raised.
    """

    @staticmethod
    def get_error_message(limit, attr_name=None):
        if attr_name:
            return f'{attr_name}: достигнуто максимальное кол-во ({limit}).'
        return f'Достигнуто максимальное кол-во ({limit}).'

    @staticmethod
    def check_amount_limit(
        existing_objs_amount: int,
        new_objs_amount: int,
        amount_limit: int,
        attr_name: str = 'objects',
    ) -> None:
        """
        Raises AmountLimitExceeded custom exception if objects amount exceeded.
        """
        if existing_objs_amount + new_objs_amount > amount_limit:
            raise AmountLimitExceeded(
                detail=AmountLimits.get_error_message(amount_limit, attr_name=attr_name)
            )
