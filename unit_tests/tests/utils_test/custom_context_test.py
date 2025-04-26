# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-few-public-methods, unnecessary-pass
"""Unit tests for custom context manager."""
from __future__ import annotations

import pytest
from pydantic import BaseModel
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from requests.exceptions import Timeout

from src.utils.custom_context import repository_custom_context


class TestModel(BaseModel):
    """Test model for ValidationError."""
    value: int


@pytest.mark.parametrize(
    'exception_class,test_data', [
        (HTTPError, 'Test error'),
        (RequestsConnectionError, 'Test error'),
        (Timeout, 'Test error'),
        (RequestException, 'Test error'),
        (ValueError, 'Test error'),
    ],
)
def test_repository_custom_context_handles_exceptions(exception_class, test_data, mocker):
    """Test that context manager handles all expected exceptions."""
    mock_handle_exceptions = mocker.patch(
        'src.utils.custom_context.handle_exceptions',
    )

    with repository_custom_context():
        raise exception_class(test_data)

    mock_handle_exceptions.assert_called_once()


def test_repository_custom_context_handles_validation_error(mocker):
    """Test that context manager handles ValidationError."""
    mock_handle_exceptions = mocker.patch(
        'src.utils.custom_context.handle_exceptions',
    )

    with repository_custom_context():
        TestModel(value='not an integer')  # This will raise ValidationError

    mock_handle_exceptions.assert_called_once()


def test_repository_custom_context_passes_no_exception():
    """Test that context manager passes when no exception occurs."""
    test_value = 'test'

    with repository_custom_context():
        result = test_value

    assert result == test_value


def test_repository_custom_context_reraises_unexpected_exception():
    """Test that context manager reraises unexpected exceptions."""
    class UnexpectedException(Exception):
        """Custom exception for testing."""
        pass  # pylint disabled = unnecessary-pass

    with pytest.raises(UnexpectedException):
        with repository_custom_context():
            raise UnexpectedException('Unexpected error')
