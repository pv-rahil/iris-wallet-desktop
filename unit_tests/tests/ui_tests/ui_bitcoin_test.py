"""Unit test for Bitcoin UI widget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions.
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.btc_model import Transaction
from src.model.enums.enums_model import AssetType
from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.selection_page_model import SelectionPageModel
from src.views.ui_bitcoin import BtcWidget


@pytest.fixture
def mock_bitcoin_widget_view_model():
    """Fixture to create a MainViewModel instance with mocked responses."""
    mock_view_model = MagicMock()
    mock_view_model.bitcoin_view_model = MagicMock()
    mock_view_model.page_navigation = MagicMock()
    return mock_view_model


@pytest.fixture
def nodeinfo_mock():
    """Fixture to create nodeinfo mock"""
    mock = MagicMock()
    mock.is_ready = MagicMock(return_value=True)
    mock.get_network_name = MagicMock(return_value='Testnet')
    return mock


@pytest.fixture
def bitcoin_widget(qtbot, mock_bitcoin_widget_view_model, nodeinfo_mock):
    """Fixture to create the BtcWidget instance and add it to qtbot."""
    with patch('src.data.service.common_operation_service.CommonOperationRepository.node_info', return_value=nodeinfo_mock):
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


def test_navigate_to_selection_page(bitcoin_widget):
    """Test navigation to the selection page with Bitcoin parameters."""
    params = SelectionPageModel(
        title='Select transfer type',
        logo_1_path=':/assets/on_chain.png',
        logo_1_title='On chain',
        logo_2_path=':/assets/off_chain.png',
        logo_2_title='Lightning',  # Ensure this matches the actual implementation
        asset_id=AssetType.BITCOIN.value,
        callback='BITCOIN',
        # Use the mocked page
        back_page_navigation=bitcoin_widget._view_model.page_navigation.bitcoin_page,
    )

    bitcoin_widget.navigate_to_selection_page('BITCOIN')

    bitcoin_widget._view_model.page_navigation.wallet_method_page.assert_called_once_with(
        params,
    )


def test_select_receive_transfer_type(bitcoin_widget):
    """Test selection of the receive transfer type."""
    bitcoin_widget.select_receive_transfer_type()

    bitcoin_widget._view_model.page_navigation.wallet_method_page.assert_called_once_with(
        SelectionPageModel(
            title='Select transfer type',
            logo_1_path=':/assets/on_chain.png',
            logo_1_title='On chain',
            logo_2_path=':/assets/off_chain.png',
            logo_2_title='Lightning',
            asset_id=AssetType.BITCOIN.value,
            callback='receive_btc',
            back_page_navigation=bitcoin_widget._view_model.page_navigation.bitcoin_page,
        ),
    )


def test_select_send_transfer_type(bitcoin_widget):
    """Test selection of the send transfer type."""
    bitcoin_widget.select_send_transfer_type()

    bitcoin_widget._view_model.page_navigation.wallet_method_page.assert_called_once_with(
        SelectionPageModel(
            title='Select transfer type',
            logo_1_path=':/assets/on_chain.png',
            logo_1_title='On chain',
            logo_2_path=':/assets/off_chain.png',
            logo_2_title='Lightning',
            asset_id=AssetType.BITCOIN.value,
            callback='send_btc',
            back_page_navigation=bitcoin_widget._view_model.page_navigation.bitcoin_page,
        ),
    )


def test_set_transaction_detail_frame(bitcoin_widget):
    """Test setting up the transaction detail frame with mock transactions."""
    transaction_list = [
        Transaction(
            transaction_type='CREATEUTXOS',
            txid='tx1',
            received=1000,
            sent=0,
            fee=10,
            amount='0.01',
            transaction_status=TransactionStatusEnumModel.SETTLED.value,  # Ensure valid enum value
            transfer_status=TransferStatusEnumModel.RECEIVED.value,  # Ensure valid enum value
            confirmation_normal_time='12:34:56',
            confirmation_date='2024-08-30',
            confirmation_time=None,
        ),
        Transaction(
            transaction_type='CREATEUTXOS',
            txid='tx2',
            received=0,
            sent=2000,
            fee=15,
            amount='0.02',
            transaction_status=TransactionStatusEnumModel.SETTLED.value,  # Ensure valid enum value
            transfer_status=TransferStatusEnumModel.SENT.value,  # Ensure valid enum value
            confirmation_normal_time='12:34:56',
            confirmation_date='2024-08-30',
            confirmation_time=None,
        ),
    ]

    bitcoin_widget._view_model.bitcoin_view_model.transaction = transaction_list

    bitcoin_widget.set_transaction_detail_frame()

    bitcoin_widget.repaint()
    bitcoin_widget.update()


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
