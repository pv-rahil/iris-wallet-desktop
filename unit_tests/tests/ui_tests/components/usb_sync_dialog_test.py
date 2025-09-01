# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `USBSyncDialog`."""
from __future__ import annotations

from unittest.mock import patch

import pytest

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
