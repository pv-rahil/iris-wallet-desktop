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
from threading import Event
from typing import Callable

from PySide6.QtCore import QObject, QTimer

from src.model.common_operation_model import USBDrive
from src.utils.logging import logger



class USBDetector(QObject):
    """Cross-platform USB drive detection utility with real-time monitoring."""
    
    _instance = None
    _monitoring_started = False

    def __new__(cls):
        """Singleton pattern to ensure only one USB detector instance."""
        if cls._instance is None:
            cls._instance = super(USBDetector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the USB detector."""
        if hasattr(self, 'platform'):  # Already initialized
            return
            
        super().__init__()
        self.platform = platform.system().lower()
        self._stop_event = Event()
        self.last_devices = self.get_available_devices()
        self._callbacks = []  # Store callbacks for re-registration
        
        # QTimer for non-blocking monitoring
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._check_for_changes)

    def get_available_devices(self) -> dict[str, dict]:
        """
        Get currently available USB devices.
        
        Returns:
            dict: Dictionary of USB devices with their information
        """
        try:
            if self.platform == 'linux':
                return self._get_linux_devices()
            elif self.platform == 'windows':
                return self._get_windows_devices()
            elif self.platform == 'darwin':
                return self._get_macos_devices()
            else:
                logger.error('Unsupported platform: %s', self.platform)
                return {}
        except Exception as exc:
            logger.error('Error getting available devices: %s', str(exc))
            return {}

    def _get_linux_devices(self) -> dict[str, dict]:
        """Get USB devices on Linux using lsblk."""
        try:
            result = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,TRAN,MOUNTPOINT,LABEL"], 
                capture_output=True, 
                text=True
            )
            data = json.loads(result.stdout)
            devices = {}

            def recurse(entry, is_usb_parent=False):
                # If this block has "tran: usb", mark it and recurse children
                if entry.get("tran") == "usb":
                    is_usb_parent = True

                # If this is a child (partition) and it's mounted under a USB parent
                if is_usb_parent and entry.get("mountpoint"):
                    name = entry.get("name")
                    devices[name] = {
                        "mountpoint": entry.get("mountpoint"),
                        "label": entry.get("label") or "Unknown",
                        "name": name,
                    }

                for child in entry.get("children", []):
                    recurse(child, is_usb_parent)

            for device in data.get("blockdevices", []):
                recurse(device)

            return devices
        except Exception as exc:
            logger.error('Linux USB detection error: %s', str(exc))
            return {}

    def _get_windows_devices(self) -> dict[str, dict]:
        """Get USB devices on Windows using PowerShell."""
        try:
            cmd = [
                "powershell", 
                "-Command", 
                "Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 2} | ConvertTo-Json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            devices = {}
            if isinstance(data, list):
                for drive in data:
                    device_id = drive.get("DeviceID", "").replace(":", "")
                    devices[device_id] = {
                        "mountpoint": drive.get("DeviceID", ""),
                        "label": drive.get("VolumeName") or "Unknown",
                        "name": device_id,
                    }
            elif isinstance(data, dict):
                device_id = data.get("DeviceID", "").replace(":", "")
                devices[device_id] = {
                    "mountpoint": data.get("DeviceID", ""),
                    "label": data.get("VolumeName") or "Unknown",
                    "name": device_id,
                }
                
            return devices
        except Exception as exc:
            logger.error('Windows USB detection error: %s', str(exc))
            return {}
    def get_mountpoint_and_label(self,device_path: str) -> tuple[str, str]:
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
                        mountpoint, label = self.get_mountpoint_and_label(device_path)

                        if mountpoint:
                            devices[device_path] = {
                                "mountpoint": mountpoint,
                                "label": label,
                                "name": device_path,
                            }

                    # Reset to avoid mixing other disks
                    current_disk = None

            return devices

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] diskutil failed: {e}")
            return []


    def changes_from_last_check(self) -> tuple[dict, dict]:
        """
        Get changes in USB devices since last check.
        
        Returns:
            tuple[dict, dict]: (added_devices, removed_devices)
        """
        current = self.get_available_devices()
        added = {k: v for k, v in current.items() if k not in self.last_devices}
        removed = {k: v for k, v in self.last_devices.items() if k not in current}
        self.last_devices = current
        return added, removed

    def start_real_time_monitoring(self, on_usb_connected: Callable, on_usb_disconnected: Callable = None):
        """
        Start real-time USB monitoring with event-based emission.
        
        Args:
            on_usb_connected: Callback function when USB is connected
            on_usb_disconnected: Callback function when USB is disconnected
        """
        self._callbacks = [on_usb_connected, on_usb_disconnected]
        
        if USBDetector._monitoring_started:
            logger.debug('USB monitoring already started, skipping')
            return
            
        try:
            self._stop_event.clear()
            # Start QTimer for monitoring (check every 1 second)
            self._monitor_timer.start(1000)  # 1000ms = 1 second
            USBDetector._monitoring_started = True
            logger.info('Real-time USB monitoring started (QTimer-based)')
            
        except Exception as exc:
            logger.error('Failed to start USB monitoring: %s', str(exc))

    def stop_real_time_monitoring(self):
        """Stop real-time USB monitoring."""
        self._monitor_timer.stop()
        self._stop_event.set()
        USBDetector._monitoring_started = False
        logger.info('Real-time USB monitoring stopped')

    def _check_for_changes(self):
        """Check for USB device changes using QTimer timeout."""
        if self._stop_event.is_set():
            return
            
        try:
            added, removed = self.changes_from_last_check()
            
            # Only call on_connect if there are actually new devices added
            if added:
                for dev_id, info in added.items():
                    logger.info(f'USB Connected: {info.get("label", "Unknown")}')
                # Call on_connect only once when new devices are detected
                if self._callbacks and len(self._callbacks) > 0 and self._callbacks[0]:
                    self._callbacks[0]()
            
            # Call on_disconnect if devices were removed
            if removed:
                for dev_id, info in removed.items():
                    logger.info(f'USB Disconnected: {info.get("label", "Unknown")}')
                if self._callbacks and len(self._callbacks) > 1 and self._callbacks[1]:
                    self._callbacks[1]()
                    
        except Exception as exc:
            logger.error('Error in USB monitoring check: %s', str(exc))

    def is_monitoring_active(self) -> bool:
        """Check if USB monitoring is currently active."""
        return USBDetector._monitoring_started

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
            
            for device_id, device_info in devices.items():
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
