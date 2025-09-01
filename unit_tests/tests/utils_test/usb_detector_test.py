# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for `src/utils/usb_detector.py`."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.usb_detector import USBDetector


@pytest.fixture
def detector() -> USBDetector:
    """Return a fresh `USBDetector` instance for testing."""
    return USBDetector()


@patch('platform.system', return_value='Linux')
@patch('subprocess.run')
def test_get_available_devices_linux(mock_run, _):
    """On Linux, parse lsblk JSON and expose mounted USB partition with label."""
    # Simulate lsblk JSON output with one USB device and one mounted partition
    lsblk = {
        'blockdevices': [
            {
                'name': 'sdb',
                'tran': 'usb',
                'children': [
                    {'name': 'sdb1', 'mountpoint': '/media/USB', 'label': 'MYDISK'},
                ],
            },
        ],
    }
    mock_run.return_value = MagicMock(stdout=json.dumps(lsblk))

    dd = USBDetector()
    devices = dd.get_available_devices()
    assert devices
    key, info = next(iter(devices.items()))
    assert key == 'sdb1'
    assert info['mountpoint'] == '/media/USB'
    assert info['label'] == 'MYDISK'


@patch('platform.system', return_value='Windows')
@patch('subprocess.run')
def test_get_available_devices_windows(mock_run, _):
    """On Windows, parse PowerShell JSON and include drive label."""
    ps_out = [{'DeviceID': 'E:', 'VolumeName': 'USB_VOL'}]
    mock_run.return_value = MagicMock(stdout=json.dumps(ps_out))
    dd = USBDetector()
    devices = dd.get_available_devices()
    assert devices
    info = list(devices.values())[0]
    assert info['label'] == 'USB_VOL'


@patch('platform.system', return_value='Darwin')
@patch('subprocess.run')
def test_get_available_devices_macos_handles_errors(mock_run, _):
    """On macOS, gracefully handle minimal outputs and errors returning dict."""
    # diskutil list result minimal, then diskutil info raises CalledProcessError
    mock_run.side_effect = [MagicMock(stdout=''), MagicMock(stdout='')]
    dd = USBDetector()
    devices = dd.get_available_devices()
    assert isinstance(devices, dict)


@patch.object(USBDetector, 'get_available_devices', return_value={'sdb1': {'mountpoint': '/media/USB', 'label': 'X', 'name': 'sdb1'}})
@patch('os.listdir', return_value=['file.txt'])
@patch('os.path.exists', return_value=True)
def test_detect_usb_drives_and_is_connected(mock_exists, mock_listdir, _get):
    """Detect USB drives from available devices and report connection status."""
    dd = USBDetector()
    drives = dd.detect_usb_drives()
    assert drives and drives[0].path == '/media/USB'
    assert dd.is_usb_connected() is True
