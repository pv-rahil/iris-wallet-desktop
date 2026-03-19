"""Unit tests for CommonOperationRepository."""
# pylint: disable=redefined-outer-name, unused-argument,too-many-arguments
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork
from rgb_lib import DatabaseType
from rgb_lib import Keys

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import KeyStorageType
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel


@pytest.fixture
def mock_generate_keys():
    """Fixture for mocking generate_keys."""
    with patch('src.data.repository.common_operations_repository.generate_keys') as mock:
        yield mock


@pytest.fixture
def mock_wallet():
    """Fixture for mocking Wallet."""
    with patch('src.data.repository.common_operations_repository.Wallet') as mock:
        yield mock


@pytest.fixture
def mock_colored_wallet():
    """Fixture for mocking colored_wallet."""
    with patch('src.data.repository.common_operations_repository.colored_wallet') as mock:
        yield mock


def test_init(mock_generate_keys):
    """Test init method."""
    # Setup
    mock_keys = MagicMock(spec=Keys)
    mock_generate_keys.return_value = mock_keys

    # Execute
    init_request = InitRequestModel(
        password='test_password', network=BitcoinNetwork.TESTNET(),
    )
    result = CommonOperationRepository.init(init_request)

    # Assert
    assert result == mock_keys
    mock_generate_keys.assert_called_once_with(BitcoinNetwork.TESTNET())


def test_unlock(mock_wallet, mock_colored_wallet):
    """Test unlock method."""
    # Setup
    mock_wallet_instance = MagicMock()
    mock_wallet.return_value = mock_wallet_instance

    # Execute
    unlock_request = WalletRequestModel(
        data_dir='/test/path',
        bitcoin_network=BitcoinNetwork.TESTNET(),
        account_xpub_colored='test_pubkey_colored',
        account_xpub_vanilla='test_pubkey_vanilla',
        mnemonic='test mnemonic',
        master_fingerprint='test_master_fingerprint',
        max_allocations_per_utxo=5,
        vanilla_keychain=1,
    )
    result = CommonOperationRepository.unlock(unlock_request)

    # Assert
    assert result == mock_wallet_instance
    mock_wallet.assert_called_once()
    mock_colored_wallet.set_wallet.assert_called_once_with(mock_wallet_instance)


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


def test_restore(mocker):
    """Test restore method."""
    # Setup
    mock_restore_backup = mocker.patch(
        'src.data.repository.common_operations_repository.restore_backup',
    )

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
    mock_restore_backup.assert_called_once_with(
        backup_path='/test/backup/path',
        password='test_password',
        data_dir='/test/data/dir',
    )


def test_restore_keys(mocker):
    """Test restore_keys method."""
    # Setup
    mock_restore_keys = mocker.patch(
        'src.data.repository.common_operations_repository.restore_keys',
    )
    mock_keys = MagicMock()
    mock_restore_keys.return_value = mock_keys

    # Test data
    bitcoin_network = BitcoinNetwork.TESTNET()
    mnemonic = 'test mnemonic phrase'

    # Execute
    result = CommonOperationRepository.restore_keys(bitcoin_network, mnemonic)

    # Assert
    mock_restore_keys.assert_called_once_with(
        bitcoin_network, mnemonic,
    )
    assert result == mock_keys


@patch('src.data.repository.common_operations_repository.colored_wallet')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.utils.decorators.require_hardware_wallet_connected.SettingRepository.get_wallet_network')
@patch('src.utils.decorators.require_hardware_wallet_connected.enumerate_ledger_devices')
@patch('src.utils.decorators.require_hardware_wallet_connected.create_ledger_client')
@patch('src.utils.decorators.require_hardware_wallet_connected.hardware_client_store')
@patch('src.data.repository.common_operations_repository.hardware_client_store')
@patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type')
def test_sign_and_finalize_psbt_hardware(
    mock_get_key_storage_type,
    repo_hc_store,
    deco_hc_store,
    mock_create_client,
    mock_enumerate,
    mock_get_wallet_network,
    mock_get_session,
    mock_colored_wallet,
):
    """Hardware wallet path: sign_psbt_with_ledger is called, result is finalized."""
    # Setup hardware flag
    mock_get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET

    # The descriptor that the wallet returns
    mock_descriptors = MagicMock()
    mock_descriptors.vanilla = 'tr(xpub_key/**)'
    mock_colored_wallet.wallet.get_descriptors.return_value = mock_descriptors

    # Decorator: return one healthy device
    mock_enumerate.return_value = [{
        'path': '/dev/hw', 'type': 'hid', 'fingerprint': 'aabbccdd', 'model': 'Bitcoin', 'error': None,
    }]
    mock_get_wallet_network.return_value = NetworkEnumModel.TESTNET
    ledger_client = MagicMock()
    mock_create_client.return_value = ledger_client

    # Repository hardware client side
    repo_client = MagicMock()
    repo_hc_store.client = repo_client

    # sign_psbt_with_ledger result
    mock_colored_wallet.wallet.finalize_psbt.return_value = 'final_psbt'

    svc = MagicMock()
    mock_get_session.return_value = svc

    # Patch sign_psbt_with_ledger to skip actual device interaction
    with patch('src.data.repository.common_operations_repository.sign_psbt_with_ledger', return_value='signed_psbt') as mock_sign:
        result = CommonOperationRepository.sign_and_finalize_psbt('unsigned_psbt')

    assert result == 'final_psbt'
    mock_sign.assert_called_once_with(
        'unsigned_psbt', repo_client, mock_descriptors.vanilla,
    )
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(signed_psbt='signed_psbt')
    svc.mark_psbt_signed.assert_called_once_with('unsigned_psbt', 'final_psbt')


@patch('src.data.repository.common_operations_repository.colored_wallet')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type')
def test_sign_and_finalize_psbt_software(mock_get_key_storage_type, mock_get_session, mock_colored_wallet):
    """Software path: uses wallet.sign_psbt and finalize_psbt; marks signed."""
    mock_get_key_storage_type.return_value = MagicMock()  # not HARDWARE_WALLET
    mock_colored_wallet.wallet.sign_psbt.return_value = 'signed_sw'
    mock_colored_wallet.wallet.finalize_psbt.return_value = 'final_psbt'
    svc = MagicMock()
    mock_get_session.return_value = svc

    result = CommonOperationRepository.sign_and_finalize_psbt('unsigned_psbt')

    assert result == 'final_psbt'
    mock_colored_wallet.wallet.sign_psbt.assert_called_once_with('unsigned_psbt')
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(signed_psbt='signed_sw')
    svc.mark_psbt_signed.assert_called_once_with('unsigned_psbt', 'final_psbt')


@patch('src.data.repository.common_operations_repository.colored_wallet')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type')
def test_sign_and_finalize_psbt_no_session(mock_get_key_storage_type, mock_get_session, mock_colored_wallet):
    """No session: ensure no mark call and still returns finalized_psbt (software path)."""
    mock_get_key_storage_type.return_value = MagicMock()  # not HARDWARE_WALLET
    mock_colored_wallet.wallet.sign_psbt.return_value = 'signed_sw'
    mock_colored_wallet.wallet.finalize_psbt.return_value = 'final_psbt'
    mock_get_session.return_value = None

    result = CommonOperationRepository.sign_and_finalize_psbt('unsigned_psbt')

    assert result == 'final_psbt'
    mock_colored_wallet.wallet.sign_psbt.assert_called_once_with('unsigned_psbt')
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(signed_psbt='signed_sw')
    mock_get_session.assert_called_once()
