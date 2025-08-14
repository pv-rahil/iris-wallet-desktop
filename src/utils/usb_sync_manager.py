"""
USB sync manager for handling wallet data synchronization with USB drives.

This module provides functionality to sync wallet data to/from USB drives
with proper validation, backup, and error handling.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import os
import shutil
import time
import zipfile

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType
from src.utils.build_app_path import app_paths
from src.utils.constant import CURRENT_RGB_LIB_VERSION
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_RGB_LIB_INCOMPATIBILITY
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.usb_detector import USBDetector
from src.utils.usb_detector import USBDrive
from src.views.components.toast import ToastManager
from src.views.components.usb_sync_dialog import USBSyncDialog


class USBSyncManager:
    """
    Manages USB synchronization for wallet data.

    The USB sync dialog will only be shown when:
    1. USB sync is enabled for the current wallet mode (offline or watch-only)
    2. A USB drive is detected
    3. The current page is the fungible page
    4. The dialog hasn't been shown for the current session on the fungible page
    """

    def __init__(self, main_window):
        """
        Initialize the USB sync manager.

        Args:
            main_window: The main window instance.
        """
        self.main_window = main_window
        self.usb_detector = USBDetector()
        self.sync_in_progress = False
        self.dialog_shown = False
        self.master_fingerprint = None
        self.selected_drive: USBDrive | None = None

    def reset_dialog_flag(self):
        """
        Reset the dialog shown flag to allow showing dialog again.
        This can be called manually if needed, but the flag is automatically
        reset when navigating away from the fungible page.
        """
        self.dialog_shown = False

    def _is_usb_sync_enabled(self) -> bool:
        """
        Check if USB sync should be enabled based on wallet mode.
        USB sync is only enabled for offline wallets and watch-only wallets.

        Returns:
            bool: True if USB sync should be enabled, False otherwise.
        """
        try:
            wallet_type = SettingRepository.get_wallet_type()
            security_type = SettingRepository.get_wallet_security_type()

            is_offline = wallet_type == WalletType.OFFLINE_TYPE_WALLET
            is_watch_only = security_type == WalletSecurityType.WATCH_ONLY

            return is_offline or is_watch_only
        except Exception as exc:
            logger.error(
                'Error checking USB sync enabled status: %s', str(exc),
            )
            return False

    def check_usb_and_prompt(self):
        """
        Check for USB drives and prompt user for sync if detected.
        Only works for offline wallets and watch-only wallets.
        Only shows dialog when on the fungible page.
        """
        try:
            self.master_fingerprint = self._get_master_fingerprint()
            # Check if USB sync is enabled for current wallet mode
            if not self._is_usb_sync_enabled():
                return

            if self.sync_in_progress:
                return

            # Only show dialog if not already shown for this session
            if not self.dialog_shown:
                self.show_usb_sync_dialog()
                self.dialog_shown = True  # Mark dialog as shown

        except Exception as exc:
            logger.error('Error checking USB drives: %s', str(exc))

    def show_usb_sync_dialog(self):
        """
        Show USB sync dialog to user.
        """
        try:
            usb_drives = self.usb_detector.detect_usb_drives()

            dialog = USBSyncDialog(usb_drives, self.main_window)
            if dialog.exec() == QDialog.Accepted:
                self.selected_drive: USBDrive = dialog.get_selected_drive()
                if self.selected_drive:
                    self._perform_sync()
            self.reset_dialog_flag()
        except Exception as exc:
            logger.error('Error showing USB sync dialog: %s', str(exc))

    def _perform_sync(self):
        """
        Perform the actual sync operation.

        Args:
        """
        try:
            self.sync_in_progress = True

            # Check if master fingerprint is available
            if not self.master_fingerprint:
                self._show_sync_error(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_master_fingerprint_not_found',
                    ),
                )
                return

            # Validate USB drive
            if not self._validate_usb_drive():
                return

            # Determine sync direction based on timestamps
            sync_direction = self._determine_sync_direction()

            if sync_direction == 'to_usb':
                self._sync_to_usb()
            elif sync_direction == 'from_usb':
                self._sync_from_usb()
            else:
                logger.info('No sync needed - data is up to date')
                self._show_sync_success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'No sync needed - data is up to date', None,
                    ),
                )

        except Exception as exc:
            logger.error('USB sync failed: %s', str(exc))
            self._show_sync_error(str(exc))
        finally:
            self.sync_in_progress = False

    def _validate_usb_drive(self) -> bool:
        """
        Validate the USB drive for sync.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Check if USB is empty (valid for new sync)
            if self.selected_drive and self.selected_drive.is_empty:
                return True

            # If USB is not empty, check if it contains valid wallet data for this fingerprint
            if not self._has_valid_wallet_data():
                self._show_sync_error(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_invalid_wallet_data',
                    ),
                )
                return False

            return True
        except Exception as exc:
            logger.error('USB drive validation failed: %s', str(exc))
            return False

    def _has_valid_wallet_data(self) -> bool:
        """
        Check if USB contains valid wallet data for the given master fingerprint.

        Args:
            usb_path: Path to USB drive.

        Returns:
            bool: True if valid wallet data found, False otherwise.
        """
        try:
            # Look for ZIP files with the same master fingerprint
            if not self.selected_drive:
                return False
            for file in os.listdir(self.selected_drive.path):
                if file.startswith(self.master_fingerprint) and file.endswith('.zip'):
                    return True
            return False
        except Exception:
            return False

    def _validate_usb_zip_and_get_ini(self, zip_path: str) -> str | None:
        """
        Validate the USB zip: check ini, RGB lib version, master fingerprint, xpub.
        Returns the ini content if valid, else None.
        """
        try:
            local_ini_path = self._get_ini_file_path()
            local_xpub_vanilla = None
            local_xpub_colored = None
            local_rgb_lib_version = None
            local_fingerprint = None

            if os.path.exists(local_ini_path):
                with open(local_ini_path, encoding='utf-8') as f:
                    local_ini = f.read()
                for line in local_ini.splitlines():
                    line = line.strip()
                    if line.startswith('account_xpub_vanilla'):
                        local_xpub_vanilla = line.strip()
                    elif line.startswith('account_xpub_colored'):
                        local_xpub_colored = line.strip()
                    elif line.startswith('rgb_lib_version'):
                        local_rgb_lib_version = line
                    elif line.startswith('master_fingerprint'):
                        local_fingerprint = line.strip()

            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                ini_file = [
                    f for f in zip_file.namelist()
                    if f.endswith('.ini')
                ]
                if not ini_file:
                    return None

                ini_content = zip_file.read(ini_file[0]).decode('utf-8')

                usb_xpub_vanilla = None
                usb_xpub_colored = None
                usb_rgb_lib_version = None
                usb_fingerprint = None
                for line in ini_content.splitlines():
                    line = line.strip()
                    if line.startswith('account_xpub_vanilla'):
                        usb_xpub_vanilla = line.strip()
                    elif line.startswith('account_xpub_colored'):
                        usb_xpub_colored = line.strip()
                    elif line.startswith('rgb_lib_version'):
                        usb_rgb_lib_version = line
                    elif line.startswith('master_fingerprint'):
                        usb_fingerprint = line.strip()

                if local_rgb_lib_version != usb_rgb_lib_version:
                    logger.error(
                        'RGB lib version mismatch (local: %s, usb: %s)',
                        local_rgb_lib_version, usb_rgb_lib_version,
                    )
                    ToastManager.error(ERROR_RGB_LIB_INCOMPATIBILITY)
                    return None
                if local_fingerprint != usb_fingerprint:
                    logger.error(
                        'Master fingerprint mismatch (local: %s, usb: %s)',
                        local_fingerprint, usb_fingerprint,
                    )
                    ToastManager.error('Master fingerprint mismatch')
                    return None

                if local_xpub_vanilla != usb_xpub_vanilla:
                    logger.error(
                        'account_xpub_vanilla mismatch (local: %s, usb: %s)',
                        local_xpub_vanilla, usb_xpub_vanilla,
                    )
                    ToastManager.error('account_xpub_vanilla mismatch')
                    return None
                if local_xpub_colored != usb_xpub_colored:
                    logger.error(
                        'account_xpub_colored mismatch (local: %s, usb: %s)',
                        local_xpub_colored, usb_xpub_colored,
                    )
                    ToastManager.error('account_xpub_colored mismatch')
                    return None

                return ini_content
        except Exception as exc:
            logger.error('USB zip validation failed: %s', str(exc))
        return None

    def _determine_sync_direction(self) -> str | None:
        """
        Determine sync direction based on counter (index) instead of timestamps.
        Returns:
            Optional[str]: 'to_usb', 'from_usb', or None if no sync needed.
        """
        try:
            if not self.selected_drive:
                return None  # critical exit, no drive selected

            # Check if wallet's INI file exists on USB
            usb_ini_exists = self._check_usb_ini_exists()

            if not usb_ini_exists:
                # Scenario 1: Initial backup - wallet's INI file NOT found
                logger.info(
                    'No wallet INI file found on USB - creating initial backup',
                )
                return 'to_usb'
            # Scenario 2: Existing sync - wallet's INI file found
            return self._determine_sync_direction_with_counter()

        except Exception as exc:
            logger.error('Error determining sync direction: %s', str(exc))
            return 'to_usb'  # default on error

    def _check_usb_ini_exists(self) -> bool:
        """
        Check if wallet's INI file exists on USB drive.
        Returns:
            bool: True if INI file exists, False otherwise.
        """
        try:
            if not self.selected_drive:
                return False

            # Look for ZIP file with master fingerprint name
            zip_filename = f'{self.master_fingerprint}.zip'
            zip_path = os.path.join(self.selected_drive.path, zip_filename)

            if os.path.exists(zip_path):
                # Check if this ZIP contains an INI file
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    ini_files = [
                        f for f in zip_file.namelist()
                        if f.endswith('.ini')
                    ]
                    if ini_files:
                        return True
            return False
        except Exception as exc:
            logger.error('Error checking USB INI existence: %s', str(exc))
            return False

    def _determine_sync_direction_with_counter(self) -> str | None:
        """
        Determine sync direction using index and runtime checksums (not stored).
        Returns:
            Optional[str]: 'to_usb', 'from_usb', or None if no sync needed.
        """
        try:
            usb_index = self._get_usb_index()
            local_index = self._get_local_index()
            logger.info(
                'USB index: %s, Local index: %s',
                usb_index, local_index,
            )
            print(
                f"[USB Sync Debug] indices -> usb_index={
                    usb_index
                }, local_index={local_index}",
            )

            # USB ahead
            if usb_index > local_index:
                usb_checksum = self._calculate_usb_wallet_checksum()
                local_checksum = self._calculate_wallet_checksum()
                print(f"[USB Sync Debug] usb_ahead checksums -> usb={
                      usb_checksum[:8]
                      }, local={local_checksum[:8]}")
                if usb_checksum == local_checksum:
                    logger.info(
                        'USB ahead but runtime checksums match - no sync needed',
                    )
                    print(
                        '[USB Sync Debug] decision -> none (usb ahead, checksums match)',
                    )
                    return None
                logger.info(
                    'USB ahead and runtime checksums differ - syncing from USB',
                )
                print(
                    '[USB Sync Debug] decision -> from_usb (usb ahead, checksums differ)',
                )
                return 'from_usb'

            # Local ahead
            if usb_index < local_index:
                usb_checksum = self._calculate_usb_wallet_checksum()
                local_checksum = self._calculate_wallet_checksum()
                print(f"[USB Sync Debug] local_ahead checksums -> usb={
                      usb_checksum[:8]
                      }, local={local_checksum[:8]}")
                if usb_checksum == local_checksum:
                    logger.info(
                        'Local ahead but runtime checksums match - no sync needed',
                    )
                    print(
                        '[USB Sync Debug] decision -> none (local ahead, checksums match)',
                    )
                    return None
                logger.info(
                    'Local ahead and runtime checksums differ - syncing to USB',
                )
                print(
                    '[USB Sync Debug] decision -> to_usb (local ahead, checksums differ)',
                )
                return 'to_usb'

            # Indices equal: compare runtime checksums
            usb_checksum = self._calculate_usb_wallet_checksum()
            local_checksum = self._calculate_wallet_checksum()
            print(f"[USB Sync Debug] equal_indices checksums -> usb={
                  usb_checksum[:8]
                  }, local={local_checksum[:8]}")
            if usb_checksum == local_checksum:
                logger.info(
                    'Indices equal and runtime checksums match - no sync needed',
                )
                print(
                    '[USB Sync Debug] decision -> none (equal indices, checksums match)',
                )
                return None
            return None
        except Exception as exc:
            logger.error(
                'Error determining sync direction with counter: %s', str(exc),
            )
            print(f"[USB Sync Debug] error determining direction: {exc}")
            return None

    def _calculate_wallet_checksum(self) -> str:
        """
        Calculate SHA256 checksum of all files in master fingerprint folder except logs.
        Files are hashed in sorted order of their relative paths (to match USB method).
        """
        try:
            wallet_data_path = self._get_wallet_data_path()
            folder_path = os.path.join(
                wallet_data_path, self.master_fingerprint,
            )

            if not os.path.exists(folder_path):
                logger.warning('Wallet folder not found: %s', folder_path)
                return hashlib.sha256(b'').hexdigest()  # Empty hash

            # Gather all relative file paths first
            file_paths = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    rel_path = os.path.relpath(
                        os.path.join(root, file), folder_path,
                    )
                    if rel_path == 'log' or rel_path.startswith('log/'):
                        continue
                    file_paths.append(rel_path)

            file_paths.sort()  # Ensure consistent global ordering

            sha256_hash = hashlib.sha256()
            included_local_files: list[str] = []

            for rel_path in file_paths:
                file_path = os.path.join(folder_path, rel_path)
                try:
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b''):
                            sha256_hash.update(chunk)
                    included_local_files.append(rel_path)
                except Exception as exc:
                    logger.warning(
                        'Could not read file for checksum: %s - %s', file_path, exc,
                    )
                    sha256_hash.update(file_path.encode())

            logger.info(
                'Calculated checksum for master fingerprint folder (excluding logs): %s',
                sha256_hash.hexdigest()[:8],
            )
            try:
                print(f'[USB Sync Debug] local files considered (count={
                      len(included_local_files)
                      }):')
                for p in included_local_files:
                    print(f'  [local] {p}')
            except Exception:
                pass
            return sha256_hash.hexdigest()

        except Exception as exc:
            logger.error('Error calculating wallet checksum: %s', str(exc))
            return hashlib.sha256(b'error').hexdigest()

    def _calculate_usb_wallet_checksum(self) -> str:
        """
        Calculate SHA256 checksum of wallet data stored inside the USB ZIP (runtime),
        excluding logs and cache directories. Files are hashed in sorted order of relative paths.
        """
        try:
            if not self.selected_drive:
                return hashlib.sha256(b'').hexdigest()

            zip_filename = f'{self.master_fingerprint}.zip'
            zip_path = os.path.join(self.selected_drive.path, zip_filename)
            if not os.path.exists(zip_path):
                return hashlib.sha256(b'').hexdigest()

            sha256_hash = hashlib.sha256()
            included_usb_files: list[str] = []

            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                prefix = self.master_fingerprint + '/'

                # Collect relevant files
                file_paths = []
                for name in zip_file.namelist():
                    if not name.startswith(prefix) or name.endswith('/'):
                        continue
                    rel = name[len(prefix):]
                    if rel == 'log' or rel.startswith('log/'):
                        continue
                    file_paths.append(rel)

                file_paths.sort()  # Ensure consistent ordering

                for rel in file_paths:
                    data = zip_file.read(prefix + rel)
                    sha256_hash.update(data)
                    included_usb_files.append(rel)

            try:
                print(f'[USB Sync Debug] usb files considered (count={
                      len(included_usb_files)
                      }):')
                for p in included_usb_files:
                    print(f'  [usb] {p}')
            except Exception:
                pass
            return sha256_hash.hexdigest()

        except Exception as exc:
            logger.error('Error calculating USB wallet checksum: %s', str(exc))
            return hashlib.sha256(b'error').hexdigest()

    def _get_usb_index(self) -> int:
        """
        Get USB index from the latest ZIP file on USB.
        Returns:
            int: USB index or 0 if not found.
        """
        try:
            if not self.selected_drive:
                return 0

            # Find ZIP file with master fingerprint name
            zip_filename = f'{self.master_fingerprint}.zip'
            zip_path = os.path.join(self.selected_drive.path, zip_filename)

            if not os.path.exists(zip_path):
                return 0

            latest_zip = zip_path

            # Extract and read INI file from ZIP
            with zipfile.ZipFile(latest_zip, 'r') as zip_file:
                ini_files = [
                    f for f in zip_file.namelist()
                    if f.endswith('.ini')
                ]
                if not ini_files:
                    return 0

                ini_content = zip_file.read(ini_files[0]).decode('utf-8')

                # Parse index from INI content
                for line in ini_content.splitlines():
                    line = line.strip()
                    if line.startswith('sync_index='):
                        try:
                            return int(line.split('=')[1].strip())
                        except (ValueError, IndexError):
                            return 0

            return 0
        except Exception as exc:
            logger.error('Error getting USB index: %s', str(exc))
            return 0

    def _get_local_index(self) -> int:
        """
        Get local index from local INI file.
        Returns:
            int: Local index or 0 if not found.
        """
        try:
            local_ini_path = self._get_ini_file_path()
            if not os.path.exists(local_ini_path):
                return 0

            with open(local_ini_path, encoding='utf-8') as f:
                ini_content = f.read()

            # Parse index from INI content
            for line in ini_content.splitlines():
                line = line.strip()
                if line.startswith('sync_index='):
                    try:
                        return int(line.split('=')[1].strip())
                    except (ValueError, IndexError):
                        return 0

            return 0
        except Exception as exc:
            logger.error('Error getting local index: %s', str(exc))
            return 0

    def _update_local_index(self, new_index: int):
        """
        Update local index in INI file.
        Args:
            new_index: New index value to set.
        """
        try:
            local_ini_path = self._get_ini_file_path()
            if not os.path.exists(local_ini_path):
                logger.warning('Local INI file not found, cannot update index')
                return

            # Read current INI content
            with open(local_ini_path, encoding='utf-8') as f:
                lines = f.readlines()

            # Update or add sync_index line
            index_updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith('sync_index='):
                    lines[i] = f'sync_index={new_index}\n'
                    index_updated = True
                    break

            if not index_updated:
                # Add sync_index line if not found
                lines.append(f'sync_index={new_index}\n')

            # Write updated content back
            with open(local_ini_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            logger.info('Updated local index to: %s', new_index)
        except Exception as exc:
            logger.error('Error updating local index: %s', str(exc))

    def _get_local_wallet_timestamp(self) -> float:
        """
        Get local wallet data timestamp (for the master fingerprint folder).
        Returns:
            float: Timestamp of local wallet data.
        """
        try:
            if not self.master_fingerprint:
                return time.time()
            folder_path = os.path.join(
                self._get_wallet_data_path(), self.master_fingerprint,
            )
            if os.path.exists(folder_path):
                return os.path.getmtime(folder_path)
            return time.time()
        except Exception:
            return time.time()

    def _sync_to_usb(self):
        """
        Sync wallet data to USB drive using counter-based approach.
        """
        try:
            # Get current local index
            current_local_index = self._get_local_index()

            # Check if this is initial backup (index = 0)
            if current_local_index == 0:
                # Initial backup: set local index = 0, write backup with index=0
                logger.info('Creating initial backup with index=0')
                self._update_local_index(0)
                wallet_data = self._create_wallet_data_package_with_index(0)

                # Prepare USB by rotating existing zip to _temp.zip (if any), then write initial backup
                filename = f'{self.master_fingerprint}.zip'
                usb_file_path = os.path.join(
                    self.selected_drive.path, filename,
                )
                self._rotate_usb_zip_backup()
                with open(usb_file_path, 'wb') as f:
                    f.write(wallet_data)

                # Update local sync index
                self._update_local_index(1)
                # Update USB INI file with index = 1
                self._update_usb_ini_index(1)

                logger.info('Initial backup created successfully')
                # Ensure only one USB temp backup exists
                self._cleanup_extra_usb_temp_backups()
                self._show_sync_success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_success',
                    ),
                )
            else:
                # Regular sync: wallet is more up-to-date
                logger.info('Regular sync: wallet is more up-to-date')

                # Create temp backup of local folder before syncing
                backup_path = self._create_local_temp_backup()
                try:
                    # Calculate new index but don't update local yet
                    new_index = current_local_index + 1

                    # Create backup with the new incremented index (but local still has old index)
                    wallet_data = self._create_wallet_data_package_with_index(
                        new_index,
                    )

                    # Prepare USB by rotating existing zip to _temp.zip
                    filename = f'{self.master_fingerprint}.zip'
                    usb_file_path = os.path.join(
                        self.selected_drive.path, filename,
                    )
                    self._rotate_usb_zip_backup()

                    # Write to USB - this is the critical operation that might fail
                    with open(usb_file_path, 'wb') as f:
                        f.write(wallet_data)

                    # Only after successful USB write, commit the local index increment
                    self._update_local_index(new_index)

                    logger.info(
                        'Successfully synced wallet data to USB with index: %s', new_index,
                    )
                    self._show_sync_success(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_success',
                        ),
                    )
                except Exception as exc:
                    # Fallback: local index was never incremented, so no rollback needed
                    # Just restore from temp backup if sync fails
                    if backup_path and os.path.exists(backup_path):
                        self._restore_local_folder_from_backup(backup_path)
                    logger.error(
                        'USB sync failed, local index remains at: %s', current_local_index,
                    )
                    raise exc
                finally:
                    # Keep temp backup for safety
                    if backup_path and os.path.exists(backup_path):
                        logger.info(
                            'Local temp backup kept at: %s (only one temp backup maintained)', backup_path,
                        )
                    # Ensure only one USB temp backup exists
                    self._cleanup_extra_usb_temp_backups()

        except Exception as exc:
            logger.error('Sync to USB failed: %s', str(exc))
            raise exc

    def _rotate_usb_zip_backup(self):
        """
        On the USB drive, keep at most two files for the fingerprint: the current
        '{fingerprint}.zip' and one backup '{fingerprint}_temp.zip'. If a current
        zip exists, move it to _temp.zip (overwriting any existing _temp.zip).
        """
        try:
            if not self.selected_drive:
                return
            base = f'{self.master_fingerprint}.zip'
            temp = f'{self.master_fingerprint}_temp.zip'
            base_path = os.path.join(self.selected_drive.path, base)
            temp_path = os.path.join(self.selected_drive.path, temp)

            # Remove old temp if present
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info('Removed old USB temp zip: %s', temp)
                except Exception as exc:
                    logger.error(
                        'Failed removing old USB temp zip %s: %s', temp, exc,
                    )

            # Move current to temp if present
            if os.path.exists(base_path):
                try:
                    os.rename(base_path, temp_path)
                    logger.info(
                        'Rotated USB zip to temp: %s -> %s', base, temp,
                    )
                except Exception as exc:
                    logger.error('Failed rotating USB zip to temp: %s', exc)
        except Exception as exc:
            logger.error('USB rotation failed: %s', str(exc))

    def _cleanup_extra_usb_temp_backups(self):
        """
        Remove any extra temp zips beyond '{fingerprint}_temp.zip' to ensure only one
        temp backup exists for the fingerprint.
        """
        try:
            if not self.selected_drive:
                return
            # Only the canonical temp name is kept; remove any others matching pattern
            keep = f'{self.master_fingerprint}_temp.zip'
            for name in os.listdir(self.selected_drive.path):
                if (
                    name.startswith(self.master_fingerprint)
                    and name.endswith('_temp.zip')
                    and name != keep
                ):
                    try:
                        os.remove(os.path.join(self.selected_drive.path, name))
                        logger.info('Removed extra USB temp zip: %s', name)
                    except Exception as exc:
                        logger.error(
                            'Failed removing extra USB temp zip %s: %s', name, exc,
                        )
        except Exception as exc:
            logger.error('USB temp cleanup failed: %s', str(exc))

    def _create_local_temp_backup(self) -> str | None:
        """
        Create a temp backup of the local master fingerprint folder as a zip in the app data path.
        Only keeps one temp backup, similar to USB behavior.
        Returns:
            Optional[str]: Path to backup file or None if failed.
        """
        try:
            folder_path = os.path.join(
                self._get_wallet_data_path(), self.master_fingerprint,
            )
            if not os.path.exists(folder_path):
                logger.warning('No local folder to backup: %s', folder_path)
                return None

            # Find existing temp backup for this master fingerprint
            temp_backup_name = f'{self.master_fingerprint}_temp.zip'
            temp_backup_path = os.path.join(
                self._get_wallet_data_path(), temp_backup_name,
            )

            # Remove old temp backup if exists
            if os.path.exists(temp_backup_path):
                try:
                    os.remove(temp_backup_path)
                    logger.info(
                        'Removed old local temp backup: %s',
                        temp_backup_name,
                    )
                except Exception as exc:
                    logger.error(
                        'Failed to remove old local temp backup %s: %s', temp_backup_name, exc,
                    )

            # Create new temp backup
            backup_path = temp_backup_path

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(folder_path):
                    rel_dir = os.path.relpath(root, folder_path)
                    if rel_dir == '.':
                        rel_dir = ''
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.join(
                            self.master_fingerprint, rel_dir, file,
                        )
                        if not rel_dir:
                            rel_path = os.path.join(
                                self.master_fingerprint, file,
                            )
                        zip_file.write(file_path, rel_path)

            logger.info('Created local temp backup: %s', backup_path)
            return backup_path
        except Exception as exc:
            logger.error('Failed to create local temp backup: %s', str(exc))
            return None

    def _sync_from_usb(self):
        """
        Sync wallet data from USB drive using counter-based approach.
        """
        try:
            # Get USB index
            usb_index = self._get_usb_index()
            if usb_index == 0:
                raise CommonException(
                    QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_no_wallet_files').format(
                        fingerprint=self.master_fingerprint,
                    ),
                )

            # Find ZIP file with master fingerprint name
            zip_filename = f'{self.master_fingerprint}.zip'
            usb_file_path = os.path.join(
                self.selected_drive.path, zip_filename,
            )

            if not os.path.exists(usb_file_path):
                raise CommonException(
                    QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_no_wallet_files').format(
                        fingerprint=self.master_fingerprint,
                    ),
                )

            # Create temp backup of local folder before restoring
            backup_path = self._create_local_temp_backup()
            try:
                with open(usb_file_path, 'rb') as f:
                    wallet_data = f.read()
                if not self._validate_wallet_data(wallet_data):
                    raise CommonException(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_invalid_data',
                        ),
                    )

                # Restore wallet data from USB
                self._restore_wallet_data(wallet_data, only_folder=True)

                # Update local index to USB index + 1 after successful restore
                # This marks local as "synced ahead" to avoid equal-index ambiguity
                self._update_local_index(usb_index + 1)

                logger.info(
                    'Successfully synced wallet data from USB (usb_index=%s), advanced local index to: %s',
                    usb_index, usb_index + 1,
                )
                self._show_sync_success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_from_success',
                    ),
                )
            except Exception as exc:
                if backup_path and os.path.exists(backup_path):
                    self._restore_local_folder_from_backup(
                        backup_path,
                    )
                raise exc
            finally:
                if backup_path and os.path.exists(backup_path):
                    logger.info(
                        'Local temp backup kept at: %s (only one temp backup maintained)', backup_path,
                    )
        except Exception as exc:
            logger.error('Sync from USB failed: %s', str(exc))
            raise exc

    def _restore_wallet_data(self, wallet_data: bytes, only_folder: bool = False):
        """
        Restore wallet data from bytes.
        Args:
            wallet_data: Wallet data bytes.
            only_folder: If True, only replace the master fingerprint folder, not the INI file.
        """
        try:
            wallet_data_path = self._get_wallet_data_path()
            # Remove the existing folder before restoring
            folder_path = os.path.join(
                wallet_data_path, self.master_fingerprint,
            )
            if only_folder and os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            with zipfile.ZipFile(io.BytesIO(wallet_data), 'r') as zip_file:
                if only_folder:
                    # Only extract the master fingerprint folder
                    folder_prefix = self.master_fingerprint + '/'
                    for member in zip_file.namelist():
                        if member.startswith(folder_prefix) and not member.endswith('/'):
                            target_path = os.path.join(
                                wallet_data_path, member,
                            )
                            os.makedirs(
                                os.path.dirname(
                                    target_path,
                                ), exist_ok=True,
                            )
                            with open(target_path, 'wb') as f:
                                f.write(zip_file.read(member))
                    logger.info(
                        'Extracted only folder: %s',
                        self.master_fingerprint,
                    )
                else:
                    # Extract all files to wallet data path
                    zip_file.extractall(wallet_data_path)
                logger.info('Extracted files: %s', zip_file.namelist())
            logger.info(
                'Successfully restored wallet data to: %s',
                wallet_data_path,
            )
        except Exception as exc:
            logger.error('Failed to restore wallet data: %s', str(exc))
            raise exc

    def _restore_local_folder_from_backup(self, backup_path: str):
        """
        Restore the local master fingerprint folder from a backup zip.
        """
        try:
            wallet_data_path = self._get_wallet_data_path()
            folder_path = os.path.join(
                wallet_data_path, self.master_fingerprint,
            )
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                for member in zip_file.namelist():
                    if member.startswith(self.master_fingerprint + '/') and not member.endswith('/'):
                        target_path = os.path.join(wallet_data_path, member)
                        os.makedirs(
                            os.path.dirname(
                                target_path,
                            ), exist_ok=True,
                        )
                        with open(target_path, 'wb') as f:
                            f.write(zip_file.read(member))
            logger.info('Restored local folder from backup: %s', backup_path)
        except Exception as exc:
            logger.error(
                'Failed to restore local folder from backup: %s', str(exc),
            )

    def _create_wallet_data_package(self) -> bytes:
        """
        Create wallet data package as ZIP containing wallet folder and INI file.

        Returns:
            bytes: ZIP data containing wallet folder and INI file.
        """
        try:
            # Get wallet data path and INI file path
            wallet_data_path = self._get_wallet_data_path()
            ini_file_path = self._get_ini_file_path()

            # Create ZIP in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add wallet folder contents (excluding logs and cache)
                self._add_wallet_folder_to_zip(zip_file, wallet_data_path)

                # Add INI file with original name
                if os.path.exists(ini_file_path):
                    zip_file.write(
                        ini_file_path, os.path.basename(ini_file_path),
                    )

            return zip_buffer.getvalue()
        except Exception as exc:
            logger.error('Failed to create wallet data package: %s', str(exc))
            raise exc

    def _create_wallet_data_package_with_index(self, index: int) -> bytes:
        """
        Create wallet data package as ZIP containing wallet folder and INI file with sync index.

        Args:
            index: Sync index to include in the package.

        Returns:
            bytes: ZIP data containing wallet folder and INI file with sync index.
        """
        try:
            # Get wallet data path and INI file path
            wallet_data_path = self._get_wallet_data_path()
            ini_file_path = self._get_ini_file_path()

            # Create ZIP in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add wallet folder contents (excluding logs and cache)
                self._add_wallet_folder_to_zip(zip_file, wallet_data_path)

                # Add INI file with sync index
                if os.path.exists(ini_file_path):
                    # Read current INI content
                    with open(ini_file_path, encoding='utf-8') as f:
                        ini_content = f.read()

                    # Add or update sync_index
                    lines = ini_content.splitlines()
                    index_updated = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith('sync_index='):
                            lines[i] = f'sync_index={index}'
                            index_updated = True
                            break

                    if not index_updated:
                        lines.append(f'sync_index={index}')

                    # Create updated INI content
                    updated_ini_content = '\n'.join(lines)

                    # Add updated INI file to ZIP
                    zip_file.writestr(
                        os.path.basename(
                            ini_file_path,
                        ), updated_ini_content,
                    )

            return zip_buffer.getvalue()
        except Exception as exc:
            logger.error(
                'Failed to create wallet data package with index: %s', str(
                    exc,
                ),
            )
            raise exc

    def _update_usb_ini_index(self, new_index: int):
        """
        Update the INI file on USB with new sync index.
        Args:
            new_index: New index value to set.
        """
        try:
            # Find ZIP file with master fingerprint name
            zip_filename = f'{self.master_fingerprint}.zip'
            latest_zip_path = os.path.join(
                self.selected_drive.path, zip_filename,
            )

            if not os.path.exists(latest_zip_path):
                logger.warning('No USB ZIP file found to update index')
                return

            # Create a new ZIP with updated INI
            temp_zip_path = latest_zip_path.replace('.zip', '_temp.zip')

            with zipfile.ZipFile(latest_zip_path, 'r') as old_zip:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for item in old_zip.infolist():
                        if item.filename.endswith('.ini'):
                            # Read current INI content
                            ini_content = old_zip.read(
                                item.filename,
                            ).decode('utf-8')
                            lines = ini_content.splitlines()

                            # Update sync_index
                            index_updated = False
                            for i, line in enumerate(lines):
                                if line.strip().startswith('sync_index='):
                                    lines[i] = f'sync_index={new_index}'
                                    index_updated = True
                                    break

                            if not index_updated:
                                lines.append(f'sync_index={new_index}')

                            # Write updated INI content
                            updated_ini_content = '\n'.join(lines)
                            new_zip.writestr(
                                item.filename, updated_ini_content,
                            )
                        else:
                            # Copy other files as-is
                            new_zip.writestr(item, old_zip.read(item.filename))

            # Replace old ZIP with new one
            os.remove(latest_zip_path)
            os.rename(temp_zip_path, latest_zip_path)

            logger.info('Updated USB INI file with index: %s', new_index)
        except Exception as exc:
            logger.error('Error updating USB INI index: %s', str(exc))

    def _update_usb_ini(self, new_index: int, checksum: str):
        """
        Update both sync_index and last_sync_checksum in the INI inside the USB ZIP.
        """
        try:
            zip_filename = f'{self.master_fingerprint}.zip'
            latest_zip_path = os.path.join(
                self.selected_drive.path, zip_filename,
            )

            if not os.path.exists(latest_zip_path):
                logger.warning('No USB ZIP file found to update INI')
                return

            temp_zip_path = latest_zip_path.replace('.zip', '_temp.zip')

            with zipfile.ZipFile(latest_zip_path, 'r') as old_zip:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for item in old_zip.infolist():
                        if item.filename.endswith('.ini'):
                            ini_content = old_zip.read(
                                item.filename,
                            ).decode('utf-8')
                            lines = ini_content.splitlines()
                            # update sync_index
                            idx_updated = False
                            chk_updated = False
                            for i, line in enumerate(lines):
                                s = line.strip()
                                if s.startswith('sync_index='):
                                    lines[i] = f'sync_index={new_index}'
                                    idx_updated = True
                                elif s.startswith('last_sync_checksum='):
                                    lines[i] = f'last_sync_checksum={checksum}'
                                    chk_updated = True
                            if not idx_updated:
                                lines.append(f'sync_index={new_index}')
                            if not chk_updated:
                                lines.append(f'last_sync_checksum={checksum}')
                            updated_ini_content = '\n'.join(lines)
                            new_zip.writestr(
                                item.filename, updated_ini_content,
                            )
                        else:
                            new_zip.writestr(item, old_zip.read(item.filename))

            os.remove(latest_zip_path)
            os.rename(temp_zip_path, latest_zip_path)
            logger.info(
                'Updated USB INI file with index=%s and checksum=%s', new_index, checksum[:8],
            )
        except Exception as exc:
            logger.error('Error updating USB INI: %s', str(exc))

    def _add_wallet_folder_to_zip(self, zip_file, wallet_path: str):
        """
        Add wallet folder contents to ZIP, excluding logs and cache.

        Args:
            zip_file: ZIP file object.
            wallet_path: Path to wallet data directory.
        """
        try:
            # Get the wallet data folder (excluding logs and cache)
            wallet_data_folder = self._get_wallet_data_folder(wallet_path)

            if not os.path.exists(wallet_data_folder):
                logger.warning(
                    'Wallet data folder not found: %s', wallet_data_folder,
                )
                return

            # Get master fingerprint for folder name
            if not self.master_fingerprint:
                logger.warning(
                    'Master fingerprint not found, using original structure',
                )
                self.master_fingerprint = os.path.basename(wallet_data_folder)

            # Always add the root folder entry (even if empty)
            zip_root = self.master_fingerprint + '/'
            zip_file.writestr(zip_root, '')

            # Walk through the wallet data folder
            for root, dirs, files in os.walk(wallet_data_folder):
                # Skip logs and cache directories
                dirs[:] = [d for d in dirs if d not in ['logs', 'cache']]
                # Add directory entry for each subdirectory
                rel_dir = os.path.relpath(root, wallet_data_folder)
                if rel_dir != '.':
                    zip_dir = os.path.join(
                        self.master_fingerprint, rel_dir,
                    ) + '/'
                    zip_file.writestr(zip_dir, '')
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path from wallet data folder
                    rel_path = os.path.relpath(file_path, wallet_data_folder)
                    # Create path with master fingerprint folder name
                    zip_path = os.path.join(self.master_fingerprint, rel_path)
                    info = zipfile.ZipInfo(zip_path)
                    stat = os.stat(file_path)
                    info.date_time = datetime.datetime.fromtimestamp(
                        stat.st_mtime,
                    ).timetuple()[:6]
                    with open(file_path, 'rb') as f:
                        zip_file.writestr(info, f.read())

        except Exception as exc:
            logger.error('Failed to add wallet folder to ZIP: %s', str(exc))
            raise exc

    def _get_master_fingerprint(self) -> str:
        """
        Get master fingerprint from local storage.

        Returns:
            str: Master fingerprint or empty string if not found.
        """
        try:
            return local_store.get_value(MASTER_FINGERPRINT)
        except Exception as exc:
            logger.error('Failed to get master fingerprint: %s', str(exc))
            return ''

    def _get_ini_file_path(self) -> str:
        """
        Get path to the INI file.

        Returns:
            str: Path to the INI file.
        """
        try:
            return app_paths.config_file_path
        except Exception as exc:
            logger.error('Failed to get INI file path: %s', str(exc))
            return ''

    def _get_wallet_data_folder(self, wallet_path: str) -> str:
        """
        Get the wallet data folder with name matching master fingerprint.

        Args:
            wallet_path: Base wallet path.

        Returns:
            str: Path to wallet data folder.
        """
        try:
            if not self.master_fingerprint:
                return wallet_path

            # Look for folder with name matching master fingerprint
            fingerprint_folder = os.path.join(
                wallet_path, self.master_fingerprint,
            )
            if os.path.exists(fingerprint_folder) and os.path.isdir(fingerprint_folder):
                logger.info('Found wallet data folder: %s', fingerprint_folder)
                return fingerprint_folder

            # Fallback: look for any folder that's not logs or cache
            for item in os.listdir(wallet_path):
                item_path = os.path.join(wallet_path, item)
                if os.path.isdir(item_path) and item not in ['logs', 'cache']:
                    logger.info(
                        'Using fallback wallet data folder: %s', item_path,
                    )
                    return item_path

            # If no folder found, return the base path
            logger.warning(
                'No wallet data folder found, using base path: %s', wallet_path,
            )
            return wallet_path
        except Exception as exc:
            logger.error('Failed to get wallet data folder: %s', str(exc))
            return wallet_path

    def _validate_wallet_data(self, wallet_data: bytes) -> bool:
        """
        Validate wallet data from USB.

        Args:
            wallet_data: Wallet data bytes.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Extract and validate ZIP
            with zipfile.ZipFile(io.BytesIO(wallet_data), 'r') as zip_file:
                # Check for INI file first
                ini_files = [
                    f for f in zip_file.namelist()
                    if f.endswith('.ini')
                ]
                if not ini_files:
                    logger.error('No INI file found in ZIP')
                    return False

                # Read and validate INI file
                ini_file_name = ini_files[0]
                ini_content = zip_file.read(ini_file_name).decode('utf-8')

                # Check for RGB lib version in INI
                if 'rgb_lib_version' not in ini_content:
                    logger.error('RGB lib version not found in INI file')
                    return False

                # Extract RGB lib version from INI
                for line in ini_content.split('\n'):
                    if line.startswith('rgb_lib_version='):
                        usb_rgb_version = line.split('=')[1].strip()
                        if usb_rgb_version != CURRENT_RGB_LIB_VERSION:
                            logger.warning(
                                'RGB lib version mismatch: %s vs %s',
                                usb_rgb_version, CURRENT_RGB_LIB_VERSION,
                            )
                            return False
                        break

                # Check for master fingerprint in INI
                current_master_fingerprint = self._get_master_fingerprint()
                if current_master_fingerprint and current_master_fingerprint not in ini_content:
                    logger.error('Master fingerprint not found in INI file')
                    return False

                return True
        except Exception as exc:
            logger.error('Wallet data validation failed: %s', str(exc))
            return False

    def _get_wallet_data_path(self) -> str:
        """
        Get path to wallet data.

        Returns:
            str: Path to wallet data.
        """
        return app_paths.app_path

    def _show_sync_error(self, message: str):
        """Show sync error message to user."""
        try:
            ToastManager.error(description=message)
        except Exception as exc:
            logger.error('Failed to show sync error: %s', str(exc))

    def _show_sync_success(self, message: str):
        """Show sync success message to user."""
        try:
            ToastManager.success(description=message)
            self.reset_dialog_flag()
        except Exception as exc:
            logger.error('Failed to show sync success: %s', str(exc))
