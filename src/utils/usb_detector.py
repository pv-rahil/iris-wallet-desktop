"""
USB detection utility for cross-platform USB drive detection with real-time monitoring.

This module provides functionality to detect USB drives on different platforms
using native system commands and tools, with real-time monitoring capabilities.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess

from PySide6.QtCore import QObject

from src.model.common_operation_model import USBDrive
from src.utils.logging import logger


class USBDetector(QObject):
    """Cross-platform USB drive detection utility with real-time monitoring."""

    def __init__(self):
        """Initialize the USB detector."""
        if hasattr(self, 'platform'):  # Already initialized
            return

        super().__init__()
        self.platform = platform.system().lower()

    def get_available_devices(self) -> dict[str, dict]:
        """
        Get currently available USB devices.

        Returns:
            dict: Dictionary of USB devices with their information
        """
        try:
            if self.platform == 'linux':
                return self._get_linux_devices()
            if self.platform == 'windows':
                return self._get_windows_devices()
            if self.platform == 'darwin':
                return self._get_macos_devices()
            logger.error('Unsupported platform: %s', self.platform)
            return {}
        except Exception as exc:
            logger.error('Error getting available devices: %s', str(exc))
            return {}

    def _get_linux_devices(self) -> dict[str, dict]:
        """Get USB devices on Linux using lsblk."""
        try:
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'NAME,TRAN,MOUNTPOINT,LABEL'],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            devices = {}

            def recurse(entry, is_usb_parent=False):
                # If this block has "tran: usb", mark it and recurse children
                if entry.get('tran') == 'usb':
                    is_usb_parent = True

                # If this is a child (partition) and it's mounted under a USB parent
                if is_usb_parent and entry.get('mountpoint'):
                    name = entry.get('name')
                    devices[name] = {
                        'mountpoint': entry.get('mountpoint'),
                        'label': entry.get('label') or 'Unknown',
                        'name': name,
                    }

                for child in entry.get('children', []):
                    recurse(child, is_usb_parent)

            for device in data.get('blockdevices', []):
                recurse(device)

            return devices
        except Exception as exc:
            logger.error('Linux USB detection error: %s', str(exc))
            return {}

    def _get_windows_devices(self) -> dict[str, dict]:
        """Get USB devices on Windows using PowerShell."""
        try:
            cmd = [
                'powershell',
                '-Command',
                'Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 2} | ConvertTo-Json',
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True,
            )
            data = json.loads(result.stdout)

            devices = {}
            if isinstance(data, list):
                for drive in data:
                    device_id = drive.get('DeviceID', '').replace(':', '')
                    devices[device_id] = {
                        'mountpoint': drive.get('DeviceID', ''),
                        'label': drive.get('VolumeName') or 'Unknown',
                        'name': device_id,
                    }
            elif isinstance(data, dict):
                device_id = data.get('DeviceID', '').replace(':', '')
                devices[device_id] = {
                    'mountpoint': data.get('DeviceID', ''),
                    'label': data.get('VolumeName') or 'Unknown',
                    'name': device_id,
                }

            return devices
        except Exception as exc:
            logger.error('Windows USB detection error: %s', str(exc))
            return {}

    def get_mountpoint_and_label(self, device_path: str) -> tuple[str, str]:
        """Get mountpoint and label for a given device path."""
        try:
            result = subprocess.run(
                ['diskutil', 'info', device_path],
                capture_output=True,
                text=True,
                check=True,
            )
            mountpoint = ''
            label = ''

            for line in result.stdout.split('\n'):
                if 'Mount Point' in line:
                    mountpoint = line.split(':', 1)[1].strip()
                elif 'Volume Name' in line:
                    label = line.split(':', 1)[1].strip()

            if mountpoint == 'Not mounted':
                mountpoint = ''

            return mountpoint, label
        except subprocess.CalledProcessError:
            return '', ''

    def _get_macos_devices(self) -> dict[str, dict]:

        try:
            result = subprocess.run(
                ['diskutil', 'list'],
                capture_output=True,
                text=True,
                check=True,
            )

            devices = {}
            current_disk = None
            lines = result.stdout.split('\n')

            for line in lines:
                line = line.strip()

                # Match parent disk (e.g., /dev/disk2)
                if line.startswith('/dev/disk') and '(external' in line.lower():
                    current_disk = line.split()[0]

                # Skip container header line
                elif current_disk and line.startswith('0:'):
                    continue

                # Look for partitions under that disk
                elif current_disk and line and line[0].isdigit():
                    parts = line.split()
                    if len(parts) >= 3:
                        identifier = parts[-1]
                        device_path = f"/dev/{identifier}"
                        mountpoint, label = self.get_mountpoint_and_label(
                            device_path,
                        )

                        if mountpoint:
                            devices[device_path] = {
                                'mountpoint': mountpoint,
                                'label': label,
                                'name': device_path,
                            }

                    # Reset to avoid mixing other disks
                    current_disk = None

            return devices

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] diskutil failed: {e}")
            return {}

    def detect_usb_drives(self) -> list[USBDrive]:
        """
        Detect USB drives on the current platform.

        Returns:
            List[USBDrive]: List of detected USB drives.

        Raises:
            RuntimeError: If USB detection fails on the current platform.
        """
        try:
            devices = self.get_available_devices()
            drives = []

            for _, device_info in devices.items():
                mountpoint = device_info['mountpoint']
                is_empty = self._is_directory_empty(mountpoint)
                drives.append(
                    USBDrive(
                        name=device_info['label'],
                        path=mountpoint,
                        size='Unknown',  # We can add size detection later if needed
                        is_empty=is_empty,
                    ),
                )

            return drives
        except Exception as exc:
            logger.error('USB detection failed: %s', str(exc))
            raise RuntimeError(f'USB detection failed: {str(exc)}') from exc

    def _is_directory_empty(self, path: str) -> bool:
        """
        Check if a directory is empty.

        Args:
            path: Directory path to check.

        Returns:
            bool: True if directory is empty, False otherwise.
        """
        try:
            if not os.path.exists(path):
                return True

            # Check if directory is empty (excluding hidden files)
            items = [
                item for item in os.listdir(path)
                if not item.startswith('.')
            ]
            return len(items) == 0
        except (OSError, PermissionError):
            logger.warning('Cannot access directory: %s', path)
            return False

    def is_usb_connected(self) -> bool:
        """
        Check if any USB drive is connected.

        Returns:
            bool: True if USB drive is connected, False otherwise.
        """
        try:
            drives = self.detect_usb_drives()
            return len(drives) > 0
        except Exception:
            return False
