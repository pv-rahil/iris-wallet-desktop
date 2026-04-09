"""Unit test for send bitcoin view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import SendBtcResponseModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
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
    # Setup - mock run_in_thread to raise exception
    with patch.object(send_bitcoin_view_model, 'run_in_thread') as mock_run:
        mock_run.side_effect = Exception('Unexpected error')

        with patch('src.views.components.toast.ToastManager.error') as mock_toast:
            # Execute - call with success=True
            send_bitcoin_view_model.on_success_authentication_btc_send(True)

            # Assert
            mock_toast.assert_called_once_with(
                description=ERROR_SOMETHING_WENT_WRONG,
            )
            mock_logger.assert_called_once()


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_authentication_btc_send_auth_failed(mock_toast, send_bitcoin_view_model):
    """Test authentication cancelled callback."""
    mock_slot = MagicMock()
    send_bitcoin_view_model.send_button_clicked.connect(mock_slot)

    send_bitcoin_view_model.on_success_authentication_btc_send(False)

    mock_slot.assert_called_once_with(False)
    mock_toast.assert_called_once_with(
        description=ERROR_AUTHENTICATION_CANCELLED,
    )


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


def test_on_success_hw_storage(send_bitcoin_view_model, mocker):
    """Test successful BTC send with HW storage emits hw_dialog_update."""
    send_bitcoin_view_model._page_navigation = mocker.Mock()
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch('src.viewmodels.send_bitcoin_view_model.ToastManager.success')
    slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(slot)

    send_bitcoin_view_model.on_success(SendBtcResponseModel(tx_id='t1'))
    slot.assert_called_once()


@patch('src.utils.logging.logger.error')
def test_on_error(mock_logger, send_bitcoin_view_model):
    """Test error handling with both CommonException and generic Exception."""
    # Create a mock slot for the signal
    mock_slot = MagicMock()
    send_bitcoin_view_model.send_button_clicked.connect(mock_slot)

    # Mock handle_viewmodel_error which is called by on_error
    with patch('src.viewmodels.send_bitcoin_view_model.handle_viewmodel_error') as mock_handle:
        # Test with CommonException
        custom_error = CommonException('Custom error message')
        send_bitcoin_view_model.on_error(custom_error)
        mock_slot.assert_called_once_with(False)
        mock_handle.assert_called_once_with(
            send_bitcoin_view_model, custom_error,
        )
        mock_logger.assert_called()

    mock_slot.reset_mock()
    mock_logger.reset_mock()

    with patch('src.viewmodels.send_bitcoin_view_model.handle_viewmodel_error') as mock_handle:
        # Test with generic Exception
        generic_error = Exception('Generic error')
        send_bitcoin_view_model.on_error(generic_error)
        mock_slot.assert_called_once_with(False)
        mock_handle.assert_called_once_with(
            send_bitcoin_view_model, generic_error,
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


@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type')
def test_on_send_click_multisig_on_device_requires_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, send_bitcoin_view_model,
):
    """Test that multisig on-device wallet requires native auth for send bitcoin."""
    mock_get_signature.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(send_bitcoin_view_model, 'run_in_thread') as mock_run:
        send_bitcoin_view_model.on_send_click('addr', 100, 2)

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type')
def test_on_send_click_standard_wallet_no_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, send_bitcoin_view_model,
):
    """Test that standard online on-device wallet DOES require native auth."""
    mock_get_signature.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(send_bitcoin_view_model, 'run_in_thread') as mock_run:
        send_bitcoin_view_model.on_send_click('addr', 100, 2)

        # Verify native auth was passed to run_in_thread (standard online on-device DOES require auth)
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type')
def test_on_send_click_hardware_wallet_no_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, send_bitcoin_view_model,
):
    """Test that hardware wallet does not require native auth for send bitcoin."""
    mock_get_signature.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_key_storage.return_value = KeyStorageType.HARDWARE_WALLET
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(send_bitcoin_view_model, 'run_in_thread') as mock_run:
        send_bitcoin_view_model.on_send_click('addr', 100, 2)

        # Verify send_btc was passed to run_in_thread (no native auth for hardware wallet)
        call_args = mock_run.call_args[0]
        expected_method = BtcRepository.send_btc
        assert call_args[0] is expected_method


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


def test_send_btc_begin_multisig(send_bitcoin_view_model, mocker):
    """send_btc_begin should trigger multisig begin properly."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )

    hw_slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    mock_run = mocker.patch.object(send_bitcoin_view_model, 'run_in_thread')

    send_bitcoin_view_model.send_btc_begin('addr', 1, 2)
    hw_slot.assert_called_once()
    mock_run.assert_called_once()
    assert 'send_btc_init' in str(
        mock_run.call_args[0],
    ) or mock_run.call_args[0][0].__name__ == 'send_btc_init'


def test_on_psbt_creation_success_watch_only_emits_unsigned(send_bitcoin_view_model, mocker):
    """If WATCH_ONLY, unsigned_psbt signal should be emitted directly."""
    # Mock both wallet access type and signature type for test isolation
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.viewmodels.viewmodel_helpers.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    slot = MagicMock()
    send_bitcoin_view_model.unsigned_psbt.connect(slot)

    # Create a mock result object with psbt attribute
    mock_result = MagicMock()
    mock_result.psbt = 'psbt'
    send_bitcoin_view_model.on_psbt_creation_success(mock_result)

    slot.assert_called_once_with('psbt')


def test_on_psbt_creation_success_non_watch_runs_sign_finalize(send_bitcoin_view_model, mocker):
    """If not WATCH_ONLY, run sign_and_finalize in thread."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_access_type',
        return_value=mocker.Mock(name='NOT_WATCH_ONLY'),
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )

    hw_slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    send_bitcoin_view_model.run_in_thread = Mock()

    send_bitcoin_view_model.on_psbt_creation_success('psbt')

    hw_slot.assert_called_once()
    send_bitcoin_view_model.run_in_thread.assert_called_once()


def test_on_psbt_creation_success_multisig(send_bitcoin_view_model, mocker):
    """Test on_psbt_creation_success handles MULTI_SIG logic and hw signals."""
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )

    # Needs a mock response with psbt and operation_idx since it's multisig
    res = mocker.Mock(psbt='psbt1', operation_idx=1)
    hw_slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    mock_run = mocker.patch.object(send_bitcoin_view_model, 'run_in_thread')

    send_bitcoin_view_model.on_psbt_creation_success(res)
    assert send_bitcoin_view_model.operation_idx == 1
    hw_slot.assert_called_once()
    mock_run.assert_called_once()
    assert 'sign_psbt' in str(
        mock_run.call_args[0],
    ) or mock_run.call_args[0][0].__name__ == 'sign_psbt'


def test_on_multisig_psbt_signed(send_bitcoin_view_model, mocker):
    """Test on_multisig_psbt_signed triggers bridge post."""
    send_bitcoin_view_model.operation_idx = 1
    hw_slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    mock_run = mocker.patch.object(send_bitcoin_view_model, 'run_in_thread')

    send_bitcoin_view_model.on_multisig_psbt_signed('signed1')
    hw_slot.assert_called_once()
    mock_run.assert_called_once()
    assert 'respond_to_operation' in str(
        mock_run.call_args[0],
    ) or mock_run.call_args[0][0].__name__ == 'respond_to_operation'


def test_on_success_multisig_post(send_bitcoin_view_model, mocker):
    """Test on_success_multisig_post emits success, toasts, and triggers sync."""
    send_bitcoin_view_model._page_navigation = mocker.Mock()
    hw_slot = mocker.Mock()
    send_bitcoin_view_model.hw_dialog_update.connect(hw_slot)
    mock_toast = mocker.patch(
        'src.viewmodels.send_bitcoin_view_model.ToastManager.success',
    )
    mock_run = mocker.patch.object(send_bitcoin_view_model, 'run_in_thread')

    send_bitcoin_view_model.on_success_multisig_post()
    hw_slot.assert_called_once()
    mock_toast.assert_called_once()
    mock_run.assert_called_once()
    assert 'sync_with_hub' in str(
        mock_run.call_args[0],
    ) or mock_run.call_args[0][0].__name__ == 'sync_with_hub'


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

    send_bitcoin_view_model.on_psbt_signed_and_finalized_success('final')

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
