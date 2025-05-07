"""Unit tests for SettingCardRepository"""
# pylint: disable=redefined-outer-name, unused-argument
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.data.repository.setting_card_repository import SettingCardRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultIndexerUrl
from src.model.setting_model import DefaultMinConfirmation
from src.model.setting_model import DefaultProxyEndpoint
from src.utils.constant import FEE_RATE
from src.utils.constant import INDEXER_URL_MAINNET
from src.utils.constant import INDEXER_URL_REGTEST
from src.utils.constant import INDEXER_URL_TESTNET
from src.utils.constant import MIN_CONFIRMATION
from src.utils.constant import PROXY_ENDPOINT_MAINNET
from src.utils.constant import PROXY_ENDPOINT_REGTEST
from src.utils.constant import PROXY_ENDPOINT_TESTNET
from src.utils.constant import SAVED_INDEXER_URL
from src.utils.constant import SAVED_PROXY_ENDPOINT


@pytest.fixture
def mock_local_store():
    """Fixture for mocking local_store"""
    with patch('src.data.repository.setting_card_repository.local_store') as mock:
        yield mock


@pytest.fixture
def mock_handle_exceptions():
    """Fixture for mocking handle_exceptions"""
    with patch('src.data.repository.setting_card_repository.handle_exceptions') as mock:
        mock.return_value = 'Error handled'
        yield mock


def test_set_default_fee_rate_success(mock_local_store):
    """Test setting default fee rate successfully"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = 5

    # Execute
    result = SettingCardRepository.set_default_fee_rate('5')

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with('defaultFeeRate', '5')
    mock_local_store.get_value.assert_called_once_with(
        'defaultFeeRate', value_type=int,
    )


def test_set_default_fee_rate_failure(mock_local_store):
    """Test setting default fee rate failure"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.set_default_fee_rate('5')

    # Assert
    assert result.is_enabled is False
    mock_local_store.set_value.assert_called_once_with('defaultFeeRate', '5')
    mock_local_store.get_value.assert_called_once_with(
        'defaultFeeRate', value_type=int,
    )


def test_set_default_fee_rate_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling when setting default fee rate"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingCardRepository.set_default_fee_rate('5')

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with('defaultFeeRate', '5')
    mock_handle_exceptions.assert_called_once()


def test_get_default_fee_rate_success(mock_local_store):
    """Test getting default fee rate successfully"""
    # Setup
    mock_local_store.get_value.return_value = 5

    # Execute
    result = SettingCardRepository.get_default_fee_rate()

    # Assert
    assert isinstance(result, DefaultFeeRate)
    assert result.fee_rate == 5
    mock_local_store.get_value.assert_called_once_with('defaultFeeRate')


def test_get_default_fee_rate_none(mock_local_store):
    """Test getting default fee rate when none is set"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_fee_rate()

    # Assert
    assert isinstance(result, DefaultFeeRate)
    assert result.fee_rate == FEE_RATE
    mock_local_store.get_value.assert_called_once_with('defaultFeeRate')


def test_get_default_fee_rate_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling when getting default fee rate"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingCardRepository.get_default_fee_rate()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with('defaultFeeRate')
    mock_handle_exceptions.assert_called_once()


def test_set_default_endpoints_success_string(mock_local_store):
    """Test setting default endpoints successfully with string value"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = 'test_url'

    # Execute
    result = SettingCardRepository.set_default_endpoints(
        'test_key', 'test_url',
    )

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with('test_key', 'test_url')
    mock_local_store.get_value.assert_called_once_with('test_key')


def test_set_default_endpoints_success_int(mock_local_store):
    """Test setting default endpoints successfully with int value"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = '5'

    # Execute
    result = SettingCardRepository.set_default_endpoints('test_key', 5)

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with('test_key', 5)
    mock_local_store.get_value.assert_called_once_with('test_key')


def test_set_default_endpoints_failure(mock_local_store, mock_handle_exceptions):
    """Test setting default endpoints failure with type conversion error"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = 'test_url'
    mock_handle_exceptions.side_effect = lambda e: 'Error handled'

    # Execute
    # Simulate an exception in the repository
    mock_local_store.set_value.side_effect = Exception('Test exception')
    result = SettingCardRepository.set_default_endpoints('test_key', 5)

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with('test_key', 5)
    mock_handle_exceptions.assert_called_once()


def test_set_default_endpoints_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling when setting default endpoints"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingCardRepository.set_default_endpoints(
        'test_key', 'test_url',
    )

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with('test_key', 'test_url')
    mock_handle_exceptions.assert_called_once()


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_indexer_url_mainnet(mock_setting_repo, mock_local_store):
    """Test getting default indexer URL for mainnet"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_indexer_url()

    # Assert
    assert isinstance(result, DefaultIndexerUrl)
    assert result.url == INDEXER_URL_MAINNET
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_INDEXER_URL)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_indexer_url_testnet(mock_setting_repo, mock_local_store):
    """Test getting default indexer URL for testnet"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_indexer_url()

    # Assert
    assert isinstance(result, DefaultIndexerUrl)
    assert result.url == INDEXER_URL_TESTNET
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_INDEXER_URL)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_indexer_url_regtest(mock_setting_repo, mock_local_store):
    """Test getting default indexer URL for regtest"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.REGTEST
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_indexer_url()

    # Assert
    assert isinstance(result, DefaultIndexerUrl)
    assert result.url == INDEXER_URL_REGTEST
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_INDEXER_URL)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_indexer_url_custom(mock_setting_repo, mock_local_store):
    """Test getting custom indexer URL"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET
    mock_local_store.get_value.return_value = 'custom_url'

    # Execute
    result = SettingCardRepository.get_default_indexer_url()

    # Assert
    assert isinstance(result, DefaultIndexerUrl)
    assert result.url == 'custom_url'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_INDEXER_URL)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_indexer_url_exception(mock_setting_repo, mock_local_store, mock_handle_exceptions):
    """Test exception handling when getting default indexer URL"""
    # Setup
    mock_setting_repo.get_wallet_network.side_effect = Exception(
        'Test exception',
    )

    # Execute
    result = SettingCardRepository.get_default_indexer_url()

    # Assert
    assert result == 'Error handled'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_handle_exceptions.assert_called_once()
    mock_local_store.get_value.assert_not_called()


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_proxy_endpoint_mainnet(mock_setting_repo, mock_local_store):
    """Test getting default proxy endpoint for mainnet"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_proxy_endpoint()

    # Assert
    assert isinstance(result, DefaultProxyEndpoint)
    assert result.endpoint == PROXY_ENDPOINT_MAINNET
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_PROXY_ENDPOINT)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_proxy_endpoint_testnet(mock_setting_repo, mock_local_store):
    """Test getting default proxy endpoint for testnet"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_proxy_endpoint()

    # Assert
    assert isinstance(result, DefaultProxyEndpoint)
    assert result.endpoint == PROXY_ENDPOINT_TESTNET
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_PROXY_ENDPOINT)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_proxy_endpoint_regtest(mock_setting_repo, mock_local_store):
    """Test getting default proxy endpoint for regtest"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.REGTEST
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_proxy_endpoint()

    # Assert
    assert isinstance(result, DefaultProxyEndpoint)
    assert result.endpoint == PROXY_ENDPOINT_REGTEST
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_PROXY_ENDPOINT)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_proxy_endpoint_custom(mock_setting_repo, mock_local_store):
    """Test getting custom proxy endpoint"""
    # Setup
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET
    mock_local_store.get_value.return_value = 'custom_endpoint'

    # Execute
    result = SettingCardRepository.get_default_proxy_endpoint()

    # Assert
    assert isinstance(result, DefaultProxyEndpoint)
    assert result.endpoint == 'custom_endpoint'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_local_store.get_value.assert_called_once_with(SAVED_PROXY_ENDPOINT)


@patch('src.data.repository.setting_card_repository.SettingRepository')
def test_get_default_proxy_endpoint_exception(mock_setting_repo, mock_local_store, mock_handle_exceptions):
    """Test exception handling when getting default proxy endpoint"""
    # Setup
    mock_setting_repo.get_wallet_network.side_effect = Exception(
        'Test exception',
    )

    # Execute
    result = SettingCardRepository.get_default_proxy_endpoint()

    # Assert
    assert result == 'Error handled'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_handle_exceptions.assert_called_once()
    mock_local_store.get_value.assert_not_called()


def test_set_default_min_confirmation_success(mock_local_store):
    """Test setting default min confirmation successfully"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = 3

    # Execute
    result = SettingCardRepository.set_default_min_confirmation(3)

    # Assert
    assert result.is_enabled is True
    mock_local_store.set_value.assert_called_once_with(
        'defaultMinConfirmation', 3,
    )
    mock_local_store.get_value.assert_called_once_with(
        'defaultMinConfirmation', value_type=int,
    )


def test_set_default_min_confirmation_failure(mock_local_store):
    """Test setting default min confirmation failure"""
    # Setup
    mock_local_store.set_value.return_value = None
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.set_default_min_confirmation(3)

    # Assert
    assert result.is_enabled is False
    mock_local_store.set_value.assert_called_once_with(
        'defaultMinConfirmation', 3,
    )
    mock_local_store.get_value.assert_called_once_with(
        'defaultMinConfirmation', value_type=int,
    )


def test_set_default_min_confirmation_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling when setting default min confirmation"""
    # Setup
    mock_local_store.set_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingCardRepository.set_default_min_confirmation(3)

    # Assert
    assert result == 'Error handled'
    mock_local_store.set_value.assert_called_once_with(
        'defaultMinConfirmation', 3,
    )
    mock_handle_exceptions.assert_called_once()


def test_get_default_min_confirmation_success(mock_local_store):
    """Test getting default min confirmation successfully"""
    # Setup
    mock_local_store.get_value.return_value = 3

    # Execute
    result = SettingCardRepository.get_default_min_confirmation()

    # Assert
    assert isinstance(result, DefaultMinConfirmation)
    assert result.min_confirmation == 3
    mock_local_store.get_value.assert_called_once_with(
        'defaultMinConfirmation',
    )


def test_get_default_min_confirmation_none(mock_local_store):
    """Test getting default min confirmation when none is set"""
    # Setup
    mock_local_store.get_value.return_value = None

    # Execute
    result = SettingCardRepository.get_default_min_confirmation()

    # Assert
    assert isinstance(result, DefaultMinConfirmation)
    assert result.min_confirmation == MIN_CONFIRMATION
    mock_local_store.get_value.assert_called_once_with(
        'defaultMinConfirmation',
    )


def test_get_default_min_confirmation_exception(mock_local_store, mock_handle_exceptions):
    """Test exception handling when getting default min confirmation"""
    # Setup
    mock_local_store.get_value.side_effect = Exception('Test exception')

    # Execute
    result = SettingCardRepository.get_default_min_confirmation()

    # Assert
    assert result == 'Error handled'
    mock_local_store.get_value.assert_called_once_with(
        'defaultMinConfirmation',
    )
    mock_handle_exceptions.assert_called_once()
