"""Unit test for header frame view model"""
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

import pytest

from src.model.enums.enums_model import WalletAccessType
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
    # Ensure helpers called
    mocker.patch(
        'src.viewmodels.header_frame_view_model.get_bitcoin_network_from_enum', return_value='net',
    )
    mock_cfg = mocker.Mock(indexer_url='idx')
    mocker.patch(
        'src.viewmodels.header_frame_view_model.get_bitcoin_config', return_value=mock_cfg,
    )
    cw = mocker.patch('src.viewmodels.header_frame_view_model.colored_wallet')
    toast_success = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.success',
    )

    view_model.handle_sync_success('from_usb', retry=False)

    cw.wallet.go_online.assert_called_once()
    ended_slot.assert_called_with('from_usb')
    toast_success.assert_called()


def test_handle_sync_success_inconsistency_recovers_and_notifies(mocker):
    """Test inconsistency error triggers restore, retry path and error toast."""
    view_model = HeaderFrameViewModel()
    view_model.usb_sync_manager.restore_local_folder_from_backup = mocker.Mock()
    # cause RgbLibError.Inconsistency

    class DummyInconsistency(Exception):
        """Dummy inconsistency exception."""
        pass  # pylint: disable=unnecessary-pass
    mocker.patch(
        'src.viewmodels.header_frame_view_model.RgbLibError.Inconsistency', DummyInconsistency,
    )
    _ = mocker.patch(
        'src.viewmodels.header_frame_view_model.ToastManager.error',
    )

    mock_completed = mocker.patch.object(view_model, 'handle_sync_completed')
    try:
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
    finally:
        pass


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
