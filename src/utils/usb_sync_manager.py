"""
USB sync manager for handling wallet data synchronization with USB drives.

Provides functionality to sync wallet data to/from USB drives with validation,
backup, and error handling.
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

from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletType
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import COMPATIBLE_RGB_LIB_VERSION
from src.utils.constant import EPOCH_TIME
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import LAST_SYNC_DIRECTION
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import SYNC_INDEX
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_RGB_LIB_INCOMPATIBILITY
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.usb_detector import USBDetector
from src.utils.usb_detector import USBDrive


class USBSyncManager:
    """Manages USB synchronization for wallet data."""

    def __init__(self):
        """Initialize USB sync manager state and dependencies."""
        self.usb_detector = USBDetector()
        self.sync_in_progress = False
        self.dialog_shown = False
        self.master_fingerprint: str = None
        self.selected_drive: USBDrive = None
        self.temp_local_wallet_data = None

    def reset_dialog_flag(self):
        """Reset the internal dialog visibility flag."""
        self.dialog_shown = False

    def perform_sync(self, selected_drive: USBDrive):
        """Perform sync to or from the given USB drive and return the direction."""
        try:
            self.selected_drive = selected_drive
            self.reset_dialog_flag()
            self.master_fingerprint = local_store.get_value(MASTER_FINGERPRINT)
            self.sync_in_progress = True
            if not self.master_fingerprint:
                return None
            if not self._validate_usb_drive():
                raise CommonException(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT,
                        'usb_invalid_wallet_data',
                    ),
                )

            direction = self._determine_sync_direction()
            if direction == 'to_usb':
                self.sync_to_usb()
                return 'to_usb'
            if direction == 'from_usb':
                self.sync_from_usb()
                return 'from_usb'
            return 'no_sync'
        except Exception as exc:
            logger.error('USB sync failed: %s', exc)
            raise exc
        finally:
            self.sync_in_progress = False

    def _validate_usb_drive(self) -> bool:
        """Validate the selected USB drive for wallet sync operations."""
        try:
            if self.selected_drive and self.selected_drive.is_empty:
                return True
            if not self._has_valid_wallet_data():
                return False
            return True
        except Exception as exc:
            logger.error('USB drive validation failed: %s', exc)
            return False

    def _has_valid_wallet_data(self) -> bool:
        """Check if the selected USB contains a wallet ZIP for the fingerprint."""
        try:
            if not self.selected_drive:
                return False
            return any(
                f.startswith(self.master_fingerprint) and f.endswith('.zip')
                for f in os.listdir(self.selected_drive.path)
            )
        except Exception:
            return False

    def _determine_sync_direction(self) -> str | None:
        """Decide whether to sync to USB, from USB, or do nothing."""
        try:
            if not self.selected_drive:
                return None
            if not self._check_usb_ini_exists():
                logger.info('No wallet data on USB - creating initial backup')
                return 'to_usb'
            return self._determine_sync_direction_with_counter()
        except Exception as exc:
            logger.error('Error determining sync direction: %s', exc)
            return None

    def _check_usb_ini_exists(self) -> bool:
        """Return True if the USB wallet ZIP contains an INI file."""
        try:
            if not self.selected_drive:
                return False
            path = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            if not os.path.exists(path):
                return False
            with zipfile.ZipFile(path, 'r') as z:
                return any(f.endswith('.ini') for f in z.namelist())
        except Exception as exc:
            logger.error('Error checking USB INI existence: %s', exc)
            return False

    def _determine_sync_direction_with_counter(self) -> str | None:
        """Resolve sync direction using sync_index values and checksum comparison."""
        try:
            usb_index = self._get_usb_index()
            local_index = local_store.get_value(SYNC_INDEX)
            if local_index is None:
                local_index = 0
            else:
                local_index = int(local_index)

            usb_checksum = self._calculate_usb_wallet_checksum()
            local_checksum = self._calculate_wallet_checksum()

            # Case 1: USB index ahead
            if usb_index > local_index:
                return None if usb_checksum == local_checksum else 'from_usb'

            # Case 2: Local index ahead
            if local_index > usb_index:
                return None if usb_checksum == local_checksum else 'to_usb'

            # Case 3: Index same but checksum mismatch
            if usb_index == local_index and usb_checksum != local_checksum:
                last_dir = local_store.get_value(LAST_SYNC_DIRECTION)
                if last_dir:
                    return 'to_usb' if last_dir == 'wallet_to_usb' else 'from_usb'

            return None

        except Exception as exc:
            logger.error(
                'Error determining sync direction with counter: %s', exc,
            )
            return None

    def _get_usb_index(self) -> int:
        """Read sync_index from the INI stored inside the USB ZIP."""
        try:
            zip_path = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            if not os.path.exists(zip_path):
                return 0
            with zipfile.ZipFile(zip_path, 'r') as z:
                ini_name = None
                for name in z.namelist():
                    if name.endswith('.ini'):
                        ini_name = name
                        break
                if not ini_name:
                    return 0
                ini_content = z.read(ini_name).decode()
                for line in ini_content.splitlines():
                    if line.startswith('sync_index='):
                        try:
                            return int(line.split('=', 1)[1].strip() or 0)
                        except ValueError:
                            return 0
            return 0
        except Exception as exc:
            logger.error('Error getting USB index: %s', exc)
            return 0

    def _update_usb_ini_index(self, new_index: int):
        """Update sync_index in the USB ZIP INI by rewriting the archive."""
        try:
            if not self.selected_drive:
                return
            zip_path = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            if not os.path.exists(zip_path):
                logger.warning(
                    'USB ZIP not found to update index: %s', zip_path,
                )
                return

            temp_zip = zip_path + '.updating'
            with zipfile.ZipFile(zip_path, 'r') as zin, zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
                ini_found = False
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename.endswith('.ini'):
                        ini_found = True
                        try:
                            text = data.decode('utf-8')
                        except Exception:
                            text = ''
                        lines = text.splitlines()
                        for i, line in enumerate(lines):
                            if line.startswith('sync_index='):
                                lines[i] = f"sync_index={new_index}"
                                break
                        else:
                            lines.append(f"sync_index={new_index}")
                        data = ('\n'.join(lines)).encode('utf-8')
                    zout.writestr(item, data)

                # Edge: if INI wasn't present at all, create a minimal one at root
                if not ini_found:
                    zout.writestr('wallet.ini', f"sync_index={new_index}\n")

            # Replace original
            os.replace(temp_zip, zip_path)
            logger.info('Updated USB INI index to %s', new_index)
        except Exception as exc:
            logger.error('Error updating USB ini index: %s', exc)

    def sync_to_usb(self):
        """Package local wallet data and write/update it on the USB drive."""
        try:
            try:
                wallet_service = None
                if SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET:
                    wallet_service = WalletDataService.get_session()
                    if wallet_service is not None:
                        wallet_service.refresh_wallet_data()
            except Exception as exc:
                logger.warning(
                    'Failed refreshing wallet-data before USB sync: %s', exc,
                )
            current_local_index = local_store.get_value(SYNC_INDEX)
            if current_local_index is None:  # initial backup
                logger.info('Creating initial USB backup')
                local_store.set_value(SYNC_INDEX, 0)
                data = self._create_wallet_data_package_with_index(0)

                usb_file = os.path.join(
                    self.selected_drive.path, f"{
                        self.master_fingerprint
                    }.zip",
                )
                self._create_usb_temp_file()
                with open(usb_file, 'wb') as f:
                    f.write(data)

                local_store.set_value(SYNC_INDEX, 1)
                self._update_usb_ini_index(1)
                self._cleanup_extra_usb_temp_backups()

                local_store.set_value(LAST_SYNC_DIRECTION, 'wallet_to_usb')
            else:
                logger.info('Regular sync: wallet newer than USB')
                try:
                    new_index = int(current_local_index) + 1
                    data = self._create_wallet_data_package_with_index(
                        new_index,
                    )

                    # Validate the package before writing to USB
                    if not self._validate_wallet_data(data):
                        if SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD:
                            local_store.clear_settings()
                            local_store.remove_file(
                                MNEMONIC_KEY, app_paths.mnemonic_file_path,
                            )
                        raise CommonException(
                            QCoreApplication.translate(
                                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_invalid_data',
                            ),
                        )

                    usb_file = os.path.join(
                        self.selected_drive.path, f"{
                            self.master_fingerprint
                        }.zip",
                    )
                    self._create_usb_temp_file()
                    with open(usb_file, 'wb') as f:
                        f.write(data)

                    local_store.set_value(SYNC_INDEX, new_index)

                    local_store.set_value(LAST_SYNC_DIRECTION, 'wallet_to_usb')
                except Exception as exc:
                    self._restore_usb_wallet_from_backup()
                    logger.error(
                        'USB sync failed, local index stays %s', current_local_index,
                    )
                    raise exc
                finally:
                    self._cleanup_extra_usb_temp_backups()
        except Exception as exc:
            logger.error('Sync to USB failed: %s', exc)
            raise exc

    def sync_from_usb(self, usb_drive=None, master_fingerprint=None, is_load: bool = False):
        """Restore local wallet state from the selected USB drive wallet ZIP."""
        try:
            if usb_drive and master_fingerprint:
                self.selected_drive = usb_drive
                self.master_fingerprint = master_fingerprint
            usb_index = self._get_usb_index()
            if usb_index == 0:
                raise CommonException(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT,
                        'usb_no_wallet_files',
                    ).format(fingerprint=self.master_fingerprint),
                )

            usb_file = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            if not os.path.exists(usb_file):
                raise CommonException(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT,
                        'usb_no_wallet_files',
                    ).format(fingerprint=self.master_fingerprint),
                )

            self.temp_local_wallet_data = self._create_local_temp_backup()
            try:
                with open(usb_file, 'rb') as f:
                    data = f.read()
                if not self._validate_wallet_data(data):
                    raise CommonException(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_invalid_data',
                        ),
                    )

                self._restore_wallet_data(data, only_folder=True)
                if is_load:
                    local_store.set_value(SYNC_INDEX, usb_index)
                else:
                    local_store.set_value(SYNC_INDEX, usb_index+1)
                local_store.set_value(LAST_SYNC_DIRECTION, 'usb_to_wallet')

                # --- NEW: extract epoch_time from USB ini ---
                with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
                    ini_files = [f for f in z.namelist() if f.endswith('.ini')]
                    if ini_files:
                        ini = z.read(ini_files[0]).decode('utf-8')
                        for line in ini.splitlines():
                            if line.startswith('epoch_time='):
                                epoch_time = line.split('=', 1)[1].strip()
                                local_store.set_value(EPOCH_TIME, epoch_time)
                                break

                logger.info(
                    'Restored from USB (usb_index=%s → local=%s)', usb_index, usb_index,
                )

            except Exception as exc:
                if self.temp_local_wallet_data and os.path.exists(self.temp_local_wallet_data):
                    self.restore_local_folder_from_backup()
                raise exc
        except Exception as exc:
            logger.error('Sync from USB failed: %s', exc)
            raise

    def _create_usb_temp_file(self):
        """Rotate current USB wallet ZIP into a temp backup file."""
        try:
            if not self.selected_drive:
                return
            base = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            temp = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }_temp.zip",
            )
            if os.path.exists(temp):
                os.remove(temp)
            if os.path.exists(base):
                os.rename(base, temp)
        except Exception as exc:
            logger.error('USB rotation failed: %s', exc)

    def _cleanup_extra_usb_temp_backups(self):
        """Remove extra USB temp backups keeping only the latest one."""
        try:
            if not self.selected_drive:
                return
            keep = f"{self.master_fingerprint}_temp.zip"
            for f in os.listdir(self.selected_drive.path):
                if f.startswith(self.master_fingerprint) and f.endswith('_temp.zip') and f != keep:
                    os.remove(os.path.join(self.selected_drive.path, f))
        except Exception as exc:
            logger.error('USB temp cleanup failed: %s', exc)

    def _create_local_temp_backup(self) -> str | None:
        """Create a ZIP backup of the current local wallet folder."""
        try:
            folder = os.path.join(
                app_paths.app_path, self.master_fingerprint,
            )
            if not os.path.exists(folder):
                return None
            temp = os.path.join(
                app_paths.app_path, f"{
                    self.master_fingerprint
                }_temp.zip",
            )
            if os.path.exists(temp):
                os.remove(temp)
            with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, _, files in os.walk(folder):
                    for f in files:
                        path = os.path.join(root, f)
                        rel = os.path.join(
                            self.master_fingerprint, os.path.relpath(
                                path, folder,
                            ),
                        )
                        z.write(path, rel)
            return temp
        except Exception as exc:
            logger.error('Failed to create local temp backup: %s', exc)
            return None

    def _restore_wallet_data(self, data: bytes, only_folder: bool = False):
        """Restore wallet data from ZIP; if only_folder, restore wallet folders + wallet_data only."""
        try:
            with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
                if only_folder:
                    wallet_data_prefix = 'wallet-data/'

                    for m in z.namelist():
                        # top-level directory name
                        top = m.split('/', 1)[0]

                        # skip empty entries
                        if not top:
                            continue

                        # exclude logs and cache everywhere
                        if top in ('logs', 'cache'):
                            continue

                        # allow wallet folders and wallet-data
                        if top != 'wallet-data' and not m.startswith(top + '/'):
                            continue

                        target = os.path.join(app_paths.app_path, m)

                        if m.endswith('/'):
                            os.makedirs(target, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            with open(target, 'wb') as f:
                                f.write(z.read(m))
                else:
                    z.extractall(app_paths.app_path)

        except Exception as exc:
            logger.error('Failed to restore wallet data: %s', exc)
            raise

    def restore_local_folder_from_backup(self):
        """Restore the local wallet folder from the temporary backup ZIP."""
        try:
            folder = os.path.join(app_paths.app_path, self.master_fingerprint)
            if os.path.exists(folder):
                shutil.rmtree(folder)
            with zipfile.ZipFile(self.temp_local_wallet_data, 'r') as z:
                z.extractall(app_paths.app_path)
        except Exception as exc:
            logger.error('Failed to restore from backup: %s', exc)

    def _restore_usb_wallet_from_backup(self):
        """Restore the previous USB wallet file from the temp backup, if available."""
        try:
            if not self.selected_drive:
                return
            usb_file = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            usb_temp = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }_temp.zip",
            )

            if os.path.exists(usb_temp):
                if os.path.exists(usb_file):
                    os.remove(usb_file)
                os.rename(usb_temp, usb_file)
                logger.info('Rolled back USB wallet to previous version')
        except Exception as exc:
            logger.error('Failed to rollback USB wallet: %s', exc)

    def _create_wallet_data_package_with_index(self, index: int) -> bytes:
        """Create wallet data package as ZIP containing wallet folder + wallet_data + INI file with updated sync_index and epoch_time."""
        try:
            buf = io.BytesIO()

            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
                self._add_wallet_folder_to_zip(z, app_paths.app_path)
                wallet_data_path = app_paths.wallet_data_folder_path
                if os.path.exists(wallet_data_path):
                    for root, _, files in os.walk(wallet_data_path):
                        for f in files:
                            path = os.path.join(root, f)
                            rel = os.path.relpath(path, app_paths.app_path)
                            info = zipfile.ZipInfo(rel)
                            info.date_time = datetime.datetime.fromtimestamp(
                                os.stat(path).st_mtime,
                            ).timetuple()[:6]
                            with open(path, 'rb') as fh:
                                z.writestr(info, fh.read())
                if os.path.exists(app_paths.config_file_path):
                    with open(app_paths.config_file_path, encoding='utf-8') as cfg:
                        lines = cfg.read().splitlines()
                    epoch_time = str(int(time.time()))
                    lines = self._upsert_ini_line(
                        lines, 'sync_index', str(index),
                    )
                    lines = self._upsert_ini_line(
                        lines, 'epoch_time', epoch_time,
                    )

                    z.writestr(
                        os.path.basename(
                            app_paths.config_file_path,
                        ), '\n'.join(lines),
                    )
            return buf.getvalue()
        except Exception as exc:
            logger.error('Failed to create wallet data package: %s', exc)
            raise

    def _add_wallet_folder_to_zip(self, z, wallet_path: str):
        """Add wallet folder contents to ZIP, excluding logs and cache."""
        try:
            for fingerprint in os.listdir(wallet_path):
                folder = os.path.join(wallet_path, fingerprint)

                if not os.path.isdir(folder):
                    continue

                # 🚫 skip non-wallet folders at root
                if fingerprint in ('logs', 'cache'):
                    continue

                z.writestr(fingerprint + '/', '')

                for root, dirs, files in os.walk(folder):
                    # 🚫 prevent descending into logs/cache anywhere
                    dirs[:] = [d for d in dirs if d not in ('logs', 'cache')]

                    rel_dir = os.path.relpath(root, folder)
                    if rel_dir != '.':
                        z.writestr(os.path.join(fingerprint, rel_dir) + '/', '')

                    for f in files:
                        path = os.path.join(root, f)
                        rel = os.path.relpath(path, folder)

                        # 🚫 extra safety: skip files inside logs/cache
                        if rel.split(os.sep, 1)[0] in ('logs', 'cache'):
                            continue

                        arc = os.path.join(fingerprint, rel)

                        info = zipfile.ZipInfo(arc)
                        info.date_time = datetime.datetime.fromtimestamp(
                            os.stat(path).st_mtime,
                        ).timetuple()[:6]

                        with open(path, 'rb') as fh:
                            z.writestr(info, fh.read())

        except Exception as exc:
            logger.error('Failed adding wallet folder to zip: %s', exc)
            raise

    def _validate_wallet_data(self, data: bytes) -> bool:
        """Validate wallet data from USB ZIP."""
        try:
            with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
                ini_files = [f for f in z.namelist() if f.endswith('.ini')]
                if not ini_files:
                    logger.error('No INI file found in wallet ZIP')
                    return False

                ini = z.read(ini_files[0]).decode('utf-8')

                for line in ini.splitlines():
                    if line.startswith('rgb_lib_version='):
                        rgb_lib_version = line.split('=', 1)[1].strip()
                        if rgb_lib_version not in COMPATIBLE_RGB_LIB_VERSION:
                            logger.error(ERROR_RGB_LIB_INCOMPATIBILITY)
                            raise CommonException('RGB_LIB_INCOMPATIBLE')
                        if SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD:
                            SettingRepository.set_rgb_lib_version(
                                rgb_lib_version,
                            )

                ini_kv: dict[str, str] = {}
                for line in ini.splitlines():
                    if '=' in line:
                        k, v = line.split('=', 1)
                        ini_kv[k.strip()] = v.strip()

                usb_xpub_vanilla = ini_kv.get(ACCOUNT_XPUB_VANILLA)
                usb_xpub_colored = ini_kv.get(ACCOUNT_XPUB_COLORED)

                local_xpub_vanilla = local_store.get_value(
                    ACCOUNT_XPUB_VANILLA,
                )
                local_xpub_colored = local_store.get_value(
                    ACCOUNT_XPUB_COLORED,
                )

                if usb_xpub_vanilla != local_xpub_vanilla:
                    logger.error(
                        'account_xpub_vanilla mismatch between USB and wallet',
                    )
                    return False

                if usb_xpub_colored != local_xpub_colored:
                    logger.error(
                        'account_xpub_colored mismatch between USB and wallet',
                    )
                    return False

                return True
        except Exception as exc:
            logger.error('Wallet data validation failed: %s', exc)
            return False

    def _calculate_wallet_checksum(self) -> str:
        """Calculate SHA256 checksum of all files in the wallet folder (excluding logs)."""
        def update_hash_from_dir(base_dir: str, hasher) -> None:
            """Update hash from directory."""
            if not os.path.isdir(base_dir):
                return
            files = []
            for root, _, fs in os.walk(base_dir):
                for filename in fs:
                    rel = os.path.relpath(
                        os.path.join(root, filename), base_dir,
                    )
                    if not rel.startswith('log'):
                        files.append(rel)
            files.sort()
            for rel in files:
                file_path = os.path.join(base_dir, rel)
                try:
                    with open(file_path, 'rb') as fh:
                        while chunk := fh.read(4096):
                            hasher.update(chunk)
                except Exception as exc:
                    logger.warning(
                        'Could not read file for checksum: %s (%s)', rel, exc,
                    )
                    hasher.update(rel.encode())

        try:
            h = hashlib.sha256()

            # Wallet folder
            wallet_dir = os.path.join(
                app_paths.app_path, self.master_fingerprint,
            )
            update_hash_from_dir(wallet_dir, h)

            # wallet-data folder
            wallet_data_dir = os.path.join(app_paths.app_path, 'wallet-data')
            update_hash_from_dir(wallet_data_dir, h)

            return h.hexdigest()
        except Exception as exc:
            logger.error('Error calculating wallet checksum: %s', exc)
            return hashlib.sha256(b'error').hexdigest()

    def _calculate_usb_wallet_checksum(self) -> str:
        """Calculate SHA256 checksum of wallet data stored inside the USB ZIP (excluding logs)."""
        try:
            if not self.selected_drive:
                return hashlib.sha256(b'').hexdigest()

            path = os.path.join(
                self.selected_drive.path, f"{
                    self.master_fingerprint
                }.zip",
            )
            if not os.path.exists(path):
                return hashlib.sha256(b'').hexdigest()

            h = hashlib.sha256()
            with zipfile.ZipFile(path, 'r') as z:
                prefix = self.master_fingerprint + '/'
                # Collect full zip names under master fingerprint (excluding logs)
                names = [
                    n for n in z.namelist()
                    if (
                        (n.startswith(prefix) and not n.startswith(prefix + 'log'))
                        or (n.startswith('wallet-data/') and not n.startswith('wallet-data/log'))
                    ) and not n.endswith('/')
                ]
                for name in sorted(names):
                    h.update(z.read(name))

            return h.hexdigest()
        except Exception as exc:
            logger.error('Error calculating USB checksum: %s', exc)
            return hashlib.sha256(b'error').hexdigest()

    def _upsert_ini_line(self, lines: list[str], key: str, value: str) -> list[str]:
        """Replace 'key=' line if present; otherwise append it exactly once."""
        prefix = f"{key}="
        for i, line in enumerate(lines):
            if line.startswith(prefix):
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
        return lines
