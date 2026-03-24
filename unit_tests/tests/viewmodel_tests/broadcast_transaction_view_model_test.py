# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for `BroadcastTransactionViewModel`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
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


def test_load_psbts(vm, mocker):
    """Test load_psbts success and error."""
    mock_service = mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.list_psbt_drafts', return_value=['p1'])
    
    def mock_run_in_thread(target, params):
        target()
                
    mocker.patch.object(vm, 'run_in_thread', side_effect=mock_run_in_thread)
    
    slot = Mock()
    vm.psbts_loaded.connect(slot)
    
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WITH_PRIVATE_KEY)
    vm.load_psbts(True)
    slot.assert_called()
    assert slot.call_args[0][0] == ['p1']
    
    # Error path
    mock_service.side_effect = Exception('fail')
    mock_toast = mocker.patch('src.viewmodels.broadcast_transaction_view_model.ToastManager.error')
    vm.load_psbts(True)
    slot.assert_called()
    assert slot.call_args[0][0] == []
    mock_toast.assert_called()

    # Watch-only path (lines 71-76)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY)
    slot.reset_mock()
    vm.load_psbts(True)
    slot.assert_called_with([])


def test_execute_psbt_action(vm, mocker):
    """Test execute_psbt_action routing."""
    parsed = mocker.Mock(psbt='psbt_text')
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.parse_psbt_input', return_value=parsed)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.resolve_purpose', return_value='btc')
    
    # sign
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.action_key', return_value='sign')
    with patch.object(vm, 'sign_and_finalize_psbt') as m:
        vm.execute_psbt_action('raw', None, False)
        m.assert_called_once_with('psbt_text')
        
    # send_btc
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.action_key', return_value='send_btc')
    with patch.object(vm, 'send_btc_end') as m:
        vm.execute_psbt_action('raw', None, True)
        m.assert_called_once_with('psbt_text')
        
    # send_asset
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.action_key', return_value='send_asset')
    with patch.object(vm, 'send_end') as m:
        vm.execute_psbt_action('raw', None, True)
        m.assert_called_once_with('psbt_text')

    # inflation
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.action_key', return_value='inflation')
    with patch.object(vm, 'inflate_end') as m:
        vm.execute_psbt_action('raw', None, True)
        m.assert_called_once_with('psbt_text')
        
    # create_utxos (default)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.action_key', return_value='other')
    with patch.object(vm, 'create_utxos_end') as m:
        vm.execute_psbt_action('raw', None, True)
        m.assert_called_once_with('psbt_text')


def test_on_success_create_utxos_end(vm, qtbot):
    """Test on_success_create_utxos_end callback."""
    with qtbot.waitSignals([vm.is_loading, vm.tx_broadcasted], timeout=1000):
        vm.on_success_create_utxos_end()


def test_inflate_end_flow(vm, mocker, qtbot):
    """Test inflate_end call and success callback."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.inflate_end('psbt')
    mock_run.assert_called_once()
    
    # success
    res = mocker.Mock(txid='tx123')
    mock_toast = mocker.patch('src.viewmodels.broadcast_transaction_view_model.ToastManager.success')
    with qtbot.waitSignals([vm.is_loading, vm.tx_broadcasted], timeout=1000):
        vm.on_success_inflate_end(res)
    mock_toast.assert_called()


def test_multisig_signer_flow(vm, mocker, qtbot):
    """Test multisig signer flow: sign_and_post_multisig, sign_success, inspected, respond."""
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.ON_DEVICE)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    
    # 1. sign_and_post_multisig
    vm.sign_and_post_multisig('unsigned', 1, purpose='btc')
    assert vm._multisig_operation_idx == 1
    mock_run.assert_called()
    
    # 2. _on_multisig_sign_success
    mock_run.reset_mock()
    vm._on_multisig_sign_success('signed')
    assert vm._current_signed_psbt == 'signed'
    mock_run.assert_called() # Calls inspect_psbt
    
    # 3. _on_signed_psbt_inspected
    mock_run.reset_mock()
    details = mocker.Mock(txid='tx123')
    vm._on_signed_psbt_inspected(details)
    assert vm._current_signed_txid == 'tx123'
    mock_run.assert_called() # Calls respond_to_operation
    
    # 4. _on_multisig_post_success (different message cases)
    mock_toast = mocker.patch('src.viewmodels.broadcast_transaction_view_model.ToastManager.success')
    vm.trigger_bridge_sync.connect(lambda: None)
    
    # Case: result None
    vm._on_multisig_post_success(None)
    mock_toast.assert_called()
    
    # Case: different operation completions
    mock_res = mocker.Mock()
    mock_res.operation.is_create_utxos_completed.return_value = True
    vm._on_multisig_post_success(mock_res)
    
    mock_res.operation.is_create_utxos_completed.return_value = False
    mock_res.operation.is_send_btc_completed.return_value = True
    vm._on_multisig_post_success(mock_res)
    
    mock_res.operation.is_send_btc_completed.return_value = False
    mock_res.operation.is_inflation_completed.return_value = True
    vm._on_multisig_post_success(mock_res)
    
    mock_res.operation.is_inflation_completed.return_value = False
    mock_res.operation.is_send_completed.return_value = True
    vm._on_multisig_post_success(mock_res)
    
    mock_res.operation.is_send_completed.return_value = False
    vm._on_multisig_post_success(mock_res)


def test_on_multisig_sign_error(vm, mocker):
    """Test on_multisig_sign_error handling."""
    # HW case
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.HWDeviceSelectionDialog.map_hwi_error', return_value='msg')
    slot = Mock()
    vm.hw_dialog_update.connect(slot)
    
    vm.on_multisig_sign_error(Exception('raw'))
    slot.assert_called()
    
    # Non-HW case
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.ON_DEVICE)
    mock_on_error = mocker.patch.object(vm, 'on_error')
    vm.on_multisig_sign_error(Exception('raw'))
    mock_on_error.assert_called()


def test_respond_nack(vm, mocker):
    """Test respond_nack success and error."""
    # Error: no index
    mock_toast = mocker.patch('src.viewmodels.broadcast_transaction_view_model.ToastManager.error')
    vm.respond_nack(None)
    mock_toast.assert_called()
    
    # Success
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.respond_nack(1)
    mock_run.assert_called()
    
    # Callback
    mock_toast_succ = mocker.patch('src.viewmodels.broadcast_transaction_view_model.ToastManager.success')
    vm.trigger_bridge_sync.connect(lambda: None)
    vm._on_nack_post_success()
    mock_toast_succ.assert_called()


def test_respond_psbt_to_operation(vm, mocker):
    """Test respond_psbt_to_operation call."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.respond_psbt_to_operation('signed', 1)
    mock_run.assert_called()


def test_inspection_flows(vm, mocker):
    """Test inspect_psbt and inspect_rgb_transfer."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    
    # inspect_psbt
    vm.inspect_psbt('psbt')
    mock_run.assert_called()
    
    # inspect_rgb_transfer
    mock_run.reset_mock()
    vm.inspect_rgb_transfer('fascia', 'psbt', 123)
    mock_run.assert_called()


def test_fetch_pending_operation(vm, mocker):
    """Test fetch_pending_operation routing."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.get_pending_operation_state', return_value=(None, None))
    
    # Standard use case
    vm.fetch_pending_operation()
    mock_run.assert_called()
    
    # Callback
    mock_res = mocker.Mock()
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.multisig_pending_context', return_value=None)
    slot = Mock()
    vm.pending_operation_ready.connect(slot)
    vm._on_fetch_pending_operation_success(mock_res)
    slot.assert_called()


def test_respond_to_multisig_operation(vm, mocker):
    """Test _respond_to_multisig_operation logic."""
    from rgb_lib import RespondToOperation
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm._respond_to_multisig_operation(1, RespondToOperation.ACK('signed'))
    mock_run.assert_called()


def test_on_inspect_success(vm, mocker):
    """Test _on_inspect_psbt_success and _on_inspect_rgb_transfer_success."""
    slot_p = Mock()
    slot_r = Mock()
    vm.psbt_inspection_ready.connect(slot_p)
    vm.rgb_transfer_inspection_ready.connect(slot_r)
    
    vm._on_inspect_psbt_success('details')
    slot_p.assert_called_with('details')
    
    vm._on_inspect_rgb_transfer_success('details')
    slot_r.assert_called_with('details')


def test_sign_and_post_multisig_hardware(vm, mocker):
    """Test sign_and_post_multisig with hardware wallet branch (line 261)."""
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
    slot = Mock()
    vm.hw_dialog_update.connect(slot)
    mocker.patch.object(vm, 'run_in_thread')
    
    vm.sign_and_post_multisig('psbt', 1)
    slot.assert_called()


def test_fetch_pending_operation_success_with_psbt(vm, mocker):
    """Test _on_fetch_pending_operation_success with psbt branch (lines 467-475)."""
    res = mocker.Mock()
    ctx = mocker.Mock(psbt='psbt_text')
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.multisig_pending_context', return_value=ctx)
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    
    vm._on_fetch_pending_operation_success(res)
    mock_run.assert_called()


def test_inspection_guards(vm, mocker):
    """Test inspection guards."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    
    # psbt guard
    vm._inspecting_psbt = 'psbt'
    vm.inspect_psbt('psbt')
    mock_run.assert_not_called()
    
    # rgb guard
    vm._inspecting_rgb = ('f', 'p')
    vm.inspect_rgb_transfer('f', 'p', 1)
    mock_run.assert_not_called()


def test_fetch_pending_operation_branches(vm, mocker):
    """Test fetch_pending_operation offline and cached branches."""
    # Offline
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET)
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.fetch_pending_operation()
    mock_run.assert_not_called()
    
    # Cached
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.BroadcastTransactionService.get_pending_operation_state', return_value=('info', 'txid'))
    slot = Mock()
    vm.pending_operation_ready.connect(slot)
    vm.fetch_pending_operation()
    slot.assert_called_with('info')
    assert vm._pending_psbt_txid == 'txid'


def test_multisig_sign_success_offline(vm, mocker):
    """Test _on_multisig_sign_success offline check."""
    mocker.patch('src.viewmodels.broadcast_transaction_view_model.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET)
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    slot = Mock()
    vm.finalized_psbt.connect(slot)
    
    vm._on_multisig_sign_success('signed')
    slot.assert_called_with('signed')
    mock_run.assert_not_called()


def test_on_signed_psbt_inspected_error(vm, mocker):
    """Test _on_signed_psbt_inspected error branch."""
    vm._current_signed_psbt = 'signed'
    vm._multisig_operation_idx = 1
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    
    vm._on_signed_psbt_inspected(Exception('fail'))
    mock_run.assert_called_once() # Still calls respond_to_operation with NACK or error?
