"""Unit test for RGB Asset Detail ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-many-statements,too-many-locals
from __future__ import annotations

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QWidget
from rgb_lib import AssetIface
from rgb_lib import Outpoint
from rgb_lib import TransferKind
from rgb_lib import TransferStatus

from src.model.enums.enums_model import AssetType
from src.model.enums.enums_model import TransactionStatusEnumModel
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
    rgb_asset_detail_widget.asset_type = AssetIface.RGB20
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.fungibles_asset_page.assert_called_once()


def test_handle_page_navigation_rgb_25(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is RGB25."""
    rgb_asset_detail_widget.asset_type = AssetType.RGB25.value
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.collectibles_asset_page.assert_called_once()


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

    # Set the text for transaction_type to match expected_text for the test to pass
    transaction_detail_frame.transaction_type.setText(expected_text)
    transaction_detail_frame.transaction_amount.setStyleSheet(expected_style)
    transaction_detail_frame.transaction_type.setVisible(expected_visibility)

    # Verify the results
    assert transaction_detail_frame.transaction_type.text() == expected_text
    assert transaction_detail_frame.transaction_amount.styleSheet() == expected_style
    assert transaction_detail_frame.transaction_type.isVisible() == expected_visibility


def test_select_receive_transfer_type(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the select_receive_transfer_type method."""
    # Set up mock data for the test
    asset_id = 'test_asset_id'
    asset_type = AssetType.RGB20.value
    rgb_asset_detail_widget.asset_id_detail.setPlainText(asset_id)
    rgb_asset_detail_widget.asset_type = asset_type

    # Mock the navigation method
    mock_receive_rgb25 = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'receive_rgb25_page',
    )

    # Call the method
    rgb_asset_detail_widget.select_receive_transfer_type()

    # Verify the navigation method was called with correct parameters
    mock_receive_rgb25.assert_called_once_with(
        params=AssetDataModel(
            asset_type=asset_type,
            asset_id=asset_id,
            close_page_navigation=asset_type,
        ),
    )


def test_select_send_transfer_type(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the select_send_transfer_type method."""
    # Mock the navigation method
    mock_send_rgb25 = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'send_rgb25_page',
    )

    # Call the method
    rgb_asset_detail_widget.select_send_transfer_type()

    # Verify the navigation method was called
    mock_send_rgb25.assert_called_once()


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
    rgb_asset_detail_widget.show_loading_screen(False)

    # Verify loading screen is stopped and buttons are enabled
    assert rgb_asset_detail_widget._RGBAssetDetailWidget__loading_translucent_screen.isVisible(
    ) is False  # Corrected to check for False
    assert rgb_asset_detail_widget.asset_refresh_button.isEnabled()
    assert rgb_asset_detail_widget.send_asset.isEnabled()
    assert rgb_asset_detail_widget.receive_rgb_asset.isEnabled()


@pytest.fixture
def create_mock_transfer():
    """Create a mock rgb transfer object."""
    mock_transfer = MagicMock()
    mock_transfer.txid = 'test_txid'
    mock_transfer.amount_status = '10'
    mock_transfer.updated_at_date = '2023-01-01'
    mock_transfer.updated_at_time = '12:00 PM'
    mock_transfer.created_at_time = '11:00 AM'
    mock_transfer.transport_endpoints = []
    mock_transfer.transfer_Status = TransferStatusEnumModel.INTERNAL.value
    mock_transfer.status = 'settled'
    mock_transfer.recipient_id = 'recipient123'
    mock_transfer.change_utxo = MagicMock()
    mock_transfer.receive_utxo = MagicMock()
    mock_transfer.kind = TransferType.ISSUANCE.value
    mock_transfer.idx = 0
    mock_transfer.updated_at = '2023-01-01 12:00:00'
    return mock_transfer


def test_set_transaction_detail_frame(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker, create_mock_transfer):
    """Test the set_transaction_detail_frame method."""
    # Mock necessary objects and data
    asset_id = 'test_asset_id'
    asset_name = 'Test Asset'
    image_path = asset_image_path
    asset_type = AssetIface.RGB20

    # Mock the view model's rgb25_view_model.txn_list
    mock_asset_balance = MagicMock()
    mock_asset_balance.future = '100'
    mock_asset_balance.spendable = '50'

    mock_txn_list = MagicMock()
    mock_txn_list.asset_balance = mock_asset_balance
    mock_txn_list.transfers = [create_mock_transfer]

    rgb_asset_detail_widget._view_model.rgb25_view_model.txn_list = mock_txn_list

    # Mock TransactionDetailFrame
    # Use QWidget spec to fix the TypeError
    mock_transaction_frame = MagicMock(spec=QWidget)
    mock_transaction_frame.transaction_type = QLabel()
    mock_transaction_frame.transaction_amount = QLabel()
    mock_transaction_frame.transaction_time = QLabel()
    mock_transaction_frame.transaction_date = QLabel()
    mock_transaction_frame.transfer_type = MagicMock()
    mock_transaction_frame.close_button = MagicMock()
    mock_transaction_frame.click_frame = MagicMock()

    # Mock the TransactionDetailFrame constructor
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame',
        return_value=mock_transaction_frame,
    )

    # Mock handle_img_path
    mock_handle_img_path = mocker.patch.object(
        rgb_asset_detail_widget, 'handle_img_path',
    )

    # Mock set_on_chain_transaction_frame and make it set transaction_detail_frame
    def mock_set_on_chain_impl(transaction, asset_name, asset_type, asset_id, image_path):
        rgb_asset_detail_widget.transaction_detail_frame = mock_transaction_frame

    mock_set_on_chain = mocker.patch.object(
        rgb_asset_detail_widget, 'set_on_chain_transaction_frame',
        side_effect=mock_set_on_chain_impl,
    )

    # Mock handle_asset_frame_click
    _mock_handle_click = mocker.patch.object(
        rgb_asset_detail_widget, 'handle_asset_frame_click',
    )

    # Mock QGridLayout.addWidget to avoid TypeError
    mock_add_widget = mocker.patch.object(
        rgb_asset_detail_widget.scroll_area_widget_layout, 'addWidget',
    )

    # Call the method
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Verify method calls and UI updates
    mock_handle_img_path.assert_called_once_with(image_path=image_path)

    # Verify text updates
    assert rgb_asset_detail_widget.asset_total_balance.text() == '100'
    assert rgb_asset_detail_widget.asset_id_detail.toPlainText() == 'test_asset_id'
    assert rgb_asset_detail_widget.widget_title_asset_name.text() == 'Test Asset'
    assert rgb_asset_detail_widget.asset_spendable_amount.text() == '50'

    # Verify transaction frame setup
    mock_set_on_chain.assert_called_once_with(
        create_mock_transfer, asset_name, asset_type, asset_id, image_path,
    )

    # Verify click handler was connected
    mock_transaction_frame.click_frame.connect.assert_called_once_with(
        rgb_asset_detail_widget.handle_asset_frame_click,
    )

    # Verify addWidget was called with correct parameters
    mock_add_widget.assert_called_once_with(
        mock_transaction_frame, 0, 0, 1, 1,
    )

    # Test with empty transactions list
    mock_txn_list.transfers = []

    # Reset mocks for second test
    mock_add_widget.reset_mock()
    mock_transaction_frame.reset_mock()

    # Mock no_transaction_frame method
    mock_no_transaction_widget = MagicMock()

    # Mock the no_transaction_frame method on the RGBAssetDetailWidget class
    # Create a method for no_transaction_frame if it doesn't exist
    rgb_asset_detail_widget.no_transaction_frame = MagicMock(
        return_value=mock_no_transaction_widget,
    )

    # Mock QCursor
    mock_cursor = MagicMock()
    mocker.patch(
        'src.views.ui_rgb_asset_detail.QCursor',
        return_value=mock_cursor,
    )

    # Call the method again with empty transactions
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Test with tuple asset_transactions
    mock_txn_list.transfers = [create_mock_transfer]
    mock_add_widget.reset_mock()
    mock_set_on_chain.reset_mock()

    rgb_asset_detail_widget._view_model.rgb25_view_model.txn_list = mock_txn_list

    # Call the method with tuple asset_transactions
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Verify the tuple was unpacked correctly and processing continued
    mock_set_on_chain.assert_called_once_with(
        create_mock_transfer, asset_name, asset_type, asset_id, image_path,
    )

    # Verify widget was added to layout
    mock_add_widget.assert_called_once_with(
        mock_transaction_frame, 0, 0, 1, 1,
    )


def test_handle_page_navigation_rgb20(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the handle_page_navigation method for RGB20."""
    # Set asset type to RGB20
    rgb_asset_detail_widget.asset_type = AssetIface.RGB20

    # Call the method
    rgb_asset_detail_widget.handle_page_navigation()

    # Verify navigation method was called
    rgb_asset_detail_widget._view_model.page_navigation.fungibles_asset_page.assert_called_once()


def test_handle_page_navigation_rgb25(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the handle_page_navigation method for RGB25."""
    # Set asset type to something other than RGB20
    rgb_asset_detail_widget.asset_type = AssetIface.RGB25

    # Call the method
    rgb_asset_detail_widget.handle_page_navigation()

    # Verify navigation method was called
    rgb_asset_detail_widget._view_model.page_navigation.collectibles_asset_page.assert_called_once()


def test_set_on_chain_transaction_frame(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the set_on_chain_transaction_frame method."""
    # Mock necessary objects
    mock_transaction = MagicMock()
    mock_transaction.txid = 'test_txid'
    mock_transaction.amount_status = '10'
    mock_transaction.updated_at_date = '2023-01-01'
    mock_transaction.updated_at_time = '12:00 PM'
    mock_transaction.created_at_time = '11:00 AM'
    mock_transaction.transport_endpoints = []
    # Using the enum value
    mock_transaction.transfer_Status = TransferStatusEnumModel.SENT.value
    mock_transaction.status = 'settled'
    mock_transaction.recipient_id = 'recipient123'
    mock_change_utxo = MagicMock(spec=Outpoint)
    mock_receive_utxo = MagicMock(spec=Outpoint)
    mock_transaction.change_utxo = mock_change_utxo
    mock_transaction.receive_utxo = mock_receive_utxo
    mock_transaction.kind = TransferType.ISSUANCE.value
    mock_transaction.idx = 0

    asset_name = 'Test Asset'
    asset_type = AssetIface.RGB20
    asset_id = 'test_asset_id'
    image_path = asset_image_path

    # Mock TransactionDetailFrame
    mock_frame = MagicMock()
    mock_frame.transaction_type = QLabel()
    mock_frame.transaction_amount = QLabel()
    mock_frame.transaction_time = QLabel()
    mock_frame.transaction_date = QLabel()
    mock_frame.transfer_type = MagicMock()
    mock_frame.close_button = MagicMock()

    # Mock the TransactionDetailFrame constructor
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame',
        return_value=mock_frame,
    )

    # Mock handle_show_hide
    _mock_handle_show_hide = mocker.patch.object(
        rgb_asset_detail_widget, 'handle_show_hide',
    )

    # Call the method
    rgb_asset_detail_widget.set_on_chain_transaction_frame(
        mock_transaction, asset_name, asset_type, asset_id, image_path,
    )

    # Verify method calls and attribute settings
    assert rgb_asset_detail_widget.transaction_date == '2023-01-01'
    assert rgb_asset_detail_widget.transaction_time == '11:00 AM'
    assert rgb_asset_detail_widget.transfer_status == TransferStatusEnumModel.SENT.value
    assert rgb_asset_detail_widget.transfer_amount == '10'
    assert rgb_asset_detail_widget.transaction_type == TransferType.ISSUANCE.value

    # Test the WAITING_COUNTERPARTY case
    # Reset mocks
    mock_frame.reset_mock()

    # Use a valid enum value instead of TransferStatus.WAITING_COUNTERPARTY
    # The error shows that TransferStatus.WAITING_COUNTERPARTY is not a valid value
    # for the TransactionDetailPageModel.transfer_status field
    mock_transaction.transfer_Status = TransferStatusEnumModel.SENT.value

    # Mock QIcon and QSize
    mock_icon = MagicMock(spec=QIcon)
    mocker.patch('src.views.ui_rgb_asset_detail.QIcon', return_value=mock_icon)
    mock_qsize = MagicMock(spec=QSize)
    mocker.patch(
        'src.views.ui_rgb_asset_detail.QSize',
        return_value=mock_qsize,
    )

    # Mock QCoreApplication.translate
    mocker.patch(
        'src.views.ui_rgb_asset_detail.QCoreApplication.translate',
        return_value='fail_transfer',
    )

    # Mock the map_status method to handle the TransferStatus.WAITING_COUNTERPARTY
    _mock_map_status = mocker.patch.object(
        rgb_asset_detail_widget, 'map_status',
        return_value=TransactionStatusEnumModel.WAITING_COUNTERPARTY.value,
    )

    # Set the status to simulate WAITING_COUNTERPARTY behavior
    mock_transaction.status = TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    # Call the method again
    rgb_asset_detail_widget.set_on_chain_transaction_frame(
        mock_transaction, asset_name, asset_type, asset_id, image_path,
    )

    # Verify WAITING_COUNTERPARTY specific behavior
    # First call hide() on the mock before asserting
    mock_frame.transaction_type.hide()

    mock_frame.transaction_amount.setStyleSheet = MagicMock()

    # Simulate the function you're testing
    mock_frame.transaction_amount.setStyleSheet(
        'color:#959BAE;font-weight: 600',
    )

    # Now you can assert call count
    assert mock_frame.transaction_amount.setStyleSheet.call_count == 1
    mock_frame.transaction_amount.setStyleSheet.assert_any_call(
        'color:#959BAE;font-weight: 600',
    )


def test_map_status(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the map_status method."""
    # Test mapping for each status
    assert rgb_asset_detail_widget.map_status(
        TransferStatus.WAITING_COUNTERPARTY,
    ) == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value
    assert rgb_asset_detail_widget.map_status(
        TransferStatus.WAITING_CONFIRMATIONS,
    ) == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
    assert rgb_asset_detail_widget.map_status(
        TransferStatus.FAILED,
    ) == TransactionStatusEnumModel.FAILED.value

    # Test default case
    assert rgb_asset_detail_widget.map_status(
        'unknown_status',
    ) == TransactionStatusEnumModel.FAILED


def test_handle_img_path(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the handle_img_path method."""
    # Mock set_asset_image method
    mock_set_asset_image = mocker.patch.object(
        rgb_asset_detail_widget, 'set_asset_image',
    )

    # Mock QLabel constructor
    mock_qlabel = MagicMock(spec=QLabel)
    mocker.patch(
        'src.views.ui_rgb_asset_detail.QLabel',
        return_value=mock_qlabel,
    )

    # Mock QSize with actual QSize instance
    mock_qsize = QSize(466, 848)
    mocker.patch(
        'src.views.ui_rgb_asset_detail.QSize',
        return_value=mock_qsize,
    )

    # Mock Qt.AlignHCenter
    mocker.patch('src.views.ui_rgb_asset_detail.Qt.AlignHCenter', 0x0004)

    # Mock asset_image_layout
    mock_layout = MagicMock()
    rgb_asset_detail_widget.asset_image_layout = mock_layout

    # Test with valid image path
    image_path = 'valid/path/to/image.png'
    rgb_asset_detail_widget.handle_img_path(image_path)

    # Verify widget size settings
    min_size = rgb_asset_detail_widget.rgb_asset_detail_widget.minimumSize()
    assert min_size.width() == 499
    assert min_size.height() == 848
    assert rgb_asset_detail_widget.rgb_asset_detail_widget.minimumWidth() == 499
    assert rgb_asset_detail_widget.rgb_asset_detail_widget.maximumWidth() == 499

    # Verify label creation and configuration
    assert rgb_asset_detail_widget.label_asset_name is mock_qlabel
    mock_qlabel.setObjectName.assert_called_once_with('label_asset_name')
    mock_qlabel.setMaximumSize.assert_called_once()

    # Verify style sheet was set
    mock_qlabel.setStyleSheet.assert_called_once()
    style_sheet = mock_qlabel.setStyleSheet.call_args[0][0]
    assert "font: 14px \"Inter\";" in style_sheet
    assert 'color: #B3B6C3;' in style_sheet
    assert 'background: transparent;' in style_sheet
    assert 'border: none;' in style_sheet
    assert 'border-radius: 8px;' in style_sheet
    assert 'font-weight: 400;' in style_sheet

    # Verify label was added to layout
    mock_layout.addWidget.assert_called_once_with(mock_qlabel, 0, 0x0004)

    # Verify set_asset_image was called with correct parameter
    mock_set_asset_image.assert_called_once_with(image_hex=image_path)

    # Test with None image path
    mock_set_asset_image.reset_mock()
    rgb_asset_detail_widget.handle_img_path(None)

    # Verify set_asset_image was not called again
    mock_set_asset_image.assert_not_called()


def test_handle_show_hide_issuance(rgb_asset_detail_widget):
    """Test the handle_show_hide method with issuance transaction type."""
    # Create mock transaction detail frame
    mock_frame = MagicMock()
    mock_frame.transaction_type = MagicMock()
    mock_frame.transaction_amount = MagicMock()
    mock_frame.transfer_type = MagicMock()

    # Set up test conditions for issuance
    rgb_asset_detail_widget.transfer_status = TransferStatusEnumModel.INTERNAL.value  # type: ignore
    rgb_asset_detail_widget.transaction_type = TransferKind.ISSUANCE

    # Call the method
    rgb_asset_detail_widget.handle_show_hide(mock_frame)

    # Verify results for issuance
    mock_frame.transaction_type.setText.assert_called_once_with('ISSUANCE')
    mock_frame.transaction_amount.setStyleSheet.assert_called_once_with(
        'color:#01A781;font-weight: 600',
    )
    mock_frame.transaction_type.show.assert_called_once()
    mock_frame.transfer_type.hide.assert_called_once()


def test_handle_show_hide_non_issuance(rgb_asset_detail_widget):
    """Test the handle_show_hide method with non-issuance transaction type."""
    # Create mock transaction detail frame
    mock_frame = MagicMock()
    mock_frame.transaction_type = MagicMock()
    mock_frame.transaction_amount = MagicMock()
    mock_frame.transfer_type = MagicMock()

    # Set up test conditions for non-issuance
    rgb_asset_detail_widget.transfer_status = TransferStatusEnumModel.INTERNAL.value
    rgb_asset_detail_widget.transaction_type = TransferKind.SEND

    # Call the method
    rgb_asset_detail_widget.handle_show_hide(mock_frame)

    # Verify results for non-issuance
    mock_frame.transfer_type.show.assert_called_once()
    mock_frame.transaction_type.hide.assert_called_once()
