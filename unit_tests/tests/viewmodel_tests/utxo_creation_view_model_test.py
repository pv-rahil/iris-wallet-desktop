# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for `UtxoCreationViewModel`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType, WalletSignatureType, WalletAccessType, WalletType
from src.viewmodels.utxo_creation_view_model import UtxoCreationViewModel


@pytest.fixture
def vm() -> UtxoCreationViewModel:
    """Return a fresh `UtxoCreationViewModel` instance for tests."""
    return UtxoCreationViewModel()


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.setting_card_repository.SettingCardRepository.get_default_fee_rate')
@patch('src.viewmodels.utxo_creation_view_model.colored_wallet')
def test_create_utxos_begin_calls_repo(mock_cw, mock_fee, mock_run, vm: UtxoCreationViewModel):
    """Verify create_utxos_begin calls repo."""
    mock_fee.return_value.fee_rate = 1
    vm.create_utxos_begin(purpose='create_utxos')
    assert mock_run.called
    args, _ = mock_run.call_args
    # First positional arg is the target function
    assert args[0].__name__ == 'create_utxos_begin'
    # Second positional arg is the config dict containing callbacks
    assert 'callback' in args[1] and 'error_callback' in args[1]


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.setting_card_repository.SettingCardRepository.get_default_fee_rate')
@patch('src.viewmodels.utxo_creation_view_model.colored_wallet')
@patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.MULTI_SIG_WALLET)
def test_create_utxos_begin_calls_repo_multisig(mock_sig, mock_cw, mock_fee, mock_run, vm: UtxoCreationViewModel):
    """Verify create_utxos_begin calls repo for multisig init."""
    mock_fee.return_value.fee_rate = 1
    vm.create_utxos_begin(purpose='create_utxos')
    assert mock_run.called
    args, _ = mock_run.call_args
    assert args[0].__name__ == 'create_utxos_init'


def test_on_utxo_begin_done_emits_unsigned_when_not_hw(vm: UtxoCreationViewModel, qtbot):
    """Verify on_utxo_begin_done emits unsigned_psbt when not hw."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.ON_DEVICE), \
            patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET):
        with qtbot.waitSignal(vm.unsigned_psbt, timeout=1000):
            vm.on_utxo_begin_done('psbt')


def test_on_utxo_begin_done_signs_when_hw(vm: UtxoCreationViewModel):
    """Verify on_utxo_begin_done signs when hw."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET), \
            patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET), \
            patch.object(vm, 'sign_and_finalize_psbt') as sign, \
            patch.object(vm, 'hw_dialog_update') as sig:
        vm.on_utxo_begin_done('psbt')
        sign.assert_called_once_with('psbt')
        sig.emit.assert_called()


def test_on_utxo_begin_done_watch_only(vm: UtxoCreationViewModel, mocker):
    """Verify on_utxo_begin_done emits unsigned for watch-only."""
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY)
    slot = mocker.Mock()
    vm.unsigned_psbt.connect(slot)
    vm.on_utxo_begin_done('psbt')
    slot.assert_called_once_with('psbt')


def test_on_utxo_begin_done_hw_multisig(vm: UtxoCreationViewModel, mocker):
    """Verify on_utxo_begin_done calls sign_psbt_for_multisig when hw+multisig."""
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.MULTI_SIG_WALLET)
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
    
    res = mocker.Mock(psbt='psbt1', operation_idx=1)
    
    mock_hw = mocker.Mock()
    vm.hw_dialog_update.connect(mock_hw)
    mock_sign = mocker.patch.object(vm, 'sign_psbt_for_multisig')
    
    vm.on_utxo_begin_done(res)
    mock_hw.assert_called_once()
    mock_sign.assert_called_once_with('psbt1')


def test_on_utxo_begin_done_local_multisig(vm: UtxoCreationViewModel, mocker):
    """Verify on_utxo_begin_done calls sign_psbt_for_multisig when on_device+multisig."""
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.MULTI_SIG_WALLET)
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.ON_DEVICE)
    
    res = mocker.Mock(psbt='psbt2', operation_idx=2)
    
    mock_hw = mocker.Mock()
    vm.hw_dialog_update.connect(mock_hw)
    mock_sign = mocker.patch.object(vm, 'sign_psbt_for_multisig')
    
    vm.on_utxo_begin_done(res)
    mock_hw.assert_called_once()
    mock_sign.assert_called_once_with('psbt2')


def test_sign_psbt_for_multisig(vm: UtxoCreationViewModel, mocker):
    """Test multisig signing in BG thread."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.sign_psbt_for_multisig('psbt')
    mock_run.assert_called_once()


def test_on_multisig_psbt_signed(vm: UtxoCreationViewModel, mocker):
    """Test on_multisig_psbt_signed posts to bridge."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    mock_hw = mocker.Mock()
    vm.operation_idx = 1
    vm.hw_dialog_update.connect(mock_hw)
    vm.on_multisig_psbt_signed('psbt')
    mock_hw.assert_called_once()
    mock_run.assert_called_once()


def test_on_psbt_posted_to_bridge(vm: UtxoCreationViewModel, qtbot):
    """Test signal emitted when bridging completes."""
    with qtbot.waitSignal(vm.psbt_posted_to_bridge, timeout=1000):
        vm.on_psbt_posted_to_bridge()


def test_on_utxo_signed_done(vm: UtxoCreationViewModel, mocker):
    """Test dialog emission and create_utxos_end call on signed done."""
    mock_hw = mocker.Mock()
    vm.hw_dialog_update.connect(mock_hw)
    mock_end = mocker.patch.object(vm, 'create_utxos_end')
    vm.on_utxo_signed_done('psbt')
    mock_hw.assert_called_once()
    mock_end.assert_called_once_with(finalized_psbt='psbt')


@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_sign_and_finalize_psbt_runs(mock_run, vm: UtxoCreationViewModel):
    """Verify sign_and_finalize_psbt runs in background thread."""
    vm.sign_and_finalize_psbt('psbt')
    assert mock_run.called


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.model.common_operation_model.BroadcastPsbtRequestModel')
@patch('src.data.repository.btc_repository.BtcRepository.create_utxos_end')
def test_create_utxos_end_broadcasts(mock_repo, mock_req, mock_run, vm: UtxoCreationViewModel):
    """Verify create_utxos_end broadcasts in background thread."""
    vm.param = MagicMock(online=True, skip_sync=False)
    vm.create_utxos_end('signed')
    assert mock_run.called


def test_on_utxo_end_done_emits(vm: UtxoCreationViewModel, qtbot):
    """Verify on_utxo_end_done emits utxo_created."""
    with qtbot.waitSignal(vm.utxo_created, timeout=1000):
        vm.on_utxo_end_done()


def test_on_error_non_hw_shows_toast(vm: UtxoCreationViewModel, mocker):
    """Verify on_error_non_hw_shows_toast shows toast error."""
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.ON_DEVICE)
    mocker.patch('src.viewmodels.utxo_creation_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
    with patch('src.views.components.toast.ToastManager.error') as terr:
        vm.on_error(Exception('x'))
        terr.assert_called()


def test_on_error_hw_emits_dialog(vm: UtxoCreationViewModel):
    """Verify on_error_hw_emits_dialog emits dialog_update."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET):
        with patch.object(vm, 'hw_dialog_update') as sig:
            vm.on_error(Exception('x'))
            sig.emit.assert_called()
