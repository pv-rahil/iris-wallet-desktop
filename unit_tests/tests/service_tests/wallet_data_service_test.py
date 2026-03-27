# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-few-public-methods
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
from src.model.common_operation_model import IssueAssetDraftModel
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.model.enums.enums_model import WalletSignatureType
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


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.colored_wallet')
def test_refresh_wallet_data_success(colored_mod, mock_get_access, tmp_db):
    """refresh_wallet_data should persist values and log success."""
    # Allow writes
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
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


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.colored_wallet')
def test_refresh_wallet_data_exception(colored_mod, mock_get_access, tmp_db, mocker):
    """refresh_wallet_data should log error and re-raise on exception."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
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


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_list_psbt_signed_filter(mock_get_type, mock_get_access, tmp_db):
    """list_psbt should filter by signed flag and expose purpose field."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
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


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_add_delete_psbt_gating(mock_get_type, mock_get_access, tmp_db):
    """add_psbt returns None and delete_psbt returns False when not allowed."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    assert tmp_db.add_psbt('psbt') is None
    assert tmp_db.delete_psbt('whatever') is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_draft_issue_asset_crud(mock_get_type, mock_get_access, tmp_db):
    """Draft issue asset upsert/list/delete should function when allowed."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    tmp_db.upsert_draft_issue_asset(
        IssueAssetDraftModel(
            name='name', ticker='T', issued_amount=10, file_path='/tmp/file',
        ),
    )
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
def test_refresh_wallet_data_returns_early_when_not_watch_only(mock_get_access, tmp_db, mocker):
    """refresh_wallet_data should return early if not watch-only (no repository calls)."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    colored_mock = mocker.patch(
        'src.data.service.wallet_data_service.colored_wallet',
    )
    tmp_db.refresh_wallet_data()
    assert not colored_mock.wallet.get_btc_balance.called


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_list_psbt_not_allowed_returns_empty(mock_get_type, mock_get_access, tmp_db):
    """list_psbt should return [] when not watch-only/offline."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    assert tmp_db.list_psbt(signed=False) == []
    assert tmp_db.list_psbt(signed=True) == []


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_draft_issue_asset_not_allowed_paths(mock_get_type, mock_get_access, tmp_db):
    """list/delete draft_issue_asset should be gated when not allowed."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    assert tmp_db.list_draft_issue_assets() == []
    assert tmp_db.delete_draft_issue_asset('1') is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_mark_psbt_signed_without_unsigned_row(mock_get_type, mock_get_access, tmp_db):
    """mark_psbt_signed should handle missing unsigned row (purpose None) and still insert signed row."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    signed_id = tmp_db.mark_psbt_signed('missing_unsigned', 'signed_payload')
    assert signed_id is not None
    lst = tmp_db.list_psbt(signed=True)
    assert len(
        lst,
    ) == 1 and lst[0]['id'] == signed_id and lst[0]['purpose'] is None


@patch('src.data.service.wallet_data_service.logger')
def test_connect_db_error_path_logs_and_raises(mock_logger, tmp_path, monkeypatch):
    """_connect_db should log and raise when sqlite3.connect fails."""
    class Boom(sqlite3.Error):
        """Exception class for testing."""

    def boom_connect(*args, **kwargs):
        """Exception class for testing."""
        raise Boom('nope')

    monkeypatch.setattr('sqlite3.connect', boom_connect)
    # Constructing the service tries to connect immediately
    with pytest.raises(Boom):
        WalletDataService(str(tmp_path / 'wallet.db'))
    assert mock_logger.error.called


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_initialize_service_exception_handled_returns_none(mock_get_type, mock_get_access, mocker):
    """_initialize_service should catch exceptions and return None (and log)."""
    mock_get_access.side_effect = Exception('boom')
    log = mocker.patch('src.data.service.wallet_data_service.logger')
    assert WalletDataService._initialize_service() is None
    assert log.error.called


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


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_draft_add_and_get_by_id(mock_get_type, mock_get_access, tmp_db):
    """add_ifa_secondary_draft_meta should insert and get_ifa_secondary_draft_by_id should fetch it."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    draft_id = tmp_db.add_ifa_secondary_draft_meta('AID', 'AN', 5)
    assert draft_id is not None
    row = tmp_db.get_ifa_secondary_draft_by_id(int(draft_id))
    assert row and row['asset_id'] == 'AID' and row['asset_name'] == 'AN' and row['amount'] == 5
    assert row['active_utxo'] == 1


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_attach_psbt_and_list(mock_get_type, mock_get_access, tmp_db):
    """attach_inflate_psbt_to_secondary_draft should set psbt_id and list_ifa_secondary_drafts returns it."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    _id = tmp_db.add_ifa_secondary_draft_meta('X', None, None)
    assert _id is not None
    psbt = 'psbt_base64_payload'
    psbt_id = tmp_db.attach_inflate_psbt_to_secondary_draft('X', psbt)
    assert psbt_id is not None
    rows = tmp_db.list_ifa_secondary_drafts('X')
    assert len(rows) >= 1 and rows[0]['psbt_id'] == psbt_id


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_set_active_and_get_active(mock_get_type, mock_get_access, tmp_db):
    """set_active_secondary_draft should flip active_utxo and getters should reflect it."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    a = tmp_db.add_ifa_secondary_draft_meta('A', 'N1', 1)
    b = tmp_db.add_ifa_secondary_draft_meta('A', 'N2', 2)
    assert a and b
    # Set first as active explicitly
    tmp_db.set_active_secondary_draft(int(a), 'A')
    act = tmp_db.get_active_secondary_draft_for_asset('A')
    assert act and act['id'] == int(a)
    # Switch to second
    tmp_db.set_active_secondary_draft(int(b), 'A')
    act2 = tmp_db.get_active_secondary_draft_for_asset('A')
    assert act2 and act2['id'] == int(b)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_latest_active_across_assets(mock_get_type, mock_get_access, tmp_db):
    """get_latest_active_secondary_draft should return the most recent active."""
    import time as _t
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    _ = tmp_db.add_ifa_secondary_draft_meta('Z1', 'N', 1)
    _t.sleep(1)
    last_id = tmp_db.add_ifa_secondary_draft_meta('Z2', 'N', 1)
    row = tmp_db.get_latest_active_secondary_draft()
    assert row and row['asset_id'] == 'Z2' and row['id'] == int(last_id)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_delete_by_id_and_by_psbt_and_update_psbt(mock_get_type, mock_get_access, tmp_db):
    """delete_ifa_secondary_draft returns True; delete_secondary_draft_by_psbt and update_secondary_draft_psbt_id paths work."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    did = tmp_db.add_ifa_secondary_draft_meta('B', 'NB', 3)
    assert did is not None
    # Update psbt id using update method
    old_psbt = 'old_psbt'
    new_psbt = 'new_psbt'
    # Attach old psbt first
    _ = tmp_db.attach_inflate_psbt_to_secondary_draft('B', old_psbt)
    # Update to new
    assert tmp_db.update_secondary_draft_psbt_id(old_psbt, new_psbt) is True
    # Delete by psbt
    assert tmp_db.delete_secondary_draft_by_psbt(new_psbt) is True
    # Delete again by id should be False (already deleted)
    assert tmp_db.delete_ifa_secondary_draft(int(did)) in (True, False)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_ifa_secondary_gating_when_not_allowed(mock_get_type, mock_get_access, tmp_db):
    """All secondary draft methods should no-op when not watch-only/offline."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    assert tmp_db.add_ifa_secondary_draft_meta('X', None, None) is None
    assert tmp_db.attach_inflate_psbt_to_secondary_draft('X', 'p') is None
    assert tmp_db.list_ifa_secondary_drafts('X') == []
    assert tmp_db.get_ifa_secondary_draft_by_id(1) is None
    assert tmp_db.get_active_secondary_draft_for_asset('X') is None
    assert tmp_db.get_latest_active_secondary_draft() is None
    assert tmp_db.update_secondary_draft_psbt_id('a', 'b') is False
    assert tmp_db.delete_ifa_secondary_draft(1) is False
    assert tmp_db.delete_secondary_draft_by_psbt('x') is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_is_multisig_property(mock_get_sign_type, tmp_db):
    """is_multisig should return True when signature type is MULTI_SIG_WALLET."""
    mock_get_sign_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    assert tmp_db.is_multisig is True

    mock_get_sign_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    assert tmp_db.is_multisig is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_multisig_gated_paths(mock_get_sign, mock_get_type, mock_get_access, tmp_db):
    """Methods gated behind is_multisig should execute when signature type is MULTI_SIG_WALLET."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.MULTI_SIG_WALLET

    # add_psbt - multisig gated
    pid = tmp_db.add_psbt('multisig_psbt', signed=False, purpose='send_btc')
    assert pid is not None

    # upsert_draft_issue_asset - multisig gated
    tmp_db.upsert_draft_issue_asset(IssueAssetDraftModel(name='n', ticker='T', issued_amount=1, file_path=None))
    rows = tmp_db.list_draft_issue_assets()
    assert len(rows) == 1

    # add_ifa_secondary_draft_meta - multisig gated
    did = tmp_db.add_ifa_secondary_draft_meta('ASST', 'Name', 99)
    assert did is not None

    # set_active_secondary_draft - multisig gated (no-op path verification)
    tmp_db.set_active_secondary_draft(int(did), 'ASST')
    act = tmp_db.get_active_secondary_draft_for_asset('ASST')
    assert act and act['id'] == int(did)

    # get_latest_active_secondary_draft - multisig gated
    latest = tmp_db.get_latest_active_secondary_draft()
    assert latest and latest['asset_id'] == 'ASST'

    # delete_secondary_draft_by_psbt with asset_id path (no psbt_base64)
    result = tmp_db.delete_secondary_draft_by_psbt(asset_id='ASST')
    assert result is True


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_draft_transfer_crud(mock_get_sign, mock_get_type, mock_get_access, tmp_db):
    """upsert/get/delete draft_transfer should operate correctly when allowed."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET

    tmp_db.upsert_draft_transfer('ASSET_1', 'recip_123', 500, 1.5, 1)
    row = tmp_db.get_draft_transfer('ASSET_1')
    assert row is not None
    assert row['asset_id'] == 'ASSET_1'
    assert row['amount'] == 500
    assert abs(row['fee_rate'] - 1.5) < 0.001
    assert row['min_confirmation'] == 1

    # Missing asset_id should return None
    assert tmp_db.get_draft_transfer('MISSING') is None

    deleted = tmp_db.delete_draft_transfer('ASSET_1')
    assert deleted is True

    # After deletion, should be gone
    assert tmp_db.get_draft_transfer('ASSET_1') is None


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_draft_transfer_gating_when_not_allowed(mock_get_sign, mock_get_type, mock_get_access, tmp_db):
    """draft_transfer methods should no-op when not watch-only/offline/multisig."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET

    tmp_db.upsert_draft_transfer('ASSET_1', 'r', 1, 1.0, 1)
    assert tmp_db.get_draft_transfer('ASSET_1') is None
    assert tmp_db.delete_draft_transfer('ASSET_1') is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_delete_secondary_draft_by_psbt_both_none(mock_get_type, mock_get_access, tmp_db):
    """delete_secondary_draft_by_psbt returns False when both psbt_base64 and asset_id are None."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    assert tmp_db.delete_secondary_draft_by_psbt(None, None) is False


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_paths(mock_get_type, mock_get_access, tmp_db, mocker):
    """Methods should log and re-raise sqlite3.Error on failures."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_log = mocker.patch('src.data.service.wallet_data_service.logger')

    def fail_execute(*args, **kwargs):
        raise sqlite3.Error('forced')

    # get_ifa_secondary_draft_by_id error
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.get_ifa_secondary_draft_by_id(1)
    assert mock_log.error.called

    # Restore cursor for next checks
    mock_log.reset_mock()
    tmp_db.conn = sqlite3.connect(':memory:')
    tmp_db._create_tables()


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_add_ifa_secondary_draft(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """add_ifa_secondary_draft_meta should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.add_ifa_secondary_draft_meta('X', 'N', 1)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_upsert_draft_transfer(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """upsert_draft_transfer should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.upsert_draft_transfer('A', 'r', 1, 1.0, 1)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_get_draft_transfer(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """get_draft_transfer should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn    
    with pytest.raises(sqlite3.Error):
        tmp_db.get_draft_transfer('A')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_delete_draft_transfer(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """delete_draft_transfer should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.delete_draft_transfer('ASSET_1')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_upsert_draft_issue_asset(mock_get_type, mock_get_access, tmp_db, mocker):
    """upsert_draft_issue_asset should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.upsert_draft_issue_asset(IssueAssetDraftModel(name='n', ticker='T', issued_amount=1, file_path=None))


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_list_draft_issue_assets(mock_get_type, mock_get_access, tmp_db, mocker):
    """list_draft_issue_assets should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn    
    with pytest.raises(sqlite3.Error):
        tmp_db.list_draft_issue_assets()


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_delete_draft_issue_asset(mock_get_type, mock_get_access, tmp_db, mocker):
    """delete_draft_issue_asset should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.delete_draft_issue_asset(1)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_attach_inflate_psbt(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """attach_inflate_psbt_to_secondary_draft should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.attach_inflate_psbt_to_secondary_draft('ASSET', 'psbt')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_set_active_secondary_draft(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """set_active_secondary_draft should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.set_active_secondary_draft(1, 'ASSET')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_get_active_secondary_draft(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """get_active_secondary_draft_for_asset should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.get_active_secondary_draft_for_asset('ASSET')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_get_latest_active_secondary_draft(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """get_latest_active_secondary_draft should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.get_latest_active_secondary_draft()


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_delete_ifa_secondary_draft(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """delete_ifa_secondary_draft should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.delete_ifa_secondary_draft(1)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_sqlite_error_list_ifa_secondary_drafts(mock_get_sign, mock_get_type, mock_get_access, tmp_db, mocker):
    """list_ifa_secondary_drafts should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn    
    with pytest.raises(sqlite3.Error):
        tmp_db.list_ifa_secondary_drafts('ASSET')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_add_psbt(mock_get_type, mock_get_access, tmp_db, mocker):
    """add_psbt should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.add_psbt('psbt_content')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_mark_psbt_signed(mock_get_type, mock_get_access, tmp_db, mocker):
    """mark_psbt_signed should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.mark_psbt_signed('unsigned', 'signed')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_delete_psbt(mock_get_type, mock_get_access, tmp_db, mocker):
    """delete_psbt should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.delete_psbt('some_psbt')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_list_psbt(mock_get_type, mock_get_access, tmp_db, mocker):
    """list_psbt should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_cursor = mocker.MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("fail")

    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    tmp_db.conn = mock_conn 
    with pytest.raises(sqlite3.Error):
        tmp_db.list_psbt(False)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_update_secondary_draft_psbt_id(mock_get_type, mock_get_access, tmp_db, mocker):
    """update_secondary_draft_psbt_id should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.update_secondary_draft_psbt_id('old', 'new')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_sqlite_error_delete_secondary_draft_by_psbt(mock_get_type, mock_get_access, tmp_db, mocker):
    """delete_secondary_draft_by_psbt should log and re-raise on sqlite.Error."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mocker.patch('src.data.service.wallet_data_service.logger')
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("fail")
    tmp_db.conn = mock_conn
    with pytest.raises(sqlite3.Error):
        tmp_db.delete_secondary_draft_by_psbt('psbt_content')


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_signature_type')
def test_initialize_service_multisig_creates_db(mock_get_sign, mock_get_type, mock_get_access):
    """_initialize_service should create service when signature type is MULTI_SIG_WALLET."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_sign.return_value = WalletSignatureType.MULTI_SIG_WALLET
    with tempfile.TemporaryDirectory() as d:
        with patch('src.data.service.wallet_data_service.app_paths') as app_paths:
            app_paths.wallet_data_folder_path = d
            svc = WalletDataService._initialize_service()
            assert isinstance(svc, WalletDataService)


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_add_psbt_with_rgb_context(mock_get_type, mock_get_access, tmp_db):
    """add_psbt should store RGB context (fascia_path, entropy, min_confirmations)."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    pid = tmp_db.add_psbt(
        'rgb_psbt_base64',
        signed=False,
        purpose='send_asset',
        fascia_path='/path/to/app/fascia.rgb',
        entropy=123456789,
        min_confirmations=3,
    )
    assert pid is not None

    # Verify RGB context was stored
    rows = tmp_db.list_psbt(signed=False)
    assert len(rows) == 1
    assert rows[0]['fascia_path'] == '/path/to/app/fascia.rgb'
    assert rows[0]['entropy'] == 123456789
    assert rows[0]['min_confirmations'] == 3


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_get_psbt_rgb_context(mock_get_type, mock_get_access, tmp_db):
    """get_psbt_rgb_context should retrieve RGB context for a PSBT."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    # Add PSBT with RGB context
    tmp_db.add_psbt(
        'test_psbt_rgb',
        signed=False,
        purpose='send_asset',
        fascia_path='/app/data/fascia.rgb',
        entropy=999888777,
        min_confirmations=6,
    )

    # Retrieve RGB context
    ctx = tmp_db.get_psbt_rgb_context('test_psbt_rgb')
    assert ctx is not None
    assert ctx['fascia_path'] == '/app/data/fascia.rgb'
    assert ctx['entropy'] == 999888777
    assert ctx['min_confirmations'] == 6


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_get_psbt_rgb_context_not_found(mock_get_type, mock_get_access, tmp_db):
    """get_psbt_rgb_context should return None for missing PSBT."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    ctx = tmp_db.get_psbt_rgb_context('nonexistent_psbt')
    assert ctx is None


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_update_psbt_rgb_context(mock_get_type, mock_get_access, tmp_db):
    """update_psbt_rgb_context should update RGB context for existing PSBT."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    # Add PSBT without RGB context
    tmp_db.add_psbt('psbt_to_update', signed=False, purpose='send_asset')

    # Verify no context initially
    ctx = tmp_db.get_psbt_rgb_context('psbt_to_update')
    assert ctx is not None
    assert ctx['fascia_path'] is None

    # Update RGB context
    result = tmp_db.update_psbt_rgb_context(
        'psbt_to_update',
        fascia_path='/updated/path/fascia.rgb',
        entropy=111222333,
        min_confirmations=2,
    )
    assert result is True

    # Verify updated context
    ctx = tmp_db.get_psbt_rgb_context('psbt_to_update')
    assert ctx['fascia_path'] == '/updated/path/fascia.rgb'
    assert ctx['entropy'] == 111222333
    assert ctx['min_confirmations'] == 2


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_entropy_large_value_storage(mock_get_type, mock_get_access, tmp_db):
    """entropy should be stored as TEXT to handle large integer values."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    # Use a large entropy value that would overflow INTEGER
    large_entropy = 9223372036854775807  # Max int64

    tmp_db.add_psbt(
        'large_entropy_psbt',
        signed=False,
        purpose='send_asset',
        fascia_path='/path/fascia.rgb',
        entropy=large_entropy,
        min_confirmations=1,
    )

    # Retrieve and verify
    ctx = tmp_db.get_psbt_rgb_context('large_entropy_psbt')
    assert ctx['entropy'] == large_entropy


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_entropy_zero_value(mock_get_type, mock_get_access, tmp_db):
    """entropy should handle zero value correctly."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    tmp_db.add_psbt(
        'zero_entropy_psbt',
        signed=False,
        purpose='send_asset',
        fascia_path='/path/fascia.rgb',
        entropy=0,
        min_confirmations=1,
    )

    ctx = tmp_db.get_psbt_rgb_context('zero_entropy_psbt')
    assert ctx['entropy'] == 0


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_entropy_none_value(mock_get_type, mock_get_access, tmp_db):
    """entropy should handle None value correctly."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    tmp_db.add_psbt(
        'none_entropy_psbt',
        signed=False,
        purpose='send_asset',
        fascia_path='/path/fascia.rgb',
        entropy=None,
        min_confirmations=1,
    )

    ctx = tmp_db.get_psbt_rgb_context('none_entropy_psbt')
    assert ctx['entropy'] is None


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_mark_psbt_signed_preserves_rgb_context(mock_get_type, mock_get_access, tmp_db):
    """mark_psbt_signed should preserve RGB context when signing."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    # Add unsigned PSBT with RGB context
    tmp_db.add_psbt(
        'unsigned_rgb_psbt',
        signed=False,
        purpose='send_asset',
        fascia_path='/original/fascia.rgb',
        entropy=444555666,
        min_confirmations=3,
    )

    # Sign the PSBT
    signed_id = tmp_db.mark_psbt_signed('unsigned_rgb_psbt', 'signed_rgb_psbt')
    assert signed_id is not None

    # Verify RGB context was preserved
    ctx = tmp_db.get_psbt_rgb_context('signed_rgb_psbt')
    assert ctx is not None
    assert ctx['fascia_path'] == '/original/fascia.rgb'
    assert ctx['entropy'] == 444555666
    assert ctx['min_confirmations'] == 3


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_list_psbt_includes_rgb_context(mock_get_type, mock_get_access, tmp_db):
    """list_psbt should include RGB context fields."""
    mock_get_access.return_value = WalletAccessType.WATCH_ONLY
    mock_get_type.return_value = WalletType.OFFLINE_TYPE_WALLET

    tmp_db.add_psbt(
        'list_rgb_psbt',
        signed=False,
        purpose='send_asset',
        fascia_path='/list/fascia.rgb',
        entropy=777888999,
        min_confirmations=5,
    )

    rows = tmp_db.list_psbt(signed=False)
    assert len(rows) == 1
    assert rows[0]['fascia_path'] == '/list/fascia.rgb'
    assert rows[0]['entropy'] == 777888999
    assert rows[0]['min_confirmations'] == 5


@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_access_type')
@patch('src.data.service.wallet_data_service.SettingRepository.get_wallet_type')
def test_rgb_context_gating_when_not_allowed(mock_get_type, mock_get_access, tmp_db):
    """RGB context methods should be gated when not watch-only/offline/multisig."""
    mock_get_access.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_type.return_value = WalletType.ONLINE_TYPE_WALLET

    # get_psbt_rgb_context should return None
    assert tmp_db.get_psbt_rgb_context('any_psbt') is None

    # update_psbt_rgb_context should return False
    assert tmp_db.update_psbt_rgb_context('any_psbt', '/path', 123, 1) is False

