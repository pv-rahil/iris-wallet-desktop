"""Unit tests for initialize wallet method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, too-many-arguments
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from rgb_lib import BitcoinNetwork
from rgb_lib import RgbLibError

from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.utils.custom_exception import CommonException


@patch('src.data.service.common_operation_service.app_paths')
@patch('src.data.service.common_operation_service.CommonOperationRepository')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
@patch('src.data.service.common_operation_service.colored_wallet')
@patch('src.data.service.common_operation_service.mnemonic_store')
def test_initialize_wallet(
    mock_mnemonic_store, mock_colored_wallet, mock_get_network, mock_setting_repo,
    mock_repo, mock_app_paths,
):
    """Test successful wallet initialization"""
    # Setup mocks
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET()
    mock_app_paths.app_path = '/test/path'

    mock_keys = MagicMock()
    mock_keys.account_xpub_vanilla = 'test_xpub_vanilla'
    mock_keys.account_xpub_colored = 'test_xpub_colored'
    mock_keys.mnemonic = 'skill lamp please gown put season degree collect decline account monitor insane'
    mock_keys.master_fingerprint = 'ff'
    mock_repo.init.return_value = mock_keys

    mock_wallet = MagicMock()
    mock_repo.unlock.return_value = mock_wallet

    # Execute
    result = CommonOperationService.initialize_wallet('Random@123')

    # Assert
    assert result == (mock_keys, 'Random@123')
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_get_network.assert_called_once_with(
        mock_setting_repo.get_wallet_network.return_value,
    )
    mock_repo.init.assert_called_once_with(
        InitRequestModel(
            password='Random@123',
            network=BitcoinNetwork.TESTNET(),
        ),
    )
    mock_repo.unlock.assert_called_once_with(
        WalletRequestModel(
            data_dir='/test/path',
            bitcoin_network=BitcoinNetwork.TESTNET(),
            account_xpub_vanilla='test_xpub_vanilla',
            account_xpub_colored='test_xpub_colored',
            mnemonic='skill lamp please gown put season degree collect decline account monitor insane',
            master_fingerprint='ff',
        ),
    )
    mock_colored_wallet.set_wallet.assert_called_once_with(mock_wallet)
    mock_mnemonic_store.decrypted_mnemonic = mock_keys.mnemonic


@patch('src.data.service.common_operation_service.handle_exceptions')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
def test_initialize_wallet_exception(mock_get_network, mock_setting_repo, mock_handle_exceptions):
    """Test exception handling in initialize wallet"""
    # Setup mocks
    mock_setting_repo.get_wallet_network.side_effect = CommonException(
        'Test exception',
    )
    mock_handle_exceptions.return_value = 'Error response'

    # Execute
    result = CommonOperationService.initialize_wallet('Random@123')

    # Assert
    assert result == 'Error response'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_handle_exceptions.assert_called_once()


@patch('src.data.service.common_operation_service.app_paths')
@patch('src.data.service.common_operation_service.CommonOperationRepository')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.local_store')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
@patch('src.data.service.common_operation_service.colored_wallet')
@patch('src.data.service.common_operation_service.Keys')
def test_initialize_wallet_watch_only_or_hardware_success(
    mock_keys, mock_colored_wallet, mock_get_network, mock_local_store, mock_setting_repo, mock_repo, mock_app_paths,
):
    """Covers watch-only/hardware branch using stored xpubs/fingerprint"""
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_setting_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
    mock_setting_repo.get_key_storage_type.return_value = KeyStorageType.ON_DEVICE
    mock_get_network.return_value = BitcoinNetwork.TESTNET()
    mock_app_paths.app_path = '/test/path'

    # Any non-None values are fine for branch coverage
    mock_local_store.get_value.return_value = 'val'

    result = CommonOperationService.initialize_wallet('pw')
    assert result[1] == 'pw'
    mock_keys.assert_called_once()
    mock_repo.unlock.assert_called_once()
    mock_colored_wallet.set_wallet.assert_called_once()


@patch('src.data.service.common_operation_service.handle_exceptions')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.local_store')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
def test_initialize_wallet_watch_only_missing_values_calls_handler(
    mock_get_network, mock_local_store, mock_setting_repo, mock_handle_exceptions,
):
    """Missing xpubs/fingerprint should call handle_exceptions"""
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_setting_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
    mock_setting_repo.get_key_storage_type.return_value = KeyStorageType.ON_DEVICE
    mock_get_network.return_value = BitcoinNetwork.TESTNET()
    mock_local_store.get_value.return_value = None
    mock_handle_exceptions.return_value = ('handled', 'pwd')

    result = CommonOperationService.initialize_wallet('pw')
    assert result == ('handled', 'pwd')
    mock_handle_exceptions.assert_called()


@patch('src.data.service.common_operation_service.handle_exceptions')
@patch('src.data.service.common_operation_service.CommonOperationRepository')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
def test_initialize_wallet_rgb_lib_error(mock_get_network, mock_setting_repo, mock_repo, mock_handle_exceptions):
    """Test RgbLibError handling in initialize wallet"""
    # Setup mocks
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET()
    mock_repo.init.side_effect = RgbLibError('RGB Lib error')
    mock_handle_exceptions.return_value = 'RGB Lib error response'

    # Execute
    result = CommonOperationService.initialize_wallet('Random@123')

    # Assert
    assert result == 'RGB Lib error response'
    mock_setting_repo.get_wallet_network.assert_called_once()
    mock_get_network.assert_called_once()
    mock_repo.init.assert_called_once()
    mock_handle_exceptions.assert_called_once()
