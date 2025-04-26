"""Unit test for SplashScreenWidget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import SYNCING_CHAIN_LABEL_TIMER
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_splash_screen import SplashScreenWidget


@pytest.fixture
def splash_screen_widget(qtbot):
    """Fixture to create and return an instance of SplashScreenWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = SplashScreenWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(splash_screen_widget: SplashScreenWidget):
    """Test the retranslation of UI elements in SplashScreenWidget."""
    splash_screen_widget.retranslate_ui()
    expected_title = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'iris_wallet Regtest', None,
    )
    assert splash_screen_widget.logo_text_label.text() == expected_title
    assert splash_screen_widget.note_text_label.text() == 'auth_message'


def test_set_message_text(splash_screen_widget: SplashScreenWidget):
    """Test the set_message_text method."""
    message = 'Loading wallet...'
    splash_screen_widget.set_message_text(message)

    # Assert that the message is set correctly in the label
    assert splash_screen_widget.note_text_label.text() == message


def test_set_sync_chain_info_label(splash_screen_widget: SplashScreenWidget, mocker):
    """Test that the sync chain info label is updated when the timer times out."""

    # Mock the QCoreApplication.translate to simulate translation behavior.
    mock_translate = mocker.patch.object(
        QCoreApplication, 'translate', return_value='auth_message',
    )

    # Create a mock for the syncing_chain_label_timer (this could be your actual timer object).
    mock_timer = MagicMock()
    splash_screen_widget.syncing_chain_label_timer = mock_timer

    # Create a mock for the label to verify setText method
    mock_label = MagicMock()
    splash_screen_widget.note_text_label = mock_label

    # Call the method
    splash_screen_widget.set_sync_chain_info_label()

    # Verify that the timer started with the correct interval
    splash_screen_widget.syncing_chain_label_timer.start.assert_called_once_with(
        SYNCING_CHAIN_LABEL_TIMER,
    )

    # Manually invoke the lambda that would have been called on timeout
    lambda_function = splash_screen_widget.syncing_chain_label_timer.timeout.connect.call_args[
        0
    ][0]
    lambda_function()

    # Ensure QCoreApplication.translate was called with the correct parameters
    mock_translate.assert_called_once_with(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'syncing_chain_info', None,
    )

    # Ensure that setText was called on the label with the translated text
    # Ensure setText was called with 'auth_message'
    mock_label.setText.assert_called_once_with('auth_message')
