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
import zipfile

from PySide6.QtCore import QCoreApplication

from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
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


class USBSyncManager:
    """Manages USB synchronization for wallet data."""

    def __init__(self):
        self.usb_detector = USBDetector()
        self.sync_in_progress = False
        self.dialog_shown = False
        self.master_fingerprint: str | None = None
        self.selected_drive: USBDrive | None = None
        self.temp_local_wallet_data = None

    def reset_dialog_flag(self):
        self.dialog_shown = False

    def perform_sync(self, selected_drive: USBDrive):
        try:
            self.selected_drive = selected_drive
            self.reset_dialog_flag()
            self.master_fingerprint = self._get_master_fingerprint()
            self.sync_in_progress = True
            if not self.master_fingerprint:
                return
            if not self._validate_usb_drive():
                raise CommonException(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT,
                        'usb_invalid_wallet_data',
                    ),
                )

            direction = self._determine_sync_direction()
            if direction == 'to_usb':
                self._sync_to_usb()
                return 'to_usb'
            elif direction == 'from_usb':
                self._sync_from_usb()
                return 'from_usb'
            else:
                logger.info('No sync needed - data is up to date')
                return 'no_sync'
        except Exception as exc:
            logger.error('USB sync failed: %s', exc)
            raise CommonException(str(exc))
        finally:
            self.sync_in_progress = False

    def _validate_usb_drive(self) -> bool:
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
        try:
            if not self.selected_drive:
                return None
            if not self._check_usb_ini_exists():
                logger.info('No wallet INI on USB - creating initial backup')
                return 'to_usb'
            return self._determine_sync_direction_with_counter()
        except Exception as exc:
            logger.error('Error determining sync direction: %s', exc)
            return 'to_usb'

    def _check_usb_ini_exists(self) -> bool:
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
        try:
            usb_index = self._get_usb_index()
            local_index = self._get_local_index()
            logger.debug(
                'USB index=%s, Local index=%s',
                usb_index, local_index,
            )

            usb_checksum = self._calculate_usb_wallet_checksum()
            local_checksum = self._calculate_wallet_checksum()

            # Debug log for checksum comparison
            if usb_checksum == local_checksum:
                logger.debug(
                    'Checksums match (USB=%s, Local=%s)',
                    usb_checksum, local_checksum,
                )
            else:
                logger.debug(
                    'Checksums differ (USB=%s, Local=%s)',
                    usb_checksum, local_checksum,
                )

            # Case 1: USB index ahead
            if usb_index > local_index:
                return None if usb_checksum == local_checksum else 'from_usb'

            # Case 2: Local index ahead
            if local_index > usb_index:
                return None if usb_checksum == local_checksum else 'to_usb'

            # Case 3: Index same but checksum mismatch
            if usb_index == local_index and usb_checksum != local_checksum:
                last_dir = self._get_last_sync_direction()
                if last_dir:
                    logger.info(
                        'Index same but checksum mismatch, falling back to last sync direction: %s',
                        last_dir,
                    )
                    return 'to_usb' if last_dir == 'wallet_to_usb' else 'from_usb'

            # Case 4: Index and checksum both same → no sync needed
            logger.debug(
                'Indexes and checksums are identical, no sync required',
            )
            return None

        except Exception as exc:
            logger.error(
                'Error determining sync direction with counter: %s', exc,
            )
            return None

    def _get_usb_index(self) -> int:
        """Read sync_index from the INI stored inside the USB ZIP."""
        try:
            if not self.selected_drive:
                return 0
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

    def _get_local_index(self) -> int:
        """Read sync_index from local INI file."""
        try:
            path = self._get_ini_file_path()
            if not os.path.exists(path):
                return 0
            with open(path, encoding='utf-8') as f:
                for line in f:
                    if line.startswith('sync_index='):
                        try:
                            return int(line.split('=', 1)[1].strip() or 0)
                        except ValueError:
                            return 0
        except Exception as exc:
            logger.error('Error getting local index: %s', exc)
        return 0

    def _update_local_index(self, new_index: int):
        """Update sync_index in local INI file (create if absent)."""
        try:
            path = self._get_ini_file_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            lines = []
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    lines = f.read().splitlines()

            for i, line in enumerate(lines):
                if line.startswith('sync_index='):
                    lines[i] = f"sync_index={new_index}"
                    break
            else:
                lines.append(f"sync_index={new_index}")

            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + ('\n' if lines else ''))
            logger.info('Updated local index to %s', new_index)
        except Exception as exc:
            logger.error('Error updating local index: %s', exc)

    def _update_usb_ini_index(self, new_index: int):
        """
        Update sync_index inside the INI that is stored within the USB ZIP.
        Safest approach: rewrite the ZIP with updated INI content.
        """
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

    def _sync_to_usb(self):
        try:
            current_local_index = self._get_local_index()

            if current_local_index == 0:  # initial backup
                logger.info('Creating initial USB backup')
                self._update_local_index(0)
                data = self._create_wallet_data_package_with_index(0)

                usb_file = os.path.join(
                    self.selected_drive.path, f"{
                        self.master_fingerprint
                    }.zip",
                )
                self._create_usb_temp_file()
                with open(usb_file, 'wb') as f:
                    f.write(data)

                self._update_local_index(1)
                self._update_usb_ini_index(1)
                self._cleanup_extra_usb_temp_backups()

                self._update_last_sync_direction('wallet_to_usb')
            else:
                logger.info('Regular sync: wallet newer than USB')
                try:
                    new_index = current_local_index + 1
                    data = self._create_wallet_data_package_with_index(
                        new_index,
                    )

                    # Validate the package before writing to USB
                    if not self._validate_wallet_data(data):
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

                    self._update_local_index(new_index)

                    self._update_last_sync_direction('wallet_to_usb')
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

    def _sync_from_usb(self):
        try:
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
                self._update_local_index(usb_index+1)
                self._update_last_sync_direction('usb_to_wallet')
                logger.info(
                    'Restored from USB (usb_index=%s → local=%s)', usb_index, usb_index,
                )

            except Exception as exc:
                if self.temp_local_wallet_data and os.path.exists(self.temp_local_wallet_data):
                    self.restore_local_folder_from_backup()
                raise exc
        except Exception as exc:
            logger.error('Sync from USB failed: %s', exc)
            raise exc

    def _create_usb_temp_file(self):
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
        try:
            folder = os.path.join(
                self._get_wallet_data_path(), self.master_fingerprint,
            )
            if not os.path.exists(folder):
                return None
            temp = os.path.join(
                self._get_wallet_data_path(), f"{
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
        """
        Restore wallet data from ZIP.
        If only_folder=True, restores both the master_fingerprint folder and cache folder (overwrite old files).
        Otherwise, restores everything (wallet folder, cache, ini, etc.).
        """
        try:
            base = self._get_wallet_data_path()
            fingerprint_folder = os.path.join(base, self.master_fingerprint)

            if only_folder:
                # Remove only fingerprint folder, keep cache (will be overwritten)
                if os.path.exists(fingerprint_folder):
                    shutil.rmtree(fingerprint_folder)

            with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
                if only_folder:
                    # Restore only fingerprint folder and cache folder
                    fingerprint_prefix = self.master_fingerprint + '/'
                    cache_prefix = 'cache/'

                    for m in z.namelist():
                        if (m.startswith(fingerprint_prefix) or m.startswith(cache_prefix)) and not m.endswith('/'):
                            target = os.path.join(base, m)
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            # This will overwrite if file already exists
                            with open(target, 'wb') as f:
                                f.write(z.read(m))
                else:
                    # Full restore (wallet folder + cache + ini + everything else)
                    z.extractall(base)

        except Exception as exc:
            logger.error('Failed to restore wallet data: %s', exc)
            raise

    def restore_local_folder_from_backup(self):
        try:
            base = self._get_wallet_data_path()
            folder = os.path.join(base, self.master_fingerprint)
            if os.path.exists(folder):
                shutil.rmtree(folder)
            with zipfile.ZipFile(self.temp_local_wallet_data, 'r') as z:
                z.extractall(base)
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
        """Create wallet data package as ZIP containing wallet folder + cache + INI file with updated sync_index."""
        try:
            base = self._get_wallet_data_path()
            ini = self._get_ini_file_path()
            buf = io.BytesIO()

            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
                # Add wallet folder (master_fingerprint)
                self._add_wallet_folder_to_zip(z, base)

                # Add cache folder if exists
                cache_path = os.path.join(base, 'cache')
                if os.path.exists(cache_path):
                    for root, dirs, files in os.walk(cache_path):
                        rel_dir = os.path.relpath(root, base)
                        for f in files:
                            path = os.path.join(root, f)
                            rel = os.path.relpath(path, base)
                            info = zipfile.ZipInfo(rel)
                            info.date_time = datetime.datetime.fromtimestamp(
                                os.stat(path).st_mtime,
                            ).timetuple()[:6]
                            with open(path, 'rb') as fh:
                                z.writestr(info, fh.read())

                # Update INI with sync_index
                if os.path.exists(ini):
                    with open(ini, encoding='utf-8') as f:
                        lines = f.read().splitlines()

                    for i, line in enumerate(lines):
                        if line.startswith('sync_index='):
                            lines[i] = f"sync_index={index}"
                            break
                    else:
                        lines.append(f"sync_index={index}")

                    z.writestr(os.path.basename(ini), '\n'.join(lines))

            return buf.getvalue()
        except Exception as exc:
            logger.error('Failed to create wallet data package: %s', exc)
            raise

    def _add_wallet_folder_to_zip(self, z, wallet_path: str):
        """Add wallet folder contents to ZIP, excluding logs and cache."""
        try:
            folder = os.path.join(wallet_path, self.master_fingerprint)
            if not os.path.exists(folder):
                logger.warning('Wallet folder not found: %s', folder)
                return

            z.writestr(self.master_fingerprint + '/', '')

            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if d not in ['logs']]

                rel_dir = os.path.relpath(root, folder)
                if rel_dir != '.':
                    z.writestr(
                        os.path.join(
                            self.master_fingerprint, rel_dir,
                        ) + '/', '',
                    )

                for f in files:
                    path = os.path.join(root, f)
                    rel = os.path.relpath(path, folder)
                    arc = os.path.join(self.master_fingerprint, rel)

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

                if 'rgb_lib_version=' not in ini:
                    logger.error('RGB lib version missing in INI')
                    return False

                for line in ini.splitlines():
                    if line.startswith('rgb_lib_version='):
                        if line.split('=')[1].strip() != CURRENT_RGB_LIB_VERSION:
                            logger.warning('RGB lib mismatch in wallet data')
                            ToastManager.error(
                                description=ERROR_RGB_LIB_INCOMPATIBILITY,
                            )
                            return False

                if self._get_master_fingerprint() not in ini:
                    logger.error('Master fingerprint mismatch in INI')
                    return False

                # Additional validation: ensure account XPUBs match local values
                # Build a simple key->value map from the INI content
                ini_kv: dict[str, str] = {}
                for line in ini.splitlines():
                    if '=' in line:
                        k, v = line.split('=', 1)
                        ini_kv[k.strip()] = v.strip()

                usb_xpub_vanilla = ini_kv.get('account_xpub_vanilla')
                usb_xpub_colored = ini_kv.get('account_xpub_colored')

                local_xpub_vanilla = local_store.get_value(
                    ACCOUNT_XPUB_VANILLA,
                )
                local_xpub_colored = local_store.get_value(
                    ACCOUNT_XPUB_COLORED,
                )

                if not usb_xpub_vanilla or not usb_xpub_colored:
                    logger.error(
                        'XPUBs missing in USB INI (vanilla or colored)',
                    )
                    return False

                if not local_xpub_vanilla or not local_xpub_colored:
                    logger.error(
                        'Local XPUBs not set; cannot validate USB wallet data',
                    )
                    return False

                if usb_xpub_vanilla != local_xpub_vanilla:
                    logger.error(
                        'account_xpub_vanilla mismatch between USB and local store',
                    )
                    return False

                if usb_xpub_colored != local_xpub_colored:
                    logger.error(
                        'account_xpub_colored mismatch between USB and local store',
                    )
                    return False

                return True
        except Exception as exc:
            logger.error('Wallet data validation failed: %s', exc)
            return False

    def _calculate_wallet_checksum(self) -> str:
        """Calculate SHA256 checksum of all files in master fingerprint folder (excluding logs)."""
        try:
            folder = os.path.join(
                self._get_wallet_data_path(), self.master_fingerprint,
            )
            if not os.path.exists(folder):
                return hashlib.sha256(b'').hexdigest()

            files = []
            for root, _, fs in os.walk(folder):
                for f in fs:
                    rel = os.path.relpath(os.path.join(root, f), folder)
                    if not rel.startswith('log'):
                        files.append(rel)

            files.sort()
            h = hashlib.sha256()

            for rel in files:
                try:
                    with open(os.path.join(folder, rel), 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b''):
                            h.update(chunk)
                except Exception as exc:
                    logger.warning(
                        'Could not read file for checksum: %s (%s)', rel, exc,
                    )
                    h.update(rel.encode())

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
                files = [
                    n[len(prefix):]
                    for n in z.namelist()
                    if n.startswith(prefix)
                    and not n.endswith('/')
                    and not n.startswith(prefix + 'log')
                ]
                for rel in sorted(files):
                    h.update(z.read(prefix + rel))

            return h.hexdigest()
        except Exception as exc:
            logger.error('Error calculating USB checksum: %s', exc)
            return hashlib.sha256(b'error').hexdigest()

    def _get_master_fingerprint(self) -> str:
        try:
            return local_store.get_value(MASTER_FINGERPRINT)
        except Exception as exc:
            logger.error('Failed to get master fingerprint: %s', exc)
            return ''

    def _get_ini_file_path(self) -> str:
        return app_paths.config_file_path

    def _get_wallet_data_path(self) -> str:
        return app_paths.app_path

    def _get_last_sync_direction(self) -> str | None:
        try:
            ini_path = self._get_ini_file_path()
            if not os.path.exists(ini_path):
                return None
            with open(ini_path, encoding='utf-8') as f:
                for line in f:
                    if line.startswith('last_sync_direction='):
                        return line.split('=', 1)[1].strip()
            return None
        except Exception as exc:
            logger.error('Failed to read last sync direction: %s', exc)
            return None

    def _update_last_sync_direction(self, direction: str):
        try:
            ini_path = self._get_ini_file_path()
            lines = []
            if os.path.exists(ini_path):
                with open(ini_path, encoding='utf-8') as f:
                    lines = f.read().splitlines()

            updated = False
            for i, line in enumerate(lines):
                if line.startswith('last_sync_direction='):
                    lines[i] = f"last_sync_direction={direction}"
                    updated = True
                    break

            if not updated:
                lines.append(f"last_sync_direction={direction}")

            with open(ini_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info('Updated last sync direction: %s', direction)
        except Exception as exc:
            logger.error('Failed to update last sync direction: %s', exc)
