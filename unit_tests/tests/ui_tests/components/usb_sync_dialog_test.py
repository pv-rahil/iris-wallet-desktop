# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `USBSyncDialog`."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget

from src.model.enums.enums_model import WalletEntryType
from src.utils.usb_detector import USBDrive
from src.views.components.usb_sync_dialog import USBSyncDialog


@pytest.fixture
def two_drives():
    """Provide a list of two non-empty mocked USBDrive entries."""
    return [
        USBDrive(name='USB A', path='/mnt/a', is_empty=False),
        USBDrive(name='USB B', path='/mnt/b', is_empty=False),
    ]


def test_dialog_with_drives_enables_continue_and_lists(two_drives, qt_app):
    """Dialog lists drives and enables Continue when drives are present."""
    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_entry_type',
        return_value=WalletEntryType.LOAD,
    ):
        d = USBSyncDialog(two_drives, parent=None)
        try:
            assert d.continue_button.isEnabled() is True
            assert d.drive_combobox.count() == 2
            # Default selected is index 0
            sel = d.get_selected_drive()
            assert sel and sel.name == 'USB A'
        finally:
            d.close()


def test_dialog_no_drives_disables_continue(qt_app):
    """Dialog disables Continue when no USB drives are detected."""
    d = USBSyncDialog([], parent=None)
    try:
        assert d.continue_button.isEnabled() is False
    finally:
        d.close()


def test_single_drive_combobox_disabled_and_selected(qt_app):
    """When only one drive, combobox disabled and shows that drive without dropdown."""
    drives = [USBDrive(name='USB Solo', path='/mnt/solo', is_empty=False)]
    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_entry_type',
        return_value=WalletEntryType.LOAD,
    ):
        d = USBSyncDialog(drives, parent=None)
    try:
        assert d.drive_combobox.isEnabled() is False
        assert d.drive_combobox.count() == 1
        assert d.drive_combobox.itemText(0) == 'USB Solo'
        # get_selected_drive returns the only drive
        sel = d.get_selected_drive()
        assert sel and sel.name == 'USB Solo'
    finally:
        d.close()


def test_get_selected_drive_none_and_multi_index(qt_app):
    """No drives -> None, multi drives -> reflects combobox index."""
    assert USBSyncDialog([], parent=None).get_selected_drive() is None

    drives = [
        USBDrive(name='USB A', path='/mnt/a', is_empty=False),
        USBDrive(name='USB B', path='/mnt/b', is_empty=False),
    ]
    d = USBSyncDialog(drives, parent=None)
    try:
        d.drive_combobox.setCurrentIndex(1)
        sel = d.get_selected_drive()
        assert sel and sel.name == 'USB B'
    finally:
        d.close()


def test_refresh_fingerprint_value_updates_from_list(qt_app, monkeypatch):
    """refresh_fingerprint_value reflects fingerprint based on selected drive."""
    drives = [
        USBDrive(name='USB A', path='/mnt/a', is_empty=False),
        USBDrive(name='USB B', path='/mnt/b', is_empty=False),
    ]
    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_entry_type',
        return_value=WalletEntryType.LOAD,
    ):
        d = USBSyncDialog(drives, parent=None)
    try:
        def fake_list(usb_drive):
            return ['fpA'] if usb_drive.name == 'USB A' else ['fpB']
        monkeypatch.setattr(
            USBSyncDialog, 'list_usb_zip_files',
            staticmethod(fake_list),
        )

        d.drive_combobox.setCurrentIndex(0)
        d.refresh_fingerprint_value()
        assert d.fingerprint_value_label.text() == 'fpA'
        d.drive_combobox.setCurrentIndex(1)
        d.refresh_fingerprint_value()
        assert d.fingerprint_value_label.text() == 'fpB'
    finally:
        d.close()


def test_check_usb_devices_handles_exception(qt_app, monkeypatch):
    """check_usb_devices should swallow exceptions from detector and not raise."""
    d = USBSyncDialog([], parent=None)
    try:
        monkeypatch.setattr(
            d.usb_detector, 'detect_usb_drives', staticmethod(
                lambda: (_ for _ in ()).throw(Exception('boom')),
            ),
        )
        # Should not raise
        d.check_usb_devices()
    finally:
        d.close()


def test_check_usb_devices_updates_from_empty(qt_app, monkeypatch):
    """check_usb_devices updates UI and state when new drives are detected from empty."""
    d = USBSyncDialog([], parent=None)
    try:
        new_drives = [USBDrive(name='X', path='/mnt/x', is_empty=False)]
        monkeypatch.setattr(
            d.usb_detector, 'detect_usb_drives',
            staticmethod(lambda: new_drives),
        )
        d.check_usb_devices()
        assert d.usb_drives == new_drives
        assert d.usb_row_layout is not None
    finally:
        d.close()


def test_update_usb_list_recreates_rows(qt_app):
    """update_usb_list should recreate rows and enable Continue when drives exist."""
    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_entry_type',
        return_value=WalletEntryType.LOAD,
    ):
        d = USBSyncDialog(
            [USBDrive(name='A', path='/mnt/a', is_empty=False)], parent=None,
        )
    try:
        # ensure initial row(s) exist
        assert d.usb_row_layout is not None
        # change drives and update
        d.usb_drives = [
            USBDrive(name='B', path='/mnt/b', is_empty=False),
            USBDrive(name='C', path='/mnt/c', is_empty=False),
        ]
        d.update_usb_list()
        assert d.usb_row_layout is not None
        assert d.fingerprint_row_layout is not None
        # continue button should be enabled after update
        assert d.continue_button.isEnabled() is True
    finally:
        d.close()


def test_show_and_close_events_apply_blur_and_stop_timer(qt_app):
    """showEvent applies blur; closeEvent stops timer and clears blur."""
    parent = QWidget()
    d = USBSyncDialog([], parent=parent)
    try:
        # simulate show/close events
        d.showEvent(QShowEvent())
        assert parent.graphicsEffect() is not None
        d.closeEvent(QCloseEvent())
        assert not d.usb_check_timer.isActive()
        assert parent.graphicsEffect() is None
    finally:
        d.close()


def test_accept_reject_stop_timer_and_clear_blur(qt_app):
    """accept/reject should stop the periodic USB timer and clear any blur."""
    d = USBSyncDialog([], parent=QWidget())
    try:
        assert d.usb_check_timer.isActive()
        d.accept()
        assert not d.usb_check_timer.isActive()
        # reset timer for reject path
        d.usb_check_timer.start(5000)
        assert d.usb_check_timer.isActive()
        d.reject()
        assert not d.usb_check_timer.isActive()
    finally:
        d.close()


def test_list_usb_zip_files_filters_and_error(monkeypatch, qt_app):
    """list_usb_zip_files filters out temp/non-zip and logs on error path."""
    d = USBSyncDialog([], parent=None)
    try:
        monkeypatch.setattr(
            'src.views.components.usb_sync_dialog.os.listdir',
            lambda p: ['a.zip', 'b_temp.zip', 'c.txt'],
        )
        out = d.list_usb_zip_files(
            USBDrive(name='N', path='/mnt/n', is_empty=False),
        )
        assert out == ['a']

        # error path
        calls = []
        monkeypatch.setattr(
            'src.views.components.usb_sync_dialog.os.listdir',
            lambda p: (_ for _ in ()).throw(OSError('x')),
        )
        monkeypatch.setattr(
            'src.views.components.usb_sync_dialog.logger', type(
                'L', (), {'error': lambda *a, **k: calls.append(a)},
            )(),
        )
        out2 = d.list_usb_zip_files(
            USBDrive(name='N', path='/mnt/n', is_empty=False),
        )
        assert not out2
        assert calls, 'logger.error should be called'
    finally:
        d.close()
