"""Unit tests for check_colorable_available decorator"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from rgb_lib import RgbLibError

from src.data.repository.setting_card_repository import SettingCardRepository
from src.model.setting_model import DefaultFeeRate
from src.utils.decorators.check_colorable_available import check_colorable_available
from src.utils.decorators.check_colorable_available import create_utxos
from src.utils.error_message import ERROR_CREATE_UTXO_FEE_RATE_ISSUE
from src.utils.error_message import ERROR_INSUFFICIENT_FUNDS
from src.utils.error_message import ERROR_MESSAGE_TO_CHANGE_FEE_RATE
from src.utils.handle_exception import CommonException

# Mock the colored_wallet module to avoid "Wallet not initialized" error
colored_wallet = MagicMock()
colored_wallet.wallet = MagicMock()

# Test create_utxos function


@patch('src.utils.decorators.check_colorable_available.colored_wallet', colored_wallet)
@patch('src.utils.cache.Cache.get_cache_session')
@patch.object(SettingCardRepository, 'get_default_fee_rate')
def test_create_utxos_success(mock_get_fee_rate, mock_get_cache):
    """Test successful execution of create_utxos."""
    mock_fee_rate = DefaultFeeRate(fee_rate=1)
    mock_get_fee_rate.return_value = mock_fee_rate
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache
    colored_wallet.wallet.create_utxos.reset_mock()

    create_utxos()

    colored_wallet.wallet.create_utxos.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()


@patch('src.utils.decorators.check_colorable_available.colored_wallet', colored_wallet)
@patch.object(SettingCardRepository, 'get_default_fee_rate')
def test_create_utxos_http_error(mock_get_fee_rate):
    """Test create_utxos with HTTPError."""
    mock_fee_rate = DefaultFeeRate(fee_rate=1)
    mock_get_fee_rate.return_value = mock_fee_rate

    mock_response = MagicMock()
    mock_response.json.return_value = {
        'error': ERROR_CREATE_UTXO_FEE_RATE_ISSUE,
    }
    colored_wallet.wallet.create_utxos.side_effect = HTTPError(
        response=mock_response,
    )

    with pytest.raises(CommonException) as exc_info:
        create_utxos()

    assert str(exc_info.value) == ERROR_MESSAGE_TO_CHANGE_FEE_RATE


@patch('src.utils.decorators.check_colorable_available.colored_wallet', colored_wallet)
@patch.object(SettingCardRepository, 'get_default_fee_rate')
def test_create_utxos_connection_error(mock_get_fee_rate):
    """Test create_utxos with RequestsConnectionError."""
    mock_fee_rate = DefaultFeeRate(fee_rate=1)
    mock_get_fee_rate.return_value = mock_fee_rate

    colored_wallet.wallet.create_utxos.side_effect = RequestsConnectionError()

    with pytest.raises(CommonException) as exc_info:
        create_utxos()

    assert str(exc_info.value) == 'Unable to connect to wallet'


@patch('src.utils.decorators.check_colorable_available.colored_wallet', colored_wallet)
@patch.object(SettingCardRepository, 'get_default_fee_rate')
def test_create_utxos_general_exception(mock_get_fee_rate):
    """Test create_utxos with a general exception."""
    mock_fee_rate = DefaultFeeRate(fee_rate=1)
    mock_get_fee_rate.return_value = mock_fee_rate

    colored_wallet.wallet.create_utxos.side_effect = Exception(
        'Unexpected error',
    )

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
def test_check_colorable_available_decorator_insufficient_slots(mock_create_utxos):
    """Test check_colorable_available decorator with insufficient allocation slots."""
    # First call raises InsufficientAllocationSlots, second call succeeds
    mock_method = MagicMock(
        side_effect=[
            RgbLibError.InsufficientAllocationSlots(),
            'success',
        ],
    )

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    result = decorated_method()

    # Verify create_utxos was called and the method succeeded on retry
    mock_create_utxos.assert_called_once()
    assert result == 'success'


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_insufficient_bitcoins(mock_create_utxos):
    """Test check_colorable_available decorator with insufficient bitcoins."""
    mock_method = MagicMock(
        side_effect=RgbLibError.InsufficientBitcoins(needed=2, available=1),
    )

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    with pytest.raises(CommonException) as exc_info:
        decorated_method()

    assert str(exc_info.value) == ERROR_INSUFFICIENT_FUNDS
    mock_create_utxos.assert_not_called()


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_fallback_exception(mock_create_utxos):
    """Test check_colorable_available decorator when fallback fails."""
    # Method raises InsufficientAllocationSlots
    mock_method = MagicMock(
        side_effect=RgbLibError.InsufficientAllocationSlots(),
    )

    # Fallback create_utxos raises an exception
    mock_create_utxos.side_effect = Exception('Fallback error')

    @check_colorable_available()
    def decorated_method():
        return mock_method()

    with pytest.raises(CommonException) as exc_info:
        decorated_method()

    assert 'Failed to create UTXOs in fallback' in str(exc_info.value)
    mock_create_utxos.assert_called_once()


@patch('src.utils.decorators.check_colorable_available.create_utxos')
def test_check_colorable_available_decorator_unhandled_exception(mock_create_utxos):
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
