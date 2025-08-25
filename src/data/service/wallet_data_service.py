"""
Service to persist frequently requested wallet data into an on-disk SQLite DB
inside the `wallet-data/` folder. This DB is populated only for ONLINE wallets
before syncing wallet -> USB, so the offline wallet can later read it.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import sqlite3
import threading
import time

from rgb_lib import Balance

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel
from src.model.enums.enums_model import WalletAccessType
from src.utils.build_app_path import app_paths
from src.utils.logging import logger


class WalletDataService:
    """Singleton service for managing wallet-data SQLite DB (balance, tx, unspents)."""

    _instance: WalletDataService | None = None
    _db_lock = threading.Lock()

    DB_FILE_NAME = 'wallet.db'
    BALANCE_KEY = 'balance'
    TRANSACTIONS_KEY = 'transactions'
    UNSPENTS_KEY = 'unspents'

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize persistent DB connection and ensure schema (like Cache)."""
        self._db_path = os.path.join(
            app_paths.wallet_data_folder_path, self.DB_FILE_NAME,
        )
        if not os.path.exists(app_paths.wallet_data_folder_path):
            os.makedirs(app_paths.wallet_data_folder_path, exist_ok=True)
        self.conn: sqlite3.Connection = self._connect_db()
        self._create_tables()

    def _connect_db(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            logger.info('Database connection established.')
            return conn
        except sqlite3.Error as e:
            logger.error('Failed to connect to database: %s', e)
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
            signed INTEGER NOT NULL        -- 0 = unsigned, 1 = signed
        )
        """
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(create_table_query)
                    self.conn.execute(create_psbt_table_query)
                    # Migrate legacy psbt table that had created_at column
                    try:
                        cur = self.conn.execute('PRAGMA table_info(psbt)')
                        cols = [r[1] for r in cur.fetchall()]
                        if 'created_at' in cols:
                            # Perform migration to drop created_at
                            self.conn.execute(
                                'CREATE TABLE IF NOT EXISTS psbt_new (id TEXT PRIMARY KEY, psbt TEXT NOT NULL, signed INTEGER NOT NULL)',
                            )
                            self.conn.execute(
                                'INSERT OR REPLACE INTO psbt_new (id, psbt, signed) SELECT id, psbt, signed FROM psbt',
                            )
                            self.conn.execute('DROP TABLE psbt')
                            self.conn.execute(
                                'ALTER TABLE psbt_new RENAME TO psbt',
                            )
                    except sqlite3.Error:
                        # If pragma fails, ignore; table will be used as-is
                        pass
                    logger.info('Wallet-data table ensured to exist.')
            except sqlite3.Error as exc:
                logger.error(
                    'Exception occur in wallet-data: %s, Message: %s', type(
                        exc,
                    ).__name__, str(exc),
                )
                raise

    def _ensure_dir_and_db(self) -> None:
        """Ensure folder and table exist (idempotent)."""
        if not os.path.exists(app_paths.wallet_data_folder_path):
            os.makedirs(app_paths.wallet_data_folder_path, exist_ok=True)
        self._create_tables()

    def refresh_wallet_data(self) -> None:
        """Fetch & persist latest wallet data (only for ONLINE wallets)."""
        try:
            if SettingRepository.get_wallet_access_type() != WalletAccessType.WATCH_ONLY:
                return

            self._ensure_dir_and_db()

            # Fetch latest from repositories
            balance_resp = colored_wallet.wallet.get_btc_balance()
            tx_list_resp = colored_wallet.wallet.list_transactions()
            unspents_resp = colored_wallet.wallet.list_unspents(
                UnspentListRequestModel(settled_only=False, skip_sync=False),
            )

            with self._db_lock:
                cur = self.conn.cursor()
                now_ts = int(time.time())
                # Insert/replace rows in data table
                for key, value in [
                    (self.BALANCE_KEY, balance_resp),
                    (self.TRANSACTIONS_KEY, tx_list_resp),
                    (self.UNSPENTS_KEY, unspents_resp),
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

    def _fetch_data(self, key: str):
        """Get unpickled data for given key, or None if missing."""
        self._ensure_dir_and_db()
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
        data = self._fetch_data(self.BALANCE_KEY)
        if data is not None:
            return data
        default_balance = Balance(settled=0, future=0, spendable=0)
        return BalanceResponseModel(vanilla=default_balance, colored=default_balance)

    def list_transactions(self) -> TransactionListResponse:
        data = self._fetch_data(self.TRANSACTIONS_KEY)
        if data is not None:
            return data
        return TransactionListResponse(transactions=[])

    def list_unspents(self) -> UnspentsListResponseModel:
        data = self._fetch_data(self.UNSPENTS_KEY)
        if data is not None:
            return data
        return UnspentsListResponseModel(unspents=[])

    @staticmethod
    def _psbt_id(psbt_base64: str) -> str:
        """Deterministic id for a PSBT payload (sha256 of base64 string)."""
        return hashlib.sha256(psbt_base64.encode('utf-8')).hexdigest()

    def add_psbt(self, psbt_base64: str, signed: bool = False) -> str:
        """Insert or replace a PSBT. Returns its id. Minimal fields only."""
        self._ensure_dir_and_db()
        psbt_id = self._psbt_id(psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(
                        'INSERT OR REPLACE INTO psbt (id, psbt, signed) VALUES (?, ?, ?)',
                        (psbt_id, psbt_base64, 1 if signed else 0),
                    )
                return psbt_id
            except sqlite3.Error as exc:
                logger.error('WalletDataService: add_psbt failed: %s', exc)
                raise

    def mark_psbt_signed(self, unsigned_psbt_base64: str, signed_psbt_base64: str) -> str:
        """Replace an unsigned PSBT with its signed version.
        Deletes only that unsigned PSBT and inserts the signed one.
        Returns the new signed PSBT id.
        """
        self._ensure_dir_and_db()
        unsigned_id = self._psbt_id(unsigned_psbt_base64)
        signed_id = self._psbt_id(signed_psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(
                        'DELETE FROM psbt WHERE id = ?', (unsigned_id,),
                    )
                    self.conn.execute(
                        'INSERT OR REPLACE INTO psbt (id, psbt, signed) VALUES (?, ?, ?)',
                        (signed_id, signed_psbt_base64, 1),
                    )
                return signed_id
            except sqlite3.Error as exc:
                logger.error(
                    'WalletDataService: mark_psbt_signed failed: %s', exc,
                )
                raise

    def delete_psbt(self, psbt_base64: str) -> bool:
        """Delete only the targeted PSBT (by content).
        Returns True if a row was deleted.
        """
        self._ensure_dir_and_db()
        psbt_id = self._psbt_id(psbt_base64)
        with self._db_lock:
            try:
                with self.conn:
                    cur = self.conn.execute(
                        'DELETE FROM psbt WHERE id = ?', (psbt_id,),
                    )
                return cur.rowcount > 0
            except sqlite3.Error as exc:
                logger.error('WalletDataService: delete_psbt failed: %s', exc)
                raise

    def list_psbts(self, signed: bool | None = None) -> list[dict]:
        """List psbt with optional signed filter. Returns minimal info."""
        self._ensure_dir_and_db()
        with self._db_lock:
            try:
                cur = self.conn.cursor()
                if signed is None:
                    cur.execute('SELECT id, psbt, signed FROM psbt')
                else:
                    cur.execute(
                        'SELECT id, psbt, signed FROM psbt WHERE signed = ?',
                        (1 if signed else 0,),
                    )
                rows = cur.fetchall()
                return [
                    {
                        'id': r[0],
                        'psbt': r[1],
                        'signed': bool(r[2]),
                    }
                    for r in rows
                ]
            except sqlite3.Error as exc:
                logger.error('WalletDataService: list_psbts failed: %s', exc)
                raise


# Global accessor for singleton instance
wallet_data_service = WalletDataService()
