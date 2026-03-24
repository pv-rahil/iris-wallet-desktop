# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for `src/utils/usb_detector.py`."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.usb_detector import USBDetector
from subprocess import CalledProcessError


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


@patch('platform.system', return_value='Windows')
@patch('subprocess.run')
def test_get_available_devices_windows_single_dict(mock_run, _):
    """On Windows, handle single dictionary response from PowerShell."""
    ps_out = {'DeviceID': 'F:', 'VolumeName': 'FLASH_DRIVE'}
    mock_run.return_value = MagicMock(stdout=json.dumps(ps_out))
    dd = USBDetector()
    devices = dd.get_available_devices()
    assert 'F' in devices
    assert devices['F']['label'] == 'FLASH_DRIVE'


@patch('subprocess.run')
def test_get_mountpoint_and_label_failure(mock_run):
    """Test get_mountpoint_and_label with subprocess error."""
    mock_run.side_effect = CalledProcessError(1, 'diskutil')
    dd = USBDetector()
    mount, label = dd.get_mountpoint_and_label('/dev/fail')
    assert mount == ''
    assert label == ''


def test_is_directory_empty(detector):
    """Test _is_directory_empty helper."""
    with patch('os.path.exists', return_value=False):
        assert detector._is_directory_empty('/non/existent') is True
        
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['.hidden', 'file.txt']):
            assert detector._is_directory_empty('/some/path') is False
        with patch('os.listdir', return_value=['.hidden']):
            assert detector._is_directory_empty('/some/path') is True
        with patch('os.listdir', side_effect=PermissionError()):
            assert detector._is_directory_empty('/secret') is False


@patch.object(USBDetector, 'get_available_devices', side_effect=Exception("detect failed"))
def test_detect_usb_drives_exception(mock_get):
    """Test detect_usb_drives re-raises as RuntimeError."""
    dd = USBDetector()
    with pytest.raises(RuntimeError) as exc:
        dd.detect_usb_drives()
    assert "USB detection failed" in str(exc.value)


@patch('platform.system', return_value='Linux')
@patch('subprocess.run')
def test_linux_recursion_no_mount(mock_run, _):
    """Test Linux recursion when a USB entry has no mountpoint but its children do."""
    lsblk = {
        'blockdevices': [
            {
                'name': 'sdc',
                'tran': 'usb',
                'children': [
                    {'name': 'sdc1', 'mountpoint': None}, # No mountpoint here
                    {'name': 'sdc2', 'mountpoint': '/mnt/usb', 'label': 'RECURSE'},
                ],
            },
        ],
    }
    mock_run.return_value = MagicMock(stdout=json.dumps(lsblk))
    dd = USBDetector()
    devices = dd.get_available_devices()
    assert 'sdc2' in devices
    assert 'sdc1' not in devices


@patch('platform.system', return_value='Unsupported')
def test_unsupported_platform(mock_sys):
    """Test behavior on unsupported platforms."""
    dd = USBDetector()
    assert dd.get_available_devices() == {}


@patch('platform.system', return_value='Linux')
@patch('subprocess.run', side_effect=Exception('lsblk fail'))
def test_get_available_devices_exception_linux(mock_run, _):
    """Test exception handling in _get_linux_devices."""
    dd = USBDetector()
    assert dd.get_available_devices() == {}


@patch('platform.system', return_value='Linux')
@patch.object(USBDetector, '_get_linux_devices', side_effect=Exception('general fail'))
def test_get_available_devices_exception_general(mock_get, _):
    """Test general exception handling in get_available_devices."""
    dd = USBDetector()
    assert dd.get_available_devices() == {}


@patch('platform.system', return_value='Windows')
@patch('subprocess.run', side_effect=Exception('powershell fail'))
def test_get_available_devices_exception_windows(mock_run, _):
    """Test exception handling in _get_windows_devices."""
    dd = USBDetector()
    assert dd.get_available_devices() == {}


@patch('platform.system', return_value='Darwin')
@patch('subprocess.run')
def test_get_macos_devices_called_process_error(mock_run, _):
    """Test CalledProcessError handling in _get_macos_devices."""
    mock_run.side_effect = CalledProcessError(1, 'diskutil list')
    dd = USBDetector()
    # This should be caught inside _get_macos_devices and return {}
    assert dd.get_available_devices() == {}


@patch.object(USBDetector, 'detect_usb_drives', side_effect=Exception("connection check fail"))
def test_is_usb_connected_exception(mock_detect):
    """Test is_usb_connected exception handling."""
    dd = USBDetector()
    assert dd.is_usb_connected() is False
