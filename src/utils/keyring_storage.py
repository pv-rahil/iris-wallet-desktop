"""
This module contains the keyring class, which represents
an operation manager for keyring functionalities.
"""
from __future__ import annotations

import keyring as kr

from src.utils.constant import APP_NAME
from src.utils.logging import logger


def set_value(key: str, value: str, network: str | None = None) -> bool:
    """Set a value in the keyring with a specific key, considering the backend being used.

    Args:
        key: The key under which the value is stored.
        value: The value to store.
        network: Optional network string to modify the key.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    if network is not None:
        key = f'{key}_{network}'

    try:
        # Get the current backend being used by keyring
        backend = kr.get_keyring()
        logger.info('Using backend: %s', backend)

        # Attempt to set the password
        kr.set_password(APP_NAME, key, value)
        logger.info('Password set successfully for key: %s', key)

        # Check if the value was stored correctly
        check_value = kr.get_password(APP_NAME, key)
        if check_value is None:
            return False
        return True

    except kr.errors.KeyringError as error:
        logger.error(
            'Exception occurred while value writing in keyring: %s, Message: %s',
            type(error).__name__, str(error),
        )
        return False
    except Exception as error:
        logger.error(
            'Exception occurred while value writing in keyring: %s, Message: %s',
            type(error).__name__, str(error),
        )
        return False


def get_value(key: str, network: str | None = None):
    """Get a value from the keyring based on the key.

    Args:
        key: The key for which to retrieve the value.

    Returns:
        The retrieved value or None if an error occurred.
    """
    if network is not None:
        key = f'{key}_{network}'
    try:
        return kr.get_password(APP_NAME, key)
    except kr.errors.KeyringError as error:
        logger.error(
            'Exception occurred while getting value from keyring: %s, Message: %s',
            type(error).__name__, str(error),
        )
        return None


def delete_value(key: str, network: str | None = None) -> None:
    """Delete a value in the keyring associated with a specific key.

    Args:
        key: The key for which the value should be deleted.
    """
    try:
        if network is not None:
            key = f'{key}_{network}'
        kr.delete_password(APP_NAME, key)
        logger.info('Password deleted successfully for key: %s', key)
    except kr.errors.KeyringError as error:
        logger.error(
            'Exception occurred while deleting keyring value %s, Message: %s',
            type(error).__name__, str(error),
        )
