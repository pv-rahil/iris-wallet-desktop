"""
USB sync manager for handling wallet data synchronization with USB drives.

This module provides functionality to sync wallet data to/from USB drives
with proper validation, backup, and error handling.
"""
from __future__ import annotations

import datetime
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

    def _get_local_rgb_db_mtime(self) -> float:
        """
        Get the mtime of the local <masterfingerprint>/rgb_lib_db file.
        Returns:
            float: mtime or 0 if not found.
        """
        try:
            rgb_db_path = os.path.join(
                self._get_wallet_data_path(), self.master_fingerprint, 'rgb_lib_db',
            )
            if os.path.exists(rgb_db_path):
                return os.path.getmtime(rgb_db_path)
            return 0
        except Exception:
            return 0

    def _get_usb_rgb_db_mtime(self, zip_path: str) -> float:
        """
        Get the mtime of <masterfingerprint>/rgb_lib_db inside the USB zip.
        Returns:
            float: mtime (as epoch) or 0 if not found.
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                for info in zip_file.infolist():
                    if info.filename == f'{self.master_fingerprint}/rgb_lib_db':
                        # Convert zip date_time (Y, M, D, H, M, S) to epoch
                        dt = datetime.datetime(*info.date_time)
                        return dt.timestamp()
            return 0
        except Exception:
            return 0

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
        Determine sync direction based on validated ini and rgb_lib_db mtimes.
        Returns:
            Optional[str]: 'to_usb', 'from_usb', or None if no sync needed.
        """
        direction = None
        try:
            if not self.selected_drive:
                return None  # critical exit, no drive selected

            usb_files = [
                f for f in os.listdir(self.selected_drive.path)
                if f.startswith(self.master_fingerprint)
                and f.endswith('.zip')
                and not f.endswith('_temp.zip')
            ]

            if not usb_files:
                direction = 'to_usb'
            else:
                usb_files.sort(reverse=True)
                latest_zip = os.path.join(
                    self.selected_drive.path, usb_files[0],
                )
                ini_content = self._validate_usb_zip_and_get_ini(latest_zip)
                if not ini_content:
                    logger.error('USB zip validation failed, aborting sync')
                    direction = None
                else:
                    local_mtime = self._get_local_rgb_db_mtime()
                    usb_mtime = self._get_usb_rgb_db_mtime(latest_zip)
                    if usb_mtime == 0 and local_mtime == 0:
                        direction = None
                    elif local_mtime > usb_mtime:
                        direction = 'to_usb'
                    elif usb_mtime > local_mtime:
                        direction = 'from_usb'
                    else:
                        direction = None
        except Exception as exc:
            logger.error('Error determining sync direction: %s', str(exc))
            direction = 'to_usb'  # default on error

        return direction

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
        Sync wallet data to USB drive.
        """
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            wallet_data = self._create_wallet_data_package()

            # Find all zips for this master fingerprint (excluding _temp)
            fingerprint_zips = [
                f for f in os.listdir(self.selected_drive.path)
                if f.startswith(self.master_fingerprint) and f.endswith('.zip') and not f.endswith('_temp.zip')
            ]
            # newest first by name (timestamp in name)
            fingerprint_zips.sort(reverse=True)
            temp_zips = [
                f for f in os.listdir(self.selected_drive.path)
                if f.startswith(self.master_fingerprint) and f.endswith('_temp.zip')
            ]

            # If both a normal zip and a _temp.zip exist, delete the _temp.zip
            if fingerprint_zips and temp_zips:
                for temp_zip in temp_zips:
                    try:
                        os.remove(
                            os.path.join(
                                self.selected_drive.path, temp_zip,
                            ),
                        )
                        logger.info(
                            'Removed old temp wallet zip: %s', temp_zip,
                        )
                    except Exception as exc:
                        logger.error(
                            'Failed to remove old temp wallet zip %s: %s',
                            temp_zip, exc,
                        )

            # If a normal zip exists, rename the latest one to _temp.zip (keep it)
            if fingerprint_zips:
                latest_zip = fingerprint_zips[0]
                latest_zip_path = os.path.join(
                    self.selected_drive.path, latest_zip,
                )
                temp_zip_path = os.path.join(
                    self.selected_drive.path, latest_zip.replace(
                        '.zip', '_temp.zip',
                    ),
                )
                if not os.path.exists(temp_zip_path):
                    os.rename(latest_zip_path, temp_zip_path)
                    logger.info(
                        'Renamed %s to %s as backup',
                        latest_zip, os.path.basename(temp_zip_path),
                    )

            # Write the new zip
            filename = f'{self.master_fingerprint}_{timestamp}.zip'
            usb_file_path = os.path.join(self.selected_drive.path, filename)
            with open(usb_file_path, 'wb') as f:
                f.write(wallet_data)
            logger.info(
                'Successfully synced wallet data to USB: %s', usb_file_path,
            )
            self._show_sync_success(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_success',
                ),
            )

            # After writing, ensure only two zips for this fingerprint: latest and temp
            all_fingerprint_zips = [
                f for f in os.listdir(self.selected_drive.path)
                if f.startswith(self.master_fingerprint) and (f.endswith('.zip') or f.endswith('_temp.zip'))
            ]
            # Separate temp and normal zips
            temp_zips = [
                f for f in all_fingerprint_zips if f.endswith('_temp.zip')
            ]
            normal_zips = [
                f for f in all_fingerprint_zips if f.endswith(
                    '.zip',
                ) and not f.endswith('_temp.zip')
            ]
            # Sort normal zips by name (timestamp)
            normal_zips.sort(reverse=True)
            # If more than 1 normal zip (should only be the latest), delete the oldest
            if len(normal_zips) > 1:
                for old_zip in normal_zips[1:]:
                    try:
                        os.remove(
                            os.path.join(
                                self.selected_drive.path, old_zip,
                            ),
                        )
                        logger.info('Removed old wallet zip: %s', old_zip)
                    except Exception as exc:
                        logger.error(
                            'Failed to remove old wallet zip %s: %s',
                            old_zip, exc,
                        )
            # If more than 1 temp zip, delete all but the latest
            if len(temp_zips) > 1:
                temp_zips.sort(reverse=True)
                for old_temp in temp_zips[1:]:
                    try:
                        os.remove(
                            os.path.join(
                                self.selected_drive.path, old_temp,
                            ),
                        )
                        logger.info(
                            'Removed extra temp wallet zip: %s', old_temp,
                        )
                    except Exception as exc:
                        logger.error(
                            'Failed to remove extra temp wallet zip %s: %s',
                            old_temp, exc,
                        )
        except Exception as exc:
            logger.error('Sync to USB failed: %s', str(exc))
            raise exc

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

            # Find existing temp backups for this master fingerprint
            temp_backups = []
            for file in os.listdir(self._get_wallet_data_path()):
                if file.startswith(self.master_fingerprint) and file.endswith('_temp.zip'):
                    temp_backups.append(file)

            # Remove old temp backups (keep only the latest one)
            if temp_backups:
                temp_backups.sort(reverse=True)  # Sort by name (timestamp)
                # Keep only the latest, remove others
                for old_temp in temp_backups[1:]:
                    try:
                        old_temp_path = os.path.join(
                            self._get_wallet_data_path(), old_temp,
                        )
                        os.remove(old_temp_path)
                        logger.info(
                            'Removed old local temp backup: %s', old_temp,
                        )
                    except Exception as exc:
                        logger.error(
                            'Failed to remove old local temp backup %s: %s',
                            old_temp, exc,
                        )

            # Create new temp backup
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self._get_wallet_data_path(), f'{self.master_fingerprint}_{
                    timestamp
                }_temp.zip',
            )

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
        Sync wallet data from USB drive.
        Args:
        """
        try:
            usb_files = []
            for file in os.listdir(self.selected_drive.path):
                if file.startswith(self.master_fingerprint) and file.endswith('.zip') and not file.endswith('_temp.zip'):
                    usb_files.append(file)
            if not usb_files:
                raise CommonException(
                    QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_no_wallet_files').format(
                        fingerprint=self.master_fingerprint,
                    ),
                )
            usb_files.sort(reverse=True)
            latest_file = usb_files[0]
            usb_file_path = os.path.join(self.selected_drive.path, latest_file)
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
                self._restore_wallet_data(wallet_data, only_folder=True)
                logger.info(
                    'Successfully synced wallet data from USB: %s', usb_file_path,
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


def create_usb_sync_manager(main_window) -> USBSyncManager:
    """
    Create and return a USB sync manager instance.

    Args:
        main_window: The main window instance.

    Returns:
        USBSyncManager: The USB sync manager instance.
    """
    return USBSyncManager(main_window)
