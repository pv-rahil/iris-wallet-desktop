"""
A thread-safe cache manager using SQLite for storing and managing cached data.

This module provides a `Cache` class with functionality to store, retrieve,
invalidate, and handle cache expiration. It uses SQLite as the backend and
ensures thread safety with locks for concurrent access.

Key Features:
- Cache expiration and invalidation.
- Thread-safe access to cache.
- Singleton instance for cache management.
"""
from __future__ import annotations

import os
import pickle
import sqlite3
import threading
import time
from typing import Any

from PySide6.QtCore import QCoreApplication

import src.flavour as bitcoin_network
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.build_app_path import app_paths
from src.utils.constant import CACHE_EXPIRE_TIMEOUT
from src.utils.constant import CACHE_FILE_NAME
from src.utils.constant import DEFAULT_CACHE_FILENAME
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.error_mapping import ERROR_MAPPING
from src.utils.global_toast import global_toaster
from src.utils.local_store import local_store
from src.utils.logging import logger


class Cache:
    """Custom cache manager using SQLite to store and manage cached data."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_name: str = 'cache.sqlite', expire_after: int = CACHE_EXPIRE_TIMEOUT, file_path: str | None = None):
        """
        Initialize the Cache object.

        Args:
            db_name (str): The name of the SQLite database file.
            expire_after (int): Cache expiration timeout in seconds.
            file_path (str): Full path to the SQLite database file.
        """
        super().__init__()
        self.db_name = db_name
        self.expire_after = expire_after
        if file_path is not None:
            self.cache_file_path = file_path
        self._db_lock = threading.Lock()
        self._error_lock = threading.Lock()
        self.is_error: bool = False
        self.conn: sqlite3.Connection = self._connect_db()
        self._create_table()

    @staticmethod
    def _initialize_cache() -> Cache | None:
        """
        Create and return a Cache instance with retry mechanism.

        Returns:
            Cache: A Cache instance if successful, None if all attempts fail.
        """
        try:
            current_network = NetworkEnumModel(bitcoin_network.__network__)
            file_name = f"{
                CACHE_FILE_NAME.get(
                    current_network, DEFAULT_CACHE_FILENAME
                )
            }.sqlite"
            cache_dir_path = app_paths.cache_path

            if not os.path.exists(cache_dir_path):
                local_store.create_folder(cache_dir_path)

            full_cache_file_path = os.path.join(cache_dir_path, file_name)
            return Cache(db_name=file_name, expire_after=CACHE_EXPIRE_TIMEOUT, file_path=full_cache_file_path)

        except Exception as exc:
            logger.error(
                'Exception occurred in cache: %s, Message: %s',
                type(exc).__name__, str(exc),
            )

        return None

    def _connect_db(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        try:
            conn = sqlite3.connect(
                self.cache_file_path,
                check_same_thread=False,
            )
            logger.info('Database connection established.')
            return conn
        except sqlite3.Error as e:
            logger.error('Failed to connect to database: %s', e)
            raise

    def _create_table(self):
        """Create the table to store cache data if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            data BLOB,
            timestamp INTEGER,
            invalid BOOLEAN
        );
        """
        with self._db_lock:
            try:
                with self.conn:
                    self.conn.execute(create_table_query)
                    logger.info('Cache table ensured to exist.')
            except sqlite3.Error as exc:
                logger.error(
                    'Exception occur in cache: %s, Message: %s',
                    type(exc).__name__, str(exc),
                )
                raise

    def _is_expired(self, timestamp: int) -> bool:
        """Check if the cached data is expired."""
        return (time.time() - timestamp) > self.expire_after

    def fetch_cache(self, key: str) -> tuple[Any | None, bool]:
        """
        Retrieve data from the cache or return None if not found or expired.

        Args:
            key (str): The key to fetch data for.

        Returns:
            Tuple[Optional[Any], bool]: Cached data and validity status.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT data, timestamp, invalid FROM cache WHERE key = ?', (
                    key,
                ),
            )
            row = cursor.fetchone()

            if row:
                data, timestamp, invalid = row
                data = pickle.loads(data)

                if self._is_expired(timestamp):
                    self.invalidate_cache(key)
                    return data, False
                if invalid:
                    return data, False

                return data, True
            return None, False
        except Exception as exc:
            logger.error(
                'Exception occur in cache: %s, Message: %s',
                type(exc).__name__, str(exc),
            )
            self._report_cache_error(message_key='CacheFetchFailed')
            return None, False

    def invalidate_cache(self, key: str | None = None) -> None:
        """
        Invalidate the cache entry for the specified key or all entries.

        Args:
            key (Optional[str]): The key to invalidate. Invalidates all if None.
        """
        with self._db_lock:
            try:
                cursor = self.conn.cursor()
                if key:
                    cursor.execute(
                        'UPDATE cache SET invalid = 1 WHERE key = ?', (key,),
                    )
                else:
                    cursor.execute('UPDATE cache SET invalid = 1')
                self.conn.commit()
                with self._error_lock:
                    self.is_error = False
            except Exception as exc:
                with self._error_lock:
                    self.is_error = True
                logger.error(
                    'Exception occur in cache: %s, Message: %s',
                    type(exc).__name__, str(exc),
                )
                self._report_cache_error(message_key='FailedToInvalidCache')

    def _update_cache(self, key: str, data: Any) -> None:
        """
        Store or update data in the cache.

        Args:
            key (str): The key to store the data under.
            data (Any): The data to cache.
        """
        with self._db_lock:
            try:
                timestamp = int(time.time())
                serialized_data = pickle.dumps(data)

                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cache (key, data, timestamp, invalid)
                    VALUES (?, ?, ?, 0)
                    """,
                    (key, serialized_data, timestamp),
                )
                self.conn.commit()
            except Exception as exc:
                logger.error(
                    'Exception occur in cache: %s, Message: %s',
                    type(exc).__name__, str(exc),
                )
                self._report_cache_error(message_key='FailedToUpdateCache')

    def on_success(self, key: str, result: Any) -> None:
        """
        Handle successful data fetch or computation and update the cache.

        Args:
            key (str): The cache key.
            result (Any): The result to cache.
        """
        self._update_cache(key, result)

    def _report_cache_error(self, message_key: str):
        """
        This method will emit the toaster to report user about caching error.
        """
        error_key = ERROR_MAPPING.get(message_key)
        translated_error_message = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, error_key, None,
        )
        global_toaster.cache_error_event.emit(translated_error_message)

    @staticmethod
    def get_cache_session() -> Cache | None:
        """
        Returns the singleton instance of Cache in a thread-safe manner.

        Returns:
            Cache: The singleton instance of the cache.
        """
        if Cache._instance is None:
            with Cache._lock:
                if Cache._instance is None:
                    Cache._instance = Cache._initialize_cache()
        return Cache._instance
