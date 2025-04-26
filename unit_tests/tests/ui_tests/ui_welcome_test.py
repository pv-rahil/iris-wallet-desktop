"""Unit test for Welcome ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import ToastPreset
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_welcome import WelcomeWidget


@pytest.fixture
def welcome_widget(qtbot):
    """Fixture to create and return an instance of WelcomeWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = WelcomeWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_update_create_status(welcome_widget: WelcomeWidget):
    """Test the update_create_status method of WelcomeWidget."""
    # Test when is_created is True
    welcome_widget.update_create_status(True)
    assert welcome_widget.create_btn.text() == 'Creating...'
    assert not welcome_widget.create_btn.isEnabled()

    # Test when is_created is False
    welcome_widget.update_create_status(False)
    assert welcome_widget.create_btn.text() == 'create_button'
    assert welcome_widget.create_btn.isEnabled()


def test_restore_wallet(welcome_widget: WelcomeWidget):
    """Test the restore_wallet method of WelcomeWidget."""
    with patch('PySide6.QtWidgets.QGraphicsBlurEffect') as mock_blur_effect, \
            patch('src.views.ui_welcome.RestoreMnemonicWidget') as mock_restore_widget:
        mock_blur_effect.return_value = MagicMock()
        mock_restore_widget.return_value = MagicMock()

        welcome_widget.restore_wallet()

        assert mock_restore_widget.called


def test_update_loading_state(welcome_widget: WelcomeWidget):
    """Test the update_loading_state method of WelcomeWidget."""
    # Test when is_loading is True
    welcome_widget.update_loading_state(True)
    assert not welcome_widget.create_btn.isEnabled()

    # Test when is_loading is False
    welcome_widget.update_loading_state(False)
    assert welcome_widget.create_btn.isEnabled()


def test_handle_message(welcome_widget: WelcomeWidget):
    """Test the handle_message method of WelcomeWidget."""
    with patch('src.views.ui_welcome.ToastManager') as mock_toast_manager:
        welcome_widget.handle_message(ToastPreset.ERROR, 'Test Error Message')
        mock_toast_manager.error.assert_called_once_with('Test Error Message')
        mock_toast_manager.success.assert_not_called()

        welcome_widget.handle_message(
            ToastPreset.SUCCESS, 'Test Success Message',
        )
        mock_toast_manager.error.assert_called_once()
        mock_toast_manager.success.assert_called_once_with(
            'Test Success Message',
        )
