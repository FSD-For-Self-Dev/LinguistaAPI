"""Utils to check something."""

import logging
from uuid import UUID

from apps.core.exceptions import AmountLimitExceeded

logger = logging.getLogger(__name__)


def check_amount_limit(
    current_amount: int, new_objects_amount: int, amount_limit: int, detail: str
) -> None:
    """
    Raises AmountLimitExceeded custom exception if objects amount limit exceeded.
    """
    logger.debug(f'Existing objects amount: {current_amount}')
    logger.debug(f'Objects amount limit: {amount_limit}')
    logger.debug(f'New objects amount: {new_objects_amount}')
    if current_amount + new_objects_amount > amount_limit:
        logger.error('AmountLimitExceeded exception occured.')
        raise AmountLimitExceeded(
            amount_limit=amount_limit,
            detail=detail,
        )


def is_valid_uuid(uuid_to_test):
    """
    Check if uuid_to_test is a valid UUID.
     Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}
     Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.
     Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = UUID(uuid_to_test)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test
