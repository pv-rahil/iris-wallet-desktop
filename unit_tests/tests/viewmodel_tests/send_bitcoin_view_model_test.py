"""Unit test for send bitcoin view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.btc_model import SendBtcResponseModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_BITCOIN_SENT
from src.viewmodels.send_bitcoin_view_model import SendBitcoinViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def send_bitcoin_view_model(mock_page_navigation):
    """Fixture to create an instance of the SendBitcoinViewModel class."""
    return SendBitcoinViewModel(mock_page_navigation)


@patch('src.data.repository.setting_repository.SettingRepository.native_authentication')
@patch('src.utils.logging.logger.error')
def test_on_success_authentication_btc_send_exception(mock_logger, mock_auth, send_bitcoin_view_model):
    """Test exception handling in authentication callback."""
    # Setup
    mock_auth.side_effect = Exception('Unexpected error')

    with patch('src.views.components.toast.ToastManager.error') as mock_toast:
        # Execute
        send_bitcoin_view_model.on_success_authentication_btc_send()

        # Assert
        mock_toast.assert_called_once_with(
            description=ERROR_SOMETHING_WENT_WRONG,
        )
        mock_logger.assert_called_once()


def test_on_success(send_bitcoin_view_model):
    """Test successful BTC send completion."""
    mock_response = SendBtcResponseModel(tx_id='test_txid')

    # Create a mock slot for the signal
    mock_slot = MagicMock()
    send_bitcoin_view_model.send_button_clicked.connect(mock_slot)

    with patch('src.views.components.toast.ToastManager.success') as mock_toast:
        # Execute
        send_bitcoin_view_model.on_success(mock_response)

        # Assert
        mock_slot.assert_called_once_with(False)
        mock_toast.assert_called_once_with(
            description=INFO_BITCOIN_SENT.format('test_txid'),
        )
        send_bitcoin_view_model._page_navigation.bitcoin_page.assert_called_once()


@patch('src.utils.logging.logger.error')
def test_on_error(mock_logger, send_bitcoin_view_model):
    """Test error handling with both CommonException and generic Exception."""
    # Create a mock slot for the signal
    mock_slot = MagicMock()
    send_bitcoin_view_model.send_button_clicked.connect(mock_slot)

    # Test with CommonException
    with patch('src.views.components.toast.ToastManager.error') as mock_toast:
        custom_error = CommonException('Custom error message')
        send_bitcoin_view_model.on_error(custom_error)
        mock_slot.assert_called_once_with(False)
        mock_toast.assert_called_once_with(description='Custom error message')
        mock_logger.assert_called()

    mock_slot.reset_mock()
    mock_logger.reset_mock()

    # Test with generic Exception
    with patch('src.views.components.toast.ToastManager.error') as mock_toast:
        generic_error = Exception('Generic error')
        send_bitcoin_view_model.on_error(generic_error)
        mock_slot.assert_called_once_with(False)
        mock_toast.assert_called_once_with(
            description=ERROR_SOMETHING_WENT_WRONG,
        )
        mock_logger.assert_called()


def test_on_send_click(send_bitcoin_view_model):
    """Test on_send_click method behavior with mocked dependencies"""
    # Setup test data
    test_address = 'test_address'
    test_amount = 1000
    test_fee_rate = 2

    # Mock the signal
    mock_signal = Mock()
    send_bitcoin_view_model.send_button_clicked = mock_signal

    # Mock run_in_thread
    send_bitcoin_view_model.run_in_thread = Mock()

    # Execute
    send_bitcoin_view_model.on_send_click(
        test_address, test_amount, test_fee_rate,
    )

    # Assert values were stored
    assert send_bitcoin_view_model.address == test_address
    assert send_bitcoin_view_model.amount == test_amount
    assert send_bitcoin_view_model.fee_rate == test_fee_rate

    # Assert signal was emitted with True
    mock_signal.emit.assert_called_once_with(True)

    # Assert run_in_thread was called with correct parameters
    send_bitcoin_view_model.run_in_thread.assert_called_once()


def test_on_success_hardware_wallet_emits_hw_dialog(send_bitcoin_view_model, mocker):
    """When using a hardware wallet, on_success emits hw dialog update with SUCCESS."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    hw_slot = MagicMock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    resp = SendBtcResponseModel(tx_id='abc')

    send_bitcoin_view_model.on_success(resp)

    assert hw_slot.call_count == 1


def test_on_error_hardware_wallet_emits_error(send_bitcoin_view_model, mocker):
    """on_error should emit hw_dialog_update with PsbtStatus.ERROR for hardware wallets."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    hw_slot = MagicMock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)

    send_bitcoin_view_model.on_error(Exception('boom'))

    assert hw_slot.call_count == 1


def test_send_btc_begin_hw_online_emits_signing_and_calls_repo(send_bitcoin_view_model, mocker):
    """send_btc_begin should emit signing state when HW+online and schedule repo call."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    send_bitcoin_view_model.run_in_thread = Mock()
    hw_slot = MagicMock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)

    send_bitcoin_view_model.send_btc_begin('addr', 1, 2)

    assert hw_slot.call_count == 1
    send_bitcoin_view_model.run_in_thread.assert_called_once()


def test_on_psbt_created_watch_only_emits_unsigned(send_bitcoin_view_model, mocker):
    """If WATCH_ONLY, unsigned_psbt signal should be emitted directly."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    slot = MagicMock()
    send_bitcoin_view_model.unsigned_psbt.connect(slot)

    send_bitcoin_view_model.on_psbt_created('psbt')

    slot.assert_called_once_with('psbt')


def test_on_psbt_created_non_watch_runs_sign_finalize(send_bitcoin_view_model, mocker):
    """If not WATCH_ONLY, run sign_and_finalize in thread."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_access_type',
        return_value=mocker.Mock(name='NOT_WATCH_ONLY'),
    )
    send_bitcoin_view_model.run_in_thread = Mock()

    send_bitcoin_view_model.on_psbt_created('psbt')

    send_bitcoin_view_model.run_in_thread.assert_called_once()


def test_on_psbt_signed_and_finalized_hw_online_triggers_broadcast(send_bitcoin_view_model, mocker):
    """After finalize, for HW+online, emit broadcasting and call send_btc_end."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    hw_slot = MagicMock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    send_bitcoin_view_model.send_btc_end = Mock()

    send_bitcoin_view_model.on_psbt_signed_and_finalized('final')

    assert hw_slot.call_count == 1
    send_bitcoin_view_model.send_btc_end.assert_called_once_with('final')


def test_send_end_runs_with_request(send_bitcoin_view_model, mocker):
    """send_btc_end should start background broadcast with correct request."""
    send_bitcoin_view_model.run_in_thread = Mock()
    send_bitcoin_view_model.send_btc_end('signed_psbt', skip_sync=True)
    send_bitcoin_view_model.run_in_thread.assert_called_once()


def test_cancel_operation_stops_hardware_client(send_bitcoin_view_model, mocker):
    """Cancel should emit False and stop hardware client."""
    slot = MagicMock()
    send_bitcoin_view_model.send_button_clicked.connect(slot)
    stop_client = mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.hardware_client_store.stop_client',
    )

    send_bitcoin_view_model.cancel_operation()

    slot.assert_called_once_with(False)
    stop_client.assert_called_once_with()
