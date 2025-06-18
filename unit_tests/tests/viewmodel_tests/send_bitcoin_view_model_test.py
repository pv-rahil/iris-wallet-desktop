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
