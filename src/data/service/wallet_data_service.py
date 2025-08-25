"""
Service to persist frequently requested wallet data into an on-disk SQLite DB
inside the `wallet-data/` folder. This DB is populated only for ONLINE wallets
before syncing wallet -> USB, so the offline wallet can later read it.
"""
from __future__ import annotations

import os
import pickle
import sqlite3
import threading
import time

from src.data.repository.btc_repository import BtcRepository
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
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(create_table_query)
                    logger.info('Wallet-data table ensured to exist.')
            except sqlite3.Error as exc:
                logger.error(
                    'Exception occur in wallet-data: %s, Message: %s', type(
                        exc).__name__, str(exc),
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
            balance_resp = BtcRepository.get_btc_balance()
            tx_list_resp = BtcRepository.list_transactions()
            unspents_resp = BtcRepository.list_unspents(
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
        return self._fetch_data(self.BALANCE_KEY)

    def list_transactions(self) -> TransactionListResponse:
        return self._fetch_data(self.TRANSACTIONS_KEY)

    def list_unspents(self) -> UnspentsListResponseModel:
        return self._fetch_data(self.UNSPENTS_KEY)


# Global accessor for singleton instance
wallet_data_service = WalletDataService()
