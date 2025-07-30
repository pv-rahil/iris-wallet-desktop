"""
USB detection utility for cross-platform USB drive detection.

This module provides functionality to detect USB drives on different platforms
using native system commands and tools.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess

from src.model.common_operation_model import USBDrive
from src.utils.logging import logger


class USBDetector:
    """Cross-platform USB drive detection utility."""

    def __init__(self):
        """Initialize the USB detector."""
        self.platform = platform.system().lower()

    def detect_usb_drives(self) -> list[USBDrive]:
        """
        Detect USB drives on the current platform.

        Returns:
            List[USBDrive]: List of detected USB drives.

        Raises:
            RuntimeError: If USB detection fails on the current platform.
        """
        try:
            if self.platform == 'linux':
                return self._detect_usb_linux()
            if self.platform == 'windows':
                return self._detect_usb_windows()
            if self.platform == 'darwin':
                return self._detect_usb_macos()
            else:
                raise RuntimeError(f'Unsupported platform: {self.platform}')
        except Exception as exc:
            logger.error('USB detection failed: %s', str(exc))
            raise RuntimeError(f'USB detection failed: {str(exc)}') from exc

    def _detect_usb_linux(self) -> list[USBDrive]:
        """
        Detect USB drives on Linux using lsblk command.

        Returns:
            List[USBDrive]: List of detected USB drives.
        """
        try:
            # Use lsblk to get USB drives
            output = subprocess.check_output(
                ['lsblk', '-J', '-o', 'NAME,TRAN,MOUNTPOINT,LABEL'], text=True,
            )
            block_devices = json.loads(output).get('blockdevices', [])
            usb_drives = []

            def extract(devices, parent_tran=None):
                for d in devices:
                    current_tran = d.get('tran') or parent_tran
                    if d.get('mountpoint') and current_tran == 'usb':
                        usb_drives.append({
                            'device': f"/dev/{d['name']}",
                            'mountpoint': d['mountpoint'],
                            'label': d.get('label') or 'Unknown',
                        })
                    if 'children' in d:
                        extract(d['children'], current_tran)

            extract(block_devices)

            # Convert dictionaries to USBDrive objects
            drives = []
            for usb_dict in usb_drives:
                mountpoint = usb_dict['mountpoint']
                is_empty = self._is_directory_empty(mountpoint)
                drives.append(
                    USBDrive(
                        name=usb_dict['label'],
                        path=mountpoint,
                        size='Unknown',  # We can add size detection later if needed
                        is_empty=is_empty,
                    ),
                )

            return drives
        except subprocess.CalledProcessError as exc:
            logger.error('Linux USB detection command failed: %s', str(exc))
            raise RuntimeError(f'Linux USB detection failed: {
                               str(exc)
                               }') from exc

    def _detect_usb_windows(self) -> list[USBDrive]:
        """
        Detect USB drives on Windows using WMI.

        Returns:
            List[USBDrive]: List of detected USB drives.
        """
        try:
            # Use PowerShell to get USB drives
            ps_command = '''
            Get-WmiObject -Class Win32_LogicalDisk |
            Where-Object { $_.DriveType -eq 2 } |
            Select-Object DeviceID, Size, FreeSpace |
            ConvertTo-Json
            '''

            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                check=True,
            )

            drives = []
            # Parse PowerShell JSON output
            # This is a simplified implementation
            lines = result.stdout.split('\n')

            for line in lines:
                if 'DeviceID' in line:
                    # Extract drive information from JSON-like output
                    # In production, use proper JSON parsing
                    if ':' in line:
                        drive_letter = line.split(
                            '"',
                        )[3] if '"' in line else line.split(':')[0]
                        mountpoint = f'{drive_letter}:\\'
                        is_empty = self._is_directory_empty(mountpoint)
                        drives.append(
                            USBDrive(
                                name=f'USB Drive {drive_letter}',
                                path=mountpoint,
                                size='Unknown',
                                is_empty=is_empty,
                            ),
                        )

            return drives
        except subprocess.CalledProcessError as exc:
            logger.error('Windows USB detection command failed: %s', str(exc))
            raise RuntimeError(f'Windows USB detection failed: {
                               str(exc)
                               }') from exc

    def _detect_usb_macos(self) -> list[USBDrive]:
        """
        Detect USB drives on macOS using diskutil command.

        Returns:
            List[USBDrive]: List of detected USB drives.
        """
        try:
            # Use diskutil to get USB drives
            result = subprocess.run(
                ['diskutil', 'list', '-plist'],
                capture_output=True,
                text=True,
                check=True,
            )

            drives = []
            # Parse diskutil output
            # This is a simplified implementation
            lines = result.stdout.split('\n')

            for line in lines:
                if 'usb' in line.lower() or '/dev/disk' in line:
                    # Extract drive information
                    parts = line.split()
                    if len(parts) >= 1:
                        device_path = parts[0]
                        mountpoint,label = self._get_mountpoint_macos(device_path)

                        if mountpoint:
                            is_empty = self._is_directory_empty(mountpoint)
                            drives.append(
                                USBDrive(
                                    name=label,
                                    path=mountpoint,
                                    size='Unknown',
                                    is_empty=is_empty,
                                ),
                            )

            return drives
        except subprocess.CalledProcessError as exc:
            logger.error('macOS USB detection command failed: %s', str(exc))
            raise RuntimeError(f'macOS USB detection failed: {
                               str(exc)
                               }') from exc

    def _get_mountpoint_macos(self, device_path: str) -> tuple(str,str):
        """
        Get mountpoint for a device on macOS.

        Args:
            device_path: Device path to check.

        Returns:
            str: Mountpoint path or empty string if not mounted.
        """
        try:
            result = subprocess.run(
                ['diskutil', 'info', device_path],
                capture_output=True,
                text=True,
                check=True,
            )

            mountpoint = ''
            label = ''

            lines = result.stdout.split('\n')
            for line in lines:
                if 'Mount Point' in line:
                    mountpoint = line.split(':', 1)[1].strip()
                elif 'Volume Name' in line:
                    label = line.split(':', 1)[1].strip()

            if mountpoint == 'Not mounted':
                mountpoint = ''

            return mountpoint, label
        except subprocess.CalledProcessError:
            return ''

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
