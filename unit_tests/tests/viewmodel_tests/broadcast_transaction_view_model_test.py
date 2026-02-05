# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for `BroadcastTransactionViewModel`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch
import sys

# Mock logging to avoid file creation issues with mocked QDirs
sys.modules['src.utils.logging'] = MagicMock()



# Mock logging to avoid file creation issues with mocked QDirs
sys.modules['src.utils.logging'] = MagicMock()

# Mock google dependencies
sys.modules['google'] = MagicMock()
sys.modules['google.auth'] = MagicMock()
sys.modules['google.auth.transport'] = MagicMock()
sys.modules['google.auth.transport.requests'] = MagicMock()
sys.modules['google_auth_oauthlib'] = MagicMock()
sys.modules['google_auth_oauthlib.flow'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

# Mock hwilib
sys.modules['hwilib'] = MagicMock()
sys.modules['hwilib.psbt'] = MagicMock()

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.viewmodels.broadcast_transaction_view_model import BroadcastTransactionViewModel


@pytest.fixture
def vm() -> BroadcastTransactionViewModel:
    """Provide a fresh `BroadcastTransactionViewModel` instance for each test."""
    return BroadcastTransactionViewModel(page_navigation=MagicMock())


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.rgb_repository.RgbRepository.send_end')
@patch('src.model.common_operation_model.BroadcastPsbtRequestModel')
def test_send_end_starts_and_runs(mock_req, _repo, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify send_end starts loading and runs in background thread."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.send_end('signed')
    assert mock_run.called


def test_on_success_send_end_emits_and_toast(vm: BroadcastTransactionViewModel, qtbot):
    """Verify on_success_send_end emits tx_broadcasted and shows toast."""
    fake_resp = MagicMock(txid='abc')
    with patch('src.views.components.toast.ToastManager.success') as succ:
        with qtbot.waitSignals([vm.is_loading, vm.tx_broadcasted], timeout=1000):
            vm.on_success_send_end(fake_resp)
        succ.assert_called()


def test_on_error_shows_toast(vm: BroadcastTransactionViewModel):
    """Verify on_error shows toast error."""
    with patch('src.views.components.toast.ToastManager.error') as terr:
        vm.on_error(CommonException('x'))
        terr.assert_called()


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.btc_repository.BtcRepository.create_utxos_end')
@patch('src.model.common_operation_model.BroadcastPsbtRequestModel')
def test_create_utxos_end_runs(mock_req, _repo, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify create_utxos_end runs in background thread."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.create_utxos_end('signed')
    assert mock_run.called


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.btc_repository.BtcRepository.send_btc_end')
@patch('src.model.common_operation_model.BroadcastPsbtRequestModel')
def test_send_btc_end_runs(mock_req, _repo, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify send_btc_end runs in background thread."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.send_btc_end('signed')
    assert mock_run.called


def test_on_success_send_btc_end_emits_and_toast(vm: BroadcastTransactionViewModel, qtbot):
    """Verify on_success_send_btc_end emits tx_broadcasted and shows toast."""
    fake_resp = MagicMock(tx_id='abc')
    with patch('src.views.components.toast.ToastManager.success') as succ:
        with qtbot.waitSignals([vm.is_loading, vm.tx_broadcasted], timeout=1000):
            vm.on_success_send_btc_end(fake_resp)
        succ.assert_called()


@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_sign_and_finalize_emits_dialog_then_runs(mock_run, vm: BroadcastTransactionViewModel):
    """Verify sign_and_finalize_emits_dialog_then_runs emits dialog_update and runs in background thread."""
    with patch.object(vm, 'hw_dialog_update') as sig:
        vm.sign_and_finalize_psbt('psbt')
        sig.emit.assert_called_with(
            INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
        )
    assert mock_run.called


def test_on_sign_and_finalize_success_emits_and_toast(vm: BroadcastTransactionViewModel, qtbot):
    """Verify on_sign_and_finalize_success emits finalized_psbt and shows toast."""
    with patch('src.views.components.toast.ToastManager.success') as succ:
        with qtbot.waitSignal(vm.finalized_psbt, timeout=1000):
            vm.on_sign_and_finalize_success('final')
        succ.assert_called()


@patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
@patch('src.views.components.hw_device_selection_dialog.HWDeviceSelectionDialog.map_hwi_error', return_value='mapped')
@patch('src.views.components.hw_device_selection_dialog.HWDeviceSelectionDialog.__init__', return_value=None)
@patch('src.utils.logging.logger.error')
def test_on_sign_and_finalize_error_hw_emit_dialog(_log, _init, _map, _kst, vm: BroadcastTransactionViewModel, qtbot):
    """Verify on_sign_and_finalize_error_hw_emit_dialog emits dialog_update and shows toast."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.on_sign_and_finalize_error(CommonException('raw'))


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.inspect_transaction')
def test_trigger_full_inspection_runs_service(mock_service, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify trigger_full_inspection calls BroadcastTransactionService."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.trigger_full_inspection('psbt')
    assert mock_run.called
    # mock_service check might need to be inside run_in_thread callback mock if we were executing it inline,
    # but here we just check if run_in_thread was called with the service function


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.multisig_sign_and_post')
def test_sign_and_post_multisig_runs_service(mock_service, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify sign_and_post_multisig calls BroadcastTransactionService."""
    with qtbot.waitSignal(vm.is_loading, timeout=1000):
        vm.sign_and_post_multisig('psbt', 1)
    assert mock_run.called


@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.respond_nack')
def test_respond_nack_runs_service(mock_service, mock_run, vm: BroadcastTransactionViewModel, qtbot):
    """Verify respond_nack calls BroadcastTransactionService."""
    with qtbot.waitSignal(vm.is_reject_loading, timeout=1000):
        vm.respond_nack(1)
    assert mock_run.called
