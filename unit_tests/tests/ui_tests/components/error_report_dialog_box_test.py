"""Unit test for error report dialog component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.local_store import local_store
from src.version import __version__
from src.views.components.error_report_dialog_box import ErrorReportDialog
from src.views.components.toast import ToastManager


@pytest.fixture
def error_report_dialog(qtbot):
    """Fixture to create and return an instance of ErrorReportDialog."""
    dialog = ErrorReportDialog()
    qtbot.addWidget(dialog)
    return dialog


def test_dialog_initialization(error_report_dialog):
    """Test if the ErrorReportDialog initializes with correct properties."""
    dialog = error_report_dialog

    # Test window title
    expected_title = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'error_report', None,
    )
    assert dialog.windowTitle() == expected_title

    # Test if main components exist
    assert isinstance(dialog.were_sorry_label, QLabel)
    assert isinstance(dialog.help_us_label, QLabel)
    assert isinstance(dialog.download_debug_logs, QPushButton)
    assert isinstance(dialog.copy_button, QPushButton)

    # Test labels content
    assert QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'something_went_wrong_mb', None,
    ) == dialog.were_sorry_label.text()

    # Test button properties
    assert dialog.download_debug_logs.minimumSize().width() == 120
    assert dialog.download_debug_logs.minimumSize().height() == 40


def test_download_debug_logs(error_report_dialog, qtbot):
    """Test the download debug logs functionality."""
    dialog = error_report_dialog

    with patch('src.views.components.error_report_dialog_box.QFileDialog.getSaveFileName') as mock_file_dialog, \
            patch('src.views.components.error_report_dialog_box.zip_logger_folder') as mock_zip, \
            patch('src.views.components.error_report_dialog_box.download_file') as mock_download, \
            patch('src.views.components.error_report_dialog_box.cleanup_debug_logs') as mock_cleanup_zip:

        # Mock return values
        mock_zip.return_value = ('test.zip', 'output_dir', 'path/test.zip')
        mock_file_dialog.return_value = ('save_path.zip', 'selected_filter')

        # Click download button
        qtbot.mouseClick(dialog.download_debug_logs, Qt.LeftButton)

        # Verify zip_logger_folder was called with correct path
        mock_zip.assert_called_once_with(local_store.get_path())

        # Verify download_file was called with correct parameters
        mock_download.assert_called_once_with('save_path.zip', 'output_dir')
        mock_cleanup_zip.assert_called_once_with('path/test.zip')


def test_copy_button(error_report_dialog, qtbot):
    """Test if the copy button copies email to clipboard."""
    dialog = error_report_dialog

    with patch('src.views.components.error_report_dialog_box.copy_text') as mock_copy_text, \
            patch.object(ToastManager, 'success', return_value=None):
        # Click copy button
        qtbot.mouseClick(dialog.copy_button, Qt.LeftButton)

        # Process events to allow click to propagate
        qtbot.wait(100)

        # Verify copy_text was called with correct label
        mock_copy_text.assert_called_once_with(dialog.email_label)


def test_setup_exit_button(error_report_dialog, mocker):
    """Tests if the exit button is properly set up and triggers application exit."""

    # Patch QApplication.exit at the class level before setting up the button
    mock_exit = mocker.patch('PySide6.QtWidgets.QApplication.exit')

    # Call the method that sets up the exit button
    error_report_dialog.setup_exit_button()

    # Ensure exit_button is created
    assert hasattr(
        error_report_dialog,
        'exit_button',
    ), 'Exit button was not created'
    assert error_report_dialog.exit_button.text() == 'exit'

    # Ensure button is added to button box
    assert error_report_dialog.exit_button in error_report_dialog.button_box.buttons()

    # Simulate button click
    error_report_dialog.exit_button.click()

    # Ensure QApplication.exit() was called
    mock_exit.assert_called_once()
