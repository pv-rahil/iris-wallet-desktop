"""Unit test for backup configure dialog """
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.ui_backup_configure_dialog import BackupConfigureDialog


@pytest.fixture
def backup_configure_dialog_page_navigate(mocker):
    """Fixture to mock the page_navigate object."""
    return mocker.Mock()


@pytest.fixture
def backup_configure_dialog(backup_configure_dialog_page_navigate, qtbot):
    """Fixture to create the BackupConfigureDialog instance."""
    dialog = BackupConfigureDialog(backup_configure_dialog_page_navigate)
    qtbot.addWidget(dialog)
    return dialog


def test_backup_configure_dialog_initial_state(backup_configure_dialog):
    """Test the initial state of the BackupConfigureDialog."""
    assert backup_configure_dialog.windowFlags() & Qt.FramelessWindowHint
    assert backup_configure_dialog.mnemonic_detail_text_label.text() == (
        QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'google_auth_not_found_message', None,
        )
    )
    assert backup_configure_dialog.cancel_button.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ignore_button', None,
    )
    assert backup_configure_dialog.continue_button.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configure_backup', None,
    )


def test_handle_configure(backup_configure_dialog, backup_configure_dialog_page_navigate, qtbot, mocker):
    """Test the handle_configure method."""
    # Mock the close method to verify that it's called
    mock_close = mocker.patch.object(backup_configure_dialog, 'close')

    qtbot.mouseClick(backup_configure_dialog.continue_button, Qt.LeftButton)

    backup_configure_dialog_page_navigate.backup_page.assert_called_once()
    mock_close.assert_called_once()
    backup_configure_dialog.continue_button.clicked.disconnect()


def test_handle_cancel(backup_configure_dialog, mocker, qtbot):
    """Test the handle_cancel method."""
    # Mock the close method to verify that it's called
    mock_close = mocker.patch.object(backup_configure_dialog, 'close')

    # Mock the OnCloseDialogBox to prevent actual UI interaction
    mock_on_close_dialog_box = mocker.patch(
        'src.views.ui_backup_configure_dialog.OnCloseDialogBox',
    )
    mock_on_close_dialog_box.return_value.exec.return_value = QDialog.Accepted

    qtbot.mouseClick(backup_configure_dialog.cancel_button, Qt.LeftButton)

    mock_close.assert_called_once()
    mock_on_close_dialog_box.assert_called_once_with(backup_configure_dialog)
    mock_on_close_dialog_box.return_value.exec.assert_called_once()
