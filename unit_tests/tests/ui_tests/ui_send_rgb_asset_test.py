"""Unit test for Send RGB asset ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-few-public-methods,too-many-lines
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from rgb_lib import AssetSchema
from rgb_lib import RgbLibError

from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import ToastPreset
from src.model.rgb_model import Balance
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SEND_ASSET
from src.utils.error_message import ERROR_UNEXPECTED
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_send_rgb_asset import SendRGBAssetWidget


@pytest.fixture
def send_rgb_asset_widget(qtbot):
    """Fixture to initialize the SendRGBAssetWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(
        MainViewModel(
            mock_navigation,
        ),
    )  # Mock the view model

    # Mock the asset balance
    asset_balance = Balance(future=100, spendable=50, settled=100)
    txn_list = MagicMock(ListTransferAssetWithBalanceResponseModel)
    txn_list.asset_balance = asset_balance
    view_model.cfa_view_model.txn_list = txn_list

    # Mock the attributes of cfa_view_model
    view_model.cfa_view_model.is_loading = MagicMock()
    view_model.cfa_view_model.stop_loading = MagicMock()

    widget = SendRGBAssetWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(send_rgb_asset_widget: SendRGBAssetWidget, qtbot):
    """Test the retranslate_ui method."""
    send_rgb_asset_widget.send_rgb_asset_page.retranslate_ui()

    expected_total_supply_text = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_to_pay', None,
    )

    expected_pay_to_text = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'pay_to', None,
    )

    assert send_rgb_asset_widget.send_rgb_asset_page.total_supply_label.text(
    ) == expected_total_supply_text
    assert send_rgb_asset_widget.send_rgb_asset_page.pay_to_label.text() == expected_pay_to_text


def test_handle_button_enabled(send_rgb_asset_widget: SendRGBAssetWidget, qtbot):
    """Test the handle_button_enabled method."""

    # Test with empty address and amount
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.setText('')
    send_rgb_asset_widget.send_rgb_asset_page.asset_amount_value.setText('')
    send_rgb_asset_widget.handle_button_enabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled() is False

    # Test with filled address and amount
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.setText(
        'blind_utxo_123',
    )
    send_rgb_asset_widget.send_rgb_asset_page.asset_amount_value.setText('10')

    # Mocking the spendable balance to be greater than 0
    send_rgb_asset_widget.asset_spendable_balance = 50
    send_rgb_asset_widget.handle_button_enabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled() is True

    # Test with invalid amount (zero)
    send_rgb_asset_widget.send_rgb_asset_page.asset_amount_value.setText('0')
    send_rgb_asset_widget.handle_button_enabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled() is False

    # Test with valid address and invalid spendable balance
    send_rgb_asset_widget.asset_spendable_balance = 0
    send_rgb_asset_widget.handle_button_enabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled() is False


def test_set_asset_balance(send_rgb_asset_widget: SendRGBAssetWidget, qtbot):
    """Test the set_asset_balance method."""
    send_rgb_asset_widget.set_asset_balance()

    # Verify that the labels are set correctly
    assert send_rgb_asset_widget.send_rgb_asset_page.asset_balance_label_total.text() == '100'
    assert send_rgb_asset_widget.send_rgb_asset_page.asset_balance_label_spendable.text() == '50'
    assert send_rgb_asset_widget.asset_spendable_balance == 50

    # Verify button enabled state based on spendable balance
    assert send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()

    # Test with zero spendable balance
    send_rgb_asset_widget._view_model.cfa_view_model.txn_list.asset_balance.spendable = 0
    send_rgb_asset_widget.set_asset_balance()
    assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()


def test_handle_show_message(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the handle_message method of WelcomeWidget."""
    with patch('src.views.ui_send_rgb_asset.ToastManager') as mock_toast_manager:
        send_rgb_asset_widget.handle_show_message(
            ToastPreset.ERROR, 'Test Error Message',
        )
        mock_toast_manager.error.assert_called_once_with('Test Error Message')
        mock_toast_manager.success.assert_not_called()

        send_rgb_asset_widget.handle_show_message(
            ToastPreset.SUCCESS, 'Test Success Message',
        )
        mock_toast_manager.error.assert_called_once()
        mock_toast_manager.success.assert_called_once_with(
            'Test Success Message',
        )


def test_handle_message(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the handle_message method of WelcomeWidget."""
    with patch('src.views.ui_send_rgb_asset.ToastManager') as mock_toast_manager:
        send_rgb_asset_widget.show_cfa_message(
            ToastPreset.ERROR, 'Test Error Message',
        )
        mock_toast_manager.error.assert_called_once_with('Test Error Message')
        mock_toast_manager.success.assert_not_called()

        send_rgb_asset_widget.show_cfa_message(
            ToastPreset.SUCCESS, 'Test Success Message',
        )
        mock_toast_manager.error.assert_called_once()
        mock_toast_manager.success.assert_called_once_with(
            'Test Success Message',
        )


def test_refresh_asset(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the refresh_asset method of the widget."""

    # Mock the view model and its methods
    mock_cfa_view_model = MagicMock()
    mock_view_model = MagicMock()

    send_rgb_asset_widget._view_model = mock_view_model
    send_rgb_asset_widget._view_model.cfa_view_model = mock_cfa_view_model

    # Mock the values that should be set on the view model
    mock_cfa_view_model.asset_id = '123'
    mock_cfa_view_model.asset_name = 'Asset Name'
    mock_cfa_view_model.image_path = 'path/to/image'
    mock_cfa_view_model.asset_type = 'type'

    # Mock the get_cfa_asset_detail method
    mock_get_cfa_asset_detail = MagicMock()
    mock_cfa_view_model.get_cfa_asset_detail = mock_get_cfa_asset_detail

    # Call the refresh_asset method
    send_rgb_asset_widget.refresh_asset()

    # Verify that the loading_performer was set correctly
    assert send_rgb_asset_widget.loading_performer == 'REFRESH_BUTTON'

    # Verify that on_refresh_click was called
    mock_cfa_view_model.on_refresh_click.assert_called_once()

    # Verify that the asset details were correctly assigned
    assert send_rgb_asset_widget.asset_id == '123'
    assert send_rgb_asset_widget.asset_name == 'Asset Name'
    assert send_rgb_asset_widget.image_path == 'path/to/image'
    assert send_rgb_asset_widget.asset_type == 'type'

    # Verify that get_cfa_asset_detail was called with the correct arguments
    mock_cfa_view_model.get_cfa_asset_detail.assert_called_once_with(
        asset_id='123',
        asset_name='Asset Name',
        image_path='path/to/image',
        asset_type='type',
    )


def test_set_originating_page(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the set_originating_page method of the widget."""

    # Test when asset_type is 'NIA'
    send_rgb_asset_widget.set_originating_page(AssetSchema.NIA)

    # Verify the asset_type is set to 'NIA'
    assert send_rgb_asset_widget.asset_type == AssetSchema.NIA


def test_rgb_asset_page_navigation(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the rgb_asset_page_navigation method of the widget."""

    # Mock the view model and its navigation methods
    mock_page_navigation = MagicMock()
    mock_sidebar = MagicMock()

    # Mock the view model
    send_rgb_asset_widget._view_model.page_navigation = mock_page_navigation
    mock_page_navigation.sidebar.return_value = mock_sidebar

    # Test when asset_type is 'NIA'
    send_rgb_asset_widget.asset_type = AssetSchema.NIA

    # Call the rgb_asset_page_navigation method
    send_rgb_asset_widget.rgb_asset_page_navigation()

    # Verify that the 'my_fungibles' checkbox is checked
    mock_sidebar.my_fungibles.setChecked.assert_called_once_with(True)

    # Verify that fungibles_asset_page was called
    mock_page_navigation.fungibles_asset_page.assert_called_once()

    # Test when asset_type is not 'NIA' (e.g., 'OtherType')
    send_rgb_asset_widget.asset_type = 'OtherType'

    # Call the rgb_asset_page_navigation method again
    send_rgb_asset_widget.rgb_asset_page_navigation()

    # Verify that the 'my_collectibles' checkbox is checked
    mock_sidebar.my_collectibles.setChecked.assert_called_once_with(True)

    # Verify that collectibles_asset_page was called
    mock_page_navigation.collectibles_asset_page.assert_called_once()


def test_send_rgb_asset_button_success(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the send_rgb_asset_button method on success."""

    # Mock the required objects and methods
    mock_send_rgb_asset_page = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page = mock_send_rgb_asset_page

    # Mock the text fields with correct values
    mock_send_rgb_asset_page.asset_address_value.text.return_value = 'some_invoice'
    mock_send_rgb_asset_page.asset_amount_value.text.return_value = '10'
    mock_send_rgb_asset_page.fee_rate_value.text.return_value = '0.01'

    # Mock the default minimum confirmation value
    mock_default_min_confirmation = MagicMock()
    mock_default_min_confirmation.min_confirmation = 1
    mocker.patch(
        'src.data.repository.setting_card_repository.SettingCardRepository.get_default_min_confirmation',
        return_value=mock_default_min_confirmation,
    )

    # Mock the decoded RGB invoice response
    class DummyAssign:
        """Dummy assignment class for testing."""

        def __init__(self, amount: int):
            self.amount = amount

    mock_decoded_rgb_invoice = MagicMock()
    mock_decoded_rgb_invoice.recipient_id = 'recipient_id'
    mock_decoded_rgb_invoice.transport_endpoints = 'some_endpoints'
    mock_decoded_rgb_invoice.assignment = DummyAssign(1)
    mocker.patch(
        'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
        return_value=mock_decoded_rgb_invoice,
    )

    # Force software path (not hardware/watch-only)
    send_rgb_asset_widget.is_hardware_wallet = False
    send_rgb_asset_widget.is_online_wallet = False
    send_rgb_asset_widget.is_watch_only = False

    # Mock the on_send_click method
    mock_on_send_click = MagicMock()
    send_rgb_asset_widget._view_model.cfa_view_model.on_send_click = mock_on_send_click

    # Mock ToastManager to prevent actual toast displays
    mock_toast_manager = MagicMock()
    send_rgb_asset_widget.ToastManager = mock_toast_manager

    # Simulate the button click
    send_rgb_asset_widget.send_rgb_asset_button()

    # Verify loading_performer is set correctly
    assert send_rgb_asset_widget.loading_performer == 'SEND_BUTTON'

    # Verify that on_send_click was called with expected args
    assert mock_on_send_click.called
    args, _ = mock_on_send_click.call_args
    # Expected order: recipient_id, endpoints, fee_rate, min_conf, assignment
    assert args[0] == 'recipient_id'
    assert args[1] == 'some_endpoints'
    assert args[2] == '0.01'
    assert args[3] == 1
    # last arg should have amount 10
    assert getattr(args[4], 'amount', None) == 10

    # Verify that no error toast was shown
    mock_toast_manager.error.assert_not_called()


def test_send_rgb_asset_button_decode_error(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the send_rgb_asset_button method when decode invoice fails."""

    # Mock the required objects and methods
    mock_send_rgb_asset_page = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page = mock_send_rgb_asset_page

    # Mock the text fields
    mock_send_rgb_asset_page.asset_address_value.text.return_value = 'invalid_invoice'

    # Mock RgbRepository.decode_invoice to raise CommonException
    mock_error = CommonException('Invalid invoice')
    mocker.patch(
        'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
        side_effect=mock_error,
    )

    # Use patch to mock ToastManager
    with patch('src.views.ui_send_rgb_asset.ToastManager') as mock_toast_manager:
        # Simulate the button click
        send_rgb_asset_widget.send_rgb_asset_button()

        # Verify error toast was shown with correct message
        mock_toast_manager.error.assert_called_once_with(
            description=ERROR_UNEXPECTED.format(str(mock_error.message)),
        )
        mock_toast_manager.success.assert_not_called()


def test_send_rgb_asset_button_send_error(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the send_rgb_asset_button method when send fails."""

    # Mock the required objects and methods
    mock_send_rgb_asset_page = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page = mock_send_rgb_asset_page

    # Mock the text fields
    mock_send_rgb_asset_page.asset_address_value.text.return_value = 'some_invoice'
    mock_send_rgb_asset_page.asset_amount_value.text.return_value = '10'
    mock_send_rgb_asset_page.fee_rate_value.text.return_value = '0.01'

    # Mock minimum confirmation
    mock_default_min_confirmation = MagicMock()
    mock_default_min_confirmation.min_confirmation = 1
    mocker.patch(
        'src.data.repository.setting_card_repository.SettingCardRepository.get_default_min_confirmation',
        return_value=mock_default_min_confirmation,
    )

    # Mock successful decode invoice
    mock_decoded_rgb_invoice = MagicMock()
    mock_decoded_rgb_invoice.recipient_id = 'recipient_id'
    mock_decoded_rgb_invoice.transport_endpoints = 'some_endpoints'
    mocker.patch(
        'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
        return_value=mock_decoded_rgb_invoice,
    )

    # Mock on_send_click to raise CommonException
    mock_error = CommonException('Send failed')
    mock_on_send_click = MagicMock(side_effect=mock_error)
    send_rgb_asset_widget._view_model.cfa_view_model.on_send_click = mock_on_send_click

    # Use patch to mock ToastManager
    with patch('src.views.ui_send_rgb_asset.ToastManager') as mock_toast_manager:
        # Simulate the button click
        send_rgb_asset_widget.send_rgb_asset_button()

        # Verify error toast was shown with correct message
        mock_toast_manager.error.assert_called_once_with(
            description=ERROR_SEND_ASSET.format(str(mock_error)),
        )
        mock_toast_manager.success.assert_not_called()


def test_handle_spendable_balance_validation_show_when_zero(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test that the spendable balance validation message is shown when the balance is 0."""
    # Mock asset_spendable_balance to return 0
    mocker.patch.object(
        send_rgb_asset_widget,
        'asset_spendable_balance',
        0,
    )

    # Mock the spendable_balance_validation and its methods
    mock_spendable_validation = MagicMock()
    mocker.patch.object(
        send_rgb_asset_widget.send_rgb_asset_page,
        'spendable_balance_validation',
        mock_spendable_validation,
    )

    # Mock disable_buttons method
    mock_disable_buttons = mocker.patch.object(
        send_rgb_asset_widget,
        'disable_buttons_on_fee_rate_loading',
    )

    # Call the method
    send_rgb_asset_widget.handle_spendable_balance_validation()

    # Check that the validation message is shown and buttons are disabled
    mock_spendable_validation.show.assert_called_once()
    mock_disable_buttons.assert_called_with(
        True,
    )


def test_handle_spendable_balance_validation_hide_when_non_zero(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test that the spendable balance validation message is hidden when the balance is greater than 0."""
    # Mock asset_spendable_balance to return 50
    mocker.patch.object(
        send_rgb_asset_widget,
        'asset_spendable_balance',
        50,
    )

    # Mock the spendable_balance_validation and its methods
    mock_spendable_validation = MagicMock()
    mocker.patch.object(
        send_rgb_asset_widget.send_rgb_asset_page,
        'spendable_balance_validation',
        mock_spendable_validation,
    )

    # Mock disable_buttons method
    mock_disable_buttons = mocker.patch.object(
        send_rgb_asset_widget,
        'disable_buttons_on_fee_rate_loading',
    )

    # Call the method
    send_rgb_asset_widget.handle_spendable_balance_validation()

    # Check that the validation message is hidden and buttons are enabled
    mock_spendable_validation.hide.assert_called_once()
    mock_disable_buttons.assert_called_with(
        False,
    )


@pytest.mark.parametrize('is_loading', [True, False])
def test_fee_estimation_loader(send_rgb_asset_widget: SendRGBAssetWidget, is_loading, mocker):
    """Test the fee_estimation_loader method with both loading states."""

    # Mock the update_loading_state method
    mock_update_loading_state = mocker.patch.object(
        send_rgb_asset_widget,
        'update_loading_state',
    )

    # Mock the loading_performer property
    mocker.patch.object(
        send_rgb_asset_widget,
        'loading_performer',
        'FEE_ESTIMATION',
    )

    # Call the fee_estimation_loader method
    send_rgb_asset_widget.fee_estimation_loader(is_loading)

    # Check if the loading performer was set to 'FEE_ESTIMATION'
    assert send_rgb_asset_widget.loading_performer == 'FEE_ESTIMATION'

    # Verify that update_loading_state was called with the expected loading state
    mock_update_loading_state.assert_called_once_with(
        is_loading,
    )


@pytest.mark.parametrize(
    'loading_performer,is_loading', [
        ('REFRESH_BUTTON', True),
        ('REFRESH_BUTTON', False),
        ('SEND_BUTTON', True),
        ('SEND_BUTTON', False),
        ('FEE_ESTIMATION', True),
        ('FEE_ESTIMATION', False),
    ],
)
def test_update_loading_state(send_rgb_asset_widget: SendRGBAssetWidget, loading_performer, is_loading, mocker):
    """Test the update_loading_state method for different loading performers and states."""

    # Set up mocks
    mock_loading_screen = MagicMock()
    send_rgb_asset_widget._SendRGBAssetWidget__loading_translucent_screen = mock_loading_screen
    send_rgb_asset_widget.render_timer = MagicMock()
    send_rgb_asset_widget.loading_performer = loading_performer

    # Mock send button
    mock_send_btn = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page.send_btn = mock_send_btn

    # For FEE_ESTIMATION case
    mock_fee_rate_screen = MagicMock()
    send_rgb_asset_widget.rgb_asset_fee_rate_loading_screen = mock_fee_rate_screen
    mocker.patch(
        'src.views.ui_send_rgb_asset.LoadingTranslucentScreen',
        return_value=mock_fee_rate_screen,
    )

    # Call the method
    send_rgb_asset_widget.update_loading_state(is_loading)

    if loading_performer == 'REFRESH_BUTTON':
        # Verify refresh button loading behavior
        mock_loading_screen.make_parent_disabled_during_loading.assert_called_once_with(
            is_loading,
        )
        if is_loading:
            mock_loading_screen.start.assert_called_once()
        else:
            mock_loading_screen.stop.assert_called_once()

    elif loading_performer == 'SEND_BUTTON':
        # Verify send button loading behavior
        if is_loading:
            send_rgb_asset_widget.render_timer.start.assert_called_once()
            mock_send_btn.start_loading.assert_called_once()
        else:
            send_rgb_asset_widget.render_timer.stop.assert_called_once()
            mock_send_btn.stop_loading.assert_called_once()

    elif loading_performer == 'FEE_ESTIMATION':
        # Verify fee estimation loading behavior
        if is_loading:
            mock_fee_rate_screen.start.assert_called_once()
            mock_fee_rate_screen.make_parent_disabled_during_loading.assert_called_once_with(
                True,
            )
        else:
            mock_fee_rate_screen.stop.assert_called_once()
            mock_fee_rate_screen.make_parent_disabled_during_loading.assert_called_once_with(
                False,
            )


def test_disable_buttons_on_fee_rate_loading(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the disable_buttons_on_fee_rate_loading method."""

    # Test case 1: When asset_spendable_balance > 0 and button_status is False
    send_rgb_asset_widget.asset_spendable_balance = 100
    send_rgb_asset_widget.disable_buttons_on_fee_rate_loading(False)

    # Verify buttons are enabled
    assert send_rgb_asset_widget.send_rgb_asset_page.slow_checkbox.isEnabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.medium_checkbox.isEnabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.fast_checkbox.isEnabled()
    assert send_rgb_asset_widget.send_rgb_asset_page.custom_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()

    # Test case 2: When asset_spendable_balance > 0 and button_status is True
    send_rgb_asset_widget.disable_buttons_on_fee_rate_loading(True)

    # Verify buttons are disabled
    assert not send_rgb_asset_widget.send_rgb_asset_page.slow_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.medium_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.fast_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.custom_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()

    # Test case 3: When asset_spendable_balance is 0
    send_rgb_asset_widget.asset_spendable_balance = 0
    send_rgb_asset_widget.disable_buttons_on_fee_rate_loading(False)

    # Verify buttons are disabled regardless of button_status parameter
    assert not send_rgb_asset_widget.send_rgb_asset_page.slow_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.medium_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.fast_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.custom_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()

    # Test case 4: When asset_spendable_balance is 0 and button_status is True
    send_rgb_asset_widget.disable_buttons_on_fee_rate_loading(True)

    # Verify buttons remain disabled
    assert not send_rgb_asset_widget.send_rgb_asset_page.slow_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.medium_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.fast_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.custom_checkbox.isEnabled()
    assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()


def test_validate_rgb_invoice(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the validate_rgb_invoice method."""

    # Mock the necessary attributes
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label = MagicMock()

    # Test with an empty invoice
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.text.return_value = '   '
    send_rgb_asset_widget.validate_rgb_invoice()
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.hide.assert_called_once()
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.hide.reset_mock()

    # Test with a valid invoice
    valid_invoice = 'valid_rgb_invoice_string'  # Example valid RGB invoice
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.text.return_value = valid_invoice

#     # Test with a valid invoice
    valid_invoice = 'valid_invoice_string'
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.setText(
        valid_invoice,
    )
    with patch('src.views.ui_send_rgb_asset.Invoice', return_value=None):
        send_rgb_asset_widget.validate_rgb_invoice()
        send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.hide.assert_called_once()
        send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.hide.reset_mock()

    # Test with an invalid invoice
    invalid_invoice = 'invalid_rgb_invoice_string'
    send_rgb_asset_widget.send_rgb_asset_page.asset_address_value.text.return_value = invalid_invoice

    with patch('rgb_lib.Invoice', side_effect=RgbLibError.InvalidInvoice('Invalid invoice details')):
        send_rgb_asset_widget.validate_rgb_invoice()
        send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.show.assert_called_once()
        send_rgb_asset_widget.send_rgb_asset_page.asset_address_validation_label.setText.assert_called_once_with(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'invalid_invoice',
            ),
        )
        assert not send_rgb_asset_widget.send_rgb_asset_page.send_btn.isEnabled()


def test_handle_send_rgb_hw_dialog_update_shows_when_not_visible(send_rgb_asset_widget: SendRGBAssetWidget, monkeypatch):
    """Ensure HW dialog is retrieved, updated and shown when not visible."""
    # Make widget visible so handle_send_rgb_hw_dialog_update doesn't return early
    send_rgb_asset_widget.show()
    dummy = MagicMock()
    dummy.update_dialog = MagicMock()
    dummy.show = MagicMock()
    dummy.isVisible.return_value = False
    monkeypatch.setattr(
        'src.views.ui_send_rgb_asset.HardwareWalletOperationDialog.get_instance',
        lambda parent: dummy,
    )

    msg = 'Processing'
    dtype = MagicMock()
    send_rgb_asset_widget.handle_send_rgb_hw_dialog_update(msg, dtype)

    dummy.update_dialog.assert_called_once_with(msg, dtype)
    dummy.show.assert_called_once()


def test_handle_send_rgb_hw_dialog_update_no_show_when_visible(send_rgb_asset_widget: SendRGBAssetWidget, monkeypatch):
    """If dialog already visible, do not call show()."""
    # Make widget visible so handle_send_rgb_hw_dialog_update doesn't return early
    send_rgb_asset_widget.show()
    dummy = MagicMock()
    dummy.update_dialog = MagicMock()
    dummy.show = MagicMock()
    dummy.isVisible.return_value = True
    monkeypatch.setattr(
        'src.views.ui_send_rgb_asset.HardwareWalletOperationDialog.get_instance',
        lambda parent: dummy,
    )

    send_rgb_asset_widget.handle_send_rgb_hw_dialog_update('msg', MagicMock())

    dummy.update_dialog.assert_called_once()
    dummy.show.assert_not_called()


def test_show_send_rgb_psbt_page_nia(send_rgb_asset_widget: SendRGBAssetWidget):
    """For NIA asset type, page name should be 'NIA page' and navigation invoked with ReceiveAssetModel."""
    # Make widget visible so show_send_rgb_psbt_page doesn't return early
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.asset_type = AssetSchema.NIA
    send_rgb_asset_widget.is_multisig = False  # Ensure non-multisig path
    with patch('src.views.ui_send_rgb_asset.ReceiveAssetModel') as mock_receive_model:
        model_instance = MagicMock()
        mock_receive_model.return_value = model_instance
        psbt = 'psbt-string'

        send_rgb_asset_widget.show_send_rgb_psbt_page(psbt)

        mock_receive_model.assert_called_once_with(
            page_name='NIA page', address_info='psbt_info', psbt=psbt, is_signed=False,
        )
        send_rgb_asset_widget._view_model.page_navigation.receive_asset_page.assert_called_once_with(
            model_instance,
        )


def test_show_send_rgb_psbt_page_cfa(send_rgb_asset_widget: SendRGBAssetWidget):
    """For non-NIA (CFA) asset type, page name should be 'CFA page'."""
    # Make widget visible so show_send_rgb_psbt_page doesn't return early
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.asset_type = AssetSchema.CFA
    send_rgb_asset_widget.is_multisig = False  # Ensure non-multisig path
    with patch('src.views.ui_send_rgb_asset.ReceiveAssetModel') as mock_receive_model:
        model_instance = MagicMock()
        mock_receive_model.return_value = model_instance
        psbt = 'psbt-2'

        send_rgb_asset_widget.show_send_rgb_psbt_page(psbt)

        mock_receive_model.assert_called_once_with(
            page_name='CFA page', address_info='psbt_info', psbt=psbt, is_signed=False,
        )
        send_rgb_asset_widget._view_model.page_navigation.receive_asset_page.assert_called_once_with(
            model_instance,
        )


def test_set_originating_page_ifa(send_rgb_asset_widget: SendRGBAssetWidget):
    """Test the set_originating_page method for IFA asset type."""
    send_rgb_asset_widget.set_originating_page(AssetSchema.IFA)
    assert send_rgb_asset_widget.asset_type == AssetSchema.IFA


def test_rgb_asset_page_navigation_ifa(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test the rgb_asset_page_navigation method for IFA asset type."""
    mock_page_navigation = MagicMock()
    mock_sidebar = MagicMock()
    send_rgb_asset_widget._view_model.page_navigation = mock_page_navigation
    mock_page_navigation.sidebar.return_value = mock_sidebar

    send_rgb_asset_widget.asset_type = AssetSchema.IFA
    send_rgb_asset_widget.rgb_asset_page_navigation()

    mock_sidebar.my_inflatable.setChecked.assert_called_once_with(True)
    mock_page_navigation.inflatable_asset_page.assert_called_once()


def test_show_send_rgb_psbt_page_ifa(send_rgb_asset_widget: SendRGBAssetWidget):
    """For IFA asset type, page name should be 'IFA page'."""
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.asset_type = AssetSchema.IFA
    send_rgb_asset_widget.is_multisig = False
    with patch('src.views.ui_send_rgb_asset.ReceiveAssetModel') as mock_receive_model:
        model_instance = MagicMock()
        mock_receive_model.return_value = model_instance
        psbt = 'psbt-ifa'

        send_rgb_asset_widget.show_send_rgb_psbt_page(psbt)

        mock_receive_model.assert_called_once_with(
            page_name='IFA page', address_info='psbt_info', psbt=psbt, is_signed=False,
        )


def test_show_send_rgb_psbt_page_multisig(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """For multisig wallet, show_send_rgb_psbt_page should show toast and navigate back."""
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.asset_type = AssetSchema.NIA
    send_rgb_asset_widget.is_multisig = True

    mock_toast = mocker.patch(
        'src.views.ui_send_rgb_asset.ToastManager.success',
    )
    mock_nav = mocker.patch.object(
        send_rgb_asset_widget, 'rgb_asset_page_navigation',
    )

    send_rgb_asset_widget.show_send_rgb_psbt_page('psbt-mSIG')

    mock_toast.assert_called_once()
    mock_nav.assert_called_once()


def test_show_send_rgb_psbt_page_not_visible(send_rgb_asset_widget: SendRGBAssetWidget):
    """show_send_rgb_psbt_page should return early when widget not visible."""
    send_rgb_asset_widget.hide()
    send_rgb_asset_widget.show_send_rgb_psbt_page('psbt')
    # Should not raise any errors and should return early


def test_show_send_rgb_psbt_page_no_psbt(send_rgb_asset_widget: SendRGBAssetWidget):
    """show_send_rgb_psbt_page should handle empty/None psbt gracefully."""
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.show_send_rgb_psbt_page(None)
    send_rgb_asset_widget.show_send_rgb_psbt_page('')
    # Should not raise any errors


def test_send_rgb_asset_button_hardware_wallet(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test send_rgb_asset_button for hardware wallet + online wallet path."""
    mock_send_rgb_asset_page = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page = mock_send_rgb_asset_page
    mock_send_rgb_asset_page.asset_address_value.text.return_value = 'some_invoice'
    mock_send_rgb_asset_page.asset_amount_value.text.return_value = '10'
    mock_send_rgb_asset_page.fee_rate_value.text.return_value = '0.01'

    mock_default_min_confirmation = MagicMock()
    mock_default_min_confirmation.min_confirmation = 1
    mocker.patch(
        'src.data.repository.setting_card_repository.SettingCardRepository.get_default_min_confirmation',
        return_value=mock_default_min_confirmation,
    )

    mock_decoded_rgb_invoice = MagicMock()
    mock_decoded_rgb_invoice.recipient_id = 'recipient_id'
    mock_decoded_rgb_invoice.transport_endpoints = 'some_endpoints'
    mock_decoded_rgb_invoice.assignment = type(
        'DummyAssign', (object,), {
            '__init__': lambda self, amount=1: setattr(self, 'amount', amount),
        },
    )()
    mocker.patch(
        'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
        return_value=mock_decoded_rgb_invoice,
    )

    # Force hardware wallet + online wallet path
    send_rgb_asset_widget.is_hardware_wallet = True
    send_rgb_asset_widget.is_online_wallet = True
    send_rgb_asset_widget.is_watch_only = False
    send_rgb_asset_widget.is_multisig = False

    mock_send_begin = MagicMock()
    send_rgb_asset_widget._view_model.cfa_view_model.send_begin = mock_send_begin

    send_rgb_asset_widget.send_rgb_asset_button()

    assert send_rgb_asset_widget.loading_performer == 'SEND_BUTTON'
    mock_send_begin.assert_called_once()


def test_send_rgb_asset_button_watch_only(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """Test send_rgb_asset_button for watch-only wallet path."""
    mock_send_rgb_asset_page = MagicMock()
    send_rgb_asset_widget.send_rgb_asset_page = mock_send_rgb_asset_page
    mock_send_rgb_asset_page.asset_address_value.text.return_value = 'some_invoice'
    mock_send_rgb_asset_page.asset_amount_value.text.return_value = '10'
    mock_send_rgb_asset_page.fee_rate_value.text.return_value = '0.01'

    mock_default_min_confirmation = MagicMock()
    mock_default_min_confirmation.min_confirmation = 1
    mocker.patch(
        'src.data.repository.setting_card_repository.SettingCardRepository.get_default_min_confirmation',
        return_value=mock_default_min_confirmation,
    )

    mock_decoded_rgb_invoice = MagicMock()
    mock_decoded_rgb_invoice.recipient_id = 'recipient_id'
    mock_decoded_rgb_invoice.transport_endpoints = 'some_endpoints'
    mock_decoded_rgb_invoice.assignment = type(
        'DummyAssign', (object,), {
            '__init__': lambda self, amount=1: setattr(self, 'amount', amount),
        },
    )()
    mocker.patch(
        'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
        return_value=mock_decoded_rgb_invoice,
    )

    # Force watch-only path
    send_rgb_asset_widget.is_hardware_wallet = False
    send_rgb_asset_widget.is_online_wallet = False
    send_rgb_asset_widget.is_watch_only = True
    send_rgb_asset_widget.is_multisig = False

    mock_send_begin = MagicMock()
    send_rgb_asset_widget._view_model.cfa_view_model.send_begin = mock_send_begin

    send_rgb_asset_widget.send_rgb_asset_button()

    mock_send_begin.assert_called_once()


def test_handle_send_rgb_hw_dialog_update_not_visible(send_rgb_asset_widget: SendRGBAssetWidget):
    """handle_send_rgb_hw_dialog_update should return early when widget not visible."""
    send_rgb_asset_widget.hide()
    send_rgb_asset_widget.handle_send_rgb_hw_dialog_update('msg', MagicMock())
    # Should return early without processing


def test_handle_send_rgb_hw_dialog_update_success(send_rgb_asset_widget: SendRGBAssetWidget, mocker, monkeypatch):
    """handle_send_rgb_hw_dialog_update should accept dialog on SUCCESS status."""
    send_rgb_asset_widget.show()
    dummy = MagicMock()
    dummy.isVisible.return_value = True
    monkeypatch.setattr(
        'src.views.ui_send_rgb_asset.HardwareWalletOperationDialog.get_instance',
        lambda parent: dummy,
    )

    send_rgb_asset_widget.handle_send_rgb_hw_dialog_update(
        'msg', PsbtStatus.SUCCESS,
    )

    dummy.accept.assert_called_once()


def test_handle_send_rgb_hw_dialog_update_utxo_error(send_rgb_asset_widget: SendRGBAssetWidget, mocker, monkeypatch):
    """handle_send_rgb_hw_dialog_update should handle NoAvailableUtxos error and create UTXOs."""
    send_rgb_asset_widget.show()
    send_rgb_asset_widget.is_multisig = False
    send_rgb_asset_widget.is_watch_only = False

    dummy = MagicMock()
    dummy.isVisible.return_value = True
    monkeypatch.setattr(
        'src.views.ui_send_rgb_asset.HardwareWalletOperationDialog.get_instance',
        lambda parent: dummy,
    )

    # Mock SettingRepository to simulate non-single-sig-online wallet (creates 3 UTXOs)
    mocker.patch(
        'src.views.ui_send_rgb_asset.SettingRepository.get_wallet_signature_type',
        return_value=MagicMock(value='multisig'),
    )
    mocker.patch(
        'src.views.ui_send_rgb_asset.WalletSignatureType',
        STANDARD_TYPE_WALLET=MagicMock(value='standard'),
    )
    mocker.patch(
        'src.views.ui_send_rgb_asset.WalletAccessType',
        WATCH_ONLY=MagicMock(value='watch_only'),
    )
    mocker.patch(
        'src.views.ui_send_rgb_asset.WalletType',
        ONLINE_TYPE_WALLET=MagicMock(value='online'),
    )

    # Mock the UTXO creation flow
    mock_create_utxos = mocker.patch.object(
        send_rgb_asset_widget._view_model.utxo_creation_view_model, 'create_utxos_begin',
    )

    send_rgb_asset_widget.handle_send_rgb_hw_dialog_update(
        'NoAvailableUtxos error', PsbtStatus.ERROR,
    )

    assert send_rgb_asset_widget._retry_after_utxo is True
    mock_create_utxos.assert_called_once_with(purpose='send_rgb', num=3)


def test_on_utxo_unsigned_psbt_wrong_purpose(send_rgb_asset_widget: SendRGBAssetWidget):
    """_on_utxo_unsigned_psbt should return early if purpose is not 'send_rgb'."""
    send_rgb_asset_widget._view_model.utxo_creation_view_model.current_purpose = 'other_purpose'
    send_rgb_asset_widget._on_utxo_unsigned_psbt('psbt')
    # Should return early


def test_on_utxo_unsigned_psbt_correct_purpose(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """_on_utxo_unsigned_psbt should navigate to PSBT page for 'send_rgb' purpose."""
    send_rgb_asset_widget._view_model.utxo_creation_view_model.current_purpose = 'send_rgb'
    send_rgb_asset_widget.show()
    mock_show_psbt = mocker.patch.object(
        send_rgb_asset_widget, 'show_send_rgb_psbt_page',
    )

    send_rgb_asset_widget._on_utxo_unsigned_psbt('psbt-data')

    mock_show_psbt.assert_called_once_with('psbt-data')


def test_on_utxo_created_and_retry_success(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """_on_utxo_created_and_retry should retry send when ok=True and _retry_after_utxo=True."""
    send_rgb_asset_widget._retry_after_utxo = True
    mock_send = mocker.patch.object(
        send_rgb_asset_widget, 'send_rgb_asset_button',
    )

    send_rgb_asset_widget._on_utxo_created_and_retry(True)

    assert send_rgb_asset_widget._retry_after_utxo is False
    mock_send.assert_called_once()


def test_on_utxo_created_and_retry_not_ok(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """_on_utxo_created_and_retry should not retry when ok=False."""
    send_rgb_asset_widget._retry_after_utxo = True
    mock_send = mocker.patch.object(
        send_rgb_asset_widget, 'send_rgb_asset_button',
    )

    send_rgb_asset_widget._on_utxo_created_and_retry(False)

    mock_send.assert_not_called()


def test_on_utxo_posted_to_bridge(send_rgb_asset_widget: SendRGBAssetWidget, mocker):
    """_on_utxo_posted_to_bridge should show toast and navigate back."""
    send_rgb_asset_widget.show()
    send_rgb_asset_widget._view_model.utxo_creation_view_model.current_purpose = 'send_rgb'
    send_rgb_asset_widget.send_rgb_hw_dialog = MagicMock()

    mock_toast = mocker.patch(
        'src.views.ui_send_rgb_asset.ToastManager.success',
    )
    mock_nav = mocker.patch.object(
        send_rgb_asset_widget, 'rgb_asset_page_navigation',
    )

    send_rgb_asset_widget._on_utxo_posted_to_bridge()

    mock_toast.assert_called_once()
    mock_nav.assert_called_once()
    send_rgb_asset_widget.send_rgb_hw_dialog.accept.assert_called_once()


def test_on_utxo_posted_to_bridge_wrong_purpose(send_rgb_asset_widget: SendRGBAssetWidget):
    """_on_utxo_posted_to_bridge should return early if purpose is not 'send_rgb'."""
    send_rgb_asset_widget._view_model.utxo_creation_view_model.current_purpose = 'other'
    send_rgb_asset_widget._on_utxo_posted_to_bridge()
    # Should return early


def test_on_utxo_posted_to_bridge_not_visible(send_rgb_asset_widget: SendRGBAssetWidget):
    """_on_utxo_posted_to_bridge should return early if widget not visible."""
    send_rgb_asset_widget._view_model.utxo_creation_view_model.current_purpose = 'send_rgb'
    send_rgb_asset_widget.hide()
    send_rgb_asset_widget._on_utxo_posted_to_bridge()
    # Should return early


def test_send_rgb_asset_widget_with_draft_data(qtbot, mocker):
    """Test SendRGBAssetWidget initialization with draft_data."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    asset_balance = Balance(future=100, spendable=50, settled=100)
    txn_list = MagicMock(ListTransferAssetWithBalanceResponseModel)
    txn_list.asset_balance = asset_balance
    view_model.cfa_view_model.txn_list = txn_list
    view_model.cfa_view_model.is_loading = MagicMock()
    view_model.cfa_view_model.stop_loading = MagicMock()

    draft_data = {
        'asset_id': 'test-asset-id',
        'recipient_id': 'test-recipient',
        'amount': 100,
    }

    widget = SendRGBAssetWidget(view_model, draft_data=draft_data)
    qtbot.addWidget(widget)

    assert widget.asset_id == 'test-asset-id'
    assert widget.send_rgb_asset_page.asset_address_value.text() == 'test-recipient'
    assert widget.send_rgb_asset_page.asset_amount_value.text() == '100'
