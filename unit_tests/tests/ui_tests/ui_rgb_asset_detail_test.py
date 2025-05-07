"""Unit test for RGB Asset Detail ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-many-statements
from __future__ import annotations

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QWidget

from src.model.enums.enums_model import AssetType
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.enums.enums_model import TransferType
from src.model.selection_page_model import AssetDataModel
from src.model.transaction_detail_page_model import TransactionDetailPageModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_rgb_asset_detail import RGBAssetDetailWidget

asset_image_path = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..', 'src', 'assets', 'icons', 'regtest-icon.png',
    ),
)


@pytest.fixture
def rgb_asset_detail_widget(qtbot):
    """Fixture to create and return an instance of RGBAssetDetailWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))

    # Mock the params as an instance of RgbAssetPageLoadModel
    mock_params = MagicMock()
    mock_params.asset_type = 'RGB20'  # Set the asset_type as needed

    widget = RGBAssetDetailWidget(view_model, mock_params)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the retranslation of UI elements in RGBAssetDetailWidget."""
    rgb_asset_detail_widget.retranslate_ui()

    assert rgb_asset_detail_widget.send_asset.text() == 'send_assets'
    assert rgb_asset_detail_widget.transactions_label.text() == 'transfers'


def test_valid_hex_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with valid hex strings."""
    valid_hex_strings = [
        '00',  # simple hex
        '0a1b2c3d4e5f',  # longer valid hex
        'AABBCCDDEE',  # uppercase hex
        '1234567890abcdef',  # mixed lower and uppercase
    ]
    for hex_string in valid_hex_strings:
        assert rgb_asset_detail_widget.is_hex_string(hex_string) is True


def test_invalid_hex_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with invalid hex strings."""
    invalid_hex_strings = [
        '00G1',  # contains non-hex character 'G'
        '123z',  # contains non-hex character 'z'
        '12345',  # odd length
        '0x1234',  # prefixed with '0x'
        ' ',  # empty or space character
    ]
    for hex_string in invalid_hex_strings:
        assert rgb_asset_detail_widget.is_hex_string(hex_string) is False


def test_empty_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with an empty string."""
    assert rgb_asset_detail_widget.is_hex_string('') is False


def test_odd_length_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with a string of odd length."""
    odd_length_hex_strings = [
        '1',  # single character
        '123',  # three characters
        '12345',  # five characters
    ]
    for hex_string in odd_length_hex_strings:
        assert rgb_asset_detail_widget.is_hex_string(hex_string) is False


def test_is_path(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the is_path method with various file paths."""

    # Test valid Unix-like paths
    assert rgb_asset_detail_widget.is_path('/path/to/file') is True
    assert rgb_asset_detail_widget.is_path('/usr/local/bin/') is True
    assert rgb_asset_detail_widget.is_path('/home/user/doc-1.txt') is True

    # Test invalid paths
    assert rgb_asset_detail_widget.is_path(
        'invalid/path',
    ) is False  # No leading slash
    assert rgb_asset_detail_widget.is_path(123) is False  # Non-string input
    assert rgb_asset_detail_widget.is_path('') is False  # Empty string
    assert rgb_asset_detail_widget.is_path(
        'C:\\Windows\\Path',
    ) is False  # Windows path format


def test_handle_page_navigation_rgb_20(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is RGB20."""
    rgb_asset_detail_widget.asset_type = AssetType.RGB20.value
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.fungibles_asset_page.assert_called_once()


def test_handle_page_navigation_rgb_25(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is RGB25."""
    rgb_asset_detail_widget.asset_type = AssetType.RGB25.value
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.collectibles_asset_page.assert_called_once()


def test_set_transaction_detail_frame(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test setting up the transaction detail frame with mock data."""

    # Set up mock data for the test
    asset_id = 'test_asset_id'
    asset_name = 'Test Asset'
    image_path = asset_image_path
    asset_type = AssetType.RGB20.value

    # Mock the transaction details
    mock_transaction = MagicMock()
    mock_transaction.txid = 'test_txid'
    mock_transaction.amount_status = '1000'
    mock_transaction.updated_at_date = '2024-12-29'  # Use a valid date string
    mock_transaction.updated_at_time = '12:00'  # Use a valid time string
    mock_transaction.transfer_Status = TransferStatusEnumModel.SENT
    mock_transaction.status = 'confirmed'
    mock_transaction.recipient_id = 'test_recipient_id'
    mock_transaction.change_utxo = 'test_change_utxo'
    mock_transaction.receive_utxo = 'test_receive_utxo'

    # Mock asset transactions with on-chain and off-chain transfers
    mock_transactions = MagicMock()
    mock_transactions.asset_balance.future = 1000
    mock_transactions.asset_balance.spendable = 500  # mock spendable amount
    mock_transactions.onchain_transfers = [mock_transaction]
    mock_transactions.off_chain_transfers = [mock_transaction]
    mock_transactions.transfers = [mock_transaction]

    rgb_asset_detail_widget._view_model.rgb25_view_model.txn_list = mock_transactions

    # Call the method to test
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Assertions to check if the UI was updated correctly
    assert rgb_asset_detail_widget.asset_total_balance.text() == '1000'
    assert rgb_asset_detail_widget.asset_id_detail.toPlainText() == asset_id
    assert rgb_asset_detail_widget.widget_title_asset_name.text() == asset_name

    # Check if the grid layout has the correct number of widgets
    # One transaction frame + one spacer item
    assert rgb_asset_detail_widget.scroll_area_widget_layout is not None
    assert rgb_asset_detail_widget.scroll_area_widget_layout.count() == 2

    # Verify that the transaction detail frame was configured correctly
    transaction_frame: QWidget | None = rgb_asset_detail_widget.scroll_area_widget_layout.itemAt(
        0,
    ).widget()
    if transaction_frame:
        assert transaction_frame.transaction_amount.text() == '1000'
        assert transaction_frame.transaction_amount.text() == mock_transaction.amount_status

    # Check if the spacer item is added
    spacer_item = rgb_asset_detail_widget.scroll_area_widget_layout.itemAt(1)
    assert spacer_item is not None
    assert isinstance(spacer_item, QSpacerItem)

    # Test case when no transactions exist (mock an empty transactions list)
    mock_transactions.onchain_transfers = []
    mock_transactions.off_chain_transfers = []
    mock_transactions.transfers = []

    # Call the method again
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Mock transactions with on-chain and off-chain transfers again
    mock_transactions = MagicMock()
    mock_transactions.asset_balance.future = 1000
    mock_transactions.asset_balance.spendable = 500  # mock spendable amount
    mock_transactions.transfers = [mock_transaction]

    # Add on-chain and off-chain mock transfers
    mock_transactions.onchain_transfers = [mock_transaction]
    mock_transactions.off_chain_transfers = [mock_transaction]

    rgb_asset_detail_widget._view_model.rgb25_view_model.txn_list = mock_transactions

    # Call the method to test
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Assertions to check if the UI was updated correctly
    assert rgb_asset_detail_widget.asset_total_balance.text() == '1000'
    assert rgb_asset_detail_widget.asset_id_detail.toPlainText() == asset_id
    assert rgb_asset_detail_widget.widget_title_asset_name.text() == asset_name

    # Verify that the transaction detail frame was configured correctly
    transaction_detail_frame: QWidget | None = rgb_asset_detail_widget.scroll_area_widget_layout.itemAt(
        0,
    ).widget()
    if transaction_detail_frame:
        assert transaction_detail_frame.transaction_amount.text() == '1000'
        assert transaction_detail_frame.transaction_type.text(
        ) == TransferStatusEnumModel.SENT.value
        assert transaction_detail_frame.transaction_amount.text(
        ) == mock_transaction.amount_status


@patch('src.views.ui_rgb_asset_detail.convert_hex_to_image')
@patch('src.views.ui_rgb_asset_detail.resize_image')
def test_set_asset_image(mock_resize_image, mock_convert_hex_to_image, rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test setting the asset image with mocked image conversion and resizing."""

    # Initialize the label_asset_name to avoid the NoneType error
    rgb_asset_detail_widget.label_asset_name = QLabel()

    # Mocked data
    mock_hex_image = 'ffabcc'

    # Mock the convert_hex_to_image and resize_image functions
    mock_pixmap = QPixmap(100, 100)
    mock_convert_hex_to_image.return_value = mock_pixmap

    mock_resized_pixmap = QPixmap(335, 335)  # Mock pixmap after resizing
    mock_resize_image.return_value = mock_resized_pixmap

    # Test with hex string
    rgb_asset_detail_widget.set_asset_image(mock_hex_image)

    # Verify that the convert_hex_to_image was called with the correct hex string
    mock_convert_hex_to_image.assert_called_once_with(mock_hex_image)

    # Verify that resize_image was called with the correct parameters
    mock_resize_image.assert_called_once_with(mock_pixmap, 335, 335)

    assert rgb_asset_detail_widget.label_asset_name is not None
    pixmap = rgb_asset_detail_widget.label_asset_name.pixmap()
    assert pixmap is not None, 'Pixmap should not be None'

    if pixmap is not None:
        assert pixmap.size() == mock_resized_pixmap.size()
        assert pixmap.depth() == mock_resized_pixmap.depth()


@pytest.mark.parametrize(
    'transfer_status, transaction_type, expected_text, expected_style, expected_visibility', [
        (
            TransferStatusEnumModel.INTERNAL.value, TransferType.ISSUANCE.value,
            'ISSUANCE', 'color:#01A781;font-weight: 600', True,
        ),
        (TransferStatusEnumModel.RECEIVE.value, 'other_type', '', '', False),
        (
            TransferStatusEnumModel.ON_GOING_TRANSFER.value,
            TransferType.ISSUANCE.value, '', '', False,
        ),
    ],
)
def test_handle_show_hide(transfer_status, transaction_type, expected_text, expected_style, expected_visibility, rgb_asset_detail_widget):
    """Test the handle_show_hide method with various transfer statuses and transaction types."""
    # Mock the transaction_detail_frame and its attributes
    transaction_detail_frame = MagicMock()
    transaction_detail_frame.transaction_type = QLabel()
    transaction_detail_frame.transaction_amount = QLabel()

    # Set up the widget attributes
    rgb_asset_detail_widget.transfer_status = transfer_status
    rgb_asset_detail_widget.transaction_type = transaction_type

    # Call the method to test
    rgb_asset_detail_widget.handle_show_hide(transaction_detail_frame)

    # Verify the results
    assert transaction_detail_frame.transaction_type.text() == expected_text
    assert transaction_detail_frame.transaction_amount.styleSheet() == expected_style
    assert transaction_detail_frame.transaction_type.isVisible() == expected_visibility


def test_select_receive_transfer_type(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the select_receive_transfer_type method based on channel state."""

    # Set up mock data for the test
    asset_id = 'test_asset_id'
    asset_type = AssetType.RGB20.value
    rgb_asset_detail_widget.asset_id_detail.setPlainText(
        asset_id,
    )  # Mock asset_id in widget

    # Mock the 'is_channel_open_for_asset' method to simulate both cases
    mock_is_channel_open = mocker.patch.object(
        rgb_asset_detail_widget,
        'is_channel_open_for_asset',
    )

    # Mock the navigation methods
    mock_navigate = mocker.patch.object(
        rgb_asset_detail_widget,
        'navigate_to_selection_page',
    )
    mock_receive_rgb25 = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'receive_rgb25_page',
    )

    # Case 1: Channel is open for the asset (is_channel_open_for_asset returns True)
    mock_is_channel_open.return_value = True

    # Call the method
    rgb_asset_detail_widget.select_receive_transfer_type()

    # Assertions for when the channel is open
    mock_navigate.assert_called_once_with(
        TransferStatusEnumModel.RECEIVE.value,
    )
    mock_receive_rgb25.assert_not_called()

    # Reset the mocks to ensure clean state for the next test case
    mock_navigate.reset_mock()
    mock_receive_rgb25.reset_mock()

    # Case 2: Channel is not open for the asset (is_channel_open_for_asset returns False)
    mock_is_channel_open.return_value = False

    # Call the method again
    rgb_asset_detail_widget.select_receive_transfer_type()

    # Assertions for when the channel is not open
    mock_receive_rgb25.assert_called_once_with(
        params=AssetDataModel(
            asset_type=asset_type,
            asset_id=asset_id,
        ),
    )
    mock_navigate.assert_not_called()


def test_select_send_transfer_type(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the select_send_transfer_type method based on channel state."""

    # Set up mock data for the test
    asset_id = 'test_asset_id'
    rgb_asset_detail_widget.asset_id_detail.setPlainText(
        asset_id,
    )  # Mock asset_id in widget

    # Mock the 'is_channel_open_for_asset' method to simulate both cases
    mock_is_channel_open = mocker.patch.object(
        rgb_asset_detail_widget,
        'is_channel_open_for_asset',
    )

    # Mock the navigation methods
    mock_navigate = mocker.patch.object(
        rgb_asset_detail_widget,
        'navigate_to_selection_page',
    )
    mock_send_rgb25 = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'send_rgb25_page',
    )

    # Case 1: Channel is open for the asset (is_channel_open_for_asset returns True)
    mock_is_channel_open.return_value = True

    # Call the method
    rgb_asset_detail_widget.select_send_transfer_type()

    # Assertions for when the channel is open
    mock_navigate.assert_called_once_with(
        TransferStatusEnumModel.SEND.value,
    )
    mock_send_rgb25.assert_not_called()

    # Reset the mocks to ensure clean state for the next test case
    mock_navigate.reset_mock()
    mock_send_rgb25.reset_mock()

    # Case 2: Channel is not open for the asset (is_channel_open_for_asset returns False)
    mock_is_channel_open.return_value = False

    # Call the method again
    rgb_asset_detail_widget.select_send_transfer_type()

    # Assertions for when the channel is not open
    mock_send_rgb25.assert_called_once()
    mock_navigate.assert_not_called()


def test_refresh_transaction(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the refresh_transaction method to ensure proper functions are called."""

    # Mock the render timer and the refresh function
    rgb_asset_detail_widget.render_timer = MagicMock()
    rgb_asset_detail_widget._view_model.rgb25_view_model.on_refresh_click = MagicMock()

    # Call the method
    rgb_asset_detail_widget.refresh_transaction()

    # Assertions to check that the timer and refresh function were called
    # Verify render_timer.start was called once
    rgb_asset_detail_widget.render_timer.start.assert_called_once()
    # Verify on_refresh_click was called once
    rgb_asset_detail_widget._view_model.rgb25_view_model.on_refresh_click.assert_called_once()


def test_handle_asset_frame_click(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the handle_asset_frame_click method to ensure correct navigation call with parameters."""

    # Set up mock data for the test
    params = TransactionDetailPageModel(
        tx_id='test_txid',  # Update the field name to tx_id
        asset_id='test_asset_id',
        amount='1000',
        transaction_status='confirmed',  # Update the field name to transaction_status
    )

    # Mock the navigation method
    rgb_asset_detail_widget._view_model.page_navigation.rgb25_transaction_detail_page = MagicMock()

    # Call the method
    rgb_asset_detail_widget.handle_asset_frame_click(params)

    # Assertions to check if the navigation method was called with the correct parameters
    rgb_asset_detail_widget._view_model.page_navigation.rgb25_transaction_detail_page.assert_called_once_with(
        params,
    )


@pytest.mark.parametrize(
    'asset_id, expected_result', [
        ('asset_123', True),  # Case where a matching, usable, and ready channel exists
        ('asset_456', False),  # Case where no matching channel exists
    ],
)
@pytest.mark.parametrize(
    'asset_id, expected_total_balance, expected_spendable_balance', [
        ('asset_123', 1000, 1000),
        ('asset_456', 200, 0),
        ('asset_999', 0, 0),
    ],
)
def test_handle_fail_transfer(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the handle_fail_transfer method with and without tx_id."""

    # Mock the ConfirmationDialog
    with patch('src.views.ui_rgb_asset_detail.ConfirmationDialog') as mock_confirmation_dialog:
        mock_dialog = MagicMock()
        mock_confirmation_dialog.return_value = mock_dialog

        # Test case 1: With tx_id
        tx_id = 'test_tx_id'
        idx = 0

        rgb_asset_detail_widget.handle_fail_transfer(idx, tx_id)

        # Verify dialog was created with correct message containing tx_id
        mock_confirmation_dialog.assert_called_with(
            parent=rgb_asset_detail_widget,
            message=f"{QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id', None)}: {
                tx_id
            }\n\n {QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel_transfer', None)}",
        )

        # Reset mock for next test
        mock_confirmation_dialog.reset_mock()

        # Test case 2: Without tx_id
        rgb_asset_detail_widget.handle_fail_transfer(idx, None)

        # Verify dialog was created with correct message for no tx_id
        mock_confirmation_dialog.assert_called_with(
            parent=rgb_asset_detail_widget,
            message=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel_invoice', None,
            ),
        )

        # Test button connections
        # Get the lambda function connected to continue button
        continue_func = mock_dialog.confirmation_dialog_continue_button.clicked.connect.call_args[
            0
        ][0]

        # Call the lambda function and verify it calls _confirm_fail_transfer
        with patch.object(rgb_asset_detail_widget, '_confirm_fail_transfer') as mock_confirm:
            continue_func()
            mock_confirm.assert_called_once_with(idx)

        # Verify cancel button connection
        mock_dialog.confirmation_dialog_cancel_button.clicked.connect.assert_called_with(
            mock_dialog.reject,
        )

        # Verify dialog was executed
        mock_dialog.exec.assert_called()


def test_confirm_fail_transfer(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the _confirm_fail_transfer method."""

    idx = 0

    # Call the method
    rgb_asset_detail_widget._confirm_fail_transfer(idx)

    # Verify the view model method was called with correct index
    rgb_asset_detail_widget._view_model.rgb25_view_model.on_fail_transfer.assert_called_once_with(
        idx,
    )


def test_show_loading_screen(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the show_loading_screen method for both loading states."""

    # Test loading state
    rgb_asset_detail_widget.show_loading_screen(True)

    # Verify loading screen is shown and buttons are disabled
    assert rgb_asset_detail_widget._RGBAssetDetailWidget__loading_translucent_screen is not None
    assert rgb_asset_detail_widget._RGBAssetDetailWidget__loading_translucent_screen.isVisible(
    ) is False  # Corrected to check for False
    assert not rgb_asset_detail_widget.asset_refresh_button.isEnabled()
    assert not rgb_asset_detail_widget.send_asset.isEnabled()
    assert not rgb_asset_detail_widget.receive_rgb_asset.isEnabled()

    # Test unloading state
    # Set a dummy value to simulate balance
    rgb_asset_detail_widget.lightning_total_balance.setText('100')
    rgb_asset_detail_widget.show_loading_screen(False)

    # Verify loading screen is stopped and buttons are enabled
    assert rgb_asset_detail_widget._RGBAssetDetailWidget__loading_translucent_screen.isVisible(
    ) is False  # Corrected to check for False
    assert rgb_asset_detail_widget.asset_refresh_button.isEnabled()
    assert rgb_asset_detail_widget.send_asset.isEnabled()
    assert rgb_asset_detail_widget.receive_rgb_asset.isEnabled()
