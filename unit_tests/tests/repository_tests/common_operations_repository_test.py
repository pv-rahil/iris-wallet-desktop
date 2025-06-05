"""Unit tests for CommonOperationRepository."""
# pylint: disable=redefined-outer-name, unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork
from rgb_lib import DatabaseType
from rgb_lib import Keys

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import WalletRequestModel


@pytest.fixture
def mock_rgb_lib():
    """Fixture for mocking rgb_lib."""
    with patch('src.data.repository.common_operations_repository.rgb_lib') as mock:
        yield mock


@pytest.fixture
def mock_colored_wallet():
    """Fixture for mocking colored_wallet."""
    with patch('src.data.repository.common_operations_repository.colored_wallet') as mock:
        yield mock


def test_init(mock_rgb_lib):
    """Test init method."""
    # Setup
    mock_keys = MagicMock(spec=Keys)
    mock_rgb_lib.generate_keys.return_value = mock_keys

    # Execute
    init_request = InitRequestModel(
        password='test_password', network=BitcoinNetwork.TESTNET,
    )
    result = CommonOperationRepository.init(init_request)

    # Assert
    assert result == mock_keys
    mock_rgb_lib.generate_keys.assert_called_once_with(BitcoinNetwork.TESTNET)


def test_unlock(mock_rgb_lib, mock_colored_wallet):
    """Test unlock method."""
    # Setup
    mock_wallet = MagicMock()
    mock_rgb_lib.Wallet.return_value = mock_wallet

    # Execute
    unlock_request = WalletRequestModel(
        data_dir='/test/path',
        bitcoin_network=1,
        account_xpub_colored='test_pubkey_colored',
        account_xpub_vanilla='test_pubkey_vanilla',
        mnemonic='test mnemonic',
        max_allocations_per_utxo=5,
        vanilla_keychain=1,
    )
    result = CommonOperationRepository.unlock(unlock_request)

    # Assert
    assert result == mock_wallet
    mock_rgb_lib.Wallet.assert_called_once()
    mock_colored_wallet.set_wallet.assert_called_once_with(mock_wallet)

    # Verify WalletData was created with correct parameters
    wallet_data_call = mock_rgb_lib.Wallet.call_args[0][0]
    assert isinstance(wallet_data_call, MagicMock)  # It's a mock of WalletData
    assert mock_rgb_lib.WalletData.call_args.kwargs['data_dir'] == '/test/path'
    assert mock_rgb_lib.WalletData.call_args.kwargs['bitcoin_network'] == BitcoinNetwork.TESTNET
    assert mock_rgb_lib.WalletData.call_args.kwargs['database_type'] == DatabaseType.SQLITE
    assert mock_rgb_lib.WalletData.call_args.kwargs['max_allocations_per_utxo'] == 5
    assert mock_rgb_lib.WalletData.call_args.kwargs['account_xpub_vanilla'] == 'test_pubkey_vanilla'
    assert mock_rgb_lib.WalletData.call_args.kwargs['account_xpub_colored'] == 'test_pubkey_colored'
    assert mock_rgb_lib.WalletData.call_args.kwargs['mnemonic'] == 'test mnemonic'
    assert mock_rgb_lib.WalletData.call_args.kwargs['vanilla_keychain'] == 1


def test_backup(mock_colored_wallet):
    """Test backup method."""
    # Setup
    mock_wallet = MagicMock()
    mock_colored_wallet.wallet = mock_wallet

    # Execute
    backup_request = BackupRequestModel(
        backup_path='/test/backup/path',
        password='test_password',
    )
    result = CommonOperationRepository.backup(backup_request)

    # Assert
    assert isinstance(result, BackupResponseModel)
    assert result.status is True
    mock_wallet.backup.assert_called_once_with(
        backup_path='/test/backup/path',
        password='test_password',
    )


def test_restore(mock_rgb_lib):
    """Test restore method."""
    # Setup
    mock_rgb_lib.restore_backup = MagicMock()

    # Execute
    restore_request = RestoreRequestModel(
        backup_path='/test/backup/path',
        password='test_password',
        data_dir='/test/data/dir',
    )
    result = CommonOperationRepository.restore(restore_request)

    # Assert
    assert isinstance(result, RestoreResponseModel)
    assert result.status is True
    mock_rgb_lib.restore_backup.assert_called_once_with(
        backup_path='/test/backup/path',
        password='test_password',
        data_dir='/test/data/dir',
    )


def test_restore_keys(mock_rgb_lib):
    """Test restore_keys method."""
    # Setup
    mock_rgb_lib.restore_keys = MagicMock()
    mock_rgb_lib.restore_keys.return_value = MagicMock()  # Mock Keys object

    # Test data
    bitcoin_network = BitcoinNetwork.TESTNET
    mnemonic = 'test mnemonic phrase'

    # Execute
    result = CommonOperationRepository.restore_keys(bitcoin_network, mnemonic)

    # Assert
    mock_rgb_lib.restore_keys.assert_called_once_with(
        bitcoin_network, mnemonic,
    )
    assert result == mock_rgb_lib.restore_keys.return_value
