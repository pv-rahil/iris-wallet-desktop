"""Unit tests for initialize wallet method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, unused-import
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork
from rgb_lib import Keys
from rgb_lib import RgbLibError

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel
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
    mock_get_network.return_value = BitcoinNetwork.TESTNET.value
    mock_app_paths.app_path = '/test/path'

    mock_keys = MagicMock()
    mock_keys.account_xpub_vanilla = 'test_xpub_vanilla'
    mock_keys.account_xpub_colored = 'test_xpub_colored'
    mock_keys.mnemonic = 'skill lamp please gown put season degree collect decline account monitor insane'
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
            network=BitcoinNetwork.TESTNET.value,
        ),
    )
    mock_repo.unlock.assert_called_once_with(
        WalletRequestModel(
            data_dir='/test/path',
            bitcoin_network=BitcoinNetwork.TESTNET.value,
            account_xpub_vanilla='test_xpub_vanilla',
            account_xpub_colored='test_xpub_colored',
            mnemonic='skill lamp please gown put season degree collect decline account monitor insane',
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
    mock_get_network.assert_not_called()


@patch('src.data.service.common_operation_service.handle_exceptions')
@patch('src.data.service.common_operation_service.CommonOperationRepository')
@patch('src.data.service.common_operation_service.SettingRepository')
@patch('src.data.service.common_operation_service.get_bitcoin_network_from_enum')
def test_initialize_wallet_rgb_lib_error(mock_get_network, mock_setting_repo, mock_repo, mock_handle_exceptions):
    """Test RgbLibError handling in initialize wallet"""
    # Setup mocks
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET.value
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
