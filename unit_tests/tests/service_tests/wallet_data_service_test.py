# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for `WalletDataService`.

Structured similarly to `unit_tests/tests/utils_test/cache_test.py`.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import time
from unittest.mock import patch

import pytest
from rgb_lib import Balance
from rgb_lib import BtcBalance

from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.utils.constant import DB_FILE_NAME


@pytest.fixture
def tmp_db():
    """Provide an isolated WalletDataService with a temp sqlite file."""
    with tempfile.TemporaryDirectory() as d:
        db_path = os.path.join(d, 'wallet.db')
        svc = WalletDataService(db_path)
        try:
            yield svc
        finally:
            try:
                svc.conn.close()
            except Exception:
                pass


def test_psbt_id_deterministic():
    """_psbt_id should be deterministic for the same PSBT base64."""
    p = 'cGlic2V0'
    assert WalletDataService._psbt_id(p) == WalletDataService._psbt_id(p)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.app_paths')
def test_initialize_service_creates_db_folder(app_paths, get_wallet_type, get_access_type):
    """_initialize_service should create folder and return a service when supported."""
    get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    get_access_type.return_value = WalletAccessType.WATCH_ONLY
    with tempfile.TemporaryDirectory() as d:
        app_paths.wallet_data_folder_path = d
        svc = WalletDataService._initialize_service()
        assert isinstance(svc, WalletDataService)
        assert os.path.exists(os.path.join(d, DB_FILE_NAME))


def test_create_tables_failure_logs_and_raises(tmp_db, mocker):
    """_create_tables should log and raise on sqlite error, similar to cache tests."""
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error('fail')
    tmp_db.conn = mock_conn
    tmp_db._db_lock = mocker.MagicMock()
    tmp_db._db_lock.__enter__ = lambda s: None
    tmp_db._db_lock.__exit__ = lambda s, exc_type, exc_val, exc_tb: None
    mock_logger = mocker.patch('src.data.service.wallet_data_service.logger')
    with pytest.raises(sqlite3.Error):
        tmp_db._create_tables()
    assert mock_logger.error.called
    assert 'Exception occur in wallet-data' in mock_logger.error.call_args[0][0]


@patch('src.data.service.wallet_data_service.colored_wallet')
def test_refresh_wallet_data_success(colored_mod, tmp_db):
    """refresh_wallet_data should persist values and log success."""
    # Allow writes
    tmp_db.is_watch_only = True
    # Prepare picklable balance response
    bal_resp = BtcBalance(
        vanilla=Balance(settled=1, future=2, spendable=3),
        colored=Balance(settled=4, future=5, spendable=6),
    )
    colored_mod.wallet.get_btc_balance.return_value = bal_resp
    # Use empty lists to satisfy Transaction/Unspent validation
    colored_mod.wallet.list_transactions.return_value = []
    colored_mod.wallet.list_unspents.return_value = []

    tmp_db.refresh_wallet_data()

    # Balance getter happy path
    bal = tmp_db.get_btc_balance()
    assert bal.vanilla.settled == 1 and bal.colored.settled == 4
    # Transactions/unspents happy path with empty lists
    assert tmp_db.list_transactions().transactions == []
    assert tmp_db.list_unspents().unspents == []


@patch('src.data.service.wallet_data_service.colored_wallet')
def test_refresh_wallet_data_exception(colored_mod, tmp_db, mocker):
    """refresh_wallet_data should log error and re-raise on exception."""
    tmp_db.is_watch_only = True
    colored_mod.wallet.get_btc_balance.side_effect = Exception('boom')
    mock_logger = mocker.patch('src.data.service.wallet_data_service.logger')
    with pytest.raises(Exception):
        tmp_db.refresh_wallet_data()
    assert mock_logger.error.called
    assert 'failed to refresh wallet-data' in mock_logger.error.call_args[0][0]


def test_fetch_data_unpickle_failure(tmp_db, mocker):
    """_fetch_data returns None and logs when pickle.loads fails."""
    # Manually insert bad blob
    with tmp_db.conn:
        tmp_db.conn.execute(
            'INSERT OR REPLACE INTO data (key, data, updated_at) VALUES (?, ?, ?)',
            ('abc', b'not-a-pickle', int(time.time())),
        )
    mock_logger = mocker.patch('src.data.service.wallet_data_service.logger')
    assert tmp_db._fetch_data('abc') is None
    assert mock_logger.error.called


def test_getters_return_defaults_when_no_data(tmp_db):
    """Default getters should return empty values when DB is empty."""
    bal = tmp_db.get_btc_balance()
    assert bal.vanilla.settled == 0 and bal.colored.settled == 0
    assert tmp_db.list_transactions().transactions == []
    assert tmp_db.list_unspents().unspents == []


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_psbt_crud_when_watch_only(mock_get_type, mock_get_access, tmp_db):
    """PSBT CRUD should work when watch-only/offline allowed."""
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    tmp_db.is_watch_only = True
    tmp_db.is_offline_wallet = False

    pid = tmp_db.add_psbt('base64_psbt', signed=False, purpose='send_btc')
    assert pid is not None

    lst = tmp_db.list_psbt(signed=False)
    assert lst and lst[0]['purpose'] == 'send_btc'

    signed_id = tmp_db.mark_psbt_signed('base64_psbt', 'base64_psbt_signed')
    assert signed_id is not None

    assert tmp_db.list_psbt(signed=False) == []
    sl = tmp_db.list_psbt(signed=True)
    assert sl and sl[0]['signed'] is True

    assert tmp_db.delete_psbt('base64_psbt_signed') is True


def test_list_psbt_signed_filter(tmp_db):
    """list_psbt should filter by signed flag and expose purpose field."""
    tmp_db.is_watch_only = True
    tmp_db.is_offline_wallet = False
    u_id = tmp_db.add_psbt('u_psbt', signed=False, purpose='send_btc')
    s_id = tmp_db.add_psbt('s_psbt', signed=True, purpose='send_rgb')
    assert u_id and s_id
    us = tmp_db.list_psbt(signed=False)
    ss = tmp_db.list_psbt(signed=True)
    assert len(
        us,
    ) == 1 and us[0]['purpose'] == 'send_btc' and us[0]['signed'] is False
    assert len(
        ss,
    ) == 1 and ss[0]['purpose'] == 'send_rgb' and ss[0]['signed'] is True


def test_add_delete_psbt_gating(tmp_db):
    """add_psbt returns None and delete_psbt returns False when not allowed."""
    tmp_db.is_watch_only = False
    tmp_db.is_offline_wallet = False
    assert tmp_db.add_psbt('psbt') is None
    assert tmp_db.delete_psbt('whatever') is False


def test_draft_issue_asset_crud(tmp_db):
    """Draft issue asset upsert/list/delete should function when allowed."""
    tmp_db.is_watch_only = True
    tmp_db.is_offline_wallet = False
    tmp_db.upsert_draft_issue_asset('name', 'T', 10, '/tmp/file')
    rows = tmp_db.list_draft_issue_assets()
    assert len(rows) == 1
    draft_id = rows[0]['id']
    assert tmp_db.delete_draft_issue_asset(draft_id) is True


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.app_paths')
def test_get_session_singleton_watch_only(app_paths, get_wallet_type, get_access_type):
    """get_session returns a singleton for supported types."""
    get_access_type.return_value = WalletAccessType.WATCH_ONLY
    get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    with tempfile.TemporaryDirectory() as d:
        app_paths.wallet_data_folder_path = d
        try:
            WalletDataService._instance = None
            a = WalletDataService.get_session()
            b = WalletDataService.get_session()
            assert a is not None and a is b
        finally:
            WalletDataService._instance = None


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_get_session_none_for_non_watch_only_online(get_wallet_type, get_access_type):
    """get_session returns None when unsupported."""
    get_access_type.return_value = None  # anything not WATCH_ONLY
    get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    WalletDataService._instance = None
    try:
        assert WalletDataService.get_session() is None
    finally:
        WalletDataService._instance = None
