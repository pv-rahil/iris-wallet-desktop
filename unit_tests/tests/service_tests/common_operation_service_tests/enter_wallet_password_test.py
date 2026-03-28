"""Unit tests for enter wallet password method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access, unused-import, too-many-arguments
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA


@pytest.fixture(autouse=True)
def reset_network():
    """Reset network to mainnet before each test"""
    SettingRepository.get_wallet_network()
    yield
    SettingRepository.get_wallet_network()


@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
@patch('src.data.service.common_operation_service.local_store')
@patch('src.data.service.common_operation_service.mnemonic_store')
@patch('src.data.service.common_operation_service.CommonOperationRepository.unlock')
@patch('src.data.service.common_operation_service.app_paths')
@patch('src.data.service.common_operation_service.build_keys_from_data')
@patch('src.data.service.common_operation_service.WalletRequestModel')
def test_enter_wallet_password_success(
    mock_wallet_request, mock_build_keys, mock_app_paths, mock_unlock_repo, mock_mnemonic_store,
    mock_local_store, mock_get_network,
):
    """Test successful wallet password entry"""
    # Setup mocks
    mock_app_paths.app_path = '/test/path'
    mock_app_paths.mnemonic_file_path = '/test/mnemonic/path'
    mock_get_network.return_value = BitcoinNetwork.TESTNET()

    mock_local_store.get_value.side_effect = [
        'test_xpub_vanilla', 'test_xpub_colored', 'ff',
    ]
    mock_mnemonic_store.decrypt.return_value = 'test mnemonic'
    mock_keys = MagicMock()
    mock_build_keys.return_value = mock_keys

    mock_wallet = MagicMock()
    mock_unlock_repo.return_value = mock_wallet

    # Execute
    result = CommonOperationService.enter_wallet_password(
        password='Random@123',
    )

    # Assert
    assert result == mock_wallet
    mock_get_network.assert_called()
    mock_local_store.get_value.assert_any_call(ACCOUNT_XPUB_VANILLA)
    mock_local_store.get_value.assert_any_call(ACCOUNT_XPUB_COLORED)
    mock_mnemonic_store.decrypt.assert_called_once_with(
        password='Random@123', path='/test/mnemonic/path',
    )
    mock_build_keys.assert_called_once_with(
        account_xpub_vanilla='test_xpub_vanilla',
        account_xpub_colored='test_xpub_colored',
        master_fingerprint='ff',
        mnemonic='test mnemonic',
    )
    mock_wallet_request.assert_called_once_with(
        data_dir='/test/path',
        bitcoin_network=BitcoinNetwork.TESTNET(),
        keys=mock_keys,
    )
    mock_unlock_repo.assert_called_once_with(mock_wallet_request.return_value)


@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
@patch('src.data.service.common_operation_service.handle_exceptions')
def test_enter_wallet_password_exception(mock_handle_exceptions, mock_get_network):
    """Test exception handling in wallet password entry"""
    # Setup mocks
    mock_get_network.side_effect = Exception('Test exception')
    mock_handle_exceptions.return_value = 'Error response'

    # Execute
    result = CommonOperationService.enter_wallet_password(
        password='Random@123',
    )

    # Assert
    assert result == 'Error response'
    mock_get_network.assert_called_once()
    mock_handle_exceptions.assert_called_once()


@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
@patch('src.data.service.common_operation_service.local_store')
@patch('src.data.service.common_operation_service.CommonOperationRepository.unlock')
@patch('src.data.service.common_operation_service.app_paths')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.build_keys_from_data')
@patch('src.data.service.common_operation_service.WalletRequestModel')
def test_enter_wallet_password_watch_only_hardware_path(
    mock_wallet_request, mock_build_keys, mock_setting_repo, mock_app_paths, mock_unlock_repo, mock_local_store, mock_get_network,
):
    """Covers branch where is_watch_only or is_hardware_only -> decrypted_mnemonic is None"""
    mock_app_paths.app_path = '/test/path'
    mock_get_network.return_value = BitcoinNetwork.TESTNET()
    mock_setting_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
    mock_setting_repo.get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET

    mock_local_store.get_value.side_effect = [
        'xv', 'xc', 'ff',
    ]

    resp = CommonOperationService.enter_wallet_password('pw')
    assert resp == mock_unlock_repo.return_value
    # Ensure unlock called with mnemonic None
    kwargs = mock_build_keys.call_args.kwargs
    assert kwargs.get('mnemonic') is None
