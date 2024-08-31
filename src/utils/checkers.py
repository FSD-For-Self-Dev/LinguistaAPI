"""Utils to check something."""

import logging

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
