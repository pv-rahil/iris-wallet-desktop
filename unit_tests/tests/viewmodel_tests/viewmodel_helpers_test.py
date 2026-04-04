"""Unit tests for viewmodel_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access, too-few-public-methods, too-many-arguments
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.utils.ledger_hw_client import get_ledger_error_message
from src.viewmodels.viewmodel_helpers import extract_psbt_and_operation_idx
from src.viewmodels.viewmodel_helpers import extract_psbt_result
from src.viewmodels.viewmodel_helpers import handle_hardware_wallet_signing
from src.viewmodels.viewmodel_helpers import handle_viewmodel_error
from src.viewmodels.viewmodel_helpers import on_success_multisig_post_base
from src.viewmodels.viewmodel_helpers import process_psbt_result
from src.viewmodels.viewmodel_helpers import restore_multisig_config_from_file


class MockViewModel(QObject):
    """Mock viewmodel for testing."""

    hw_dialog_update = Signal(str, PsbtStatus)
    unsigned_psbt = Signal(str)
    test_button_clicked = Signal(bool)

    def __init__(self):
        """Initialize mock viewmodel."""
        super().__init__()
        self.operation_idx = None
        self.run_in_thread_calls = []

    def run_in_thread(self, func, kwargs):
        """Track run_in_thread calls."""
        self.run_in_thread_calls.append({'func': func, 'kwargs': kwargs})


@pytest.fixture
def mock_viewmodel():
    """Fixture for mock viewmodel."""
    return MockViewModel()


def test_get_ledger_error_message_returns_empty_for_empty_input():
    """Test get_ledger_error_message returns empty string for empty input."""
    # Execute
    result = get_ledger_error_message('')

    # Assert
    assert result == ''


def test_get_ledger_error_message_returns_empty_for_none_input():
    """Test get_ledger_error_message returns empty string for None input."""
    # Execute
    result = get_ledger_error_message(None)

    # Assert
    assert result == ''


@patch('src.utils.ledger_hw_client.QCoreApplication.translate')
def test_get_ledger_error_message_translates_known_errors(mock_translate):
    """Test get_ledger_error_message translates known error patterns."""
    # Setup
    mock_translate.return_value = 'translated_message'

    # Execute
    result = get_ledger_error_message(
        'Error: not in either the bitcoin or bitcoin testnet app',
    )

    # Assert
    assert result == 'translated_message'
    mock_translate.assert_called_once()


def test_get_ledger_error_message_returns_original_for_unknown():
    """Test get_ledger_error_message returns original for unknown error."""
    # Execute
    result = get_ledger_error_message('Unknown error message')

    # Assert
    assert result == 'Unknown error message'


@patch('src.utils.ledger_hw_client.QCoreApplication.translate')
def test_get_ledger_error_message_is_case_insensitive(mock_translate):
    """Test get_ledger_error_message is case insensitive."""
    # Setup
    mock_translate.return_value = 'translated'

    # Execute
    result = get_ledger_error_message(
        'NOT IN EITHER THE BITCOIN OR BITCOIN TESTNET APP',
    )

    # Assert
    assert result == 'translated'


def test_restore_multisig_config_returns_false_for_nonexistent_file():
    """Test restore_multisig_config_from_file returns False for nonexistent file."""
    # Execute
    result = restore_multisig_config_from_file('/nonexistent/path/file.json')

    # Assert
    assert result is False


@patch('src.viewmodels.viewmodel_helpers.SettingRepository.set_threshold_confirmed')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.set_cosigners')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.set_multisig_config')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.set_wallet_signature_type')
def test_restore_multisig_config_returns_true_for_valid_config(
    mock_set_sig_type, mock_set_multisig, mock_set_cosigners, mock_set_threshold,
):
    """Test restore_multisig_config_from_file returns True for valid config."""
    # Setup
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        json.dump(
            {
                'required_signers': 2,
                'total_signers': 3,
                'cosigners': ['cosigner1', 'cosigner2'],
            }, tmp_file,
        )
        tmp_path = tmp_file.name

    try:
        # Execute
        result = restore_multisig_config_from_file(tmp_path)

        # Assert
        assert result is True
        mock_set_sig_type.assert_called_once_with(
            WalletSignatureType.MULTI_SIG_WALLET,
        )
        mock_set_multisig.assert_called_once_with(2, 3)
        mock_set_cosigners.assert_called_once_with(['cosigner1', 'cosigner2'])
        mock_set_threshold.assert_called_once_with(True)
    finally:
        os.unlink(tmp_path)


def test_restore_multisig_config_returns_false_for_invalid_json():
    """Test restore_multisig_config_from_file returns False for invalid JSON."""
    # Setup
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_file.write('invalid json content')
        tmp_path = tmp_file.name

    try:
        # Execute
        result = restore_multisig_config_from_file(tmp_path)

        # Assert
        assert result is False
    finally:
        os.unlink(tmp_path)


def test_extract_psbt_result_for_multisig():
    """Test extract_psbt_result for multisig wallet."""
    # Setup
    mock_result = MagicMock()
    mock_result.psbt = 'test_psbt'
    mock_result.operation_idx = 'test_idx'

    # Execute
    psbt, op_idx = extract_psbt_result(mock_result, is_multisig=True)

    # Assert
    assert psbt == 'test_psbt'
    assert op_idx == 'test_idx'


def test_extract_psbt_result_for_singlesig():
    """Test extract_psbt_result for singlesig wallet."""
    # Setup
    mock_result = MagicMock()
    mock_result.psbt = 'test_psbt'

    # Execute
    psbt, op_idx = extract_psbt_result(mock_result, is_multisig=False)

    # Assert
    assert psbt == mock_result
    assert op_idx is None


def test_extract_psbt_and_operation_idx_for_multisig():
    """Test extract_psbt_and_operation_idx for multisig wallet."""
    # Setup
    mock_result = MagicMock()
    mock_result.psbt = 'test_psbt'
    mock_result.operation_idx = 'test_idx'

    # Execute
    psbt, op_idx = extract_psbt_and_operation_idx(
        mock_result, is_multisig=True,
    )

    # Assert
    assert psbt == 'test_psbt'
    assert op_idx == 'test_idx'


def test_extract_psbt_and_operation_idx_for_singlesig():
    """Test extract_psbt_and_operation_idx for singlesig wallet."""
    # Setup
    mock_result = MagicMock()
    mock_result.psbt = 'test_psbt'

    # Execute
    psbt, op_idx = extract_psbt_and_operation_idx(
        mock_result, is_multisig=False,
    )

    # Assert
    assert psbt == 'test_psbt'
    assert op_idx is None


@patch('src.viewmodels.viewmodel_helpers.hardware_client_store')
def test_handle_hardware_wallet_signing_for_hw_online_singlesig(mock_hw_store, mock_viewmodel):
    """Test handle_hardware_wallet_signing for HW online singlesig."""
    # Execute
    handle_hardware_wallet_signing(
        mock_viewmodel,
        is_hw=True,
        is_online=True,
        is_multisig=False,
        is_on_device=False,
        button_signal=mock_viewmodel.test_button_clicked,
    )

    # Assert
    mock_hw_store.set_rgb_mode.assert_called_once_with(True)


@patch('src.viewmodels.viewmodel_helpers.hardware_client_store')
def test_handle_hardware_wallet_signing_for_multisig_on_device(mock_hw_store, mock_viewmodel):
    """Test handle_hardware_wallet_signing for multisig on device."""
    # Execute
    handle_hardware_wallet_signing(
        mock_viewmodel,
        is_hw=True,
        is_online=False,
        is_multisig=True,
        is_on_device=True,
        button_signal=mock_viewmodel.test_button_clicked,
    )

    # Assert
    mock_hw_store.set_rgb_mode.assert_called_once_with(True)


@patch('src.viewmodels.viewmodel_helpers.hardware_client_store')
def test_handle_hardware_wallet_signing_for_hw_multisig(mock_hw_store, mock_viewmodel):
    """Test handle_hardware_wallet_signing for HW multisig."""
    # Execute
    handle_hardware_wallet_signing(
        mock_viewmodel,
        is_hw=True,
        is_online=True,
        is_multisig=True,
        is_on_device=False,
        button_signal=mock_viewmodel.test_button_clicked,
    )

    # Assert
    mock_hw_store.set_rgb_mode.assert_called_once_with(True)


@patch('src.viewmodels.viewmodel_helpers.extract_psbt_result')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_access_type')
def test_process_psbt_result_for_watch_only_wallet(mock_get_access, mock_extract, mock_viewmodel):
    """Test process_psbt_result returns False for watch-only wallet."""
    # Setup
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_extract.return_value = ('test_psbt', 'test_idx')
    mock_result = MagicMock()

    # Execute
    psbt, should_continue = process_psbt_result(
        mock_viewmodel, mock_result, is_multisig=False,
    )

    # Assert
    assert psbt == 'test_psbt'
    assert should_continue is False


@patch('src.viewmodels.viewmodel_helpers.sign_psbt_for_multisig')
@patch('src.viewmodels.viewmodel_helpers.handle_hardware_wallet_signing')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_access_type')
@patch('src.viewmodels.viewmodel_helpers.extract_psbt_result')
def test_process_psbt_result_for_multisig_wallet(
    mock_extract, mock_get_access, mock_get_key_storage, mock_get_wallet_type,
    mock_handle_hw, mock_sign_multisig, mock_viewmodel,
):
    """Test process_psbt_result for multisig wallet."""
    # Setup
    mock_extract.return_value = ('test_psbt', 'test_idx')
    mock_get_access.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_result = MagicMock()

    # Execute
    psbt, should_continue = process_psbt_result(
        mock_viewmodel, mock_result, is_multisig=True,
    )

    # Assert
    assert psbt == 'test_psbt'
    assert should_continue is True
    assert mock_viewmodel.operation_idx == 'test_idx'


@patch('src.viewmodels.viewmodel_helpers.sign_and_finalize_psbt')
@patch('src.viewmodels.viewmodel_helpers.handle_hardware_wallet_signing')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_access_type')
@patch('src.viewmodels.viewmodel_helpers.extract_psbt_result')
def test_process_psbt_result_for_singlesig_wallet(
    mock_extract, mock_get_access, mock_get_key_storage, mock_get_wallet_type,
    mock_handle_hw, mock_sign_finalize, mock_viewmodel,
):
    """Test process_psbt_result for singlesig wallet."""
    # Setup
    mock_extract.return_value = ('test_psbt', None)
    mock_get_access.return_value = WalletAccessType.WITH_PRIVATE_KEY
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_result = MagicMock()

    # Execute
    psbt, should_continue = process_psbt_result(
        mock_viewmodel, mock_result, is_multisig=False,
    )

    # Assert
    assert psbt == 'test_psbt'
    assert should_continue is True


@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_key_storage_type')
def test_handle_viewmodel_error_for_hardware_wallet(mock_get_key_storage, mock_viewmodel):
    """Test handle_viewmodel_error for hardware wallet."""
    # Setup
    mock_get_key_storage.return_value = KeyStorageType.HARDWARE_WALLET
    error = Exception('Test error')

    # Execute
    handle_viewmodel_error(mock_viewmodel, error)

    # No exception should be raised


@patch('src.viewmodels.viewmodel_helpers.ToastManager.error')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_key_storage_type')
def test_handle_viewmodel_error_shows_toast_for_seed_wallet(
    mock_get_key_storage, mock_get_sig_type, mock_toast_error, mock_viewmodel,
):
    """Test handle_viewmodel_error shows toast for seed wallet."""
    # Setup
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    error = CommonException('Test error message')

    # Execute
    handle_viewmodel_error(mock_viewmodel, error)

    # Assert
    mock_toast_error.assert_called_once_with(description='Test error message')


@patch('src.viewmodels.viewmodel_helpers.ToastManager.error')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.viewmodel_helpers.SettingRepository.get_key_storage_type')
def test_handle_viewmodel_error_shows_generic_error_for_non_common_exception(
    mock_get_key_storage, mock_get_sig_type, mock_toast_error, mock_viewmodel,
):
    """Test handle_viewmodel_error shows generic error for non-CommonException."""
    # Setup
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_sig_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    error = ValueError('Some error')

    # Execute
    handle_viewmodel_error(mock_viewmodel, error)

    # Assert
    mock_toast_error.assert_called_once()


@patch('src.viewmodels.viewmodel_helpers.RgbRepository.sync_with_bridge')
@patch('src.viewmodels.viewmodel_helpers.ToastManager.success')
def test_on_success_multisig_post_base_emits_success_signal(
    mock_toast_success, mock_sync, mock_viewmodel,
):
    """Test on_success_multisig_post_base emits success signal."""
    # Execute
    on_success_multisig_post_base(mock_viewmodel)

    # Assert
    mock_toast_success.assert_called_once()


@patch('src.viewmodels.viewmodel_helpers.RgbRepository.sync_with_bridge')
@patch('src.viewmodels.viewmodel_helpers.ToastManager.success')
def test_on_success_multisig_post_base_calls_run_in_thread(
    mock_toast_success, mock_sync, mock_viewmodel,
):
    """Test on_success_multisig_post_base calls run_in_thread for sync."""
    # Execute
    on_success_multisig_post_base(mock_viewmodel)

    # Assert
    assert len(mock_viewmodel.run_in_thread_calls) == 1
