# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-few-public-methods
"""Unit tests for the handle_exception module."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from pydantic import BaseModel
from pydantic import ValidationError

from src.utils.custom_exception import CommonException
from src.utils.custom_exception import ServiceOperationException
from src.utils.error_message import ERROR_CONNECTION_FAILED_WITH_LN
from src.utils.error_message import ERROR_REQUEST_TIMEOUT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_TYPE_VALIDATION
from src.utils.error_message import ERROR_UNSPECIFIED_SERVER_ERROR
from src.utils.handle_exception import handle_exceptions


def test_http_error_with_json_response():
    """Test handling of HTTPError with JSON response."""
    mock_response = MagicMock()
    mock_response.text = '{"error": "Custom error message"}'
    mock_response.json.return_value = {'error': 'Custom error message'}
    mock_response.status_code = 400
    mock_response.url = 'http://test.url'

    exc = requests.exceptions.HTTPError(response=mock_response)

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == 'Custom error message'


def test_http_error_500_with_error_report():
    """Test handling of HTTPError with 500 status code."""
    mock_response = MagicMock()
    mock_response.text = '{"error": "Server error"}'
    mock_response.json.return_value = {'error': 'Server error'}
    mock_response.status_code = 500
    mock_response.url = 'http://test.url'

    exc = requests.exceptions.HTTPError(response=mock_response)

    with patch('src.utils.handle_exception.PageNavigationEventManager') as mock_manager:
        mock_instance = MagicMock()
        mock_manager.get_instance.return_value = mock_instance
        mock_instance.error_report_signal = MagicMock()

        with pytest.raises(CommonException) as exc_info:
            handle_exceptions(exc)

        # Verify error_report_signal.emit() was called with no arguments
        mock_instance.error_report_signal.emit.assert_called_once_with()
        assert str(exc_info.value) == 'Server error'


def test_http_error_without_response():
    """Test handling of HTTPError without response text."""
    exc = requests.exceptions.HTTPError()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == ERROR_UNSPECIFIED_SERVER_ERROR


def test_connection_error():
    """Test handling of RequestsConnectionError."""
    exc = requests.exceptions.ConnectionError()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == ERROR_CONNECTION_FAILED_WITH_LN


def test_timeout_error():
    """Test handling of Timeout."""
    exc = requests.exceptions.Timeout()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == ERROR_REQUEST_TIMEOUT


def test_general_request_exception():
    """Test handling of general RequestException."""
    exc = requests.exceptions.RequestException()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == ERROR_UNSPECIFIED_SERVER_ERROR


def test_validation_error_with_details():
    """Test handling of ValidationError with error details."""

    class TestModel(BaseModel):
        """class for test model"""
        field_name: str

    try:
        TestModel(field_name=None)  # This will raise ValidationError
    except ValidationError as exc:
        with pytest.raises(CommonException) as exc_info:
            handle_exceptions(exc)

        assert str(exc_info.value) == 'Input should be a valid string'


def test_validation_error_without_details():
    """Test handling of ValidationError without error details."""
    class TestModel(BaseModel):
        """class for test model"""
        field_name: str = ''

    try:
        # This will raise ValidationError with no details
        TestModel.parse_obj({})
    except ValidationError as exc:
        with pytest.raises(CommonException) as exc_info:
            handle_exceptions(exc)

        assert str(exc_info.value) == ERROR_TYPE_VALIDATION


def test_value_error_with_message():
    """Test handling of ValueError with custom message."""
    exc = ValueError('Custom value error')

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == 'Custom value error'


def test_value_error_without_message():
    """Test handling of ValueError without message."""
    exc = ValueError()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == 'Value error'


def test_service_operation_exception():
    """Test handling of ServiceOperationException."""
    exc = ServiceOperationException('Service error')

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == 'Service error'


def test_generic_exception_with_message():
    """Test handling of generic Exception with message."""
    class CustomException(Exception):
        """class for custom exception"""

        def __init__(self, message):
            super().__init__(message)
            self.message = message

    exc = CustomException('Generic error')

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == 'Generic error'


def test_generic_exception_without_message():
    """Test handling of generic Exception without message."""
    class CustomException(Exception):
        """class for custom exception"""

        def __init__(self):
            super().__init__()
            self.message = ''

    exc = CustomException()

    with pytest.raises(CommonException) as exc_info:
        handle_exceptions(exc)

    assert str(exc_info.value) == ERROR_SOMETHING_WENT_WRONG


@patch('src.utils.handle_exception.logger')
def test_logging_of_exceptions(mock_logger):
    """Test that exceptions are properly logged."""
    exc = ValueError('Test error')

    with pytest.raises(CommonException):
        handle_exceptions(exc)

    mock_logger.error.assert_called_once_with(
        'Exception occurred: %s, Message: %s',
        'ValueError',
        'Test error',
    )
