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
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletType, WalletSecurityType

from src.utils.build_app_path import app_paths
from src.utils.constant import CURRENT_RGB_LIB_VERSION
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.custom_exception import CommonException
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
        self.dialog_shown = False  # Track if dialog has been shown for current session

    def reset_dialog_flag(self):
        """
        Reset the dialog shown flag to allow showing dialog again.
        This can be called manually if needed, but the flag is automatically
        reset when navigating away from the fungible page.
        """
        self.dialog_shown = False
        logger.debug('Dialog flag reset manually')

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
            logger.error('Error checking USB sync enabled status: %s', str(exc))
            return False

    def check_usb_and_prompt(self):
        """
        Check for USB drives and prompt user for sync if detected.
        Only works for offline wallets and watch-only wallets.
        Only shows dialog when on the fungible page.
        """
        try:
            print(1)
            # Check if USB sync is enabled for current wallet mode
            if not self._is_usb_sync_enabled():
                return
                
            if self.sync_in_progress:
                return

            # # Check if current page is fungible page
            # if not self._is_on_fungible_page():
            #     return

            # Check if USB is connected
            is_usb_connected = self.usb_detector.is_usb_connected()
            
            # Return early if no USB connected
            if not is_usb_connected:
                logger.debug('No USB drives detected')
                return

            # Get list of USB drives
            usb_drives = self.usb_detector.detect_usb_drives()
            
            if not usb_drives:
                logger.debug('No accessible USB drives found')
                return

            # Only show dialog if not already shown for this session
            if not self.dialog_shown:
                self.show_usb_sync_dialog()
                self.dialog_shown = True  # Mark dialog as shown

        except Exception as exc:
            logger.error('Error checking USB drives: %s', str(exc))
            # Don't show error to user for USB detection failures

    def _is_on_fungible_page(self) -> bool:
        """
        Check if the current page is the fungible page.
        Also resets dialog flag when not on fungible page.
        
        Returns:
            bool: True if on fungible page, False otherwise.
        """
        try:
            # Import here to avoid circular imports
            from src.main import PAGE_NAVIGATION
            
            if not hasattr(PAGE_NAVIGATION, 'current_stack') or not PAGE_NAVIGATION.current_stack:
                # Reset dialog flag when no current stack
                if self.dialog_shown:
                    self.dialog_shown = False
                    logger.debug('Dialog flag reset - no current stack')
                return False
                
            current_page_name = PAGE_NAVIGATION.current_stack.get('name', '')
            is_on_fungible = current_page_name == 'FungibleAssetWidget'
            
            # Reset dialog flag when not on fungible page
            if not is_on_fungible and self.dialog_shown:
                self.dialog_shown = False
                logger.debug('Dialog flag reset - navigated away from fungible page')
                
            return is_on_fungible
        except Exception as exc:
            logger.error('Error checking current page: %s', str(exc))
            return False

    def show_usb_sync_dialog(self):
        """
        Show USB sync dialog to user.

        Args:
            usb_drives: List of detected USB drives.
        """
        try:
            usb_drives = self.usb_detector.detect_usb_drives()

            dialog = USBSyncDialog(usb_drives, self.main_window)
            if dialog.exec() == QDialog.Accepted:
                selected_drive = dialog.get_selected_drive()
                if selected_drive:
                    self._perform_sync(selected_drive)
        except Exception as exc:
            logger.error('Error showing USB sync dialog: %s', str(exc))

    def _perform_sync(self, usb_drive: USBDrive):
        """
        Perform the actual sync operation.

        Args:
            usb_drive: The selected USB drive to sync with.
        """
        try:
            self.sync_in_progress = True

            # Validate USB drive
            if not self._validate_usb_drive(usb_drive):
                return

            # Determine sync direction based on timestamps
            sync_direction = self._determine_sync_direction(usb_drive)

            if sync_direction == 'to_usb':
                self._sync_to_usb(usb_drive)
            elif sync_direction == 'from_usb':
                self._sync_from_usb(usb_drive)
            else:
                logger.info('No sync needed - data is up to date')

        except Exception as exc:
            logger.error('USB sync failed: %s', str(exc))
            self._show_sync_error(str(exc))
        finally:
            self.sync_in_progress = False

    def _validate_usb_drive(self, usb_drive: USBDrive) -> bool:
        """
        Validate the USB drive for sync.

        Args:
            usb_drive: The USB drive to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Get master fingerprint
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                self._show_sync_error(
                    'Master fingerprint not found. Please ensure wallet is properly initialized.',
                )
                return False

            # Check if USB is empty (valid for new sync)
            if usb_drive.is_empty:
                return True

            # If USB is not empty, check if it contains valid wallet data for this fingerprint
            if not self._has_valid_wallet_data(usb_drive.path, master_fingerprint):
                self._show_sync_error(
                    'USB drive contains data but not valid wallet data for this wallet. Please format the USB drive or use a different one.',
                )
                return False

            return True
        except Exception as exc:
            logger.error('USB drive validation failed: %s', str(exc))
            return False

    def _has_valid_wallet_data(self, usb_path: str, master_fingerprint: str) -> bool:
        """
        Check if USB contains valid wallet data for the given master fingerprint.

        Args:
            usb_path: Path to USB drive.
            master_fingerprint: Master fingerprint to check for.

        Returns:
            bool: True if valid wallet data found, False otherwise.
        """
        try:
            # Look for ZIP files with the same master fingerprint
            for file in os.listdir(usb_path):
                if file.startswith(master_fingerprint) and file.endswith('.zip'):
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
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                return 0
            rgb_db_path = os.path.join(
                self._get_wallet_data_path(), master_fingerprint, 'rgb_lib_db',
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
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                return 0
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                for info in zip_file.infolist():
                    if info.filename == f'{master_fingerprint}/rgb_lib_db':
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
            master_fingerprint = self._get_master_fingerprint()
            local_ini_path = self._get_ini_file_path()
            local_xpub = None
            if os.path.exists(local_ini_path):
                with open(local_ini_path) as f:
                    local_ini = f.read()
                # Find xpub in local ini (as string)
                for line in local_ini.splitlines():
                    if 'xpub' in line:
                        local_xpub = line.strip()
                        break
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                ini_file = [
                    f for f in zip_file.namelist()
                    if f.endswith('.ini')
                ]
                if not ini_file:
                    logger.error('No INI file found in USB zip')
                    return None
                ini_content = zip_file.read(ini_file[0]).decode('utf-8')
                # Check RGB lib version
                if 'rgb_lib_version' not in ini_content:
                    logger.error('RGB lib version not found in USB INI')
                    return None
                # Check master fingerprint
                if master_fingerprint not in ini_content:
                    logger.error('Master fingerprint not found in USB INI')
                    return None
                # Check xpub
                usb_xpub = None
                for line in ini_content.splitlines():
                    if 'xpub' in line:
                        usb_xpub = line.strip()
                        break
                if not local_xpub or not usb_xpub or local_xpub != usb_xpub:
                    logger.error(
                        'xpub mismatch or not found (local: %s, usb: %s)', local_xpub, usb_xpub,
                    )
                    return None
                return ini_content
        except Exception as exc:
            logger.error('USB zip validation failed: %s', str(exc))
            return None

    def _determine_sync_direction(self, usb_drive: USBDrive) -> str | None:
        """
        Determine sync direction based on validated ini and rgb_lib_db mtimes.
        Returns:
            Optional[str]: 'to_usb', 'from_usb', or None if no sync needed.
        """
        try:
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                return None
            # Find latest zip for master fingerprint
            usb_files = [
                f for f in os.listdir(usb_drive.path) if f.startswith(
                    master_fingerprint,
                ) and f.endswith('.zip') and not f.endswith('_temp.zip')
            ]
            if not usb_files:
                return 'to_usb'
            usb_files.sort(reverse=True)
            latest_zip = os.path.join(usb_drive.path, usb_files[0])
            # Validate USB zip and ini
            ini_content = self._validate_usb_zip_and_get_ini(latest_zip)
            if not ini_content:
                logger.error('USB zip validation failed, aborting sync')
                return None
            # Get mtimes
            local_mtime = self._get_local_rgb_db_mtime()
            usb_mtime = self._get_usb_rgb_db_mtime(latest_zip)
            if usb_mtime == 0 and local_mtime == 0:
                return None
            if local_mtime > usb_mtime:
                return 'to_usb'
            elif usb_mtime > local_mtime:
                return 'from_usb'
            else:
                return None
        except Exception as exc:
            logger.error('Error determining sync direction: %s', str(exc))
            return 'to_usb'  # Default to sync to USB

    def _get_local_wallet_timestamp(self) -> float:
        """
        Get local wallet data timestamp (for the master fingerprint folder).
        Returns:
            float: Timestamp of local wallet data.
        """
        try:
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                return time.time()
            folder_path = os.path.join(
                self._get_wallet_data_path(), master_fingerprint,
            )
            if os.path.exists(folder_path):
                return os.path.getmtime(folder_path)
            return time.time()
        except Exception:
            return time.time()

    def _get_usb_wallet_timestamp(self, usb_path: str) -> float | None:
        """
        Get USB wallet data timestamp.

        Args:
            usb_path: Path to USB drive.

        Returns:
            Optional[float]: Timestamp of USB wallet data or None if not found.
        """
        try:
            # Get master fingerprint
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                return None

            # Look for the latest ZIP file with matching master fingerprint
            usb_files = []
            for file in os.listdir(usb_path):
                if file.startswith(master_fingerprint) and file.endswith('.zip') and not file.endswith('_temp.zip'):
                    usb_files.append(file)

            if not usb_files:
                return None

            # Sort by timestamp (newest first) and get the latest
            usb_files.sort(reverse=True)
            latest_file = usb_files[0]
            wallet_file = os.path.join(usb_path, latest_file)

            if os.path.exists(wallet_file):
                return os.path.getmtime(wallet_file)
            return None
        except Exception:
            return None

    def _sync_to_usb(self, usb_drive: USBDrive):
        """
        Sync wallet data to USB drive.

        Args:
            usb_drive: The USB drive to sync to.
        """
        try:
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                raise CommonException('Master fingerprint not found')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            wallet_data = self._create_wallet_data_package()

            # Find all zips for this master fingerprint (excluding _temp)
            fingerprint_zips = [
                f for f in os.listdir(usb_drive.path)
                if f.startswith(master_fingerprint) and f.endswith('.zip') and not f.endswith('_temp.zip')
            ]
            # newest first by name (timestamp in name)
            fingerprint_zips.sort(reverse=True)
            temp_zips = [
                f for f in os.listdir(usb_drive.path)
                if f.startswith(master_fingerprint) and f.endswith('_temp.zip')
            ]

            # If both a normal zip and a _temp.zip exist, delete the _temp.zip
            if fingerprint_zips and temp_zips:
                for temp_zip in temp_zips:
                    try:
                        os.remove(os.path.join(usb_drive.path, temp_zip))
                        logger.info(f'Removed old temp wallet zip: {temp_zip}')
                    except Exception as exc:
                        logger.error(f'Failed to remove old temp wallet zip {
                                     temp_zip
                                     }: {exc}')

            # If a normal zip exists, rename the latest one to _temp.zip (keep it)
            if fingerprint_zips:
                latest_zip = fingerprint_zips[0]
                latest_zip_path = os.path.join(usb_drive.path, latest_zip)
                temp_zip_path = os.path.join(
                    usb_drive.path, latest_zip.replace('.zip', '_temp.zip'),
                )
                if not os.path.exists(temp_zip_path):
                    os.rename(latest_zip_path, temp_zip_path)
                    logger.info(f'Renamed {latest_zip} to {
                                os.path.basename(temp_zip_path)
                                } as backup')

            # Write the new zip
            filename = f'{master_fingerprint}_{timestamp}.zip'
            usb_file_path = os.path.join(usb_drive.path, filename)
            with open(usb_file_path, 'wb') as f:
                f.write(wallet_data)
            logger.info(
                'Successfully synced wallet data to USB: %s', usb_file_path,
            )
            self._show_sync_success('Wallet data synced to USB successfully')

            # After writing, ensure only two zips for this fingerprint: latest and temp
            all_fingerprint_zips = [
                f for f in os.listdir(usb_drive.path)
                if f.startswith(master_fingerprint) and (f.endswith('.zip') or f.endswith('_temp.zip'))
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
                        os.remove(os.path.join(usb_drive.path, old_zip))
                        logger.info(f'Removed old wallet zip: {old_zip}')
                    except Exception as exc:
                        logger.error(f'Failed to remove old wallet zip {
                                     old_zip
                                     }: {exc}')
            # If more than 1 temp zip, delete all but the latest
            if len(temp_zips) > 1:
                temp_zips.sort(reverse=True)
                for old_temp in temp_zips[1:]:
                    try:
                        os.remove(os.path.join(usb_drive.path, old_temp))
                        logger.info(
                            f'Removed extra temp wallet zip: {old_temp}',
                        )
                    except Exception as exc:
                        logger.error(f'Failed to remove extra temp wallet zip {
                                     old_temp
                                     }: {exc}')
        except Exception as exc:
            logger.error('Sync to USB failed: %s', str(exc))
            raise exc

    def _create_local_temp_backup(self) -> str | None:
        """
        Create a temp backup of the local master fingerprint folder as a zip in the app data path.
        Returns:
            Optional[str]: Path to backup file or None if failed.
        """
        try:
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                raise CommonException('Master fingerprint not found')
            folder_path = os.path.join(
                self._get_wallet_data_path(), master_fingerprint,
            )
            if not os.path.exists(folder_path):
                logger.warning('No local folder to backup: %s', folder_path)
                return None
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self._get_wallet_data_path(), f'{
                    master_fingerprint
                }_{timestamp}_temp.zip',
            )
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    rel_dir = os.path.relpath(root, folder_path)
                    if rel_dir == '.':
                        rel_dir = ''
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.join(master_fingerprint, rel_dir, file) if rel_dir else os.path.join(
                            master_fingerprint, file,
                        )
                        zip_file.write(file_path, rel_path)
            logger.info('Created local temp backup: %s', backup_path)
            return backup_path
        except Exception as exc:
            logger.error('Failed to create local temp backup: %s', str(exc))
            return None

    def _sync_from_usb(self, usb_drive: USBDrive):
        """
        Sync wallet data from USB drive.
        Args:
            usb_drive: The USB drive to sync from.
        """
        try:
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                raise CommonException('Master fingerprint not found')
            usb_files = []
            for file in os.listdir(usb_drive.path):
                if file.startswith(master_fingerprint) and file.endswith('.zip') and not file.endswith('_temp.zip'):
                    usb_files.append(file)
            if not usb_files:
                raise CommonException(f'No wallet data files found for master fingerprint: {
                                      master_fingerprint
                                      }')
            usb_files.sort(reverse=True)
            latest_file = usb_files[0]
            usb_file_path = os.path.join(usb_drive.path, latest_file)
            # Create temp backup of local folder before restoring
            backup_path = self._create_local_temp_backup()
            try:
                with open(usb_file_path, 'rb') as f:
                    wallet_data = f.read()
                if not self._validate_wallet_data(wallet_data):
                    raise CommonException('Invalid wallet data on USB drive')
                self._restore_wallet_data(wallet_data, only_folder=True)
                logger.info(
                    'Successfully synced wallet data from USB: %s', usb_file_path,
                )
                self._show_sync_success(
                    'Wallet data synced from USB successfully',
                )
            except Exception as exc:
                if backup_path and os.path.exists(backup_path):
                    self._restore_local_folder_from_backup(
                        backup_path, master_fingerprint,
                    )
                raise exc
            finally:
                if backup_path and os.path.exists(backup_path):
                    logger.info('Local temp backup kept at: %s', backup_path)
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
            master_fingerprint = self._get_master_fingerprint()
            # Remove the existing folder before restoring
            folder_path = os.path.join(wallet_data_path, master_fingerprint)
            if only_folder and os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            with zipfile.ZipFile(io.BytesIO(wallet_data), 'r') as zip_file:
                if only_folder:
                    # Only extract the master fingerprint folder
                    folder_prefix = master_fingerprint + '/'
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
                        master_fingerprint,
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

    def _restore_local_folder_from_backup(self, backup_path: str, master_fingerprint: str):
        """
        Restore the local master fingerprint folder from a backup zip.
        """
        try:
            wallet_data_path = self._get_wallet_data_path()
            folder_path = os.path.join(wallet_data_path, master_fingerprint)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                for member in zip_file.namelist():
                    if member.startswith(master_fingerprint + '/') and not member.endswith('/'):
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
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                logger.warning(
                    'Master fingerprint not found, using original structure',
                )
                master_fingerprint = os.path.basename(wallet_data_folder)

            # Always add the root folder entry (even if empty)
            zip_root = master_fingerprint + '/'
            zip_file.writestr(zip_root, '')

            # Walk through the wallet data folder
            for root, dirs, files in os.walk(wallet_data_folder):
                # Skip logs and cache directories
                dirs[:] = [d for d in dirs if d not in ['logs', 'cache']]
                # Add directory entry for each subdirectory
                rel_dir = os.path.relpath(root, wallet_data_folder)
                if rel_dir != '.':
                    zip_dir = os.path.join(master_fingerprint, rel_dir) + '/'
                    zip_file.writestr(zip_dir, '')
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path from wallet data folder
                    rel_path = os.path.relpath(file_path, wallet_data_folder)
                    # Create path with master fingerprint folder name
                    zip_path = os.path.join(master_fingerprint, rel_path)
                    zip_file.write(file_path, zip_path)
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
            # Get master fingerprint
            master_fingerprint = self._get_master_fingerprint()
            if not master_fingerprint:
                logger.warning('Master fingerprint not found, using base path')
                return wallet_path

            # Look for folder with name matching master fingerprint
            fingerprint_folder = os.path.join(wallet_path, master_fingerprint)
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
