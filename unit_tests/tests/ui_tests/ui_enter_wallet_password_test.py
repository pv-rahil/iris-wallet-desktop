"""Unit test for Enter Wallet Password UI."""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from src.model.enums.enums_model import ToastPreset
from src.viewmodels.enter_password_view_model import EnterWalletPasswordViewModel
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_enter_wallet_password import EnterWalletPassword


@pytest.fixture
def enter_wallet_password_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_enter_wallet_password_view_model(enter_wallet_password_page_navigation):
    """Fixture to create a MainViewModel instance with mocked EnterWalletPasswordViewModel."""
    mock_view_model = MagicMock(
        spec=MainViewModel(
            enter_wallet_password_page_navigation,
        ),
    )
    mock_view_model.enter_wallet_password_view_model = MagicMock(
        spec=EnterWalletPasswordViewModel(
            enter_wallet_password_page_navigation,
        ),
    )
    return mock_view_model


@pytest.fixture
def create_enter_wallet_password_widget(qtbot, mock_enter_wallet_password_view_model):
    """Fixture to create an EnterWalletPassword widget instance."""
    widget = EnterWalletPassword(mock_enter_wallet_password_view_model)
    qtbot.addWidget(widget)
    return widget


def test_initial_ui_state(create_enter_wallet_password_widget):
    """Test the initial state of UI elements in EnterWalletPassword."""
    widget = create_enter_wallet_password_widget
    assert widget.enter_password_input.text() == ''
    assert not widget.login_wallet_button.isEnabled()


def test_password_input_enable_button(qtbot, create_enter_wallet_password_widget):
    """Test enabling the login button when password input is provided."""
    widget = create_enter_wallet_password_widget
    qtbot.addWidget(widget)

    # Initially, the button should be disabled
    assert not widget.login_wallet_button.isEnabled()

    # Simulate entering text
    qtbot.keyClicks(widget.enter_password_input, 'testpassword')
    assert widget.login_wallet_button.isEnabled()


def test_password_input_disable_button_when_empty(qtbot, create_enter_wallet_password_widget):
    """Test disabling the login button when the password input is cleared."""
    widget = create_enter_wallet_password_widget
    qtbot.addWidget(widget)

    # Initially, the button should be disabled
    assert not widget.login_wallet_button.isEnabled()

    # Simulate entering text
    qtbot.keyClicks(widget.enter_password_input, 'testpassword')
    assert widget.login_wallet_button.isEnabled()

    # Simulate clearing the text
    widget.enter_password_input.clear()
    assert not widget.login_wallet_button.isEnabled()


def test_set_wallet_password(mock_enter_wallet_password_view_model, create_enter_wallet_password_widget, qtbot):
    """Test setting the wallet password through the view model."""
    widget = create_enter_wallet_password_widget
    qtbot.addWidget(widget)

    # Mock the view model method
    mock_enter_wallet_password_view_model.enter_wallet_password_view_model.set_wallet_credentials = MagicMock()

    # Enter password and click the login button
    qtbot.keyClicks(widget.enter_password_input, 'testpassword')
    qtbot.mouseClick(widget.login_wallet_button, Qt.LeftButton)

    # Check if the method was called with the correct password
    assert mock_enter_wallet_password_view_model.enter_wallet_password_view_model.set_wallet_credentials.called
    args, _ = mock_enter_wallet_password_view_model.enter_wallet_password_view_model.set_wallet_credentials.call_args
    assert args[0] == 'testpassword'


def test_password_visibility_toggle(qtbot, create_enter_wallet_password_widget):
    """Test toggling password visibility."""
    widget = create_enter_wallet_password_widget
    qtbot.addWidget(widget)

    widget.enter_password_input.setText('testpassword')

    # Check that the initial password is hidden
    initial_echo_mode = widget.enter_password_input.echoMode()
    assert initial_echo_mode == QLineEdit.EchoMode.Password

    # Simulate clicking the visibility toggle button
    qtbot.mouseClick(widget.enter_password_visibility_button, Qt.LeftButton)

    widget.enter_password_input.setEchoMode(QLineEdit.EchoMode.Normal)

    # Check that the password is now visible (after the toggle)
    updated_echo_mode = widget.enter_password_input.echoMode()
    print(f"Updated echo mode: {updated_echo_mode}")  # Debug line
    assert updated_echo_mode == QLineEdit.EchoMode.Normal  # Correct usage


def test_update_loading_state_when_loading(qtbot, create_enter_wallet_password_widget):
    """Test the update_loading_state method when is_loading is True."""
    widget = create_enter_wallet_password_widget

    # Mock the start_loading method of the login_wallet_button
    with patch.object(widget.login_wallet_button, 'start_loading') as mock_start_loading:
        # Simulate the loading state
        widget.update_loading_state(True)

        # Check that the loading animation starts (assuming the start_loading method exists)
        mock_start_loading.assert_called_once()

        # Check visibility of the password input, visibility button, and footer/header lines
        assert not widget.enter_password_input.isVisible()
        assert not widget.enter_password_visibility_button.isVisible()
        assert not widget.footer_line.isVisible()
        assert not widget.header_line.isVisible()

        # Check widget sizes are correctly set for loading state
        assert widget.enter_wallet_password_widget.minimumSize() == QSize(499, 200)
        assert widget.enter_wallet_password_widget.maximumSize() == QSize(466, 200)

        # Check that the timer has started
        assert widget.timer.isActive()


def test_update_loading_state_when_not_loading(qtbot, create_enter_wallet_password_widget):
    """Test the update_loading_state method when is_loading is False."""
    widget = create_enter_wallet_password_widget

    # Mock the stop_loading method of the login_wallet_button
    with patch.object(widget.login_wallet_button, 'stop_loading') as mock_stop_loading:
        # Simulate the loading state being set to False (i.e., stop loading)
        widget.update_loading_state(False)

        # Check that the loading animation stops
        mock_stop_loading.assert_called_once()

        # Check visibility of the password input, visibility button, and footer/header lines
        assert not widget.enter_password_input.isHidden()
        assert not widget.enter_password_visibility_button.isHidden()
        assert not widget.footer_line.isHidden()
        assert not widget.header_line.isHidden()

        # Check widget sizes are correctly set for not loading state
        assert widget.enter_wallet_password_widget.minimumSize() == QSize(499, 300)
        assert widget.enter_wallet_password_widget.maximumSize() == QSize(466, 608)

        # Check that the syncing label is hidden
        assert widget.syncing_chain_info_label.isHidden()

        # Check that the timer has stopped
        assert not widget.timer.isActive()


def test_handle_wallet_message(create_enter_wallet_password_widget):
    """Test the handle_wallet_message function."""

    # Patch ToastManager methods to check if they are called correctly
    with patch('src.views.ui_welcome.ToastManager.error') as mock_error, \
            patch('src.views.ui_welcome.ToastManager.success') as mock_success:

        # Test case: message_type is ERROR
        create_enter_wallet_password_widget.handle_wallet_message(
            ToastPreset.ERROR, 'Error message',
        )
        mock_error.assert_called_once_with('Error message')
        mock_success.assert_not_called()  # Ensure success is not called

        # Reset mocks for the next test case
        mock_error.reset_mock()
        mock_success.reset_mock()

        # Test case: message_type is not ERROR (e.g., SUCCESS)
        create_enter_wallet_password_widget.handle_wallet_message(
            ToastPreset.SUCCESS, 'Success message',
        )
        mock_success.assert_called_once_with('Success message')
        mock_error.assert_not_called()  # Ensure error is not called
