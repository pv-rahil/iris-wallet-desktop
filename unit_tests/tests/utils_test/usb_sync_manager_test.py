# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for `USBSyncManager`."""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletType
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import COMPATIBLE_RGB_LIB_VERSION
from src.utils.constant import EPOCH_TIME
from src.utils.constant import LAST_SYNC_DIRECTION
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import SYNC_INDEX
from src.utils.usb_detector import USBDrive
from src.utils.usb_sync_manager import USBSyncManager


@pytest.fixture
def manager() -> USBSyncManager:
    """Return a fresh `USBSyncManager` instance for testing."""
    return USBSyncManager()


@pytest.fixture()
def fake_local_store():
    """Provide a simple in-memory `local_store` stub."""
    store = {'values': {}}

    def get_value(k):
        """Get a value from the store."""
        return store['values'].get(k)

    def set_value(k, v):
        """Set a value in the store."""
        store['values'][k] = v

    def clear_settings():
        """Clear all values from the store."""
        store['values'].clear()

    def remove_file(**kwargs):
        """Remove a file from the store."""
        return True

    return SimpleNamespace(
        get_value=get_value,
        set_value=set_value,
        clear_settings=clear_settings,
        remove_file=remove_file,
    )


@pytest.fixture(autouse=True)
def _patch_local_store_autouse(monkeypatch, fake_local_store):
    """Ensure tests never mutate real local_store by patching module attribute."""
    monkeypatch.setattr(
        'src.utils.usb_sync_manager.local_store', fake_local_store,
    )


def make_drive(tmp_path):
    """Helper to construct a non-empty `USBDrive` at tmp_path."""
    d = USBDrive(name='USB', path=str(tmp_path), is_empty=False)
    return d


def test_validate_usb_drive_empty_true(manager: USBSyncManager, tmp_path):
    """When selected drive is empty, validation should pass (True)."""
    drv = USBDrive(name='USB', path=str(tmp_path), is_empty=True)
    manager.selected_drive = drv
    assert manager._validate_usb_drive() is True


@patch('os.listdir', return_value=['other.zip'])
def test_has_valid_wallet_data_false(_ls, manager: USBSyncManager, tmp_path):
    """If required zip not present, `_has_valid_wallet_data` returns False."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    assert manager._has_valid_wallet_data() is False


@patch('os.path.exists', return_value=False)
def test_determine_sync_direction_no_ini_returns_to_usb(_exists, manager: USBSyncManager, tmp_path):
    """Without ini on USB, direction should be 'to_usb'."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    # _check_usb_ini_exists will return False -> 'to_usb'
    assert manager._determine_sync_direction() == 'to_usb'


def test_determine_sync_direction_with_counter_prefers_last_direction(manager: USBSyncManager, tmp_path, fake_local_store):
    """With equal counters but different checksums, follow LAST_SYNC_DIRECTION."""
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = make_drive(tmp_path)
    fake_local_store.set_value(SYNC_INDEX, 1)
    fake_local_store.set_value(LAST_SYNC_DIRECTION, 'wallet_to_usb')

    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch.object(manager, '_check_usb_ini_exists', return_value=True), \
            patch.object(manager, '_get_usb_index', return_value=1), \
            patch.object(manager, '_calculate_usb_wallet_checksum', return_value='u1'), \
            patch.object(manager, '_calculate_wallet_checksum', return_value='l2'):
        # same index, different checksum -> follow LAST_SYNC_DIRECTION -> to_usb
        assert manager._determine_sync_direction_with_counter() == 'to_usb'


def make_usb_with_zip(tmp_path, master_fingerprint: str, ini_text: str, extra: dict[str, bytes] | None = None):
    """Create a USB folder with `<fingerprint>.zip` containing wallet.ini and optional extra files."""
    d = tmp_path / 'usb'
    d.mkdir(exist_ok=True)
    zp = d / f"{master_fingerprint}.zip"
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('wallet.ini', ini_text)
        if extra:
            for n, data in extra.items():
                z.writestr(n, data)
    return str(d), str(zp)


def sandbox_app_paths(tmp_path):
    """Return a namespace mimicking app_paths within a sandbox tmp directory."""
    return SimpleNamespace(
        app_path=str(tmp_path / 'app'),
        wallet_data_folder_path=str(tmp_path / 'app' / 'wallet-data'),
        config_file_path=str(tmp_path / 'app' / 'config.ini'),
        logs_folder_path=str(tmp_path / 'app' / 'logs'),
        cache_folder_path=str(tmp_path / 'app' / 'cache'),
        multisig_cosigners_file_path=str(
            tmp_path / 'app' / 'multisig_cosigners.json',
        ),
    )


def test_perform_sync_none_when_no_fingerprint(manager: USBSyncManager, tmp_path, fake_local_store):
    """Return None when `MASTER_FINGERPRINT` is missing in local store."""
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='msg'):
        fake_local_store.set_value(MASTER_FINGERPRINT, None)
        manager.selected_drive = USBDrive(
            name='USB', path=str(tmp_path), is_empty=False,
        )
        res = manager.perform_sync(manager.selected_drive)
        assert res is None
        assert manager.sync_in_progress is False


def test_perform_sync_invalid_drive_raises(manager: USBSyncManager, tmp_path, fake_local_store):
    """Raise when drive validation fails and wallet data is invalid."""
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='usb_invalid_wallet_data'):
        fake_local_store.set_value(MASTER_FINGERPRINT, 'abcd')
        manager.selected_drive = USBDrive(
            name='USB', path=str(tmp_path), is_empty=False,
        )
        with patch.object(manager, '_has_valid_wallet_data', return_value=False):
            with pytest.raises(Exception):
                manager.perform_sync(manager.selected_drive)


def test_check_usb_ini_exists_true_false(manager: USBSyncManager, tmp_path):
    """`_check_usb_ini_exists` returns True for matching zip and False otherwise."""
    manager.master_fingerprint = 'abcd'
    usb_dir, _ = make_usb_with_zip(tmp_path, 'abcd', 'sync_index=1\n')
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)
    assert manager._check_usb_ini_exists() is True
    manager.master_fingerprint = 'ef'
    assert manager._check_usb_ini_exists() is False


def test_get_usb_index_parsing_and_invalid(manager: USBSyncManager, tmp_path):
    """Parse valid `sync_index` and default to 0 for invalid values."""
    manager.master_fingerprint = 'abcd'
    usb_dir, _ = make_usb_with_zip(tmp_path, 'abcd', 'sync_index=5\n')
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)
    assert manager._get_usb_index() == 5

    # invalid value -> 0
    usb_dir2, _ = make_usb_with_zip(tmp_path, 'abcd', 'sync_index=notanint\n')
    manager.selected_drive = USBDrive(
        name='USB', path=usb_dir2, is_empty=False,
    )
    assert manager._get_usb_index() == 0


def test_update_usb_ini_index_updates_or_creates(manager: USBSyncManager, tmp_path):
    """Update existing `sync_index` or create wallet.ini when missing."""
    manager.master_fingerprint = 'abcd'
    usb_dir, zip_path = make_usb_with_zip(tmp_path, 'abcd', 'sync_index=1\n')
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)
    manager._update_usb_ini_index(7)
    with zipfile.ZipFile(zip_path, 'r') as z:
        ini = z.read('wallet.ini').decode()
        assert 'sync_index=7' in ini

    # no ini initially
    zp = os.path.join(usb_dir, 'abcd.zip')
    os.remove(zp)
    with zipfile.ZipFile(zp, 'w') as z:
        z.writestr('other.txt', b'x')
    manager._update_usb_ini_index(3)
    with zipfile.ZipFile(zp, 'r') as z:
        assert 'wallet.ini' in z.namelist()


def test_create_usb_temp_file_and_cleanup(manager: USBSyncManager, tmp_path):
    """Create temp USB backup and cleanup old temp backups."""
    manager.master_fingerprint = 'abcd'
    d = tmp_path / 'usb'
    d.mkdir()
    base = d / 'abcd.zip'
    base.write_bytes(b'zip')
    temp_extra = d / 'abcd_temp.zip'
    temp_extra.write_bytes(b'old')
    keep_extra = d / 'abcd_temp.zip'
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager._create_usb_temp_file()
    assert not base.exists() and keep_extra.exists()
    # create other temps matching cleanup pattern and cleanup
    (d / 'abcd_old_temp.zip').write_bytes(b'x')
    (d / 'abcd_prev_temp.zip').write_bytes(b'x')
    manager._cleanup_extra_usb_temp_backups()
    assert (d / 'abcd_old_temp.zip').exists() is False
    assert (d / 'abcd_prev_temp.zip').exists() is False


def test_create_local_temp_backup_and_restore_local(manager: USBSyncManager, tmp_path):
    """Create local temp backup zip and restore local folder from it."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    # build fingerprint folder with file
    manager.master_fingerprint = 'abcd'
    fp = os.path.join(ap.app_path, 'abcd')
    os.makedirs(fp, exist_ok=True)
    with open(os.path.join(fp, 'a.txt'), 'wb') as f:
        f.write(b'data')
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        temp = manager._create_local_temp_backup()
        assert temp and os.path.exists(temp)
        # now delete folder and restore from backup
        shutil = __import__('shutil')
        shutil.rmtree(fp)
        manager.temp_local_wallet_data = temp
        manager.restore_local_folder_from_backup()
        assert os.path.exists(fp)


def test_create_local_temp_backup_no_folder_returns_none(manager: USBSyncManager, tmp_path):
    """Return None when wallet folder does not exist for local backup."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        assert manager._create_local_temp_backup() is None


def test_perform_sync_from_usb_and_no_sync(manager: USBSyncManager, tmp_path, fake_local_store):
    """Return 'from_usb' when direction is from USB; 'no_sync' when direction is None."""
    manager.master_fingerprint = 'abcd'
    d = tmp_path / 'usb'
    d.mkdir()
    drv = USBDrive(name='USB', path=str(d), is_empty=False)
    # perform_sync reads MASTER_FINGERPRINT from local_store; ensure it's set
    fake_local_store.set_value(MASTER_FINGERPRINT, 'abcd')
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch.object(manager, '_validate_usb_drive', return_value=True), \
            patch.object(manager, '_determine_sync_direction', return_value='from_usb'), \
            patch.object(manager, 'sync_from_usb') as sfu:
        assert manager.perform_sync(drv) == 'from_usb'
        sfu.assert_called_once()

    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch.object(manager, '_validate_usb_drive', return_value=True), \
            patch.object(manager, '_determine_sync_direction', return_value=None):
        assert manager.perform_sync(drv) == 'no_sync'


def test_validate_usb_drive_exception_returns_false(manager: USBSyncManager):
    """Return False when `_has_valid_wallet_data` raises an exception."""
    manager.selected_drive = USBDrive(
        name='USB', path='/dev/null', is_empty=False,
    )
    with patch.object(manager, '_has_valid_wallet_data', side_effect=RuntimeError('boom')):
        assert manager._validate_usb_drive() is False


def test_has_valid_wallet_data_handles_errors(manager: USBSyncManager, tmp_path):
    """Return False when listing USB directory raises an error."""
    manager.selected_drive = USBDrive(
        name='USB', path=str(tmp_path), is_empty=False,
    )
    manager.master_fingerprint = 'abcd'
    with patch('os.listdir', side_effect=OSError('x')):
        assert manager._has_valid_wallet_data() is False


def test_check_usb_ini_exists_exception(manager: USBSyncManager, tmp_path):
    """Return False when reading USB zip raises an exception."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    f = d / 'abcd.zip'
    f.write_bytes(b'notzip')
    with patch('zipfile.ZipFile', side_effect=OSError('z')):
        assert manager._check_usb_ini_exists() is False


def test_get_usb_index_exception(manager: USBSyncManager, tmp_path):
    """Return 0 when reading or parsing `sync_index` raises an exception."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    (d / 'abcd.zip').write_bytes(b'content')
    with patch('zipfile.ZipFile', side_effect=RuntimeError('e')):
        assert manager._get_usb_index() == 0


def test_update_usb_ini_index_paths_and_exception(manager: USBSyncManager, tmp_path):
    """Cover branches for missing zip, ini creation and exception during replace."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    # when zip missing -> early return
    manager._update_usb_ini_index(3)
    # create zip without ini -> ini created
    with zipfile.ZipFile(d / 'abcd.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('abcd/file.txt', 'x')
    manager._update_usb_ini_index(4)
    with zipfile.ZipFile(d / 'abcd.zip', 'r') as z:
        assert any(n.endswith('.ini') for n in z.namelist())
    # exception branch
    with patch('os.replace', side_effect=OSError('r')):
        manager._update_usb_ini_index(5)  # should log error, not raise


def test_sync_to_usb_refresh_exception_path(manager: USBSyncManager, tmp_path, fake_local_store):
    """Do not raise when refresh path fails during initial backup; proceed and bump SYNC_INDEX."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    fake_local_store.set_value(SYNC_INDEX, None)
    with patch('src.utils.usb_sync_manager.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET), \
            patch('src.data.service.wallet_data_service.WalletDataService.get_session', return_value=object()), \
            patch('src.utils.usb_sync_manager.WalletDataService.refresh_wallet_data', side_effect=Exception('fail')):
        # Should not raise; initial backup continues
        manager.sync_to_usb()
        # SYNC_INDEX bumped to 1 and zip created
        assert fake_local_store.get_value(SYNC_INDEX) == 1
        assert (d / 'abcd.zip').exists()


def test_create_usb_temp_file_exception_and_cleanup_exception(manager: USBSyncManager, tmp_path):
    """Do not raise when temp file creation or cleanup throws OS errors."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    (d / 'abcd.zip').write_bytes(b'x')
    with patch('os.rename', side_effect=OSError('e')):
        manager._create_usb_temp_file()  # should log error
    with patch('os.listdir', side_effect=OSError('e')):
        manager._cleanup_extra_usb_temp_backups()  # should log error


def test_create_local_temp_backup_exception(manager: USBSyncManager, tmp_path):
    """Return None when zipping local temp backup raises an exception."""
    ap = sandbox_app_paths(tmp_path)
    manager.master_fingerprint = 'abcd'
    folder = os.path.join(ap.app_path, 'abcd')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'a.txt'), 'wb') as f:
        f.write(b'x')
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('zipfile.ZipFile', side_effect=OSError('z')):
        assert manager._create_local_temp_backup() is None


def test_restore_wallet_data_only_folder_and_full_and_exception(manager: USBSyncManager, tmp_path):
    """Restore wallet folder only, then full restore; raise on bad zip."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    # build zip with fingerprint and wallet-data
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('abcd/file.txt', 'x')
        z.writestr('wallet-data/data.bin', b'y')
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        manager._restore_wallet_data(buf.getvalue(), only_folder=True)
        assert os.path.exists(os.path.join(ap.app_path, 'abcd', 'file.txt'))
        # full restore
        manager._restore_wallet_data(buf.getvalue(), only_folder=False)
    # exception path
    with pytest.raises(Exception):
        manager._restore_wallet_data(b'badzip', only_folder=True)


def test_restore_local_folder_from_backup_success(manager: USBSyncManager, tmp_path):
    """Restore local folder from a prepared backup zip successfully."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    # create a backup zip content
    zpath = tmp_path / 'bk.zip'
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('abcd/a.txt', 'x')
    # set existing folder to be removed
    folder = os.path.join(ap.app_path, 'abcd')
    os.makedirs(folder, exist_ok=True)
    manager.temp_local_wallet_data = str(zpath)
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        manager.restore_local_folder_from_backup()
        assert os.path.exists(os.path.join(ap.app_path, 'abcd', 'a.txt'))


def test_create_wallet_data_package_with_index_exception(manager: USBSyncManager, tmp_path):
    """Raise when creating wallet data package zip fails."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('zipfile.ZipFile', side_effect=OSError('z')):
        with pytest.raises(Exception):
            manager._create_wallet_data_package_with_index(1)


def test_restore_usb_wallet_from_backup_when_base_exists(manager: USBSyncManager, tmp_path):
    """Restore USB zip from temp when base zip already exists."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    base = d / 'abcd.zip'
    temp = d / 'abcd_temp.zip'
    base.write_bytes(b'old')
    temp.write_bytes(b'new')
    manager._restore_usb_wallet_from_backup()
    assert base.read_bytes() == b'new'
    assert not temp.exists()


def test_create_wallet_data_package_includes_wallet_data_files(manager: USBSyncManager, tmp_path):
    """Include wallet-data files while creating wallet data package zip."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    os.makedirs(ap.wallet_data_folder_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    # add wallet folder file so method runs normally
    wfolder = os.path.join(ap.app_path, 'abcd')
    os.makedirs(wfolder, exist_ok=True)
    with open(os.path.join(wfolder, 'wf.txt'), 'wb') as f:
        f.write(b'w')
    # add wallet-data file to include
    with open(os.path.join(ap.wallet_data_folder_path, 'd.bin'), 'wb') as f:
        f.write(b'y')
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        data = manager._create_wallet_data_package_with_index(2)
    with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
        names = z.namelist()
        # should include wallet-data/d.bin
        assert 'wallet-data/d.bin' in names


def test_add_wallet_folder_to_zip_exception(manager: USBSyncManager, tmp_path):
    """Raise during adding wallet folder to zip when walking the tree fails."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(os.path.join(ap.app_path, 'abcd'), exist_ok=True)
    manager.master_fingerprint = 'abcd'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z, \
            patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('os.walk', side_effect=OSError('w')):
        with pytest.raises(Exception):
            manager._add_wallet_folder_to_zip(z, ap.app_path)


def test_validate_wallet_data_rgb_incompatible_returns_false(manager: USBSyncManager):
    """Return False for incompatible rgb_lib_version in wallet.ini."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('wallet.ini', 'rgb_lib_version=0.0.0\n')
    assert manager._validate_wallet_data(buf.getvalue()) is False


def test_calculate_usb_wallet_checksum_exception(manager: USBSyncManager, tmp_path):
    """Return a hex digest even if reading USB zip raises an exception."""
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    manager.master_fingerprint = 'abcd'
    (d / 'abcd.zip').write_bytes(b'x')
    with patch('zipfile.ZipFile', side_effect=OSError('z')):
        h = manager._calculate_usb_wallet_checksum()
        assert isinstance(h, str) and len(h) == 64
    # Nothing else: this test only covers the exception branch in checksum


def test_perform_sync_returns_none_when_no_master_fingerprint(manager: USBSyncManager, tmp_path, fake_local_store):
    """Return None from perform_sync when MASTER_FINGERPRINT is None."""
    d = tmp_path / 'usb'
    d.mkdir()
    drv = USBDrive(name='USB', path=str(d), is_empty=False)
    # Ensure MASTER_FINGERPRINT missing
    fake_local_store.set_value(MASTER_FINGERPRINT, None)
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store):
        assert manager.perform_sync(drv) is None


def test_validate_usb_drive_true_when_empty(manager: USBSyncManager):
    """Validation passes (True) when selected USB drive is empty."""
    manager.selected_drive = USBDrive(
        name='USB', path='/dev/null', is_empty=True,
    )
    assert manager._validate_usb_drive() is True


def test_validate_wallet_data_paths(manager: USBSyncManager, fake_local_store):
    """Validate wallet-data: match xpubs, compatible RGB versions, and update version."""
    # compatible rgb version and matching xpubs
    rgb_ok = next(iter(COMPATIBLE_RGB_LIB_VERSION))
    ini = f"wallet.ini\n{ACCOUNT_XPUB_VANILLA}=X1\n{
        ACCOUNT_XPUB_COLORED
    }=C1\nrgb_lib_version={rgb_ok}\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('wallet.ini', ini)
    data = buf.getvalue()
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.SettingRepository.get_wallet_entry_type', return_value=WalletEntryType.LOAD), \
            patch('src.utils.usb_sync_manager.SettingRepository.set_rgb_lib_version') as set_ver:
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'X1')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'C1')
        assert manager._validate_wallet_data(data) is True
        set_ver.assert_called_once()

    # mismatch returns False
    with patch('src.utils.usb_sync_manager.local_store', fake_local_store):
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'X2')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'C1')
        assert manager._validate_wallet_data(data) is False

    # incompatible rgb -> False (exception handled inside)
    bad_ini = 'wallet.ini\nrgb_lib_version=0.0.0\n'
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('wallet.ini', bad_ini)
    assert manager._validate_wallet_data(buf2.getvalue()) is False


def test_calculate_wallet_checksum_and_usb_checksum(manager: USBSyncManager, tmp_path):
    """Compute checksums for local wallet and USB zip and return hex digests."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    os.makedirs(ap.wallet_data_folder_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    fp = os.path.join(ap.app_path, 'abcd')
    os.makedirs(fp, exist_ok=True)
    with open(os.path.join(fp, 'f.txt'), 'wb') as f:
        f.write(b'hello')
    with open(os.path.join(ap.wallet_data_folder_path, 'g.bin'), 'wb') as f:
        f.write(b'world')
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        h1 = manager._calculate_wallet_checksum()
        assert isinstance(h1, str) and len(h1) == 64

    # USB checksum from zip
    usb_dir, _ = make_usb_with_zip(
        tmp_path, 'abcd', 'sync_index=1\n', {
            'abcd/a.txt': b'x', 'wallet-data/b.bin': b'y',
        },
    )
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)
    h2 = manager._calculate_usb_wallet_checksum()
    assert isinstance(h2, str) and len(h2) == 64


def test_upsert_ini_line_replace_and_append(manager: USBSyncManager):
    """Replace existing key or append a new `key=value` line into INI list."""
    out = manager._upsert_ini_line(['a=1', 'sync_index=3'], 'sync_index', '5')
    assert 'sync_index=5' in out and len(out) == 2
    out2 = manager._upsert_ini_line(['a=1'], 'sync_index', '1')
    assert 'sync_index=1' in out2


def test_sync_to_usb_initial_and_regular(manager: USBSyncManager, tmp_path, fake_local_store):
    """Perform initial and regular sync-to-USB flows, bumping SYNC_INDEX."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    # prepare config file for packaging
    with open(ap.config_file_path, 'w', encoding='utf-8') as f:
        f.write('sync_index=0\n')
    manager.master_fingerprint = 'abcd'
    manager.selected_drive = USBDrive(
        name='USB', path=str(tmp_path / 'usb'), is_empty=False,
    )
    os.makedirs(manager.selected_drive.path, exist_ok=True)
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='msg'):
        # initial backup path
        fake_local_store.set_value(SYNC_INDEX, None)
        manager.sync_to_usb()
        assert fake_local_store.get_value(SYNC_INDEX) == 1
        # regular path success (validate True)
        fake_local_store.set_value(SYNC_INDEX, 1)
        with patch.object(manager, '_validate_wallet_data', return_value=True):
            manager.sync_to_usb()
            assert fake_local_store.get_value(SYNC_INDEX) == 2


def test_sync_to_usb_regular_invalid_rolls_back_and_raises(manager: USBSyncManager, tmp_path, fake_local_store):
    """Roll back USB zip and raise when validation of new data fails."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    with open(ap.config_file_path, 'w', encoding='utf-8') as f:
        f.write('sync_index=1\n')
    manager.master_fingerprint = 'abcd'
    d = tmp_path / 'usb'
    d.mkdir()
    manager.selected_drive = USBDrive(name='USB', path=str(d), is_empty=False)
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='inv'):
        fake_local_store.set_value(SYNC_INDEX, 1)
        # prepare an existing base to enable rotation, then make _validate return False
        (d / 'abcd.zip').write_bytes(b'x')
        with patch.object(manager, '_validate_wallet_data', return_value=False), \
                patch.object(manager, '_restore_usb_wallet_from_backup') as rb:
            with pytest.raises(Exception):
                manager.sync_to_usb()
            rb.assert_called_once()


def test_sync_from_usb_paths(manager: USBSyncManager, tmp_path, fake_local_store):
    """Sync from USB happy path, then error branches for zero index and missing zip."""
    # setup usb with ini and valid data
    rgb_ok = next(iter(COMPATIBLE_RGB_LIB_VERSION))
    ini = f"sync_index=2\nepoch_time=123\n{ACCOUNT_XPUB_VANILLA}=X1\n{
        ACCOUNT_XPUB_COLORED
    }=C1\nrgb_lib_version={rgb_ok}\n"
    usb_dir, _ = make_usb_with_zip(tmp_path, 'abcd', ini)
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)
    manager.master_fingerprint = 'abcd'
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='msg'):
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'X1')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'C1')
        # happy path
        manager.sync_from_usb()
        assert fake_local_store.get_value(SYNC_INDEX) == 3
        assert fake_local_store.get_value(
            LAST_SYNC_DIRECTION,
        ) == 'usb_to_wallet'
        assert fake_local_store.get_value(EPOCH_TIME) == '123'

        # usb_index == 0 -> raises
        manager.master_fingerprint = 'ef'
        with pytest.raises(Exception):
            manager.sync_from_usb()

        # file missing -> raises
        manager.master_fingerprint = 'abcd'
        os.remove(os.path.join(usb_dir, 'abcd.zip'))
        with pytest.raises(Exception):
            manager.sync_from_usb()

    # validation failure triggers restore
    usb_dir2, _ = make_usb_with_zip(tmp_path, 'abcd', ini)
    manager.selected_drive = USBDrive(
        name='USB', path=usb_dir2, is_empty=False,
    )
    manager.master_fingerprint = 'abcd'
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch('src.utils.usb_sync_manager.QCoreApplication.translate', return_value='msg'), \
            patch.object(manager, '_create_local_temp_backup', return_value=str(tmp_path / 'bk.zip')):
        (tmp_path / 'bk.zip').write_bytes(b'0')
        with patch.object(manager, '_validate_wallet_data', return_value=False), \
                patch.object(manager, 'restore_local_folder_from_backup') as rlb:
            with pytest.raises(Exception):
                manager.sync_from_usb()
            rlb.assert_called_once()


def test_restore_wallet_data_multisig(manager, tmp_path):
    """Restore multisig cosigners from ZIP."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    cosigners_file = os.path.basename(ap.multisig_cosigners_file_path)

    # Case 1: valid json with required_signers
    data = {'cosigners': ['c1'], 'required_signers': 1, 'total_signers': 1}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(cosigners_file, json.dumps(data))
        z.writestr('other/', '')  # covered line 491-492

    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.SettingRepository.set_multisig_config') as mock_conf, \
            patch('src.utils.usb_sync_manager.SettingRepository.set_cosigners') as mock_cos:
        manager._restore_wallet_data(buf.getvalue(), only_folder=True)
        mock_conf.assert_called_with(1, 1)
        mock_cos.assert_called_with(['c1'])

    # Case 2: valid json without required_signers
    data = {'cosigners': ['c1']}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(cosigners_file, json.dumps(data))
    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.SettingRepository.set_cosigners') as mock_cos:
        manager._restore_wallet_data(buf.getvalue(), only_folder=True)
        mock_cos.assert_called_with(['c1'])

    # Case 3: raw binary (backward compatibility or raw file)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(cosigners_file, b'{"not_cosigners": 1}')
    with patch('src.utils.usb_sync_manager.app_paths', ap):
        manager._restore_wallet_data(buf.getvalue(), only_folder=True)
        assert os.path.exists(ap.multisig_cosigners_file_path)


def test_create_wallet_data_package_multisig(manager, tmp_path):
    """Include multisig in package."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'F1'
    os.makedirs(os.path.join(ap.app_path, 'F1'), exist_ok=True)

    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.SettingRepository.get_cosigners', return_value=['c1']), \
            patch('src.utils.usb_sync_manager.SettingRepository.get_multisig_config', return_value=(1, 2)):
        data = manager._create_wallet_data_package_with_index(1)
        with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
            assert os.path.basename(
                ap.multisig_cosigners_file_path,
            ) in z.namelist()


def test_sync_from_usb_is_load(manager, tmp_path, fake_local_store):
    """Test sync_from_usb with is_load=True/False."""
    ap = sandbox_app_paths(tmp_path)
    os.makedirs(ap.app_path, exist_ok=True)
    manager.master_fingerprint = 'abcd'
    ini = f"sync_index=10\nrgb_lib_version={next(iter(COMPATIBLE_RGB_LIB_VERSION))}\n{
        ACCOUNT_XPUB_VANILLA
    }=X\n{ACCOUNT_XPUB_COLORED}=C\n"
    usb_dir, _ = make_usb_with_zip(tmp_path, 'abcd', ini)
    manager.selected_drive = USBDrive(name='USB', path=usb_dir, is_empty=False)

    with patch('src.utils.usb_sync_manager.app_paths', ap), \
            patch('src.utils.usb_sync_manager.local_store', fake_local_store):
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'X')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'C')

        # is_load=True
        manager.sync_from_usb(is_load=True)
        assert fake_local_store.get_value(SYNC_INDEX) == 10

        # is_load=False
        manager.sync_from_usb(is_load=False)
        assert fake_local_store.get_value(SYNC_INDEX) == 11


def test_misc_exceptions(manager, tmp_path):
    """Cover various exception catch-all blocks."""
    manager.selected_drive = None
    assert manager._determine_sync_direction() is None  # line 117

    # 722: _calculate_wallet_checksum handle non-dir
    with patch('os.path.isdir', return_value=False):
        h = manager._calculate_wallet_checksum()
        assert isinstance(h, str) and len(h) == 64

    # 766: _calculate_usb_wallet_checksum no drive
    manager.selected_drive = None
    assert manager._calculate_usb_wallet_checksum() == hashlib.sha256(b'').hexdigest()


def test_perform_sync_to_usb_integration(manager, tmp_path, fake_local_store):
    """Test perform_sync hits to_usb branch naturally."""
    usb_dir = tmp_path / 'usb'
    usb_dir.mkdir()
    drv = USBDrive(name='USB', path=str(usb_dir), is_empty=True)
    fake_local_store.set_value(MASTER_FINGERPRINT, 'abcd')

    with patch('src.utils.usb_sync_manager.local_store', fake_local_store), \
            patch.object(manager, 'sync_to_usb') as mock_to:
        assert manager.perform_sync(drv) == 'to_usb'
        mock_to.assert_called_once()


def test_validate_wallet_data_mismatches(manager, fake_local_store):
    """Test xpub mismatches in _validate_wallet_data."""
    rgb_ok = next(iter(COMPATIBLE_RGB_LIB_VERSION))

    # Vanilla mismatch
    ini = f"wallet.ini\n{ACCOUNT_XPUB_VANILLA}=USB_V\n{
        ACCOUNT_XPUB_COLORED
    }=C\nrgb_lib_version={rgb_ok}\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('wallet.ini', ini)

    with patch('src.utils.usb_sync_manager.local_store', fake_local_store):
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'LOCAL_V')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'C')
        assert manager._validate_wallet_data(buf.getvalue()) is False

    # Colored mismatch
    ini = f"wallet.ini\n{ACCOUNT_XPUB_VANILLA}=V\n{
        ACCOUNT_XPUB_COLORED
    }=USB_C\nrgb_lib_version={rgb_ok}\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('wallet.ini', ini)

    with patch('src.utils.usb_sync_manager.local_store', fake_local_store):
        fake_local_store.set_value(ACCOUNT_XPUB_VANILLA, 'V')
        fake_local_store.set_value(ACCOUNT_XPUB_COLORED, 'LOCAL_C')
        assert manager._validate_wallet_data(buf.getvalue()) is False


def test_determine_sync_direction_exceptions(manager):
    """Trigger exceptions in direction determination."""
    manager.selected_drive = MagicMock()
    with patch.object(manager, '_check_usb_ini_exists', side_effect=Exception('oops')):
        assert manager._determine_sync_direction() is None

    with patch.object(manager, '_get_usb_index', side_effect=Exception('oops')):
        assert manager._determine_sync_direction_with_counter() is None
