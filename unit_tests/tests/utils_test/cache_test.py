# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for the Cache class."""
from __future__ import annotations

import os
import pickle
import sqlite3
import time
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.cache import Cache


@patch('src.utils.cache.Cache._connect_db')
@patch('src.utils.cache.Cache._create_table')
def test_cache_initialization(mock_create_table, mock_connect_db):
    """test cache init"""
    mock_connect_db.return_value = MagicMock()
    cache = Cache(
        db_name='test.db', expire_after=300,
        file_path='/tmp/test.db',
    )
    assert cache.db_name == 'test.db'
    assert cache.expire_after == 300
    assert cache.cache_file_path == '/tmp/test.db'
    mock_connect_db.assert_called_once()
    mock_create_table.assert_called_once()


@patch('src.utils.cache.Cache.invalidate_cache')
@patch('src.utils.cache.Cache._is_expired')
@patch('src.utils.cache.pickle.loads')
def test_fetch_cache_valid_data(mock_pickle_loads, mock_is_expired, mock_invalidate_cache):
    """Test fetching valid cache data."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    # Create properly pickled data
    test_data = pickle.dumps('test_data')
    mock_cursor.fetchone.return_value = (test_data, int(time.time()), False)

    mock_pickle_loads.return_value = 'unpickled_data'
    mock_is_expired.return_value = False

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache()
        data, valid = cache.fetch_cache('test_key')
        assert data == 'unpickled_data'
        assert valid is True
        mock_cursor.execute.assert_called_with(
            'SELECT data, timestamp, invalid FROM cache WHERE key = ?', (
                'test_key',
            ),
        )


@patch('src.utils.cache.Cache.invalidate_cache')
@patch('src.utils.cache.Cache._is_expired')
def test_fetch_cache_expired_data(mock_is_expired, mock_invalidate_cache):
    """Test fetching expired cache data."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    # Create properly pickled data
    test_data = pickle.dumps('test_data')
    mock_cursor.fetchone.return_value = (
        test_data, int(time.time()) - 500, False,
    )

    mock_is_expired.return_value = True

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(expire_after=300)
        data, valid = cache.fetch_cache('test_key')
        assert data == pickle.loads(test_data)
        assert valid is False
        mock_invalidate_cache.assert_called_once_with('test_key')


@patch('src.utils.cache.Cache._connect_db')
def test_fetch_cache_no_data(mock_connect_db):
    """Test fetching no cache data."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = None

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(db_name='test.db', file_path='/tmp/test.db')
        data, valid = cache.fetch_cache('missing_key')
        assert data is None
        assert valid is False
        mock_cursor.execute.assert_called_with(
            'SELECT data, timestamp, invalid FROM cache WHERE key = ?', (
                'missing_key',
            ),
        )


@patch('src.utils.cache.Cache._connect_db')
@patch('src.utils.cache.Cache._report_cache_error')
def test_fetch_cache_exception(mock_report_cache_error, mock_connect_db):
    """Test fetching cache data with an exception."""
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = sqlite3.Error('Database error')

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(db_name='test.db', file_path='/tmp/test.db')
        data, valid = cache.fetch_cache('error_key')
        assert data is None
        assert valid is False
        mock_report_cache_error.assert_called_once_with(
            message_key='CacheFetchFailed',
        )


@patch('src.utils.cache.Cache._connect_db')
def test_invalidate_cache_key(mock_connect_db):
    """Test invalidating a cache key."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(db_name='test.db', file_path='/tmp/test.db')
        cache.invalidate_cache('test_key')
        mock_cursor.execute.assert_called_with(
            'UPDATE cache SET invalid = 1 WHERE key = ?', ('test_key',),
        )


@patch('src.utils.cache.Cache._connect_db')
def test_invalidate_all_cache(mock_connect_db):
    """Test invalidating all cache."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(db_name='test.db', file_path='/tmp/test.db')
        cache.invalidate_cache()
        mock_cursor.execute.assert_called_with('UPDATE cache SET invalid = 1')


@patch('src.utils.cache.Cache._connect_db')
@patch('src.utils.cache.pickle.dumps')
def test_update_cache(mock_pickle_dumps, mock_connect_db):
    """Test updating cache."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value

    mock_pickle_dumps.return_value = b'serialized_data'

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        cache = Cache(db_name='test.db', file_path='/tmp/test.db')
        cache._update_cache('test_key', {'test': 'data'})
        mock_pickle_dumps.assert_called_once_with({'test': 'data'})
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT OR REPLACE INTO cache' in call_args[0]
        assert 'VALUES (?, ?, ?, 0)' in call_args[0]
        assert call_args[1] == (
            'test_key', b'serialized_data', int(time.time()),
        )


@patch('src.utils.cache.Cache._update_cache')
def test_on_success(mock_update_cache):
    """Test on success."""
    cache = Cache(db_name='test.db', file_path='/tmp/test.db')
    cache.on_success('success_key', {'result': 'success'})
    mock_update_cache.assert_called_once_with(
        'success_key', {'result': 'success'},
    )


@patch('src.utils.cache.Cache._connect_db')
def test_report_cache_error(mock_connect_db):
    """Test reporting cache error."""
    mock_conn = MagicMock()
    # Create a mock for the event
    mock_event = MagicMock()

    with patch.object(Cache, '_connect_db', return_value=mock_conn):
        # Patch the cache_error_event
        with patch('src.utils.cache.global_toaster.cache_error_event', mock_event):
            cache = Cache()
            cache._report_cache_error('cache_fetch_failed')
            mock_event.emit.assert_called_once_with('')


@pytest.mark.parametrize(
    'network, file_name', [
        ('mainnet', 'iris_cache_mainnet.sqlite'),
        ('testnet', 'iris_cache_testnet.sqlite'),
        ('regtest', 'iris_cache_regtest.sqlite'),
    ],
)
@patch('src.utils.cache.CACHE_FILE_NAME', {'mainnet': 'iris_cache_mainnet', 'testnet': 'iris_cache_testnet', 'regtest': 'iris_cache_regtest'})
@patch('src.utils.cache.DEFAULT_CACHE_FILENAME', 'iris_cache_default')
@patch('src.utils.cache.CACHE_EXPIRE_TIMEOUT', 123)
def test_initialize_cache_success(file_name, network):
    """Test initializing cache with success."""
    # Patch all dependencies with at most 4 arguments per patch
    with patch('src.utils.cache.NetworkEnumModel') as mock_network_enum, \
            patch('src.utils.cache.bitcoin_network') as mock_bitcoin_network, \
            patch('src.utils.cache.app_paths') as mock_app_paths, \
            patch('src.utils.cache.local_store') as mock_local_store, \
            patch('src.utils.cache.Cache') as mock_cache_cls, \
            patch('os.path.exists', return_value=False) as mock_exists, \
            patch('os.path.join', side_effect=os.path.join):

        mock_bitcoin_network.__network__ = network
        mock_network_enum.return_value = network
        mock_app_paths.cache_path = '/mock/cache/dir'
        mock_cache_instance = MagicMock(spec=Cache)
        mock_cache_cls.return_value = mock_cache_instance

        result = Cache._initialize_cache()
        mock_exists.assert_called_once_with('/mock/cache/dir')
        mock_local_store.create_folder.assert_called_once_with(
            '/mock/cache/dir',
        )
        expected_path = os.path.join('/mock/cache/dir', file_name)
        mock_cache_cls.assert_called_once_with(
            db_name=file_name,
            expire_after=123,
            file_path=expected_path,
        )
        assert result == mock_cache_instance


def test_initialize_cache_exception():
    """Test that _initialize_cache logs and raises on exception."""
    with patch('src.utils.cache.NetworkEnumModel', side_effect=Exception('fail')), \
            patch('src.utils.cache.logger') as mock_logger:
        result = Cache._initialize_cache()
        assert result is None
        assert mock_logger.error.called
        assert 'Exception occurred in cache' in mock_logger.error.call_args[0][0]


def test_create_table_success(mocker):
    """Test that _create_table executes the table creation query."""
    mocker.patch.object(Cache, '_connect_db', return_value=mocker.MagicMock())
    mock_conn = mocker.MagicMock()
    cache = Cache()
    cache.conn = mock_conn
    cache._db_lock = mocker.MagicMock()
    cache._db_lock.__enter__ = lambda s: None
    cache._db_lock.__exit__ = lambda s, exc_type, exc_val, exc_tb: None
    mock_logger = mocker.patch('src.utils.cache.logger')
    cache._create_table()
    assert mock_conn.execute.called
    mock_logger.info.assert_any_call('Cache table ensured to exist.')


def test_create_table_failure(mocker):
    """Test that _create_table logs and raises on error."""
    # Patch _connect_db to avoid AttributeError on cache_file_path
    mocker.patch.object(Cache, '_connect_db', return_value=mocker.MagicMock())
    mock_conn = mocker.MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error('fail')
    cache = Cache()
    cache.conn = mock_conn
    cache._db_lock = mocker.MagicMock()
    cache._db_lock.__enter__ = lambda s: None
    cache._db_lock.__exit__ = lambda s, exc_type, exc_val, exc_tb: None
    mock_logger = mocker.patch('src.utils.cache.logger')
    try:
        cache._create_table()
    except sqlite3.Error:
        pass
    else:
        assert False, 'Should have raised'
    mock_logger.error.assert_called()
    assert 'Exception occur in cache' in mock_logger.error.call_args[0][0]


def test_is_expired_true_and_false(mocker):
    """Test _is_expired returns correct boolean."""
    # Patch _connect_db to avoid AttributeError on cache_file_path
    mocker.patch.object(Cache, '_connect_db', return_value=mocker.MagicMock())
    cache = Cache(expire_after=10)
    now = int(time.time())
    assert cache._is_expired(now - 20) is True
    assert cache._is_expired(now) is False


@patch('src.utils.cache.Cache._initialize_cache')
def test_get_cache_session_singleton(mock_initialize_cache):
    """Test that get_cache_session returns a singleton Cache instance in a thread-safe manner."""
    # Reset singleton for test isolation
    Cache._instance = None

    mock_cache_instance = MagicMock(spec=Cache)
    mock_initialize_cache.return_value = mock_cache_instance

    # First call should initialize
    result1 = Cache.get_cache_session()
    assert result1 is mock_cache_instance
    mock_initialize_cache.assert_called_once()

    # Second call should not re-initialize
    result2 = Cache.get_cache_session()
    assert result2 is mock_cache_instance
    # Still only one initialization
    mock_initialize_cache.assert_called_once()

    # Clean up for other tests
    Cache._instance = None


@patch('src.utils.cache.Cache._initialize_cache')
def test_get_cache_session_returns_none_if_initialize_returns_none(mock_initialize_cache):
    """Test get_cache_session returns None if _initialize_cache returns None."""
    Cache._instance = None
    mock_initialize_cache.return_value = None

    result = Cache.get_cache_session()
    assert result is None
    mock_initialize_cache.assert_called_once()

    # Clean up for other tests
    Cache._instance = None


def test_invalidate_cache_exception(mocker):
    """Test that invalidate_cache handles exceptions and sets is_error True, logs error, and calls _report_cache_error."""
    mocker.patch.object(Cache, '_connect_db', return_value=mocker.MagicMock())
    cache = Cache()
    cache.conn = mocker.MagicMock()
    cache._db_lock = mocker.MagicMock()
    cache._error_lock = mocker.MagicMock()
    cache.is_error = False

    # Simulate exception on cursor()
    cache.conn.cursor.side_effect = Exception('DB error')

    # Patch logger and _report_cache_error
    mock_logger = mocker.patch('src.utils.cache.logger')
    mock_report = mocker.patch.object(cache, '_report_cache_error')

    cache.invalidate_cache('some_key')

    # is_error should be set to True
    assert cache.is_error is True

    # logger.error should be called with correct message
    assert mock_logger.error.called
    error_call = mock_logger.error.call_args
    assert 'Exception occur in cache' in error_call[0][0]
    assert 'DB error' in error_call[0][2]

    # _report_cache_error should be called with correct message_key
    mock_report.assert_called_once_with(message_key='FailedToInvalidCache')
