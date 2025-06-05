"""Unit tests for enter wallet password method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access, unused-import
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import WalletRequestModel
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_password


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
def test_enter_wallet_password_success(
    mock_app_paths, mock_unlock_repo, mock_mnemonic_store,
    mock_local_store, mock_get_network,
):
    """Test successful wallet password entry"""
    # Setup mocks
    mock_app_paths.app_path = '/test/path'
    mock_app_paths.mnemonic_file_path = '/test/mnemonic/path'
    mock_get_network.return_value = 1  # Testnet

    mock_local_store.get_value.side_effect = [
        'test_xpub_vanilla', 'test_xpub_colored',
    ]
    mock_mnemonic_store.decrypt.return_value = 'test mnemonic'

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
    mock_unlock_repo.assert_called_once_with(
        WalletRequestModel(
            data_dir='/test/path',
            bitcoin_network=1,
            account_xpub_vanilla='test_xpub_vanilla',
            account_xpub_colored='test_xpub_colored',
            mnemonic='test mnemonic',
        ),
    )


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
