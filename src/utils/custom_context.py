"""Context manager to handle HTTP exceptions uniformly."""
from __future__ import annotations

from contextlib import contextmanager

from pydantic import ValidationError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from requests.exceptions import Timeout

from src.utils.handle_exception import handle_exceptions


@contextmanager
def repository_custom_context():
    """Context manager to handle HTTP exceptions uniformly."""
    try:
        yield
    except (
        HTTPError,
        RequestsConnectionError,
        Timeout,
        RequestException,
        ValidationError,
        ValueError,
    ) as exc:
        handle_exceptions(exc)
