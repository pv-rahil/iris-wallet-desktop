# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for the Cache class."""
from __future__ import annotations

import pickle
import sqlite3
import time
from unittest.mock import MagicMock
from unittest.mock import patch

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
