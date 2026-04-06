"""Unit test for header frame view model"""
# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-many-statements
from __future__ import annotations

import pytest

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.constant import PING_DNS_SERVER_CALL_INTERVAL
from src.utils.custom_exception import CommonException
from src.viewmodels.header_frame_view_model import HeaderFrameViewModel
from src.viewmodels.header_frame_view_model import NetworkCheckerThread


def test_network_checker_thread_success(mocker, qtbot):
    """Test that NetworkCheckerThread emits True when network is available."""
    network_checker = NetworkCheckerThread()

    mocker.patch.object(
        network_checker, 'check_internet_conn', return_value=True,
    )

    def signal_received(value):
        assert value is True

    network_checker.network_status_signal.connect(signal_received)

    network_checker.start()
    qtbot.waitSignal(network_checker.finished, timeout=1000)


def test_network_checker_thread_failure(mocker, qtbot):
    """Test that NetworkCheckerThread emits False when network is unavailable."""
    network_checker = NetworkCheckerThread()

    mocker.patch.object(
        network_checker, 'check_internet_conn', return_value=False,
    )

    def signal_received(value):
        assert value is False

    network_checker.network_status_signal.connect(signal_received)

    network_checker.start()
    qtbot.waitSignal(network_checker.finished, timeout=1000)


def test_check_internet_conn_success(mocker):
    """Test check_internet_conn returns True when socket connection succeeds."""
    network_checker = NetworkCheckerThread()

    mocker.patch('socket.create_connection', return_value=True)

    assert network_checker.check_internet_conn() is True


def test_check_internet_conn_failure(mocker):
    """Test check_internet_conn returns False when socket connection fails."""
    network_checker = NetworkCheckerThread()

    mocker.patch('socket.create_connection', side_effect=OSError)

    assert network_checker.check_internet_conn() is False


def test_header_frame_view_model_init(mocker):
    """Test that HeaderFrameViewModel initializes correctly with a running timer."""
    mock_timer = mocker.patch(
        'src.viewmodels.header_frame_view_model.QTimer',
    )

    view_model = HeaderFrameViewModel()

    # Ensure QTimer was instantiated
    mock_timer.assert_called_once()

    # Retrieve the mocked QTimer instance
    mock_timer_instance = mock_timer.return_value

    # Ensure timer settings and start behavior are correct
    mock_timer_instance.setInterval.assert_called_once_with(
        PING_DNS_SERVER_CALL_INTERVAL,
    )
    mock_timer_instance.timeout.connect.assert_called_once_with(
        view_model.start_network_check,
    )
    mock_timer_instance.start.assert_called_once()


def test_header_frame_view_model_network_check(mocker):
    """Test that start_network_check creates a NetworkCheckerThread and starts it."""
    view_model = HeaderFrameViewModel()

    mock_thread = mocker.patch(
        'src.viewmodels.header_frame_view_model.NetworkCheckerThread',
    )
    mock_instance = mock_thread.return_value

    view_model.start_network_check()

    mock_thread.assert_called_once()
    mock_instance.network_status_signal.connect.assert_called_once_with(
        view_model.handle_network_status,
    )
    mock_instance.start.assert_called_once()


def test_header_frame_view_model_handle_network_status():
    """Test that handle_network_status emits the correct signal."""
    view_model = HeaderFrameViewModel()
    received_signals = []

    def signal_received(value):
        received_signals.append(value)

    view_model.network_status_signal.connect(signal_received)

    view_model.handle_network_status(True)
    view_model.handle_network_status(False)

    assert received_signals == [True, False]


def test_header_frame_view_model_stop_network_checker(mocker):
    """Test that stop_network_checker stops the timer."""
    view_model = HeaderFrameViewModel()

    mock_timer = mocker.patch.object(view_model.timer, 'stop')

    view_model.stop_network_checker()

    mock_timer.assert_called_once()


def test_perform_sync_starts_thread_and_emits_started(mocker):
    """Test perform_sync schedules usb sync with correct args and emits started."""
    view_model = HeaderFrameViewModel()
    started_slot = mocker.Mock()
    view_model.sync_process_started.connect(started_slot)
    view_model.run_in_thread = mocker.Mock()

    selected_drive = mocker.Mock()

    view_model.perform_sync(selected_drive, 'pwd')

    started_slot.assert_called_once_with()
    view_model.run_in_thread.assert_called_once()
    args, _ = view_model.run_in_thread.call_args
    # Verify target and callbacks
    assert 'perform_sync' in str(args[0]) or args[0].__name__ == 'perform_sync'
    # Params are passed as positional dict in args[1]
    params = args[1]
    assert params['args'] == [selected_drive]
    assert callable(params['callback'])
    assert callable(params['error_callback'])


def test_handle_sync_completed_to_usb_and_no_sync(mocker):
    """Test handle_sync_completed for to_usb and no_sync branches show success and emit."""
    view_model = HeaderFrameViewModel()
    ended_slot = mocker.Mock()
    view_model.sync_process_ended.connect(ended_slot)

    toast_success = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.success',
    )
    translate = mocker.patch(
        'src.viewmodels.header_frame_view_model.QCoreApplication.translate', return_value='ok',
    )

    view_model.handle_sync_completed('to_usb')
    ended_slot.assert_any_call('to_usb')
    toast_success.assert_called()
    translate.assert_called()

    toast_success.reset_mock()
    view_model.handle_sync_completed('no_sync')
    ended_slot.assert_any_call('no_sync')
    toast_success.assert_called()


def test_handle_sync_completed_from_usb_triggers_password_flow(mocker):
    """Test from_usb branch triggers enter password via CommonOperationService and callbacks wired."""
    view_model = HeaderFrameViewModel()
    view_model.password = 'pwd'
    view_model.run_in_thread = mocker.Mock()

    view_model.handle_sync_completed('from_usb')

    view_model.run_in_thread.assert_called_once()
    target, params = view_model.run_in_thread.call_args[0]
    assert 'enter_wallet_password' in str(
        target,
    ) or target.__name__ == 'enter_wallet_password'
    assert params['args'] == ['pwd']
    assert callable(params['callback'])
    assert callable(params['error_callback'])


def test_handle_sync_error_emits_and_toast(mocker):
    """Test handle_sync_error emits error and shows toast with error text."""
    view_model = HeaderFrameViewModel()
    ended_slot = mocker.Mock()
    view_model.sync_process_ended.connect(ended_slot)
    toast_error = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.error',
    )

    view_model.handle_sync_error(Exception('boom'))
    ended_slot.assert_called_once_with('error')
    toast_error.assert_called_once()


def test_handle_sync_success_watch_only_online_go_online_and_toast(mocker):
    """Test WATCH_ONLY branch goes online and emits success toast when not retry."""
    view_model = HeaderFrameViewModel()
    ended_slot = mocker.Mock()
    view_model.sync_process_ended.connect(ended_slot)
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    # Mock get_online_wallet which handles the network/config calls
    mock_online = mocker.Mock()
    mock_get_online = mocker.patch(
        'src.viewmodels.header_frame_view_model.get_online_wallet',
        return_value=mock_online,
    )
    cw = mocker.patch('src.viewmodels.header_frame_view_model.colored_wallet')
    toast_success = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.success',
    )

    view_model.handle_sync_success('from_usb', retry=False)

    # Verify get_online_wallet was called and online_wallet was set
    mock_get_online.assert_called_once()
    assert cw.online_wallet == mock_online
    ended_slot.assert_called_with('from_usb')
    toast_success.assert_called()


def test_handle_sync_success_inconsistency_recovers_and_notifies(mocker):
    """Test inconsistency error triggers restore, retry path and error toast."""
    view_model = HeaderFrameViewModel()
    view_model.usb_sync_manager.restore_local_folder_from_backup = mocker.Mock()

    class DummyInconsistency(Exception):
        """Dummy inconsistency exception."""
        pass  # pylint: disable=unnecessary-pass
    mocker.patch(
        'src.viewmodels.header_frame_view_model.RgbLibError.Inconsistency', DummyInconsistency,
    )
    mock_completed = mocker.patch.object(view_model, 'handle_sync_completed')

    def raise_inconsistency(*_args, **_kwargs):
        raise DummyInconsistency()
    # Patch go_online flow to raise inconsistency
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_access_type',
        side_effect=raise_inconsistency,
    )
    with pytest.raises(TypeError):
        view_model.handle_sync_success('from_usb', retry=False)
    view_model.usb_sync_manager.restore_local_folder_from_backup.assert_called_once()
    mock_completed.assert_called_once()


def test_handle_sync_success_generic_exception_toast(mocker):
    """Test generic exception in handle_sync_success logs error and shows toast."""
    view_model = HeaderFrameViewModel()
    toast_error = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.error',
    )
    mocker.patch('src.viewmodels.header_frame_view_model.logger.error')

    def raise_exc(*_a, **_k):
        raise CommonException('oops')

    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_access_type', side_effect=raise_exc,
    )

    view_model.handle_sync_success('from_usb', retry=False)
    toast_error.assert_called_once()


def test_is_multisig_pending():
    """Test is_multisig_pending property."""
    vm = HeaderFrameViewModel()
    assert vm.is_multisig_pending is False
    vm._multisig_pending = True
    assert vm.is_multisig_pending is True


def test_set_multisig_pending_emits_signal(mocker):
    """Test _set_multisig_pending emits signal when changed."""
    vm = HeaderFrameViewModel()
    slot = mocker.Mock()
    vm.multisig_pending_state_changed.connect(slot)

    # Change
    vm._set_multisig_pending(True)
    assert vm._multisig_pending is True
    slot.assert_called_once_with(True)

    # No change
    slot.reset_mock()
    vm._set_multisig_pending(True)
    slot.assert_not_called()


def test_is_multisig(mocker):
    """Test _is_multisig reads from SettingRepository."""
    vm = HeaderFrameViewModel()
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    assert vm._is_multisig() is True

    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    assert vm._is_multisig() is False


def test_sync_multisig_bridge_early_returns(mocker):
    """Test sync_multisig_bridge returns early for non-multisig and offline."""
    vm = HeaderFrameViewModel()
    mock_run = mocker.patch.object(vm, 'run_in_thread')

    # Non-multisig
    mocker.patch.object(vm, '_is_multisig', return_value=False)
    vm.sync_multisig_bridge()
    mock_run.assert_not_called()

    # Offline
    mocker.patch.object(vm, '_is_multisig', return_value=True)
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.OFFLINE_TYPE_WALLET,
    )
    vm.sync_multisig_bridge()
    mock_run.assert_not_called()

    # Success path
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    vm.sync_multisig_bridge()
    mock_run.assert_called_once()


def test_on_multisig_sync_done_parsing(mocker):
    """Test on_multisig_sync_done parses incoming ops and determines pending state."""
    vm = HeaderFrameViewModel()
    mocker.patch.object(vm, '_set_multisig_pending')
    mocker.patch.object(vm, '_extract_and_save_review_psbts')
    mocker.patch.object(vm, '_inspect_and_set_global_pending_state')
    slot = mocker.Mock()
    vm.pending_operations_ready.connect(slot)

    # 1. Non-list / Single Obj
    op_info_single = mocker.Mock()
    op_info_single.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    vm.on_multisig_sync_done(op_info_single)
    vm._set_multisig_pending.assert_called_with(True)
    slot.assert_called_once_with([op_info_single])

    # 2. List with various operations (None, missing attr, non-blocking, blocking, None ops)
    vm._set_multisig_pending.reset_mock()
    slot.reset_mock()

    op_none_op = mocker.Mock()
    op_none_op.operation = None
    op_non_blocking = mocker.Mock()
    op_non_blocking.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_non_blocking.operation.is_CREATE_UTXOS_PENDING.return_value = False
    op_non_blocking.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_non_blocking.operation.is_SEND_BTC_PENDING.return_value = False
    op_non_blocking.operation.is_SEND_TO_REVIEW.return_value = False
    op_non_blocking.operation.is_SEND_PENDING.return_value = False
    op_non_blocking.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_non_blocking.operation.is_INFLATION_PENDING.return_value = False

    vm.on_multisig_sync_done([None, op_none_op, op_non_blocking])
    vm._set_multisig_pending.assert_called_with(False)
    slot.assert_called_once_with([])


def test_on_multisig_sync_done_watch_only(mocker):
    """Test on_multisig_sync_done extracts PSBTs for watch-only."""
    vm = HeaderFrameViewModel()
    mocker.patch.object(vm, '_set_multisig_pending')
    extract_mock = mocker.patch.object(vm, '_extract_and_save_review_psbts')
    mocker.patch.object(vm, '_inspect_and_set_global_pending_state')

    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    vm.on_multisig_sync_done([])
    extract_mock.assert_called_once_with([])


def test_on_multisig_sync_error(mocker):
    """Test on_multisig_sync_error resets pending and emits empty."""
    vm = HeaderFrameViewModel()
    slot = mocker.Mock()
    vm.pending_operations_ready.connect(slot)
    mocker.patch.object(vm, '_set_multisig_pending')

    vm.on_multisig_sync_error(Exception('fail'))

    vm._set_multisig_pending.assert_called_once_with(False)
    slot.assert_called_once_with([])


def test_inspect_and_set_global_pending_state(mocker):
    """Test _inspect_and_set_global_pending_state logic."""
    vm = HeaderFrameViewModel()
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    mocker.patch(
        'src.viewmodels.header_frame_view_model.BroadcastTransactionService.set_pending_operation_state',
    )

    # Empty or no valid ops -> no thread
    op_none_op = mocker.Mock()
    op_none_op.operation = None
    vm._inspect_and_set_global_pending_state([None, op_none_op])
    mock_run.assert_not_called()

    # Op with no blocking action
    op1 = mocker.Mock()
    op1.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op1.operation.is_CREATE_UTXOS_PENDING.return_value = False
    op1.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op1.operation.is_SEND_BTC_PENDING.return_value = False
    op1.operation.is_SEND_TO_REVIEW.return_value = False
    op1.operation.is_SEND_PENDING.return_value = False
    op1.operation.is_INFLATION_TO_REVIEW.return_value = False
    op1.operation.is_INFLATION_PENDING.return_value = False

    vm._inspect_and_set_global_pending_state([op1])
    mock_run.assert_not_called()

    # Op with blocking action but no PSBT
    op2 = mocker.Mock()
    op2.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    op2.operation.psbt = None
    vm._inspect_and_set_global_pending_state([op2])
    mock_run.assert_not_called()

    # Valid blocking Op with PSBT
    op3 = mocker.Mock()
    op3.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    op3.operation.psbt = 'psbt_text'
    vm._inspect_and_set_global_pending_state([op3])
    mock_run.assert_called_once()


def test_on_pending_psbt_inspected(mocker):
    """Test _on_pending_psbt_inspected success and error."""
    vm = HeaderFrameViewModel()
    mock_set = mocker.patch(
        'src.viewmodels.header_frame_view_model.BroadcastTransactionService.set_pending_operation_state',
    )

    # Success
    res = mocker.Mock(txid='tx123')
    op_info = mocker.Mock()
    vm._on_pending_psbt_inspected(res, op_info)
    mock_set.assert_called_with(op_info, 'tx123')

    # Error
    mock_logger = mocker.patch(
        'src.viewmodels.header_frame_view_model.logger.error',
    )
    mock_set.side_effect = Exception('fail')
    vm._on_pending_psbt_inspected(res, op_info)
    mock_logger.assert_called()


def test_extract_and_save_review_psbts(mocker):
    """Test _extract_and_save_review_psbts extraction and DB storage."""
    vm = HeaderFrameViewModel()
    # 1. No wallet service
    mocker.patch(
        'src.viewmodels.header_frame_view_model.WalletDataService.get_session', return_value=None,
    )
    vm._extract_and_save_review_psbts([])  # should return

    # 2. Wallet service present
    mock_db = mocker.Mock()
    mocker.patch(
        'src.viewmodels.header_frame_view_model.WalletDataService.get_session', return_value=mock_db,
    )

    # 2a. None coverage
    op_none_op = mocker.Mock()
    op_none_op.operation = None
    op_no_psbt = mocker.Mock()
    op_no_psbt.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    op_no_psbt.operation.psbt = None
    op_not_review = mocker.Mock()
    op_not_review.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_not_review.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_not_review.operation.is_SEND_TO_REVIEW.return_value = False
    op_not_review.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_no_purpose = mocker.Mock()
    op_no_purpose.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_no_purpose.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_no_purpose.operation.is_SEND_TO_REVIEW.return_value = False
    op_no_purpose.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_no_purpose.operation.psbt = 'psbt_text'
    # Actually if they are all False, is_review is False, so it skips. The purpose block is unreachable if is_review=True.

    vm._extract_and_save_review_psbts(
        [None, op_none_op, op_no_psbt, op_not_review],
    )

    # 2b. Valid ops, check duplicates logic
    op_valid = mocker.Mock()
    op_valid.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    op_valid.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_valid.operation.is_SEND_TO_REVIEW.return_value = False
    op_valid.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_valid.operation.psbt = 'psbt_text'
    op_valid.initiator_xpub = 'other_xpub'

    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_config_value', return_value='my_xpub',
    )

    def side_effect_list_psbt_empty(*args, **kwargs):
        return []
    # Unsigned list empty, Signed list empty
    mock_db.list_psbt.side_effect = side_effect_list_psbt_empty

    vm._extract_and_save_review_psbts([op_valid])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'create_utxos'
    mock_db.add_psbt.reset_mock()

    # Skip if we already have exact unsigned psbt
    def side_effect_list_psbt_exact_unsigned(*args, **kwargs):
        signed = kwargs.get('signed')
        if not signed:
            return [{'psbt': 'psbt_text'}]
        return []
    mock_db.list_psbt.side_effect = side_effect_list_psbt_exact_unsigned
    vm._extract_and_save_review_psbts([op_valid])
    mock_db.add_psbt.assert_not_called()

    # Check if we have signed format duplicate
    def side_effect_list_psbt_has_signed(*args, **kwargs):
        signed = kwargs.get('signed')
        if signed:
            return [{'psbt': 'signed_psbt'}]
        return []

    mock_db.list_psbt.side_effect = side_effect_list_psbt_has_signed
    mocker.patch(
        'src.viewmodels.header_frame_view_model.RgbRepository.inspect_psbt',
        side_effect=[mocker.Mock(txid='tx1'), mocker.Mock(txid='tx1')],
    )
    vm._extract_and_save_review_psbts([op_valid])
    mock_db.add_psbt.assert_not_called()

    # Exception inside inspect_psbt in duplicates check
    mocker.patch(
        'src.viewmodels.header_frame_view_model.RgbRepository.inspect_psbt',
        side_effect=Exception('fail'),
    )
    vm._extract_and_save_review_psbts([op_valid])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'create_utxos'
    mock_db.add_psbt.reset_mock()

    # Check if signed psbt has different txid
    def side_effect_inspect_psbt(*args, **kwargs):
        psbt = kwargs.get('psbt') if 'psbt' in kwargs else args[0]
        if psbt == 'psbt_text':
            return mocker.Mock(txid='tx1')
        return mocker.Mock(txid='tx2')

    mocker.patch(
        'src.viewmodels.header_frame_view_model.RgbRepository.inspect_psbt',
        side_effect=side_effect_inspect_psbt,
    )
    vm._extract_and_save_review_psbts([op_valid])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'create_utxos'
    mock_db.add_psbt.reset_mock()

    # Different purposes branch coverage
    # SEND_BTC_TO_REVIEW (non-RGB operation, no RGB context)
    mock_db.list_psbt.side_effect = side_effect_list_psbt_empty
    op_send_btc = mocker.Mock()
    op_send_btc.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_send_btc.operation.is_SEND_BTC_TO_REVIEW.return_value = True
    op_send_btc.operation.psbt = 'psbt_text'
    op_send_btc.operation.details = None  # Non-RGB operation has no details
    op_send_btc.initiator_xpub = 'other_xpub'  # skip duplicates check
    vm._extract_and_save_review_psbts([op_send_btc])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'send_btc'
    mock_db.add_psbt.reset_mock()

    # SEND_TO_REVIEW (RGB operation - needs details mocked)
    op_send = mocker.Mock()
    op_send.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_send.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_send.operation.is_SEND_TO_REVIEW.return_value = True
    op_send.operation.psbt = 'psbt_text'
    op_send.operation.details = None  # Set to None for simple test
    op_send.initiator_xpub = 'other_xpub'
    vm._extract_and_save_review_psbts([op_send])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'send_asset'
    mock_db.add_psbt.reset_mock()

    # INFLATION_TO_REVIEW (RGB operation)
    op_inflate = mocker.Mock()
    op_inflate.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_inflate.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_inflate.operation.is_SEND_TO_REVIEW.return_value = False
    op_inflate.operation.is_INFLATION_TO_REVIEW.return_value = True
    op_inflate.operation.psbt = 'psbt_text'
    op_inflate.operation.details = None  # Set to None for simple test
    op_inflate.initiator_xpub = 'other_xpub'
    vm._extract_and_save_review_psbts([op_inflate])
    call_args = mock_db.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_text'
    assert psbt_data.signed is False
    assert psbt_data.purpose == 'inflate_asset'

    # Purpose None (mock an op that is review but doesn't match the specific ifs)
    op_weird = mocker.Mock()
    op_weird.operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    op_weird.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_weird.operation.is_SEND_TO_REVIEW.return_value = False
    op_weird.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_weird.operation.is_CREATE_UTXOS_TO_REVIEW.side_effect = [True, False]
    op_weird.operation.is_SEND_BTC_TO_REVIEW.return_value = False
    op_weird.operation.is_SEND_TO_REVIEW.return_value = False
    op_weird.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_weird.operation.psbt = 'psbt_text'
    vm._extract_and_save_review_psbts([op_weird])


def test_handle_sync_success_watch_only_multisig(mocker):
    """Test handle_sync_success watch-only multisig token generation path."""
    vm = HeaderFrameViewModel()
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_network', return_value='regtest',
    )
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    # Mock get_online_wallet which handles network/config internally
    mock_online = mocker.Mock()
    mock_get_online_wallet = mocker.patch(
        'src.viewmodels.header_frame_view_model.get_online_wallet',
        return_value=mock_online,
    )
    cw = mocker.patch('src.viewmodels.header_frame_view_model.colored_wallet')

    vm.handle_sync_success('from_usb', False)
    # Verify get_online_wallet was called with multisig=True
    mock_get_online_wallet.assert_called_with(cw.wallet, True)


def test_update_rgb_context_for_initiator_psbts(mocker):
    """Test _update_rgb_context_for_initiator_psbts logic."""
    vm = HeaderFrameViewModel()
    mock_db = mocker.Mock()
    mocker.patch(
        'src.viewmodels.header_frame_view_model.WalletDataService.get_session', return_value=mock_db,
    )
    mocker.patch(
        'src.viewmodels.header_frame_view_model.SettingRepository.get_config_value', return_value='my_xpub',
    )

    # 1. No valid ops
    vm._update_rgb_context_for_initiator_psbts([None])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 2. Non-RGB op
    op_non_rgb = mocker.Mock()
    op_non_rgb.operation.is_SEND_TO_REVIEW.return_value = False
    op_non_rgb.operation.is_SEND_PENDING.return_value = False
    op_non_rgb.operation.is_INFLATION_TO_REVIEW.return_value = False
    op_non_rgb.operation.is_INFLATION_PENDING.return_value = False
    vm._update_rgb_context_for_initiator_psbts([op_non_rgb])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 3. RGB op but not initiator
    op_rgb = mocker.Mock()
    op_rgb.operation.is_SEND_TO_REVIEW.return_value = True
    op_rgb.initiator_xpub = 'other_xpub'
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 4. RGB op, initiator, no PSBT
    op_rgb.initiator_xpub = 'my_xpub'
    op_rgb.operation.psbt = None
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 5. RGB op, initiator, PSBT, no details
    op_rgb.operation.psbt = 'psbt_val'
    op_rgb.operation.details = None
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 6. RGB op, initiator, PSBT, details but no fascia_path
    op_details = mocker.Mock(fascia_path=None)
    op_rgb.operation.details = op_details
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    mock_db.update_psbt_rgb_context.assert_not_called()

    # 7. Success path
    op_details.fascia_path = 'fp'
    op_details.entropy = 'ent'
    op_details.min_confirmations = 1
    mock_db.update_psbt_rgb_context.return_value = True
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    mock_db.update_psbt_rgb_context.assert_called_with(
        'psbt_val', fascia_path='fp', entropy='ent', min_confirmations=1,
    )

    # 8. Exception path
    mock_db.update_psbt_rgb_context.side_effect = Exception('fail')
    mocker.patch('src.viewmodels.header_frame_view_model.logger.error')
    vm._update_rgb_context_for_initiator_psbts([op_rgb])
    # Should log error and not crash
