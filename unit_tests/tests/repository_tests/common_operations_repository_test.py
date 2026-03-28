"""Unit tests for CommonOperationRepository."""
# pylint: disable=redefined-outer-name, unused-argument,too-many-arguments, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import BitcoinNetwork
from rgb_lib import Keys
from rgb_lib import MultisigKeys
from rgb_lib import RgbLibError
from rgb_lib import SinglesigKeys

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import KeyStorageType
from src.model.common_operation_model import BackupRequestModel
from src.model.common_operation_model import BackupResponseModel
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import RestoreRequestModel
from src.model.common_operation_model import RestoreResponseModel
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletSignatureType
from src.utils.custom_exception import CommonException


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

    with patch('src.data.repository.common_operations_repository.SettingRepository.get_wallet_signature_type') as mock_sign_type:
        mock_sign_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET

        # Build SinglesigKeys
        keys = MagicMock(spec=SinglesigKeys)

        # Execute
        unlock_request = WalletRequestModel(
            data_dir='/test/path',
            bitcoin_network=BitcoinNetwork.TESTNET(),
            max_allocations_per_utxo=5,
            keys=keys,
        )
        result = CommonOperationRepository.unlock(unlock_request)

    # Assert
    assert result == mock_wallet_instance
    mock_wallet.assert_called_once()
    mock_colored_wallet.set_wallet.assert_called_once_with(
        mock_wallet_instance,
    )


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
        result = CommonOperationRepository.sign_and_finalize_psbt(
            'unsigned_psbt',
        )

    assert result == 'final_psbt'
    mock_sign.assert_called_once_with(
        'unsigned_psbt', repo_client, mock_descriptors,
    )
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(
        signed_psbt='signed_psbt',
    )
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
    mock_colored_wallet.wallet.sign_psbt.assert_called_once_with(
        'unsigned_psbt',
    )
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(
        signed_psbt='signed_sw',
    )
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
    mock_colored_wallet.wallet.sign_psbt.assert_called_once_with(
        'unsigned_psbt',
    )
    mock_colored_wallet.wallet.finalize_psbt.assert_called_once_with(
        signed_psbt='signed_sw',
    )
    mock_get_session.assert_called_once()


def test_unlock_multisig(mocker, mock_colored_wallet):
    """Test unlock method for multisig wallet."""
    # Setup
    mock_multisig_wallet_cls = mocker.patch(
        'src.data.repository.common_operations_repository.MultisigWallet',
    )
    mock_multisig_instance = MagicMock()
    mock_multisig_wallet_cls.return_value = mock_multisig_instance

    with patch('src.data.repository.common_operations_repository.SettingRepository.get_wallet_signature_type') as mock_sign_type:
        mock_sign_type.return_value = WalletSignatureType.MULTI_SIG_WALLET

        # Build MultisigKeys (mocked as any key type)
        keys = MagicMock(spec=MultisigKeys)

        # Execute
        unlock_request = WalletRequestModel(
            data_dir='/test/path',
            bitcoin_network=BitcoinNetwork.TESTNET(),
            max_allocations_per_utxo=5,
            keys=keys,
        )
        result = CommonOperationRepository.unlock(unlock_request)

    # Assert
    assert result == mock_multisig_instance
    mock_multisig_wallet_cls.assert_called_once()
    mock_colored_wallet.set_wallet.assert_called_once_with(
        mock_multisig_instance,
    )


@patch('src.data.repository.common_operations_repository.mnemonic_store')
@patch('src.data.repository.common_operations_repository.SettingRepository')
@patch('src.data.repository.common_operations_repository.get_bitcoin_network_from_enum')
@patch('src.data.repository.common_operations_repository.restore_keys')
@patch('src.data.repository.common_operations_repository.Wallet')
@patch('src.data.repository.common_operations_repository.app_paths')
def test_get_temp_singlesig_wallet(
    mock_app_paths,
    mock_wallet_cls,
    mock_restore_keys,
    mock_get_network,
    mock_setting_repo,
    mock_mnemonic_store,
):
    """Test _get_temp_singlesig_wallet creation."""
    # Setup
    mock_mnemonic_store.decrypted_mnemonic = 'test mnemonic'
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_network.return_value = BitcoinNetwork.TESTNET()

    mock_keys = MagicMock()
    mock_keys.account_xpub_vanilla = 'xpub1'
    mock_keys.account_xpub_colored = 'xpub2'
    mock_keys.master_fingerprint = 'mpf'
    mock_restore_keys.return_value = mock_keys

    mock_app_paths.app_path = '/app/path'

    mock_wallet_instance = MagicMock()
    mock_wallet_cls.return_value = mock_wallet_instance

    # Execute
    result = CommonOperationRepository._get_temp_singlesig_wallet()

    # Assert
    assert result == mock_wallet_instance
    mock_wallet_cls.assert_called_once()


@patch('src.data.repository.common_operations_repository.mnemonic_store')
def test_get_temp_singlesig_wallet_no_mnemonic(mock_mnemonic_store):
    """Test _get_temp_singlesig_wallet raises exception if mnemonic not available."""
    # Ensure it evaluates to False
    mock_mnemonic_store.decrypted_mnemonic = ''
    with pytest.raises(CommonException, match='Mnemonic not available for signing'):
        CommonOperationRepository._get_temp_singlesig_wallet()


@patch('src.data.repository.common_operations_repository.colored_wallet')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type')
@patch('src.data.repository.common_operations_repository.mnemonic_store')
@patch('src.data.repository.common_operations_repository.restore_keys')
@patch('src.data.repository.common_operations_repository.Wallet')
def test_sign_psbt_software(mock_wallet_cls, mock_restore_keys, mock_mnemonic_store, mock_get_key_storage_type, mock_get_session, mock_colored_wallet):
    """Test software path for sign_psbt (multisig signing)."""
    mock_get_key_storage_type.return_value = KeyStorageType.ON_DEVICE  # not HARDWARE_WALLET

    # Mocking _get_temp_singlesig_wallet dependencies
    mock_mnemonic_store.decrypted_mnemonic = 'test mnemonic'
    mock_keys = MagicMock()
    mock_keys.account_xpub_vanilla = 'x1'
    mock_keys.account_xpub_colored = 'x2'
    mock_keys.master_fingerprint = 'mp'
    mock_restore_keys.return_value = mock_keys

    mock_temp_wallet = MagicMock()
    mock_temp_wallet.sign_psbt.return_value = 'partially_signed_psbt'
    mock_wallet_cls.return_value = mock_temp_wallet

    svc = MagicMock()
    mock_get_session.return_value = svc

    # Execute
    result = CommonOperationRepository.sign_psbt('unsigned_psbt')

    # Assert
    assert result == 'partially_signed_psbt'
    mock_temp_wallet.sign_psbt.assert_called_once_with('unsigned_psbt')
    svc.mark_psbt_signed.assert_called_once()


@patch('src.data.repository.common_operations_repository.colored_wallet')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.utils.decorators.require_hardware_wallet_connected.enumerate_ledger_devices')
@patch('src.utils.decorators.require_hardware_wallet_connected.create_ledger_client')
@patch('src.utils.decorators.require_hardware_wallet_connected.SettingRepository.get_wallet_network')
@patch('src.data.repository.common_operations_repository.hardware_client_store')
@patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type')
@patch('src.data.repository.common_operations_repository.sign_psbt_with_ledger')
def test_sign_psbt_hardware(
    mock_sign_with_ledger,
    mock_get_key_storage_type,
    repo_hc_store,
    mock_get_network,
    mock_create_client,
    mock_enumerate,
    mock_get_session,
    mock_colored_wallet,
):
    """Test hardware path for sign_psbt."""
    mock_get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET

    # Decorator requirements
    mock_enumerate.return_value = [{'path': '/dev/hw', 'error': None}]
    mock_get_network.return_value = NetworkEnumModel.TESTNET

    repo_hc_store.client = MagicMock()
    mock_sign_with_ledger.return_value = 'signed_hw'

    svc = MagicMock()
    mock_get_session.return_value = svc

    # Execute
    result = CommonOperationRepository.sign_psbt('unsigned_psbt')

    # Assert
    assert result == 'signed_hw'
    mock_sign_with_ledger.assert_called_once()
    svc.mark_psbt_signed.assert_called_once()


@patch('src.utils.custom_context.handle_exceptions')
@patch('src.data.repository.common_operations_repository.mnemonic_store')
def test_get_temp_singlesig_wallet_exception(mock_mnemonic_store, mock_handle_exceptions):
    """Test _get_temp_singlesig_wallet exception path."""
    mock_mnemonic_store.decrypted_mnemonic = 'mnemonic'
    with patch('src.data.repository.common_operations_repository.restore_keys', side_effect=RgbLibError.InvalidIndexer('Test')):
        CommonOperationRepository._get_temp_singlesig_wallet()


@patch('src.utils.custom_context.handle_exceptions')
def test_sign_psbt_exception(mock_handle_exceptions):
    """Test sign_psbt exception path."""
    with patch('src.data.repository.common_operations_repository.SettingRepository.get_key_storage_type', side_effect=RgbLibError.InvalidIndexer('Test')):
        with pytest.raises(RgbLibError.InvalidIndexer):
            CommonOperationRepository.sign_psbt('psbt')
