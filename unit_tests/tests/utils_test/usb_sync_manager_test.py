# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for `USBSyncManager`."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.utils.constant import LAST_SYNC_DIRECTION
from src.utils.constant import SYNC_INDEX
from src.utils.local_store import local_store
from src.utils.usb_detector import USBDrive
from src.utils.usb_sync_manager import USBSyncManager


@pytest.fixture
def manager() -> USBSyncManager:
    """Return a fresh `USBSyncManager` instance for testing."""
    return USBSyncManager()


def make_drive(tmp_path):
    """Helper to construct a non-empty `USBDrive` at tmp_path."""
    d = USBDrive(name='USB', path=str(tmp_path), is_empty=False)
    return d


def test_validate_usb_drive_empty_true(manager: USBSyncManager, tmp_path):
    """When selected drive is empty, validation should pass (True)."""
    drv = USBDrive(name='USB', path=str(tmp_path), is_empty=True)
    manager.selected_drive = drv
    assert manager._validate_usb_drive() is True


@patch('os.listdir', return_value=['other.zip'])
def test_has_valid_wallet_data_false(_ls, manager: USBSyncManager, tmp_path):
    """If required zip not present, `_has_valid_wallet_data` returns False."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    assert manager._has_valid_wallet_data() is False


@patch('os.path.exists', return_value=False)
def test_determine_sync_direction_no_ini_returns_to_usb(_exists, manager: USBSyncManager, tmp_path):
    """Without ini on USB, direction should be 'to_usb'."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    # _check_usb_ini_exists will return False -> 'to_usb'
    assert manager._determine_sync_direction() == 'to_usb'


def test_determine_sync_direction_with_counter_prefers_last_direction(manager: USBSyncManager, tmp_path):
    """With equal counters but different checksums, follow LAST_SYNC_DIRECTION."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    local_store.set_value(SYNC_INDEX, 1)
    local_store.set_value(LAST_SYNC_DIRECTION, 'wallet_to_usb')

    with patch.object(manager, '_check_usb_ini_exists', return_value=True), \
            patch.object(manager, '_get_usb_index', return_value=1), \
            patch.object(manager, '_calculate_usb_wallet_checksum', return_value='u1'), \
            patch.object(manager, '_calculate_wallet_checksum', return_value='l2'):
        # same index, different checksum -> follow LAST_SYNC_DIRECTION -> to_usb
        assert manager._determine_sync_direction_with_counter() == 'to_usb'
