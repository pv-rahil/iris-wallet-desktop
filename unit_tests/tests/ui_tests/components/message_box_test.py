"""Unit test for message box."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import patch

from src.views.components.message_box import MessageBox


@patch('src.views.components.message_box.QMessageBox')
def test_message_box_information(mock_msg_box):
    """Test the MessageBox class with 'information' type."""
    mock_instance = mock_msg_box.return_value

    message_type = 'information'
    message_text = 'This is an information message.'

    # Create the MessageBox instance
    _ = MessageBox(message_type, message_text)

    # Assertions to ensure QMessageBox methods are called correctly
    mock_msg_box.assert_called_once()
    mock_instance.setWindowTitle.assert_called_once_with('Information')
    mock_instance.setIcon.assert_called_once_with(mock_msg_box.Information)
    mock_instance.setText.assert_called_once_with(message_text)
    mock_instance.exec.assert_called_once()


@patch('src.views.components.message_box.QMessageBox')
def test_message_box_warning(mock_msg_box):
    """Test the MessageBox class with 'warning' type."""
    mock_instance = mock_msg_box.return_value

    message_type = 'warning'
    message_text = 'This is a warning message.'

    # Create the MessageBox instance
    _ = MessageBox(message_type, message_text)

    # Assertions to ensure QMessageBox methods are called correctly
    mock_msg_box.assert_called_once()
    mock_instance.setWindowTitle.assert_called_once_with('Warning')
    mock_instance.setIcon.assert_called_once_with(mock_msg_box.Warning)
    mock_instance.setText.assert_called_once_with(message_text)
    mock_instance.exec.assert_called_once()


@patch('src.views.components.message_box.QMessageBox')
def test_message_box_critical(mock_msg_box):
    """Test the MessageBox class with 'critical' type."""
    mock_instance = mock_msg_box.return_value

    message_type = 'critical'
    message_text = 'This is a critical message.'

    # Create the MessageBox instance
    _ = MessageBox(message_type, message_text)

    # Assertions to ensure QMessageBox methods are called correctly
    mock_msg_box.assert_called_once()
    mock_instance.setWindowTitle.assert_called_once_with('Critical')
    mock_instance.setIcon.assert_called_once_with(mock_msg_box.Critical)
    mock_instance.setText.assert_called_once_with(message_text)
    mock_instance.exec.assert_called_once()


@patch('src.views.components.message_box.QMessageBox')
def test_message_box_success(mock_msg_box):
    """Test the MessageBox class with 'success' type."""
    mock_instance = mock_msg_box.return_value

    message_type = 'success'
    message_text = 'This is a success message.'

    # Create the MessageBox instance
    _ = MessageBox(message_type, message_text)

    # Assertions to ensure QMessageBox methods are called correctly
    mock_msg_box.assert_called_once()
    mock_instance.setWindowTitle.assert_called_once_with('Success')
    mock_instance.setIcon.assert_called_once_with(mock_msg_box.Information)
    mock_instance.setText.assert_called_once_with(message_text)
    mock_instance.exec.assert_called_once()


@patch('src.views.components.message_box.QMessageBox')
def test_message_box_noicon(mock_msg_box):
    """Test the MessageBox class with an unknown type."""
    mock_instance = mock_msg_box.return_value

    message_type = 'unknown'
    message_text = 'This is a message with no icon.'

    # Create the MessageBox instance
    _ = MessageBox(message_type, message_text)

    # Assertions to ensure QMessageBox methods are called correctly
    mock_msg_box.assert_called_once()
    mock_instance.setWindowTitle.assert_called_once_with('Unknown')
    mock_instance.setIcon.assert_called_once_with(mock_msg_box.NoIcon)
    mock_instance.setText.assert_called_once_with(message_text)
    mock_instance.exec.assert_called_once()
