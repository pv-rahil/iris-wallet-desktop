"""Unit test for Restore Mnemonic ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize

from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


@pytest.fixture
def restore_mnemonic_widget(qtbot):
    """Fixture to create and return an instance of RestoreMnemonicWidget."""
    mock_navigation = MagicMock()
    view_model = MainViewModel(mock_navigation)
    view_model.backup_view_model = MagicMock()
    widget = RestoreMnemonicWidget(None, view_model)
    qtbot.addWidget(widget)
    return widget


def test_setup_ui_connection(restore_mnemonic_widget):
    """Test that UI connections are set up correctly."""
    restore_mnemonic_widget.cancel_button.clicked.emit()
    restore_mnemonic_widget.password_input.textChanged.emit('password')
    restore_mnemonic_widget.mnemonic_input.textChanged.emit('mnemonic')

    restore_mnemonic_widget.cancel_button.clicked.disconnect()
    restore_mnemonic_widget.password_input.textChanged.disconnect()
    restore_mnemonic_widget.mnemonic_input.textChanged.disconnect()


def test_handle_button_enable(restore_mnemonic_widget, qtbot):
    """Test the enable/disable state of the continue button based on input fields."""
    # Test when mnemonic is visible and both fields are empty
    restore_mnemonic_widget.mnemonic_visibility = True
    restore_mnemonic_widget.mnemonic_input.setText('')
    restore_mnemonic_widget.password_input.setText('')
    restore_mnemonic_widget.handle_button_enable()
    assert not restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is visible and both fields are filled
    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_button_enable()
    assert restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is not visible and password is empty
    restore_mnemonic_widget.mnemonic_visibility = False
    restore_mnemonic_widget.password_input.setText('')
    restore_mnemonic_widget.handle_button_enable()
    assert not restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is not visible and password is filled
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_button_enable()
    assert restore_mnemonic_widget.continue_button.isEnabled()


def test_retranslate_ui(restore_mnemonic_widget, qtbot):
    """Test that UI texts are set correctly."""
    restore_mnemonic_widget.retranslate_ui()

    assert restore_mnemonic_widget.mnemonic_detail_text_label.text(
    ) == 'enter_mnemonic_phrase_info'
    assert restore_mnemonic_widget.mnemonic_input.placeholderText() == 'input_phrase'
    assert restore_mnemonic_widget.cancel_button.text() == 'cancel'
    assert restore_mnemonic_widget.continue_button.text() == 'continue'
    assert restore_mnemonic_widget.password_input.placeholderText() == 'enter_wallet_password'


def test_handle_on_keyring_toggle_enable(restore_mnemonic_widget, qtbot):
    """Test that enable_keyring is called with correct arguments and dialog closes."""
    restore_mnemonic_widget._view_model.setting_view_model.enable_keyring = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_on_keyring_toggle_enable()

    restore_mnemonic_widget._view_model.setting_view_model.enable_keyring.assert_called_once_with(
        mnemonic='mnemonic', password='password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_restore_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on restore_page."""
    restore_mnemonic_widget.origin_page = 'restore_page'
    restore_mnemonic_widget.restore_wallet = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.restore_wallet.assert_called_once()
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_setting_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on setting_page."""
    restore_mnemonic_widget.origin_page = 'setting_page'
    restore_mnemonic_widget.handle_on_keyring_toggle_enable = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.handle_on_keyring_toggle_enable.assert_called_once()
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_backup_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on backup_page."""
    restore_mnemonic_widget.origin_page = 'backup_page'
    restore_mnemonic_widget._view_model.backup_view_model.backup_when_keyring_unaccessible = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget._view_model.backup_view_model.backup_when_keyring_unaccessible.assert_called_once_with(
        mnemonic='mnemonic', password='password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_on_close(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on on_close."""
    restore_mnemonic_widget.origin_page = 'on_close'
    restore_mnemonic_widget.on_continue = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.on_continue.emit.assert_called_once_with(
        'mnemonic', 'password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_setting_card(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on setting_card."""
    restore_mnemonic_widget.origin_page = 'setting_card'
    restore_mnemonic_widget.accept = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.accept.assert_called_once()


def test_on_continue_button_click_unknown_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked with unknown origin page."""
    restore_mnemonic_widget.origin_page = 'unknown_page'
    mock_toast = MagicMock()

    with patch('src.views.ui_restore_mnemonic.ToastManager', mock_toast):
        restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
        restore_mnemonic_widget.password_input.setText('password')
        restore_mnemonic_widget.on_continue_button_click()

        mock_toast.error.assert_called_once_with('Unknown origin page')


def test_on_click_cancel(restore_mnemonic_widget, qtbot):
    """Test that the dialog closes when cancel button is clicked."""
    restore_mnemonic_widget.close = MagicMock()

    restore_mnemonic_widget.on_click_cancel()

    restore_mnemonic_widget.close.assert_called_once()


def test_handle_mnemonic_input_visibility(restore_mnemonic_widget):
    """Test the handle_mnemonic_input_visibility method."""
    # Mock the mnemonic_input
    restore_mnemonic_widget.mnemonic_input = MagicMock()

    # Test when mnemonic_visibility is False
    restore_mnemonic_widget.mnemonic_visibility = False
    restore_mnemonic_widget.handle_mnemonic_input_visibility()

    # Verify mnemonic input is hidden and size is reduced
    restore_mnemonic_widget.mnemonic_input.hide.assert_called_once()
    assert restore_mnemonic_widget.maximumSize() == QSize(370, 220)

    # Reset mock
    restore_mnemonic_widget.mnemonic_input.reset_mock()

    # Test when mnemonic_visibility is True
    restore_mnemonic_widget.mnemonic_visibility = True
    restore_mnemonic_widget.handle_mnemonic_input_visibility()

    # Verify size is expanded first
    assert restore_mnemonic_widget.maximumSize() == QSize(370, 292)

    # Then verify mnemonic input is shown
    restore_mnemonic_widget.mnemonic_input.show.assert_called_once()
