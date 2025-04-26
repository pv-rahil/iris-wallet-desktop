"""Unit test for Set wallet password ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-many-statements
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel

from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletType
from src.utils.constant import SYNCING_CHAIN_LABEL_TIMER
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_set_wallet_password import SetWalletPasswordWidget


@pytest.fixture
def set_wallet_password_widget(qtbot):
    """Fixture to create and return an instance of SetWalletPasswordWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = SetWalletPasswordWidget(
        view_model, WalletType.REMOTE_TYPE_WALLET.value,
    )
    qtbot.addWidget(widget)
    return widget


def test_close_navigation(set_wallet_password_widget: SetWalletPasswordWidget):
    """Test the close_navigation method."""
    set_wallet_password_widget.originating_page = WalletType.EMBEDDED_TYPE_WALLET.value

    # Test for Embedded Wallet Type
    set_wallet_password_widget.close_navigation()
    set_wallet_password_widget._view_model.page_navigation.welcome_page.assert_called_once()

    # Test for Connect Wallet Type
    set_wallet_password_widget.originating_page = WalletType.REMOTE_TYPE_WALLET.value
    set_wallet_password_widget.close_navigation()

    # Verify that wallet_connection_page is called with the correct parameters
    set_wallet_password_widget._view_model.page_navigation.wallet_connection_page.assert_called_once()
    args = set_wallet_password_widget._view_model.page_navigation.wallet_connection_page.call_args[
        0
    ]
    params = args[0]
    assert params.title == 'connection_type'
    assert params.logo_1_title == WalletType.EMBEDDED_TYPE_WALLET.value
    assert params.logo_2_title == WalletType.REMOTE_TYPE_WALLET.value


def test_set_password_suggestion(set_wallet_password_widget: SetWalletPasswordWidget):
    """Test the set_password_suggestion method."""
    # Mock the generate_password function
    set_wallet_password_widget._view_model.set_wallet_password_view_model.generate_password = MagicMock(
        return_value='StrongPass123',
    )

    set_wallet_password_widget.set_password_suggestion()

    # Verify that the text fields are set to the generated password
    assert set_wallet_password_widget.enter_password_input.text() == 'StrongPass123'
    assert set_wallet_password_widget.confirm_password_input.text() == 'StrongPass123'


def test_show_password_validation_label(set_wallet_password_widget: SetWalletPasswordWidget):
    """Test the show_password_validation_label method."""
    message = 'Password is too weak'
    set_wallet_password_widget.show_password_validation_label(message)

    assert isinstance(set_wallet_password_widget.password_validation, QLabel)
    assert set_wallet_password_widget.password_validation.text() == message
    assert set_wallet_password_widget.password_validation.objectName() == 'password_validation'
    assert set_wallet_password_widget.password_validation.minimumSize() == QSize(0, 25)
    style = set_wallet_password_widget.password_validation.styleSheet()
    assert 'font: 12px "Inter"' in style
    assert 'color: rgb(237, 51, 59);' in style
    assert 'background: transparent;' in style
    assert 'border: none;' in style
    assert 'font-weight: 400;' in style


def test_handle_button_enabled(set_wallet_password_widget: SetWalletPasswordWidget):
    """Test the handle_button_enabled method."""

    # Test when both fields are filled
    set_wallet_password_widget.enter_password_input.setText('password123')
    set_wallet_password_widget.confirm_password_input.setText('password123')
    set_wallet_password_widget.handle_button_enabled()
    assert set_wallet_password_widget.proceed_wallet_password.isEnabled()

    # Test when one field is empty
    set_wallet_password_widget.confirm_password_input.setText('')
    set_wallet_password_widget.handle_button_enabled()
    assert not set_wallet_password_widget.proceed_wallet_password.isEnabled()


def test_handle_message(set_wallet_password_widget: SetWalletPasswordWidget):
    """Test the handle_message method."""
    with patch('src.views.ui_set_wallet_password.ToastManager') as mock_toast_manager:
        # Test error message
        set_wallet_password_widget.handle_message(
            ToastPreset.ERROR, 'Test Error Message',
        )
        mock_toast_manager.error.assert_called_once_with('Test Error Message')
        mock_toast_manager.success.assert_not_called()

        # Reset mock
        mock_toast_manager.reset_mock()

        # Test success message
        set_wallet_password_widget.handle_message(
            ToastPreset.SUCCESS, 'Test Success Message',
        )
        mock_toast_manager.success.assert_called_once_with(
            'Test Success Message',
        )
        mock_toast_manager.error.assert_not_called()


def test_update_loading_state(set_wallet_password_widget: SetWalletPasswordWidget, mocker):
    """Test the update_loading_state method of SetWalletPasswordWidget."""

    # Mock UI elements and methods that will be interacted with in update_loading_state
    mock_proceed_wallet_password = MagicMock()
    set_wallet_password_widget.proceed_wallet_password = mock_proceed_wallet_password

    mock_close_btn_set_password_page = MagicMock()
    set_wallet_password_widget.close_btn_set_password_page = mock_close_btn_set_password_page

    mock_enter_password_input = MagicMock()
    set_wallet_password_widget.enter_password_input = mock_enter_password_input

    mock_confirm_password_input = MagicMock()
    set_wallet_password_widget.confirm_password_input = mock_confirm_password_input

    mock_password_suggestion_button = MagicMock()
    set_wallet_password_widget.password_suggestion_button = mock_password_suggestion_button

    mock_confirm_password_visibility_button = MagicMock()
    set_wallet_password_widget.confirm_password_visibility_button = mock_confirm_password_visibility_button

    mock_enter_password_visibility_button = MagicMock()
    set_wallet_password_widget.enter_password_visibility_button = mock_enter_password_visibility_button

    mock_header_line = MagicMock()
    set_wallet_password_widget.header_line = mock_header_line

    mock_footer_line = MagicMock()
    set_wallet_password_widget.footer_line = mock_footer_line

    mock_setup_wallet_password_widget = MagicMock()
    set_wallet_password_widget.setup_wallet_password_widget = mock_setup_wallet_password_widget

    mock_timer = MagicMock()
    set_wallet_password_widget.timer = mock_timer

    mock_syncing_chain_info_label = MagicMock()
    set_wallet_password_widget.syncing_chain_info_label = mock_syncing_chain_info_label

    # Test case 1: is_loading = True
    set_wallet_password_widget.update_loading_state(True)

    # Verify that the loading state started and UI elements were hidden or resized
    mock_proceed_wallet_password.start_loading.assert_called_once()
    mock_close_btn_set_password_page.hide.assert_called_once()
    mock_enter_password_input.hide.assert_called_once()
    mock_confirm_password_input.hide.assert_called_once()
    mock_password_suggestion_button.hide.assert_called_once()
    mock_confirm_password_visibility_button.hide.assert_called_once()
    mock_enter_password_visibility_button.hide.assert_called_once()
    mock_header_line.hide.assert_called_once()
    mock_footer_line.hide.assert_called_once()
    mock_setup_wallet_password_widget.setMinimumSize.assert_called_once_with(
        QSize(499, 150),
    )
    mock_setup_wallet_password_widget.setMaximumSize.assert_called_once_with(
        QSize(466, 200),
    )
    mock_timer.start.assert_called_once_with(SYNCING_CHAIN_LABEL_TIMER)

    # Test case 2: is_loading = False
    set_wallet_password_widget.update_loading_state(False)

    # Verify that the loading state stopped and UI elements were shown or resized
    mock_proceed_wallet_password.stop_loading.assert_called_once()
    mock_close_btn_set_password_page.show.assert_called_once()
    mock_enter_password_input.show.assert_called_once()
    mock_confirm_password_input.show.assert_called_once()
    mock_password_suggestion_button.show.assert_called_once()
    mock_confirm_password_visibility_button.show.assert_called_once()
    mock_enter_password_visibility_button.show.assert_called_once()
    mock_header_line.show.assert_called_once()
    mock_footer_line.show.assert_called_once()

    # Assert that setMinimumSize was called with the expected sizes, allowing for both calls
    mock_setup_wallet_password_widget.setMinimumSize.assert_any_call(
        QSize(499, 150),
    )
    mock_setup_wallet_password_widget.setMinimumSize.assert_any_call(
        QSize(499, 350),
    )

    mock_syncing_chain_info_label.hide.assert_called_once()
    mock_timer.stop.assert_called_once()


def test_toggle_password_visibility(set_wallet_password_widget: SetWalletPasswordWidget, mocker):
    """Test the toggle_password_visibility method of SetWalletPasswordWidget."""

    # Mock the view model and its set_wallet_password_view_model attribute
    mock_view_model = MagicMock()
    # Assign the mocked view model
    set_wallet_password_widget._view_model = mock_view_model

    mock_set_wallet_password_view_model = MagicMock()
    # Assign the mocked view model instance
    mock_view_model.set_wallet_password_view_model = mock_set_wallet_password_view_model

    # Mock the toggle_password_visibility method
    mock_toggle_password_visibility = mocker.patch.object(
        mock_set_wallet_password_view_model, 'toggle_password_visibility',
    )

    # Mock the line_edit element (the input field for the password)
    mock_line_edit = MagicMock()

    # Call the method to toggle the password visibility
    set_wallet_password_widget.toggle_password_visibility(mock_line_edit)

    # Verify that the toggle_password_visibility method was called once with the correct line_edit
    mock_toggle_password_visibility.assert_called_once_with(mock_line_edit)


def test_set_wallet_password(set_wallet_password_widget: SetWalletPasswordWidget, mocker):
    """Test the set_wallet_password method of SetWalletPasswordWidget."""

    # Mock the view model and its set_wallet_password_view_model attribute
    mock_view_model = MagicMock()
    mock_set_wallet_password_view_model = MagicMock()

    # Patch the view model and its attributes
    mocker.patch.object(
        set_wallet_password_widget,
        '_view_model',
        mock_view_model,
    )
    mocker.patch.object(
        mock_view_model,
        'set_wallet_password_view_model',
        mock_set_wallet_password_view_model,
    )

    # Mock the set_wallet_password_in_thread method
    mock_set_wallet_password_in_thread = mocker.patch.object(
        mock_set_wallet_password_view_model,
        'set_wallet_password_in_thread',
    )

    # Mock the enter_password_input, vertical_layout_setup_wallet_password
    mock_enter_password_input = MagicMock()
    mock_vertical_layout_setup_wallet_password = MagicMock()

    # Mock the show_password_validation_label
    mock_show_password_validation_label = MagicMock()
    mocker.patch.object(
        set_wallet_password_widget,
        'show_password_validation_label',
        mock_show_password_validation_label,
    )

    # Call the method to set the wallet password
    set_wallet_password_widget.set_wallet_password(
        mock_enter_password_input,
        mock_vertical_layout_setup_wallet_password,
    )

    # Verify that the set_wallet_password_in_thread method was called once with the correct parameters
    mock_set_wallet_password_in_thread.assert_called_once_with(
        mock_enter_password_input,
        mock_vertical_layout_setup_wallet_password,
        mock_show_password_validation_label,
    )
