"""Unit tests for check_colorable_available decprator"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

from src.utils.decorators.check_colorable_available import check_colorable_available
from src.utils.decorators.check_colorable_available import create_utxos
from src.utils.error_message import ERROR_CREATE_UTXO_FEE_RATE_ISSUE
from src.utils.error_message import ERROR_MESSAGE_TO_CHANGE_FEE_RATE
from src.utils.handle_exception import CommonException
from src.utils.request import Request

# Test create_utxos function


@patch.object(Request, 'post')
@patch('src.utils.cache.Cache.get_cache_session')
def test_create_utxos_success(mock_get_cache, mock_post):
    """Test successful execution of create_utxos."""
    mock_post.return_value = MagicMock(status_code=200)
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache

    create_utxos()

    mock_post.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()


@patch.object(Request, 'post')
def test_create_utxos_http_error(mock_post):
    """Test create_utxos with HTTPError."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        'error': ERROR_CREATE_UTXO_FEE_RATE_ISSUE,
    }
    mock_post.side_effect = HTTPError(response=mock_response)

    with pytest.raises(CommonException) as exc_info:
        create_utxos()

    assert str(exc_info.value) == ERROR_MESSAGE_TO_CHANGE_FEE_RATE


@patch.object(Request, 'post')
def test_create_utxos_connection_error(mock_post):
    """Test create_utxos with RequestsConnectionError."""
    mock_post.side_effect = RequestsConnectionError()

    with pytest.raises(CommonException) as exc_info:
        create_utxos()

    assert str(exc_info.value) == 'Unable to connect to node'


@patch.object(Request, 'post')
def test_create_utxos_general_exception(mock_post):
    """Test create_utxos with a general exception."""
    mock_post.side_effect = Exception('Unexpected error')

    with pytest.raises(CommonException) as exc_info:
        create_utxos()

    assert 'Decorator(check_colorable_available): Error while calling create utxos API' in str(
        exc_info.value,
    )

# Test check_colorable_available decorator


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_success(mock_create_utxos):
    """Test check_colorable_available decorator when UTXOs are available."""
    mock_method = MagicMock(return_value='success')

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    result = decorated_method()
    assert result == 'success'
    mock_create_utxos.assert_not_called()


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_create_utxos(mock_create_utxos):
    """Test check_colorable_available decorator fallback to create_utxos."""
    # Create CommonException with name attribute
    exc = CommonException('Error message', {'name': 'NoAvailableUtxos'})

    # Mock method that raises the exception twice
    mock_method = MagicMock(side_effect=[exc, exc])

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    with pytest.raises(CommonException) as exc_info:
        decorated_method()

    # Verify create_utxos was called
    mock_create_utxos.assert_called_once()

    # Verify the exception has the correct name
    assert exc_info.value.name == 'NoAvailableUtxos'


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_exception(mock_create_utxos):
    """Test check_colorable_available decorator with unhandled exception."""
    mock_method = MagicMock(side_effect=Exception('Unhandled error'))

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    with pytest.raises(CommonException) as exc_info:
        decorated_method()

    assert 'Decorator(check_colorable_available): Unhandled error' in str(
        exc_info.value,
    )
    mock_create_utxos.assert_not_called()
