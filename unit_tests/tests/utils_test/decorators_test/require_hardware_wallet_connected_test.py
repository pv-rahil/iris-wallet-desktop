# pylint: disable=redefined-outer-name,unused-argument
"""Tests for `require_hardware_wallet_connected` decorator."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.hardware_client_store import hardware_client_store


@pytest.fixture(autouse=True)
def cleanup_store():
    """Clear the shared hardware_client_store before and after each test."""
    hardware_client_store.clear_client()
    yield
    hardware_client_store.clear_client()


def test_decorator_no_hw_wallet_calls_function():
    """When key storage is on-device, decorator should pass-through to function."""
    @require_hardware_wallet_connected()
    def mock(x):
        return x + 1

    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.ON_DEVICE,
    ):
        assert mock(1) == 2


@patch('src.utils.decorators.require_hardware_wallet_connected.enumerate_ledger_devices')
@patch('src.utils.decorators.require_hardware_wallet_connected.create_ledger_client')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network')
@patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type')
def test_decorator_hw_wallet_success(mock_get_kst, mock_get_net, mock_ledger, mock_enum):
    """With HW wallet available, decorated function should execute successfully."""
    mock_get_kst.return_value = KeyStorageType.HARDWARE_WALLET
    mock_get_net.return_value = NetworkEnumModel.TESTNET
    mock_enum.return_value = [{'path': '/dev/hw', 'fingerprint': 'abcd'}]

    @require_hardware_wallet_connected()
    def mock():
        return 'ok'

    assert mock() == 'ok'
    mock_ledger.assert_called_once()


@patch('src.utils.decorators.require_hardware_wallet_connected.enumerate_ledger_devices', return_value=[])
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET)
@patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
@patch('src.utils.logging.logger.error')
def test_decorator_hw_wallet_no_device_raises(mock_log, *_):
    """If no HW device is enumerated, decorator should raise and log error."""
    @require_hardware_wallet_connected()
    def mock():
        return 'ok'

    with pytest.raises(RuntimeError):
        mock()
    assert mock_log.called
