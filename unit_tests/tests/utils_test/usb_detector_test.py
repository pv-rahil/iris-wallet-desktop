# pylint: disable=redefined-outer-name, unused-argument, protected-access
"""Unit tests for USB detector utility."""
from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.usb_detector import USBDetector


@pytest.fixture
def detector() -> USBDetector:
    """Return a fresh `USBDetector` instance for testing."""
    return USBDetector()


@patch('src.utils.usb_detector.platform.system')
def test_init(mock_system):
    """Test initialization and platform detection."""
    mock_system.return_value = 'Linux'
    detector = USBDetector()
    assert detector.platform == 'linux'


@patch('src.utils.usb_detector.USBDetector._get_linux_devices')
def test_get_available_devices_linux(mock_get_linux, detector):
    """Test getting devices on Linux platform."""
    detector.platform = 'linux'
    detector.get_available_devices()
    mock_get_linux.assert_called_once()


@patch('src.utils.usb_detector.USBDetector._get_windows_devices')
def test_get_available_devices_windows(mock_get_windows, detector):
    """Test getting devices on Windows platform."""
    detector.platform = 'windows'
    detector.get_available_devices()
    mock_get_windows.assert_called_once()


@patch('src.utils.usb_detector.USBDetector._get_macos_devices')
def test_get_available_devices_macos(mock_get_macos, detector):
    """Test getting devices on MacOS platform."""
    detector.platform = 'darwin'
    detector.get_available_devices()
    mock_get_macos.assert_called_once()


def test_get_available_devices_unsupported(detector):
    """Test unsupported platform (Line 43-44)."""
    detector.platform = 'unknown'
    assert detector.get_available_devices() == {}


@patch('src.utils.usb_detector.USBDetector._get_linux_devices')
def test_get_available_devices_exception(mock_get_linux, detector):
    """Test exception handling in get_available_devices (Line 45-47)."""
    detector.platform = 'linux'
    mock_get_linux.side_effect = Exception('Test Error')
    assert detector.get_available_devices() == {}


@patch('src.utils.usb_detector.subprocess.run')
def test_get_linux_devices_success(mock_run, detector):
    """Test successful Linux device detection (Lines 59-64, 76-80)."""
    mock_stdout = json.dumps({
        'blockdevices': [
            {
                'name': 'sda',
                'tran': 'sata',
                'children': [{'name': 'sda1', 'mountpoint': '/'}],
            },
            {
                'name': 'sdb',
                'tran': 'usb',
                'children': [
                    {
                        'name': 'sdb1', 'mountpoint': '/media/usb1',
                        'label': 'USB_DRIVE',
                    },
                    {'name': 'sdb2', 'mountpoint': None},
                ],
            },
        ],
    })
    mock_run.return_value = MagicMock(stdout=mock_stdout)

    devices = detector._get_linux_devices()
    assert 'sdb1' in devices
    assert devices['sdb1']['mountpoint'] == '/media/usb1'
    assert devices['sdb1']['label'] == 'USB_DRIVE'
    assert 'sda1' not in devices
    assert 'sdb2' not in devices


@patch('src.utils.usb_detector.subprocess.run')
def test_get_linux_devices_error(mock_run, detector):
    """Test Linux device detection error (Line 82-84)."""
    mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')
    assert detector._get_linux_devices() == {}


@patch('src.utils.usb_detector.subprocess.run')
def test_get_windows_devices_success_list(mock_run, detector):
    """Test successful Windows device detection - list response."""
    mock_stdout = json.dumps([
        {'DeviceID': 'E:', 'VolumeName': 'TEST_USB'},
        {'DeviceID': 'F:', 'VolumeName': None},
    ])
    mock_run.return_value = MagicMock(stdout=mock_stdout)
    devices = detector._get_windows_devices()
    assert 'E' in devices
    assert devices['E']['mountpoint'] == 'E:'
    assert devices['E']['label'] == 'TEST_USB'
    assert 'F' in devices
    assert devices['F']['label'] == 'Unknown'


@patch('src.utils.usb_detector.subprocess.run')
def test_get_windows_devices_success_dict(mock_run, detector):
    """Test successful Windows device detection - single dict response."""
    mock_stdout = json.dumps({'DeviceID': 'G:', 'VolumeName': 'SINGLE_USB'})
    mock_run.return_value = MagicMock(stdout=mock_stdout)
    devices = detector._get_windows_devices()
    assert 'G' in devices
    assert devices['G']['mountpoint'] == 'G:'


@patch('src.utils.usb_detector.subprocess.run')
def test_get_windows_devices_error(mock_run, detector):
    """Test Windows device detection error (Line 117-119)."""
    mock_run.side_effect = Exception('Win Error')
    assert detector._get_windows_devices() == {}


@patch('src.utils.usb_detector.subprocess.run')
def test_get_mountpoint_and_label_success(mock_run, detector):
    """Test diskutil info parsing for MacOS."""
    mock_stdout = '   Mount Point: /Volumes/USB\n   Volume Name: MacOS_USB\n'
    mock_run.return_value = MagicMock(stdout=mock_stdout)
    mount, label = detector.get_mountpoint_and_label('/dev/disk2s1')
    assert mount == '/Volumes/USB'
    assert label == 'MacOS_USB'


@patch('src.utils.usb_detector.subprocess.run')
def test_get_mountpoint_and_label_not_mounted(mock_run, detector):
    """Test diskutil info when not mounted."""
    mock_stdout = '   Mount Point: Not mounted\n'
    mock_run.return_value = MagicMock(stdout=mock_stdout)
    mount, _ = detector.get_mountpoint_and_label('/dev/disk2s1')
    assert mount == ''


@patch('src.utils.usb_detector.subprocess.run')
@patch('src.utils.usb_detector.USBDetector.get_mountpoint_and_label')
def test_get_macos_devices_success(mock_get_info, mock_run, detector):
    """Test successful MacOS device detection."""
    mock_run.return_value = MagicMock(
        stdout='/dev/disk2 (external, physical):\n 0: GUID_partition_scheme\n 1: EFI\n 2: Apple_APFS Disk2S2 disk2s2',
    )
    mock_get_info.return_value = ('/Volumes/USB', 'USB_LABEL')
    devices = detector._get_macos_devices()
    assert '/dev/disk2s2' in devices
    assert devices['/dev/disk2s2']['mountpoint'] == '/Volumes/USB'


@patch('src.utils.usb_detector.subprocess.run')
def test_get_macos_devices_error(mock_run, detector):
    """Test MacOS device detection error (Line 193-195)."""
    mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')
    assert detector._get_macos_devices() == {}


@patch('src.utils.usb_detector.USBDetector.get_available_devices')
def test_detect_usb_drives_success(mock_get_available, detector):
    """Test detect_usb_drives (Success)."""
    mock_get_available.return_value = {
        'usb1': {'mountpoint': '/m1', 'label': 'L1'},
    }
    with patch('src.utils.usb_detector.USBDetector._is_directory_empty') as mock_empty:
        mock_empty.return_value = True
        drives = detector.detect_usb_drives()
        assert len(drives) == 1
        assert drives[0].name == 'L1'
        assert drives[0].is_empty is True


@patch('src.utils.usb_detector.USBDetector.get_available_devices')
def test_detect_usb_drives_exception(mock_get_available, detector):
    """Test detect_usb_drives exception (Line 224-226)."""
    mock_get_available.side_effect = Exception('Fatal Error')
    with pytest.raises(RuntimeError, match='USB detection failed'):
        detector.detect_usb_drives()


@patch('src.utils.usb_detector.os.path.exists')
@patch('src.utils.usb_detector.os.listdir')
def test_is_directory_empty(mock_listdir, mock_exists, detector):
    """Test directory status checks (Line 238-250)."""
    mock_exists.return_value = False
    assert detector._is_directory_empty('/wrong') is True

    mock_exists.return_value = True
    mock_listdir.return_value = ['.hidden', 'file.txt']
    assert detector._is_directory_empty('/not_empty') is False

    mock_listdir.return_value = ['.hidden']
    assert detector._is_directory_empty('/empty_with_hidden') is True

    mock_listdir.side_effect = PermissionError()
    assert detector._is_directory_empty('/no_access') is False


@patch('src.utils.usb_detector.USBDetector.detect_usb_drives')
def test_is_usb_connected(mock_detect, detector):
    """Test is_usb_connected check (Line 252-263)."""
    mock_detect.return_value = [MagicMock()]
    assert detector.is_usb_connected() is True

    mock_detect.return_value = []
    assert detector.is_usb_connected() is False

    mock_detect.side_effect = Exception('Error')
    assert detector.is_usb_connected() is False
