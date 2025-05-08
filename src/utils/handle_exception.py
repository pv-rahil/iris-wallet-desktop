# pylint: disable=too-many-function-args
"""
Handles exceptions uniformly, providing specific error messages.
"""
from __future__ import annotations

from pydantic import ValidationError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from requests.exceptions import Timeout
from rgb_lib import RgbLibError

from src.utils.custom_exception import CommonException
from src.utils.custom_exception import ServiceOperationException
from src.utils.error_message import ERROR_CONNECTION_FAILED_WITH_PROVIDED_URL
from src.utils.error_message import ERROR_REQUEST_TIMEOUT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_TYPE_VALIDATION
from src.utils.error_message import ERROR_UNSPECIFIED_SERVER_ERROR
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager


def handle_exceptions(exc):
    """
    Handles exceptions uniformly, providing specific error messages.
    """
    logger.error(
        'Exception occurred: %s, Message: %s',
        type(exc).__name__, str(exc),
    )
    # Check if the exception is an HTTPError
    if isinstance(exc, HTTPError):
        if exc.response is not None and exc.response.text:
            error_details = exc.response.json()
            error_message = error_details.get(
                'error',
                ERROR_UNSPECIFIED_SERVER_ERROR,
            )

            if exc.response.status_code == 500:
                PageNavigationEventManager.get_instance().error_report_signal.emit()
            raw_exc = exc.response.json()
            raise CommonException(error_message, raw_exc) from exc

        error_message = ERROR_UNSPECIFIED_SERVER_ERROR
        raise CommonException(error_message) from exc

    # Check if the exception is a RequestsConnectionError
    if isinstance(exc, RequestsConnectionError):
        raise CommonException(
            ERROR_CONNECTION_FAILED_WITH_PROVIDED_URL,
        ) from exc

    # Check if the exception is a Timeout
    if isinstance(exc, Timeout):
        raise CommonException(ERROR_REQUEST_TIMEOUT) from exc

    # Check if the exception is a general RequestException
    if isinstance(exc, RequestException):
        raise CommonException(ERROR_UNSPECIFIED_SERVER_ERROR) from exc

    # Check if the exception is a ValidationError (from Pydantic)
    if isinstance(exc, ValidationError):
        error_details = exc.errors()
        if error_details:
            first_error = error_details[0]
            error_message = first_error.get('msg', ERROR_TYPE_VALIDATION)
        else:
            error_message = ERROR_TYPE_VALIDATION
        raise CommonException(error_message) from exc

    # Check if the exception is a ValueError
    if isinstance(exc, ValueError):
        error_message = str(exc) or 'Value error'
        raise CommonException(error_message) from exc

    # Check if the exception is a ServiceOperationException
    if isinstance(exc, ServiceOperationException):
        raise CommonException(exc.message) from exc

    if isinstance(exc, RgbLibError):
        raise CommonException(type(exc).__name__) from exc

    # If no specific type matches, use a default error message
    error_message = getattr(exc, 'message', None) or str(
        exc,
    ) or ERROR_SOMETHING_WENT_WRONG
    raise CommonException(error_message) from exc
