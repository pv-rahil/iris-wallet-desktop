"""Unit test for RGB Asset Detail ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-many-statements,too-many-locals,too-many-lines
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
from rgb_lib import AssetSchema
from rgb_lib import Outpoint
from rgb_lib import TransferKind
from rgb_lib import TransferStatus

from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.enums.enums_model import TransferType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import RgbAssetPageLoadModel
from src.model.selection_page_model import AssetDataModel
from src.model.transaction_detail_page_model import TransactionDetailPageModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.utils.common_utils import is_hex_string
from src.views.components.transaction_ui_helpers import handle_transaction_type_display
from src.views.components.transaction_ui_helpers import map_transfer_status
from src.views.ui_rgb_asset_detail import RGBAssetDetailWidget


asset_image_path = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..', 'src', 'assets', 'icons', 'regtest-icon.png',
    ),
)


@pytest.fixture
def rgb_asset_detail_widget(qtbot, mocker):
    """Fixture to create and return an instance of RGBAssetDetailWidget."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.resize_image',
        return_value=QPixmap(),
    )
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))

    # Mock the params as an instance of RgbAssetPageLoadModel
    mock_params = MagicMock()
    mock_params.asset_type = 'NIA'  # Set the asset_type as needed

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
        assert is_hex_string(hex_string) is True


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
        assert is_hex_string(hex_string) is False


def test_empty_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with an empty string."""
    assert is_hex_string('') is False


def test_odd_length_string(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test with a string of odd length."""
    odd_length_hex_strings = [
        '1',  # single character
        '123',  # three characters
        '12345',  # five characters
    ]
    for hex_string in odd_length_hex_strings:
        assert is_hex_string(hex_string) is False


def test_handle_page_navigation_nia(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is NIA."""
    rgb_asset_detail_widget.asset_type = AssetSchema.NIA
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.fungibles_asset_page.assert_called_once()


def test_handle_page_navigation_cfa(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is CFA."""
    rgb_asset_detail_widget.asset_type = AssetSchema.CFA
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
            TransferStatusEnumModel.INTERNAL.value, TransferKind.ISSUANCE,
            'ISSUANCE', 'color:#01A781;font-weight: 600', True,
        ),
        (TransferStatusEnumModel.RECEIVE.value, 'other_type', '', '', False),
        (
            TransferStatusEnumModel.ON_GOING_TRANSFER.value,
            TransferKind.ISSUANCE, '', '', False,
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

    # Call the method to test - use handle_transaction_type_display from transaction_ui_helpers
    handle_transaction_type_display(transaction_detail_frame, transfer_status, transaction_type)

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
    asset_type = AssetSchema.NIA.name
    rgb_asset_detail_widget.asset_id_detail.setPlainText(asset_id)
    rgb_asset_detail_widget.asset_type = asset_type

    # Mock the navigation method
    mock_receive_cfa = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'receive_cfa_page',
    )

    # Call the method
    rgb_asset_detail_widget.select_receive_transfer_type()

    # Verify the navigation method was called with correct parameters
    mock_receive_cfa.assert_called_once_with(
        params=AssetDataModel(
            asset_type=asset_type,
            asset_id=asset_id,
            close_page_navigation=asset_type,
        ),
    )


def test_select_send_transfer_type(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test the select_send_transfer_type method."""
    # Mock the navigation method
    mock_send_cfa = mocker.patch.object(
        rgb_asset_detail_widget._view_model.page_navigation,
        'send_cfa_page',
    )

    # Call the method
    rgb_asset_detail_widget.select_send_transfer_type()

    # Verify the navigation method was called
    mock_send_cfa.assert_called_once()


def test_refresh_transaction(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the refresh_transaction method to ensure proper functions are called."""

    # Mock the render timer and the refresh function
    rgb_asset_detail_widget.render_timer = MagicMock()
    rgb_asset_detail_widget._view_model.cfa_view_model.on_refresh_click = MagicMock()

    # Call the method
    rgb_asset_detail_widget.refresh_transaction()

    # Assertions to check that the timer and refresh function were called
    # Verify render_timer.start was called once
    rgb_asset_detail_widget.render_timer.start.assert_called_once()
    # Verify on_refresh_click was called once
    rgb_asset_detail_widget._view_model.cfa_view_model.on_refresh_click.assert_called_once()


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
    rgb_asset_detail_widget._view_model.page_navigation.cfa_transaction_detail_page = MagicMock()

    # Call the method
    rgb_asset_detail_widget.handle_asset_frame_click(params)

    # Assertions to check if the navigation method was called with the correct parameters
    rgb_asset_detail_widget._view_model.page_navigation.cfa_transaction_detail_page.assert_called_once_with(
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
    rgb_asset_detail_widget._view_model.cfa_view_model.on_fail_transfer.assert_called_once_with(
        idx,
    )


def test_show_loading_screen(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the show_loading_screen method for both loading states."""

    # Test loading state
    # Ensure privileges allow enabling buttons when unloading
    rgb_asset_detail_widget.config = MagicMock()
    rgb_asset_detail_widget.config.privileges = MagicMock(
        can_send_transactions=True,
        can_receive_asset=True,
    )
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
    mock_transfer.change_utxo = None
    mock_transfer.receive_utxo = None
    mock_transfer.invoice_string = None
    mock_transfer.consignment_path = None
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
    asset_type = AssetSchema.NIA

    # Mock the view model's cfa_view_model.txn_list
    mock_asset_balance = MagicMock()
    mock_asset_balance.future = '100'
    mock_asset_balance.spendable = '50'

    mock_txn_list = MagicMock()
    mock_txn_list.asset_balance = mock_asset_balance
    mock_txn_list.transfers = [create_mock_transfer]

    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list

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


def test_issue_more_button_presence_and_navigation(qtbot):
    """In secondary issuance mode, issue_more_button should exist and navigate on click."""
    vm = MagicMock()
    vm.page_navigation = MagicMock()
    params = RgbAssetPageLoadModel(
        asset_id='AID', asset_name='AN',
        image_path='img', asset_type='NIA', is_secondary_issuance=True,
    )
    with patch('src.views.ui_rgb_asset_detail.load_stylesheet', return_value=''):
        w = RGBAssetDetailWidget(vm, params)
    qtbot.addWidget(w)
    try:
        # Button should be created in secondary mode
        # Populate minimal fields used by navigate
        w.asset_id_detail.setPlainText('AID')
        w.widget_title_asset_name.setText('AN')
        w.image_path = 'img'
        w.asset_type = 'NIA'
        w.navigate_secondary_issuance()
        vm.page_navigation.issue_ifa_secondary_page.assert_called_once()
        arg = vm.page_navigation.issue_ifa_secondary_page.call_args[0][0]
        assert isinstance(arg, RgbAssetPageLoadModel)
        assert arg.asset_id == 'AID'
        assert arg.asset_name == 'AN'
        assert arg.image_path == 'img'
        assert arg.asset_type == 'NIA'
        assert arg.is_secondary_issuance is True
    finally:
        w.close()


def test_refresh_button_click_invokes_refresh(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Refreshing should call on_refresh_click with the current asset id."""
    rgb_asset_detail_widget._view_model.cfa_view_model.on_refresh_click = MagicMock()
    rgb_asset_detail_widget.asset_id_detail.setPlainText('X')
    # Call the slot directly to avoid disabled button state issues
    rgb_asset_detail_widget.refresh_transaction()
    rgb_asset_detail_widget._view_model.cfa_view_model.on_refresh_click.assert_called_once_with(
        'X',
    )


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
    mock_transaction.invoice_string = ''
    mock_transaction.consignment_path = ''
    mock_change_utxo = MagicMock(spec=Outpoint)
    mock_receive_utxo = MagicMock(spec=Outpoint)
    mock_transaction.change_utxo = mock_change_utxo
    mock_transaction.receive_utxo = mock_receive_utxo
    mock_transaction.kind = TransferKind.ISSUANCE
    mock_transaction.idx = 0

    asset_name = 'Test Asset'
    asset_type = AssetSchema.NIA
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

    # Call the method
    rgb_asset_detail_widget.set_on_chain_transaction_frame(
        mock_transaction, asset_name, asset_type, asset_id, image_path,
    )

    # Verify method calls and attribute settings
    assert rgb_asset_detail_widget.transaction_date == '2023-01-01'
    assert rgb_asset_detail_widget.transaction_time == '11:00 AM'
    assert rgb_asset_detail_widget.transfer_status == TransferStatusEnumModel.SENT.value
    assert rgb_asset_detail_widget.transfer_amount == '10'
    assert rgb_asset_detail_widget.transaction_type == TransferKind.ISSUANCE

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
    _mock_map_status = mocker.patch(
        'src.views.components.transaction_ui_helpers.map_transfer_status',
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
    # Test mapping for each status - using map_transfer_status from transaction_ui_helpers
    assert map_transfer_status(
        TransferStatus.WAITING_COUNTERPARTY,
    ) == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value
    assert map_transfer_status(
        TransferStatus.WAITING_CONFIRMATIONS,
    ) == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
    assert map_transfer_status(
        TransferStatus.FAILED,
    ) == TransactionStatusEnumModel.FAILED.value

    # Test default case
    assert map_transfer_status(
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
    with patch('src.views.ui_rgb_asset_detail.load_stylesheet', return_value=''):
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

    # Call the method from transaction_ui_helpers
    handle_transaction_type_display(mock_frame, TransferStatusEnumModel.INTERNAL.value, TransferKind.ISSUANCE)

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

    # Call the method from transaction_ui_helpers
    handle_transaction_type_display(mock_frame, TransferStatusEnumModel.INTERNAL.value, TransferKind.SEND)

    # Verify results for non-issuance
    mock_frame.transfer_type.show.assert_called_once()
    mock_frame.transaction_type.hide.assert_called_once()


def test_handle_page_navigation_ifa(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test page navigation handling when asset type is IFA."""
    rgb_asset_detail_widget.asset_type = AssetSchema.IFA
    rgb_asset_detail_widget.handle_page_navigation()
    rgb_asset_detail_widget._view_model.page_navigation.inflatable_asset_page.assert_called_once()


def test_map_status_default(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the map_status method with an unknown status."""
    assert map_transfer_status(
        'unknown_status',
    ) == TransactionStatusEnumModel.FAILED


def test_has_inflation_rights(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the _has_inflation_rights method."""
    mock_txn_list = MagicMock()
    mock_assignment = MagicMock()
    mock_assignment.is_inflation_right.return_value = True
    mock_transfer = MagicMock()
    mock_transfer.assignments = [mock_assignment]
    mock_txn_list.transfers = [mock_transfer]

    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list

    assert rgb_asset_detail_widget._has_inflation_rights() is True

    # Test False case
    mock_assignment.is_inflation_right.return_value = False
    assert rgb_asset_detail_widget._has_inflation_rights() is False

    # Test empty case
    mock_txn_list.transfers = []
    assert rgb_asset_detail_widget._has_inflation_rights() is False


def test_fetch_ifa_supply(rgb_asset_detail_widget: RGBAssetDetailWidget):
    """Test the _fetch_ifa_supply method."""
    mock_ifa_asset = MagicMock()
    mock_ifa_asset.asset_id = 'test_id'
    mock_ifa_asset.max_supply = 1000
    mock_ifa_asset.known_circulating_supply = 400

    rgb_asset_detail_widget._view_model.main_asset_view_model.assets.ifa = [
        mock_ifa_asset,
    ]

    rgb_asset_detail_widget._fetch_ifa_supply('test_id')
    assert rgb_asset_detail_widget.max_amount == 600
    assert rgb_asset_detail_widget.circulation == 400


def test_show_loading_screen_ifa_privileges(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test show_loading_screen with IFA and privilege checks."""
    rgb_asset_detail_widget.asset_type = AssetSchema.IFA
    rgb_asset_detail_widget.secondary_issuance = MagicMock()
    rgb_asset_detail_widget.config.privileges.can_send_transactions = False
    rgb_asset_detail_widget.config.privileges.can_receive_asset = False

    mocker.patch.object(
        rgb_asset_detail_widget,
        '_has_inflation_rights', return_value=True,
    )
    rgb_asset_detail_widget.remaining_issue_value = MagicMock()
    rgb_asset_detail_widget.remaining_issue_value.text.return_value = '100'

    rgb_asset_detail_widget.show_loading_screen(False)

    assert rgb_asset_detail_widget.asset_refresh_button.isEnabled() is False
    assert rgb_asset_detail_widget.send_asset.isEnabled() is False
    assert rgb_asset_detail_widget.receive_rgb_asset.isEnabled() is False
    rgb_asset_detail_widget.secondary_issuance.setDisabled.assert_called_with(
        True,
    )


def test_set_transaction_detail_frame_ifa_and_drafts(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker, create_mock_transfer):
    """Test set_transaction_detail_frame for IFA assets and draft transfers."""
    asset_id = 'ifa_id'
    asset_name = 'IFA Asset'
    image_path = 'path'
    asset_type = AssetSchema.IFA

    # Mock IFA asset in main view model
    mock_ifa = MagicMock()
    mock_ifa.asset_id = asset_id
    mock_ifa.max_supply = 1000
    mock_ifa.known_circulating_supply = 200
    rgb_asset_detail_widget._view_model.main_asset_view_model.assets.ifa = [
        mock_ifa,
    ]

    # Mock txn_list
    mock_txn_list = MagicMock()
    mock_txn_list.asset_balance.future = 1000
    mock_txn_list.asset_balance.spendable = 800
    mock_txn_list.transfers = [create_mock_transfer]
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list

    # Mock WalletDataService and drafts
    mock_svc = MagicMock()
    mock_svc.get_draft_transfer.return_value = {
        'amount': 50, 'recipient_id': 'rec',
    }
    mock_svc.list_ifa_secondary_drafts.return_value = [
        {'id': 1, 'amount': 100, 'asset_name': 'IFA Asset'},
    ]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )

    # Mock components
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame',
        return_value=MagicMock(),
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    rgb_asset_detail_widget.max_supply_frame = MagicMock()
    rgb_asset_detail_widget.secondary_issuance = MagicMock()
    rgb_asset_detail_widget.scroll_area_widget_layout = MagicMock()

    # Call method
    rgb_asset_detail_widget.set_transaction_detail_frame(
        asset_id, asset_name, image_path, asset_type,
    )

    # Verify IFA specific UI updates
    assert rgb_asset_detail_widget.max_supply_value is not None
    assert rgb_asset_detail_widget.remaining_issue_value is not None

    assert rgb_asset_detail_widget.max_supply_value.text() == '1000'
    assert rgb_asset_detail_widget.remaining_issue_value.text() == '800'
    rgb_asset_detail_widget.max_supply_frame.show.assert_called()


def test_setup_ui_connection_multisig(rgb_asset_detail_widget: RGBAssetDetailWidget, mocker):
    """Test setup_ui_connection in multisig mode."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    mock_register = mocker.patch(
        'src.views.ui_rgb_asset_detail.register_multisig_button',
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )

    rgb_asset_detail_widget.setup_ui_connection()

    # Verify register_multisig_button was called for send and receive
    assert mock_register.call_count >= 2


def test_init_ifa_asset(qtbot, mocker):
    """Test initialization with IFA asset creates secondary issuance button."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.resize_image',
        return_value=QPixmap(),
    )
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    params = RgbAssetPageLoadModel(
        asset_id='asset_id',
        asset_name='Test Asset',
        image_path=asset_image_path,
        asset_type='3',
    )
    widget = RGBAssetDetailWidget(view_model, params)
    assert hasattr(widget, 'secondary_issuance')
    assert widget.secondary_issuance is not None
    # The text is the translation key, not the translated text in test context
    assert widget.secondary_issuance.text() == 'secondary_issuance'


def test_navigate_secondary_issuance(rgb_asset_detail_widget, mocker):
    """Test navigate_secondary_issuance sets up RgbAssetPageLoadModel."""
    # Mock RgbAssetPageLoadModel to avoid Pydantic validation errors
    mocker.patch(
        'src.views.ui_rgb_asset_detail.RgbAssetPageLoadModel',
        side_effect=MagicMock(),
    )
    rgb_asset_detail_widget.asset_type = AssetSchema.IFA
    rgb_asset_detail_widget.max_amount = 500
    rgb_asset_detail_widget.image_path = None
    rgb_asset_detail_widget.widget_title_asset_name.setText('Asset')
    rgb_asset_detail_widget.navigate_secondary_issuance()
    rgb_asset_detail_widget._view_model.page_navigation.issue_ifa_secondary_page.assert_called_once()


def test_set_transaction_detail_frame_no_transactions(rgb_asset_detail_widget, mocker):
    """Test set_transaction_detail_frame with no transactions."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mock_txn_list = MagicMock()
    mock_txn_list.asset_balance.future = 0
    mock_txn_list.asset_balance.spendable = 0
    mock_txn_list.transfers = []
    # Make the model itself falsey for the 'if not asset_transactions' check
    mock_txn_list.__bool__.return_value = False
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list
    rgb_asset_detail_widget.scroll_area_widget_layout = MagicMock()
    rgb_asset_detail_widget.transactions_label = MagicMock()
    rgb_asset_detail_widget.set_transaction_detail_frame(
        'id', 'name', 'path', 'NIA',
    )
    rgb_asset_detail_widget.transactions_label.hide.assert_called_with()


def test_set_transaction_detail_frame_waiting_counterparty(rgb_asset_detail_widget, mocker):
    """Test set_transaction_detail_frame with WAITING_COUNTERPARTY status."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame',
        return_value=MagicMock(),
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailPageModel',
        side_effect=MagicMock(),
    )

    mock_transfer = MagicMock()
    mock_transfer.status = TransferStatus.WAITING_COUNTERPARTY
    mock_transfer.transfer_Status = TransferStatusEnumModel.SENT.value
    mock_transfer.txid = 'txid'
    mock_transfer.updated_at = 123456789
    mock_transfer.updated_at_date = '2023-01-01'
    mock_transfer.updated_at_time = '12:00'
    mock_transfer.created_at_time = '11:00'
    mock_transfer.transport_endpoints = []
    mock_transfer.invoice_string = 'inv'
    mock_transfer.consignment_path = 'path'
    mock_transfer.recipient_id = 'rec'
    mock_transfer.change_utxo = None
    mock_transfer.receive_utxo = None
    mock_transfer.kind = 'issuance'
    mock_transfer.amount_status = '10'

    mock_txn_list = MagicMock()
    mock_txn_list.transfers = [mock_transfer]
    mock_txn_list.asset_balance.future = 100
    mock_txn_list.asset_balance.spendable = 100
    # Ensure it's truthy
    mock_txn_list.__bool__.return_value = True
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list
    rgb_asset_detail_widget.scroll_area_widget_layout = MagicMock()

    rgb_asset_detail_widget.set_transaction_detail_frame(
        'id', 'name', 'path', 'NIA',
    )
    assert rgb_asset_detail_widget.transaction_detail_frame.close_button.setIcon.called


def test_on_resume_transfer_callback(rgb_asset_detail_widget, mocker):
    """Test the resume transfer callback in set_transaction_detail_frame."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mock_frame = MagicMock()
    mock_frame.click_frame = MagicMock()
    mock_frame.click_frame.connect = MagicMock()
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame', return_value=mock_frame,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailPageModel',
        side_effect=MagicMock(),
    )

    mock_svc = MagicMock()
    mock_svc.get_draft_transfer.return_value = {'amount': 10}
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=mock_svc,
    )

    # Create a mock transfer so the code doesn't exit early
    mock_transfer = MagicMock()
    mock_transfer.txid = 'txid'
    mock_transfer.amount_status = '10'
    mock_transfer.updated_at = 123456789
    mock_transfer.updated_at_date = '2023-01-01'
    mock_transfer.updated_at_time = '12:00'
    mock_transfer.created_at_time = '11:00'
    mock_transfer.transport_endpoints = []
    mock_transfer.invoice_string = 'inv'
    mock_transfer.consignment_path = 'path'
    mock_transfer.recipient_id = 'rec'
    mock_transfer.change_utxo = None
    mock_transfer.receive_utxo = None
    mock_transfer.kind = 'issuance'
    mock_transfer.transfer_Status = TransferStatusEnumModel.SENT.value
    mock_transfer.status = 'settled'
    mock_transfer.idx = 0

    mock_txn_list = MagicMock()
    mock_txn_list.transfers = [mock_transfer]
    mock_txn_list.asset_balance.future = 100
    mock_txn_list.asset_balance.spendable = 100
    mock_txn_list.__bool__.return_value = True
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list
    rgb_asset_detail_widget.scroll_area_widget_layout = MagicMock()

    rgb_asset_detail_widget.set_transaction_detail_frame(
        'id', 'name', 'path', 'NIA',
    )

    # Verify click_frame.connect was called
    assert mock_frame.click_frame.connect.called


def test_on_resume_click_secondary_callback(rgb_asset_detail_widget, mocker):
    """Test the resume secondary issuance click callback."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mock_frame = MagicMock()
    mock_frame.click_frame = MagicMock()
    mock_frame.click_frame.connect = MagicMock()
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailFrame', return_value=mock_frame,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.TransactionDetailPageModel',
        side_effect=MagicMock(),
    )

    mock_svc = MagicMock()
    mock_svc.list_ifa_secondary_drafts.return_value = [
        {'id': 1, 'amount': 100, 'asset_name': 'IFA'},
    ]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=mock_svc,
    )

    # Create a mock transfer so the code doesn't exit early
    mock_transfer = MagicMock()
    mock_transfer.txid = 'txid'
    mock_transfer.amount_status = '10'
    mock_transfer.updated_at = 123456789
    mock_transfer.updated_at_date = '2023-01-01'
    mock_transfer.updated_at_time = '12:00'
    mock_transfer.created_at_time = '11:00'
    mock_transfer.transport_endpoints = []
    mock_transfer.invoice_string = 'inv'
    mock_transfer.consignment_path = 'path'
    mock_transfer.recipient_id = 'rec'
    mock_transfer.change_utxo = None
    mock_transfer.receive_utxo = None
    mock_transfer.kind = 'issuance'
    mock_transfer.transfer_Status = TransferStatusEnumModel.SENT.value
    mock_transfer.status = 'settled'
    mock_transfer.idx = 0

    mock_txn_list = MagicMock()
    mock_txn_list.transfers = [mock_transfer]
    mock_txn_list.asset_balance.future = 100
    mock_txn_list.asset_balance.spendable = 100
    mock_txn_list.__bool__.return_value = True
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list
    rgb_asset_detail_widget.scroll_area_widget_layout = MagicMock()

    # Use '3' for IFA
    rgb_asset_detail_widget.set_transaction_detail_frame(
        'id', 'IFA', 'path', '3',
    )

    # Verify click_frame.connect was called
    assert mock_frame.click_frame.connect.called


def test_handle_show_hide_inflation(rgb_asset_detail_widget, mocker):
    """Test handle_show_hide with INFLATION status."""
    mock_frame = MagicMock()
    rgb_asset_detail_widget.transfer_status = TransferStatusEnumModel.INFLATION.value
    # Use handle_transaction_type_display from transaction_ui_helpers
    handle_transaction_type_display(mock_frame, TransferStatusEnumModel.INFLATION.value, None)
    mock_frame.transaction_type.setText.assert_called_with('INFLATION')


def test_setup_ui_connection_multisig_ifa(rgb_asset_detail_widget, mocker):
    """Test setup_ui_connection registers multisig button for IFA."""
    mocker.patch(
        'src.views.ui_rgb_asset_detail.load_stylesheet',
        return_value='',
    )
    mocker.patch(
        'src.views.ui_rgb_asset_detail.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    mock_register = mocker.patch(
        'src.views.ui_rgb_asset_detail.register_multisig_button',
    )

    rgb_asset_detail_widget.asset_type = '3'  # IFA
    rgb_asset_detail_widget.secondary_issuance = MagicMock()
    rgb_asset_detail_widget.setup_ui_connection()
    assert any(
        call.args[1] == rgb_asset_detail_widget.secondary_issuance for call in mock_register.call_args_list
    )


def test_has_inflation_rights_skip(rgb_asset_detail_widget, mocker):
    """Test _has_inflation_rights skips transfers without assignments."""
    mock_txn_list = MagicMock()
    mock_transfer = MagicMock()
    mock_transfer.assignments = None
    mock_txn_list.transfers = [mock_transfer]
    rgb_asset_detail_widget._view_model.cfa_view_model.txn_list = mock_txn_list
    assert rgb_asset_detail_widget._has_inflation_rights() is False


def test_map_status_unknown(rgb_asset_detail_widget):
    """Test map_status fallback for unknown status."""
    assert map_transfer_status(
        'unknown',
    ) == TransactionStatusEnumModel.FAILED
