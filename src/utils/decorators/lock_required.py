"""
This module contains custom decorators to insure node locked.
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from typing import Callable

from requests import HTTPError
from requests.exceptions import ConnectionError as RequestsConnectionError

from src.utils.custom_exception import CommonException
from src.utils.endpoints import LOCK_ENDPOINT
from src.utils.endpoints import NODE_INFO_ENDPOINT
from src.utils.error_message import ERROR_NODE_IS_LOCKED_CALL_UNLOCK
from src.utils.logging import logger
from src.utils.request import Request


def is_node_locked() -> bool:
    """Check if the node is locked by sending a request to the node info endpoint."""
    try:
        response = Request.get(NODE_INFO_ENDPOINT)
        response.raise_for_status()
        return False
    except HTTPError as error:
        if error.response.status_code == 403:
            try:
                error_data = error.response.json()
                if error_data.get('error') == ERROR_NODE_IS_LOCKED_CALL_UNLOCK and error_data.get('code') == 403:
                    return True
            except ValueError:
                pass
        else:
            error_data = error.response.json()
            error_message = error_data.get('error', 'Unhandled error')
            logger.error(error_message)
            raise CommonException(error_message) from error
    except RequestsConnectionError as exc:
        logger.error(
            'Exception occurred at Decorator(lock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException('Unable to connect to node') from exc
    except Exception as exc:
        logger.error(
            'Exception occurred at Decorator(lock_required): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException(
            'Decorator(lock_required): Error while checking if node is locked',
        ) from exc
        # This return statement ensures that the function always returns a boolean value
    return False


def call_lock() -> None:
    """Unlock the node by sending a request to the unlock endpoint."""
    try:
        response = Request.post(LOCK_ENDPOINT)
        response.raise_for_status()
    except HTTPError as exc:
        error_details = exc.response.json()
        error_message = error_details.get(
            'error',
            'Unspecified server error',
        )
        raise CommonException(error_message) from exc
    except RequestsConnectionError as exc:
        logger.error(
            'Exception occurred at Decorator(call_lock): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException('Unable to connect to node') from exc
    except Exception as exc:
        logger.error(
            'Exception occurred at Decorator(call_lock): %s, Message: %s',
            type(exc).__name__, str(exc),
        )
        raise CommonException(
            'Decorator(call_lock): Error while calling lock API',
        ) from exc


def lock_required(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to ensure the node is unlocked before proceeding with the decorated method."""
    @wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_node_locked():
            call_lock()
        return method(*args, **kwargs)

    return wrapper
