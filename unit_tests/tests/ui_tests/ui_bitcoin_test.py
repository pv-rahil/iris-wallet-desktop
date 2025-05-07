"""Unit test for Bitcoin UI widget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions.
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget
from rgb_lib import TransactionType

from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.views.ui_bitcoin import BtcWidget


@pytest.fixture
def mock_bitcoin_widget_view_model():
    """Fixture to create a MainViewModel instance with mocked responses."""
    mock_view_model = MagicMock()
    mock_view_model.bitcoin_view_model = MagicMock()
    mock_view_model.page_navigation = MagicMock()
    return mock_view_model


@pytest.fixture
def bitcoin_widget(qtbot, mock_bitcoin_widget_view_model):
    """Fixture to create the BtcWidget instance and add it to qtbot."""
    widget = BtcWidget(mock_bitcoin_widget_view_model)
    qtbot.addWidget(widget)
    # Ensure the main window is set for ToastManager to avoid ValueError
    return widget


def test_initial_ui_elements(bitcoin_widget):
    """Test initial UI elements for correct text."""
    assert bitcoin_widget.bitcoin_title.text() == 'bitcoin (regtest)'
    assert bitcoin_widget.transactions.text() == 'transfers'
    assert bitcoin_widget.balance_value.text() == 'total_balance'
    assert bitcoin_widget.bitcoin_balance.text() == 'SAT'
    assert bitcoin_widget.receive_asset_btn.text() == 'receive_assets'
    assert bitcoin_widget.send_asset_btn.text() == 'send_assets'


def test_retranslate_ui(bitcoin_widget):
    """Test that UI elements are correctly updated when network changes."""
    bitcoin_widget.network = 'testnet'
    bitcoin_widget.retranslate_ui()
    assert bitcoin_widget.bitcoin_title.text() == 'bitcoin (testnet)'


def test_handle_asset_frame_click(bitcoin_widget):
    """Test handling of asset frame click event."""
    signal_value = MagicMock()

    bitcoin_widget.handle_asset_frame_click(signal_value)

    bitcoin_widget._view_model.page_navigation.bitcoin_transaction_detail_page.assert_called_once_with(
        params=signal_value,
    )


def test_refresh_bitcoin_page(bitcoin_widget):
    """Test refreshing the Bitcoin page."""
    bitcoin_widget.refresh_bitcoin_page()

    bitcoin_widget._view_model.bitcoin_view_model.on_hard_refresh.assert_called_once()


def test_fungible_page_navigation(bitcoin_widget):
    """Test navigation to the fungible asset page."""
    bitcoin_widget.fungible_page_navigation()

    bitcoin_widget._view_model.page_navigation.fungibles_asset_page.assert_called_once()


def test_receive_asset(bitcoin_widget):
    """Test handling of the receive asset button click."""
    bitcoin_widget.receive_asset()

    bitcoin_widget._view_model.bitcoin_view_model.on_receive_bitcoin_click.assert_called_once()


def test_send_bitcoin(bitcoin_widget):
    """Test handling of the send Bitcoin button click."""
    bitcoin_widget.send_bitcoin()

    bitcoin_widget._view_model.bitcoin_view_model.on_send_bitcoin_click.assert_called_once()


def test_select_receive_transfer_type(bitcoin_widget):
    """Test selection of the receive transfer type."""
    bitcoin_widget.select_receive_transfer_type()

    bitcoin_widget._view_model.bitcoin_view_model.on_receive_bitcoin_click.assert_called_once()


def test_select_send_transfer_type(bitcoin_widget):
    """Test selection of the send transfer type."""
    bitcoin_widget.select_send_transfer_type()

    bitcoin_widget._view_model.bitcoin_view_model.on_send_bitcoin_click.assert_called_once()


def test_set_transaction_detail_frame(bitcoin_widget):
    """Test setting up the transaction detail frame in the UI."""
    # Create mock transaction data
    mock_transaction = MagicMock()
    mock_transaction.txid = '123'
    mock_transaction.amount = '1.5'
    mock_transaction.confirmation_time.timestamp = 1234567890
    mock_transaction.transaction_status = TransactionStatusEnumModel.WAITING_CONFIRMATIONS
    mock_transaction.transfer_status = TransferStatusEnumModel.SEND
    mock_transaction.transaction_type = TransactionType.USER

    # Create mock view model with transactions
    mock_btc_view_model = MagicMock()
    mock_btc_view_model.transaction = [mock_transaction]
    bitcoin_widget._view_model.bitcoin_view_model = mock_btc_view_model

    # Mock the grid layout and its methods
    bitcoin_widget.btc_grid_layout_20 = MagicMock()
    bitcoin_widget.btc_grid_layout_20.count.return_value = 0

    # Mock the scroll area widget contents
    bitcoin_widget.btc_scroll_area_widget_contents = QWidget()

    # Mock the transactions widget and its click frame
    mock_click_frame = MagicMock()
    bitcoin_widget.transactions = MagicMock()
    bitcoin_widget.transactions.click_frame = mock_click_frame

    # Call the method to test
    bitcoin_widget.set_transaction_detail_frame()

    # Verify transactions widget is shown
    bitcoin_widget.transactions.show.assert_called_once()

    # Verify transaction detail frame was created and added to layout
    assert bitcoin_widget.btc_grid_layout_20.addWidget.call_count == 1

    # Test with no transactions
    mock_btc_view_model.transaction = []
    bitcoin_widget.set_transaction_detail_frame()

    # Verify transactions widget is hidden
    bitcoin_widget.transactions.hide.assert_called_once()

    assert bitcoin_widget.btc_grid_layout_20.addWidget.call_count == 2

    bitcoin_widget.btc_grid_layout_20.addItem.assert_called_once()


def test_set_bitcoin_balance(bitcoin_widget):
    """Test setting the Bitcoin balance displayed in the UI."""
    # Create a mock for the bitcoin view model
    mock_btc_view_model = MagicMock()
    mock_btc_view_model.total_bitcoin_balance_with_suffix = '1.23 BTC'
    mock_btc_view_model.spendable_bitcoin_balance_with_suffix = '0.45 BTC'
    bitcoin_widget._view_model.bitcoin_view_model = mock_btc_view_model

    # Call the method to set the balances
    bitcoin_widget.set_bitcoin_balance()

    # Trigger UI updates
    bitcoin_widget.repaint()
    bitcoin_widget.update()

    assert bitcoin_widget.bitcoin_balance.text() == '1.23 BTC'

    assert bitcoin_widget.spendable_balance_value.text() == '0.45 BTC'


def test_hide_loading_screen(bitcoin_widget):
    """Test the hide_loading_screen method to ensure it stops the loading screen and enables buttons."""

    # Simulate the loading screen being active
    bitcoin_widget._BtcWidget__loading_translucent_screen = MagicMock()
    bitcoin_widget.render_timer = MagicMock()
    bitcoin_widget.refresh_button = MagicMock()
    bitcoin_widget.send_asset_btn = MagicMock()
    bitcoin_widget.receive_asset_btn = MagicMock()

    # Call the method to test
    bitcoin_widget.hide_loading_screen()

    # Assert that the loading screen and timer are stopped
    bitcoin_widget._BtcWidget__loading_translucent_screen.stop.assert_called_once()
    bitcoin_widget.render_timer.stop.assert_called_once()

    # Assert that the buttons are enabled
    bitcoin_widget.refresh_button.setDisabled.assert_called_once_with(False)
    bitcoin_widget.send_asset_btn.setDisabled.assert_called_once_with(False)
    bitcoin_widget.receive_asset_btn.setDisabled.assert_called_once_with(False)
