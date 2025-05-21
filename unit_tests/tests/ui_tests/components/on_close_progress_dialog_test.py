"""Unit test for On close progress dialog."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

from src.data.repository.setting_repository import SettingRepository
from src.data.service.backup_service import BackupService
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.views.components.on_close_progress_dialog import OnCloseDialogBox
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


@pytest.fixture
def on_close_progress_dialog_widget(qtbot):
    """Fixture to create and return an instance of OnCloseDialogBox."""
    widget = OnCloseDialogBox()
    qtbot.addWidget(widget)
    return widget


@patch.object(OnCloseDialogBox, '_close_app')
def test_start_process_without_backup_required(mock_close_app, on_close_progress_dialog_widget):
    """Test _start_process method when backup is not required."""
    on_close_progress_dialog_widget._start_process(is_backup_require=False)
    mock_close_app.assert_called_once()


@patch.object(RestoreMnemonicWidget, 'exec')
@patch.object(SettingRepository, 'get_keyring_status', return_value=True)
def test_start_process_with_backup_required_keyring(mock_keyring_status, mock_exec, on_close_progress_dialog_widget):
    """Test _start_process method when backup is required and keyring is enabled."""
    on_close_progress_dialog_widget._start_process(is_backup_require=True)
    mock_keyring_status.assert_called_once()
    mock_exec.assert_called_once()


@patch('src.views.components.on_close_progress_dialog.mnemonic_store')
@patch('src.views.components.on_close_progress_dialog.get_value')
@patch.object(SettingRepository, 'get_wallet_network', return_value=MagicMock(value='testnet'))
@patch.object(OnCloseDialogBox, '_start_backup')
@patch.object(SettingRepository, 'get_keyring_status', return_value=False)
def test_start_process_with_backup_required_no_keyring(
    mock_keyring_status, mock_start_backup, mock_wallet_network, mock_get_value, mock_mnemonic_store, on_close_progress_dialog_widget,
):
    """Test _start_process method when backup is required and keyring is not used."""

    # Mock mnemonic_store.decrypted_mnemonic
    mock_mnemonic_store.decrypted_mnemonic = 'mocked_mnemonic'

    # Mock get_value to return password
    mock_get_value.return_value = 'mocked_password'

    # Call the method under test
    on_close_progress_dialog_widget._start_process(is_backup_require=True)

    # Verify that get_value is called with the correct arguments
    mock_get_value.assert_called_once_with(
        key=WALLET_PASSWORD_KEY,
        network='testnet',
    )

    # Verify the correct arguments are passed to _start_backup
    mock_start_backup.assert_called_once_with(
        'mocked_mnemonic', 'mocked_password',
    )


@patch.object(OnCloseDialogBox, '_close_app')
def test_on_success_of_backup(mock_close_app, on_close_progress_dialog_widget):
    """Test _on_success_of_backup method to ensure app closes after successful backup."""
    on_close_progress_dialog_widget._on_success_of_backup()
    assert on_close_progress_dialog_widget.is_backup_onprogress is False
    mock_close_app.assert_called_once()


@patch.object(QMessageBox, 'critical')
@patch.object(OnCloseDialogBox, '_close_app')
def test_on_error_of_backup(mock_close_app, mock_critical, on_close_progress_dialog_widget):
    """Test _on_error_of_backup method to ensure error handling during backup."""
    on_close_progress_dialog_widget._on_error_of_backup()
    assert on_close_progress_dialog_widget.is_backup_onprogress is False
    mock_critical.assert_called_once_with(
        on_close_progress_dialog_widget, 'Failed', ERROR_SOMETHING_WENT_WRONG,
    )
    mock_close_app.assert_called_once()


@patch.object(QApplication, 'exit')
def test_close_app(mock_exit, on_close_progress_dialog_widget):
    """Test _close_app method to ensure application quits."""
    with patch('src.views.components.on_close_progress_dialog.HeaderFrameViewModel') as mock_header_view_model:
        # Configure the mock to return itself when instantiated
        mock_instance = MagicMock()
        mock_header_view_model.return_value = mock_instance

        on_close_progress_dialog_widget._close_app()
        assert on_close_progress_dialog_widget.is_backup_onprogress is False
        # mock_instance.stop_network_checker.assert_called_once()
        mock_exit.assert_called_once()


def test_close_event_backup_in_progress(on_close_progress_dialog_widget):
    """Test closeEvent when backup is in progress."""
    event = MagicMock()  # Mock the QCloseEvent

    # Case 1: Backup in progress, user confirms to close (Yes)
    on_close_progress_dialog_widget.is_backup_onprogress = True
    with patch('PySide6.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
        with patch.object(on_close_progress_dialog_widget, '_close_app') as mock_close_app:
            on_close_progress_dialog_widget.closeEvent(event)
            event.accept.assert_called_once()
            event.ignore.assert_not_called()
            mock_close_app.assert_called_once()

    # Reset the mock for the next case
    event.reset_mock()

    # Case 2: Backup in progress, user cancels the close (No)
    on_close_progress_dialog_widget.is_backup_onprogress = True
    with patch('PySide6.QtWidgets.QMessageBox.question', return_value=QMessageBox.No):
        on_close_progress_dialog_widget.closeEvent(event)
        event.ignore.assert_called_once()
        event.accept.assert_not_called()

    # Reset the mock for the next case
    event.reset_mock()

    # Case 3: No backup in progress
    on_close_progress_dialog_widget.is_backup_onprogress = False
    with patch.object(QApplication, 'instance') as mock_instance:
        mock_app = MagicMock()
        mock_instance.return_value = mock_app
        on_close_progress_dialog_widget.closeEvent(event)
        event.accept.assert_called_once()
        mock_app.exit.assert_called_once()


def test_ui(on_close_progress_dialog_widget: OnCloseDialogBox):
    """Test the UI elements in OnCloseDialogBox."""
    assert on_close_progress_dialog_widget.windowTitle() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT,
        'backup_dialog_title',
        None,
    )
    assert on_close_progress_dialog_widget.status_label.text() == 'Starting backup...'
    assert on_close_progress_dialog_widget.loading_movie.isValid()


@patch.object(OnCloseDialogBox, '_update_status')
@patch.object(OnCloseDialogBox, 'run_in_thread')
def test_start_backup(mock_run_in_thread, mock_update_status, on_close_progress_dialog_widget):
    """Test _start_backup method to ensure status update and thread initiation."""
    mnemonic = 'test_mnemonic'
    password = 'test_password'

    # Automatically simulate the backup process without manual intervention
    on_close_progress_dialog_widget._start_backup(mnemonic, password)

    # Verify that the status is updated
    mock_update_status.assert_called_once_with('Backup process started')

    # Verify that is_backup_onprogress is set to True
    assert on_close_progress_dialog_widget.is_backup_onprogress is True

    # Verify that run_in_thread is called with the correct arguments
    mock_run_in_thread.assert_called_once_with(
        BackupService.backup, {
            'args': [mnemonic, password],
            'callback': on_close_progress_dialog_widget._on_success_of_backup,
            'error_callback': on_close_progress_dialog_widget._on_error_of_backup,
        },
    )
