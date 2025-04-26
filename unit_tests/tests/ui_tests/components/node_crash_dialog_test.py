# pylint:disable = unused-variable
"""Unit tests for node crash dialog box"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox

from src.views.components.node_crash_dialog import CrashDialogBox


@patch('src.views.components.node_crash_dialog.QMessageBox')
@patch('src.views.components.node_crash_dialog.QCoreApplication.translate')
def test_crash_dialog_box(mock_translate, mock_qmessagebox):
    """Test CrashDialogBox initialization and dialog setup."""

    # Mock translations
    mock_translate.side_effect = lambda ctx, text, _: f"Translated-{text}"

    # Mock QMessageBox instance
    mock_message_box_instance = MagicMock()
    mock_qmessagebox.return_value = mock_message_box_instance

    # Explicitly configure the mocked QMessageBox to return the real enum value
    mock_qmessagebox.Icon.Critical = QMessageBox.Icon.Critical

    # Initialize the CrashDialogBox
    crash_dialog = CrashDialogBox()

    # Verify QMessageBox instance was created
    mock_qmessagebox.assert_called_once()

    # Check icon setup (now correctly returning the real QMessageBox.Icon.Critical)
    mock_message_box_instance.setIcon.assert_called_once_with(
        QMessageBox.Icon.Critical,
    )
