"""
A thread-safe wallet data manager using SQLite for storing and managing wallet state.

This module provides a `WalletDataService` class with functionality to store,
retrieve, and update wallet-related data such as PSBTs, balances, transactions,
and UTXOs. It uses SQLite as the backend and ensures thread safety with locks
for concurrent access.

Key Features:
- Thread-safe access to wallet database.
- Stores balances, transactions, and unspents.
- Singleton instance for watch-only and offline wallet types only.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import sqlite3
import threading
import time

from rgb_lib import Balance
from rgb_lib import BtcBalance
from rgb_lib import Transaction
from rgb_lib import Unspent

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentsListResponseModel
from src.model.common_operation_model import IssueAssetDraftModel
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.build_app_path import app_paths
from src.utils.constant import BALANCE_KEY
from src.utils.constant import DB_FILE_NAME
from src.utils.constant import TRANSACTIONS_KEY
from src.utils.constant import UNSPENTS_KEY
from src.utils.logging import logger


class WalletDataService:
    """Custom wallet data manager using SQLite to store and manage wallet information."""

    _instance: WalletDataService | None = None
    _lock = threading.Lock()

    def __init__(self, db_path: str):
        """
        Initialize the WalletDataService object.

        Args:
            db_path (str): The full path to the SQLite database file.
        """
        super().__init__()
        self.db_path = db_path
        self._db_lock = threading.Lock()
        self.conn: sqlite3.Connection = self._connect_db()
        self._create_tables()

    @property
    def is_watch_only(self) -> bool:
        """Return True if wallet is watch-only."""
        return SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY

    @property
    def is_offline_wallet(self) -> bool:
        """Return True if wallet is offline."""
        return SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET

    @property
    def is_multisig(self) -> bool:
        """Return True if wallet is multisig."""
        return SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET

    @staticmethod
    def _initialize_service() -> WalletDataService | None:
        """
        Create and return a WalletDataService instance if the wallet type supports it.

        Returns:
            WalletDataService | None: Instance if supported, None otherwise.
        """
        try:
            access_type = SettingRepository.get_wallet_access_type()
            wallet_type = SettingRepository.get_wallet_type()
            sign_type = SettingRepository.get_wallet_signature_type()
            if access_type == WalletAccessType.WATCH_ONLY or wallet_type == WalletType.OFFLINE_TYPE_WALLET or sign_type == WalletSignatureType.MULTI_SIG_WALLET:
                if not os.path.exists(app_paths.wallet_data_folder_path):
                    os.makedirs(
                        app_paths.wallet_data_folder_path,
                        exist_ok=True,
                    )

                db_path = os.path.join(
                    app_paths.wallet_data_folder_path, DB_FILE_NAME,
                )
                return WalletDataService(db_path=db_path)
            return None

        except Exception as exc:
            logger.error(
                'Exception occurred in WalletDataService: %s, Message: %s',
                type(exc).__name__, str(exc),
            )

        return None

    def _connect_db(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )
            logger.info('Wallet database connection established.')
            return conn
        except sqlite3.Error as e:
            logger.error('Failed to connect to wallet database: %s', e)
            raise

    def _create_tables(self) -> None:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS data (
            key TEXT PRIMARY KEY,
            data BLOB NOT NULL,
            updated_at INTEGER
        )
        """
        create_psbt_table_query = """
        CREATE TABLE IF NOT EXISTS psbt (
            id TEXT PRIMARY KEY,           -- sha256 of PSBT base64
            psbt TEXT NOT NULL,            -- PSBT in base64
            signed INTEGER NOT NULL,       -- 0 = unsigned, 1 = signed
            purpose TEXT                   -- optional context e.g. 'issue_asset', 'send_btc', 'send_asset', 'inflate_asset'
        )
        """
        create_draft_issue_asset_table_query = """
        CREATE TABLE IF NOT EXISTS draft_issue_asset (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            ticker TEXT NOT NULL,
            issued_amount INTEGER NOT NULL,
            file_path TEXT,
            inflation_amounts INTEGER
        )
        """
        create_ifa_secondary_draft_table_query = """
        CREATE TABLE IF NOT EXISTS ifa_secondary_draft (
            id INTEGER PRIMARY KEY,
            asset_id TEXT NOT NULL,
            asset_name TEXT,
            amount INTEGER,
            psbt_id TEXT UNIQUE,
            active_utxo INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """
        create_draft_transfer_table_query = """
        CREATE TABLE IF NOT EXISTS draft_transfer (
            asset_id TEXT PRIMARY KEY,
            recipient_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            fee_rate INTEGER NOT NULL,
            min_confirmation INTEGER NOT NULL,
            created_at INTEGER
        )
        """
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(create_table_query)
                    self.conn.execute(create_psbt_table_query)
                    self.conn.execute(create_draft_issue_asset_table_query)
                    self.conn.execute(create_ifa_secondary_draft_table_query)
                    self.conn.execute(create_draft_transfer_table_query)
            except sqlite3.Error as exc:
                logger.error(
                    'Exception occur in wallet-data: %s, Message: %s', type(
                        exc,
                    ).__name__, str(exc),
                )
                raise

    def get_ifa_secondary_draft_by_id(self, draft_id: int) -> dict | None:
        """
        Get a secondary draft by ID.
        """
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    'SELECT id, asset_id, asset_name, amount, psbt_id, active_utxo, created_at FROM ifa_secondary_draft WHERE id = ? LIMIT 1',
                    (draft_id,),
                )
                r = cur.fetchone()
                if not r:
                    return None
                return {
                    'id': r[0], 'asset_id': r[1], 'asset_name': r[2], 'amount': r[3], 'psbt_id': r[4], 'active_utxo': int(r[5]), 'created_at': r[6],
                }
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: get_ifa_secondary_draft_by_id failed: %s', exc,
                )
                raise

    def refresh_wallet_data(self) -> None:
        """Fetch & persist latest wallet data (only for ONLINE wallets)."""
        try:
            if not self.is_watch_only:
                return

            # Fetch latest from repositories
            balance_resp: BtcBalance = colored_wallet.wallet.get_btc_balance(
                online=colored_wallet.online, skip_sync=False,
            )
            tx_list_resp: list[Transaction] = colored_wallet.wallet.list_transactions(
                online=colored_wallet.online, skip_sync=False,
            )
            unspents_resp: list[Unspent] = colored_wallet.wallet.list_unspents(
                online=colored_wallet.online, settled_only=False, skip_sync=False,
            )

            with self._db_lock:
                cur = self.conn.cursor()
                now_ts = int(time.time())
                # Insert/replace rows in data table
                for key, value in [
                    (BALANCE_KEY, balance_resp),
                    (TRANSACTIONS_KEY, tx_list_resp),
                    (UNSPENTS_KEY, unspents_resp),
                ]:
                    cur.execute(
                        'INSERT OR REPLACE INTO data (key, data, updated_at) VALUES (?, ?, ?)',
                        (key, pickle.dumps(value), now_ts),
                    )
                self.conn.commit()

            logger.info('WalletDataService: wallet-data refreshed')

        except Exception as exc:
            logger.error(
                'WalletDataService: failed to refresh wallet-data: %s', exc,
            )
            raise

    def upsert_draft_transfer(self, asset_id: str, recipient_id: str, amount: int, fee_rate: float, min_confirmation: int) -> None:
        """Insert or replace a draft transfer row."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(
                        'INSERT OR REPLACE INTO draft_transfer (asset_id, recipient_id, amount, fee_rate, min_confirmation) VALUES (?, ?, ?, ?, ?)',
                        (asset_id, recipient_id, amount, fee_rate, min_confirmation),
                    )
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: upsert_draft_transfer failed: %s', exc,
                )
                raise

    def get_draft_transfer(self, asset_id: str) -> dict | None:
        """Get a draft transfer by asset ID."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    'SELECT asset_id, recipient_id, amount, fee_rate, min_confirmation FROM draft_transfer WHERE asset_id = ?',
                    (asset_id,),
                )
                r = cur.fetchone()
                if not r:
                    return None
                return {
                    'asset_id': r[0],
                    'recipient_id': r[1],
                    'amount': int(r[2]),
                    'fee_rate': float(r[3]),
                    'min_confirmation': int(r[4]),
                }
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: get_draft_transfer failed: %s', exc,
                )
                raise

    def delete_draft_transfer(self, asset_id: str) -> bool:
        """Delete a draft transfer by asset ID."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return False
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'DELETE FROM draft_transfer WHERE asset_id = ?', (
                            asset_id,
                        ),
                    )
                return cur.rowcount > 0
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: delete_draft_transfer failed: %s', exc,
                )
                raise

    def upsert_draft_issue_asset(self, issue_asset_draft_model: IssueAssetDraftModel) -> None:
        """Insert or replace a draft issue asset row."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return
        with self._db_lock:
            try:
                # Use a transaction so the insert is committed and survives app restarts
                with self.conn:
                    self.conn.execute(
                        'INSERT INTO draft_issue_asset (name, ticker, issued_amount, file_path, inflation_amounts) VALUES (?, ?, ?, ?, ?)',
                        (
                            issue_asset_draft_model.name, issue_asset_draft_model.ticker, int(
                                issue_asset_draft_model.issued_amount,
                            ), issue_asset_draft_model.file_path,
                            issue_asset_draft_model.inflation_amounts,
                        ),
                    )
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: upsert_draft_issue_asset failed: %s', exc,
                )
                raise

    def list_draft_issue_assets(self) -> list[dict]:
        """Return all draft issue assets with minimal metadata."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return []
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    'SELECT id, name, ticker, issued_amount, file_path, inflation_amounts, replace_rights_num FROM draft_issue_asset ORDER BY id DESC',
                )
                rows = cur.fetchall()
                return [
                    {
                        'id': r[0],
                        'name': r[1],
                        'ticker': r[2],
                        'issued_amount': int(r[3]),
                        'file_path': r[4],
                        'inflation_amounts': r[5],
                        'replace_rights_num': r[6],
                    }
                    for r in rows
                ]
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: list_draft_issue_assets failed: %s', exc,
                )
                raise

    def delete_draft_issue_asset(self, draft_id: str) -> bool:
        """Delete a draft issue asset row by ID."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return False
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(
                        'DELETE FROM draft_issue_asset WHERE id = ?', (
                            draft_id,
                        ),
                    )
                return True
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: delete_draft_issue_asset failed: %s', exc,
                )
                raise

    def _fetch_data(self, key: str):
        """Get unpickled data for given key, or None if missing."""
        with self._db_lock:
            cur = self.conn.cursor()
            cur.execute('SELECT data FROM data WHERE key = ?', (key,))
            row = cur.fetchone()
            if not row:
                return None
            try:
                return pickle.loads(row[0])
            except Exception as exc:
                logger.error(
                    'WalletDataService: failed to unpickle %s: %s', key, exc,
                )
                return None

    def get_btc_balance(self) -> BalanceResponseModel:
        """Get the current balance of the wallet."""
        data = self._fetch_data(BALANCE_KEY)
        if data is not None:
            return BalanceResponseModel(vanilla=data.vanilla, colored=data.colored)
        default_balance = Balance(settled=0, future=0, spendable=0)
        return BalanceResponseModel(vanilla=default_balance, colored=default_balance)

    def list_transactions(self) -> TransactionListResponse:
        """Get the list of transactions."""
        data = self._fetch_data(TRANSACTIONS_KEY)
        if data is not None:
            return TransactionListResponse(transactions=data)
        return TransactionListResponse(transactions=[])

    def list_unspents(self) -> UnspentsListResponseModel:
        """Get the list of unspent outputs."""
        data = self._fetch_data(UNSPENTS_KEY)
        if data is not None:
            return UnspentsListResponseModel(unspents=data)
        return UnspentsListResponseModel(unspents=[])

    # -------- Secondary issuance drafts (IFA inflate) --------
    def add_ifa_secondary_draft_meta(self, asset_id: str, asset_name: str | None, amount: int | None) -> int | None:
        """Add a secondary draft meta."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'INSERT INTO ifa_secondary_draft (asset_id, asset_name, amount, psbt_id, active_utxo, created_at) VALUES (?, ?, ?, NULL, 1, ?)',
                        (asset_id, asset_name, amount, int(time.time())),
                    )
                    return cur.lastrowid
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: add_ifa_secondary_draft_meta failed: %s', exc,
                )
                raise

    def attach_inflate_psbt_to_secondary_draft(self, asset_id: str, psbt_base64: str) -> str | None:
        """Attach a PSBT to a secondary draft."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        psbt_id = self._psbt_id(psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    # Attach to latest draft for this asset (prefer active one)
                    cur = self.conn.execute(
                        'SELECT id FROM ifa_secondary_draft WHERE asset_id = ? ORDER BY active_utxo DESC, created_at DESC, id DESC LIMIT 1',
                        (asset_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    self.conn.execute(
                        'UPDATE ifa_secondary_draft SET psbt_id = ? WHERE id = ?',
                        (psbt_id, row[0]),
                    )
                return psbt_id
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: attach_inflate_psbt_to_secondary_draft failed: %s', exc,
                )
                raise

    def list_ifa_secondary_drafts(self, asset_id: str) -> list[dict]:
        """List all secondary drafts for a given asset."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return []
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    '''SELECT id, asset_id, asset_name, amount, psbt_id, active_utxo,
                    created_at FROM ifa_secondary_draft WHERE asset_id = ? ORDER BY created_at DESC, id DESC''',
                    (asset_id,),
                )
                rows = cur.fetchall()
                return [
                    {
                        'id': r[0], 'asset_id': r[1], 'asset_name': r[2], 'amount': r[3], 'psbt_id': r[4], 'active_utxo': int(r[5]), 'created_at': r[6],
                    }
                    for r in rows
                ]
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: list_ifa_secondary_drafts failed: %s', exc,
                )
                raise

    def set_active_secondary_draft(self, draft_id: int, asset_id: str) -> None:
        """Set a secondary draft as active."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(
                        'UPDATE ifa_secondary_draft SET active_utxo = 0 WHERE asset_id = ?', (
                            asset_id,
                        ),
                    )
                    self.conn.execute(
                        'UPDATE ifa_secondary_draft SET active_utxo = 1 WHERE id = ?', (
                            draft_id,
                        ),
                    )
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: set_active_secondary_draft failed: %s', exc,
                )
                raise

    def get_active_secondary_draft_for_asset(self, asset_id: str) -> dict | None:
        """Get the active secondary draft for a given asset."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    '''SELECT id, asset_id, asset_name, amount, psbt_id, active_utxo,
                    created_at FROM ifa_secondary_draft WHERE asset_id = ? AND active_utxo = 1 ORDER BY created_at DESC, id DESC LIMIT 1''',
                    (asset_id,),
                )
                r = cur.fetchone()
                if not r:
                    return None
                return {
                    'id': r[0], 'asset_id': r[1], 'asset_name': r[2], 'amount': r[3], 'psbt_id': r[4], 'active_utxo': int(r[5]), 'created_at': r[6],
                }
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: get_active_secondary_draft_for_asset failed: %s', exc,
                )
                raise

    def get_latest_active_secondary_draft(self) -> dict | None:
        """Get the most recent active secondary draft across all assets, if any."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return None
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    '''SELECT id, asset_id, asset_name, amount, psbt_id, active_utxo,
                    created_at FROM ifa_secondary_draft WHERE active_utxo = 1 ORDER BY created_at DESC, id DESC LIMIT 1''',
                )
                r = cur.fetchone()
                if not r:
                    return None
                return {
                    'id': r[0], 'asset_id': r[1], 'asset_name': r[2], 'amount': r[3], 'psbt_id': r[4], 'active_utxo': int(r[5]), 'created_at': r[6],
                }
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: get_latest_active_secondary_draft failed: %s', exc,
                )
                raise

    def delete_ifa_secondary_draft(self, draft_id: int) -> bool:
        """Delete a secondary draft by its ID."""
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return False
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'DELETE FROM ifa_secondary_draft WHERE id = ?', (
                            draft_id,
                        ),
                    )
                return cur.rowcount > 0
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: delete_ifa_secondary_draft failed: %s', exc,
                )
                raise

    def delete_secondary_draft_by_psbt(self, psbt_base64: str) -> bool:
        """Delete secondary issuance draft row by attached psbt content (unsigned/signed base64).
        Returns True if a row was deleted.
        """
        if not (self.is_watch_only or self.is_offline_wallet or self.is_multisig):
            return False
        psbt_id = self._psbt_id(psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'DELETE FROM ifa_secondary_draft WHERE psbt_id = ?', (
                            psbt_id,
                        ),
                    )
                return cur.rowcount > 0
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: delete_secondary_draft_by_psbt failed: %s', exc,
                )
                raise

    def update_secondary_draft_psbt_id(self, old_psbt_base64: str, new_psbt_base64: str) -> bool:
        """If a secondary draft is anchored to the unsigned psbt id, switch it to the signed psbt id.
        Returns True if a row was updated.
        """
        if not (self.is_watch_only or self.is_offline_wallet):
            return False
        old_id = self._psbt_id(old_psbt_base64)
        new_id = self._psbt_id(new_psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'UPDATE ifa_secondary_draft SET psbt_id = ? WHERE psbt_id = ?',
                        (new_id, old_id),
                    )
                return cur.rowcount > 0
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: update_secondary_draft_psbt_id failed: %s', exc,
                )
                raise

    @staticmethod
    def _psbt_id(psbt_base64: str) -> str:
        """Deterministic id for a PSBT payload (sha256 of normalized base64 string)."""
        # Normalize: remote whitespace to ensure consistent ID
        normalized = ''.join(psbt_base64.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def add_psbt(
        self,
        psbt_base64: str,
        signed: bool = False,
        purpose: str | None = None,
    ) -> str | None:
        """Insert or replace a PSBT. Returns its id. Minimal fields only.
        Optionally set a purpose (e.g., 'send_btc', 'create_utxos', 'issue_asset').
        """
        if self.is_watch_only or self.is_offline_wallet or self.is_multisig:
            # Also store the normalized version to match the ID
            normalized_psbt = ''.join(psbt_base64.split())
            psbt_id = self._psbt_id(normalized_psbt)
            with self._db_lock:
                try:
                    with self.conn:
                        self.conn.execute(
                            'INSERT OR REPLACE INTO psbt (id, psbt, signed, purpose) VALUES (?, ?, ?, ?)',
                            (psbt_id, normalized_psbt, 1 if signed else 0, purpose),
                        )
                    return psbt_id
                except sqlite3.Error as exc:
                    logger.error('WalletDataService: add_psbt failed: %s', exc)
                    raise
        return None

    def mark_psbt_signed(self, unsigned_psbt_base64: str, signed_psbt_base64: str) -> str | None:
        """Replace an unsigned PSBT with its signed version.
        Deletes only that unsigned PSBT and inserts the signed one.
        Returns the new signed PSBT id.
        """
        if self.is_watch_only or self.is_offline_wallet or self.is_multisig:
            unsigned_id = self._psbt_id(unsigned_psbt_base64)
            normalized_signed_psbt = ''.join((signed_psbt_base64 or '').split())
            signed_id = self._psbt_id(normalized_signed_psbt)
            with self._db_lock:
                try:
                    with self.conn:
                        cur = self.conn.execute(
                            'SELECT purpose FROM psbt WHERE id = ?', (
                                unsigned_id,
                            ),
                        )
                        row = cur.fetchone()
                        purpose = row[0] if row is not None else None
                        self.conn.execute(
                            'DELETE FROM psbt WHERE id = ?', (unsigned_id,),
                        )
                        self.conn.execute(
                            'INSERT OR REPLACE INTO psbt (id, psbt, signed, purpose) VALUES (?, ?, ?, ?)',
                            (signed_id, normalized_signed_psbt, 1, purpose),
                        )
                    return signed_id
                except sqlite3.Error as exc:
                    logger.error(
                        'WalletDataService: mark_psbt_signed failed: %s', exc,
                    )
                    raise
        return None

    def delete_psbt(self, psbt_base64: str) -> bool:
        """Delete only the targeted PSBT (by content).
        Returns True if a row was deleted.
        """
        if self.is_watch_only or self.is_offline_wallet:
            psbt_id = self._psbt_id(psbt_base64)
            with self._db_lock:
                try:
                    with self.conn:
                        cur = self.conn.execute(
                            'DELETE FROM psbt WHERE id = ?', (psbt_id,),
                        )
                    return cur.rowcount > 0
                except sqlite3.Error as exc:
                    logger.error(
                        'WalletDataService: delete_psbt failed: %s', exc,
                    )
                    raise
        return False

    def list_psbt(self, signed: bool) -> list[dict]:
        """List psbt with optional signed filter. Returns minimal info (including purpose)."""
        if self.is_watch_only or self.is_offline_wallet:
            with self._db_lock:
                try:
                    cur = self.conn.cursor()
                    cur.execute(
                        'SELECT id, psbt, signed, purpose FROM psbt WHERE signed = ?',
                        (1 if signed else 0,),
                    )
                    rows = cur.fetchall()
                    return [
                        {
                            'id': r[0],
                            'psbt': r[1],
                            'signed': bool(r[2]),
                            'purpose': r[3] if len(r) > 3 else None,
                        }
                        for r in rows
                    ]
                except sqlite3.Error as exc:
                    logger.error(
                        'WalletDataService: list_psbt failed: %s', exc,
                    )
                    raise
        return []

    @staticmethod
    def get_session() -> WalletDataService | None:
        """
        Returns the singleton instance of WalletDataService in a thread-safe manner.

        Returns:
            WalletDataService | None: The singleton instance of the service if supported.
        """
        if WalletDataService._instance is None:
            with WalletDataService._lock:
                if WalletDataService._instance is None:
                    WalletDataService._instance = WalletDataService._initialize_service()
        return WalletDataService._instance
