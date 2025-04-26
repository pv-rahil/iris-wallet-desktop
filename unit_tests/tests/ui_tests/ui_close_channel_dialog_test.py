"""Unit test for Close Channel Dialog."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions.
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_close_channel_dialog import CloseChannelDialog


@pytest.fixture
def close_channel_dialog_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_close_channel_dialog_view_model(close_channel_dialog_page_navigation):
    """Fixture to create a MainViewModel instance with mocked page navigation."""
    return MainViewModel(close_channel_dialog_page_navigation)


@pytest.fixture
def close_channel_dialog(qtbot, mock_close_channel_dialog_view_model):
    """Fixture to create the CloseChannelDialog instance."""
    dialog = CloseChannelDialog(
        page_navigate='Fungibles Page', pub_key='mock_pub_key', channel_id='mock_channel_id',
    )
    qtbot.addWidget(dialog)
    return dialog


def test_dialog_initialization(close_channel_dialog):
    """Test initialization of the CloseChannelDialog."""
    # Ensure that the dialog initializes with the correct public key and channel ID
    assert close_channel_dialog.pub_key == 'mock_pub_key'
    assert close_channel_dialog.channel_id == 'mock_channel_id'

    # Verify that the dialog has the correct window flags
    assert close_channel_dialog.windowFlags() & Qt.FramelessWindowHint

    # Check the labels and buttons are initialized with the correct text
    assert close_channel_dialog.close_channel_detail_text_label.text(
    ) == 'close_channel_prompt mock_pub_key?'
    assert close_channel_dialog.close_channel_cancel_button.text() == 'cancel'
    assert close_channel_dialog.close_channel_continue_button.text() == 'continue'


def test_cancel_button_closes_dialog(close_channel_dialog):
    """Test that clicking the cancel button closes the dialog."""
    # Mock the close method to verify it is called
    close_channel_dialog.close = MagicMock()

    # Simulate clicking the cancel button
    close_channel_dialog.close_channel_cancel_button.click()

    # Verify that the dialog's close method was called
    close_channel_dialog.close.assert_called_once()


def test_continue_button_closes_channel(close_channel_dialog):
    """Test that clicking the continue button closes the dialog and triggers channel close."""
    # Mock the close method and channel closing method
    close_channel_dialog.close = MagicMock()
    close_channel_dialog._view_model.channel_view_model.close_channel = MagicMock()

    # Simulate clicking the continue button
    close_channel_dialog.close_channel_continue_button.click()

    # Verify that the dialog's close method was called
    close_channel_dialog.close.assert_called_once()

    # Ensure the channel close method was called with correct arguments
    close_channel_dialog._view_model.channel_view_model.close_channel.assert_called_once_with(
        channel_id='mock_channel_id', pub_key='mock_pub_key',
    )


def test_dialog_cancel_action(close_channel_dialog):
    """Test that clicking cancel closes the dialog without calling the close_channel method."""
    # Mock the close method and the channel close method
    close_channel_dialog.close = MagicMock()
    close_channel_dialog._view_model.channel_view_model.close_channel = MagicMock()

    # Simulate clicking the cancel button
    close_channel_dialog.close_channel_cancel_button.click()

    # Verify that the channel close method was NOT called
    close_channel_dialog._view_model.channel_view_model.close_channel.assert_not_called()

    # Verify that the dialog's close method was called
    close_channel_dialog.close.assert_called_once()


def test_channel_close_functionality(close_channel_dialog):
    """Test that the close_channel function behaves as expected."""
    # Mock the close method
    close_channel_dialog.close = MagicMock()

    # Mock the close_channel method in the view model
    close_channel_dialog._view_model.channel_view_model.close_channel = MagicMock()

    # Call the close_channel method directly
    close_channel_dialog.close_channel()

    # Verify that the view model's close_channel method was called with the correct arguments
    close_channel_dialog._view_model.channel_view_model.close_channel.assert_called_once_with(
        channel_id='mock_channel_id', pub_key='mock_pub_key',
    )

    # Verify that the dialog close method was called
    close_channel_dialog.close.assert_called_once()


def test_close_channel_without_pub_key(close_channel_dialog):
    """Test for invalid pub_key scenario (empty pub_key)."""
    # Mock the close_channel method
    close_channel_dialog._view_model.channel_view_model.close_channel = MagicMock()

    close_channel_dialog.pub_key = ''  # Set an empty pub_key

    # Call the close_channel method directly with invalid pub_key
    close_channel_dialog.close_channel()

    # Ensure that the close_channel method was still called with empty pub_key
    close_channel_dialog._view_model.channel_view_model.close_channel.assert_called_once_with(
        channel_id='mock_channel_id', pub_key='',
    )


def test_close_channel_without_channel_id(close_channel_dialog):
    """Test for invalid channel_id scenario (empty channel_id)."""
    close_channel_dialog.channel_id = ''  # Set invalid channel_id

    # Mock the close method
    close_channel_dialog.close = MagicMock()

    # Mock the close_channel method in the view model
    close_channel_dialog._view_model.channel_view_model.close_channel = MagicMock()

    # Call the close_channel method directly
    close_channel_dialog.close_channel()

    # Ensure that the close_channel method was still called with the invalid channel_id
    close_channel_dialog._view_model.channel_view_model.close_channel.assert_called_once_with(
        channel_id='', pub_key='mock_pub_key',
    )

    # Verify that the dialog's close method was called
    close_channel_dialog.close.assert_called_once()


@pytest.mark.parametrize(
    'pub_key, channel_id, expected_text',
    [
        ('mock_pub_key', 'mock_channel_id', 'close_channel_prompt mock_pub_key?'),
        (
            'invalid_pub_key', 'invalid_channel_id',
            'close_channel_prompt invalid_pub_key?',
        ),
    ],
)
def test_dynamic_retranslates_ui(close_channel_dialog, pub_key, channel_id, expected_text):
    """Test that the dialog text is updated dynamically."""
    close_channel_dialog.pub_key = pub_key
    close_channel_dialog.channel_id = channel_id
    close_channel_dialog.retranslate_ui()

    # Verify the dynamic text update for different pub_key and channel_id
    assert close_channel_dialog.close_channel_detail_text_label.text() == expected_text
