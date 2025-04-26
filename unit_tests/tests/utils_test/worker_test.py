# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-few-public-methods
"""Unit tests for the Worker class."""
from __future__ import annotations

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.custom_exception import CommonException
from src.utils.worker import ThreadManager
from src.utils.worker import WorkerWithCache
from src.utils.worker import WorkerWithoutCache


def sample_function(*args, **kwargs):
    """Sample function."""
    return 'Success'


def sample_error_function(*args, **kwargs):
    """Sample error function."""
    raise ValueError('Test Error')


@pytest.fixture
def thread_manager():
    """Mock the ThreadManager."""
    return ThreadManager()


def test_run_in_thread_without_cache(thread_manager):
    """Test run in thread without cache."""
    callback = MagicMock()
    error_callback = MagicMock()

    thread_manager.run_in_thread(
        func=sample_function,
        options={
            'args': [1, 2], 'kwargs': {'key': 'value'},
            'callback': callback, 'error_callback': error_callback,
        },
    )

    assert isinstance(thread_manager.worker, WorkerWithoutCache)
    callback.assert_not_called()
    error_callback.assert_not_called()


def test_run_in_thread_with_cache(thread_manager):
    """Test run in thread with cache."""
    callback = MagicMock()
    error_callback = MagicMock()

    with patch('src.utils.cache.Cache.get_cache_session') as mock_cache_session:
        mock_cache = MagicMock()
        mock_cache_session.return_value = mock_cache
        mock_cache.fetch_cache.return_value = ('Cached Result', True)

        # Mocking WorkerWithCache to simulate thread execution
        with patch('src.utils.worker.WorkerWithCache.run', autospec=True):
            thread_manager.run_in_thread(
                func=sample_function,
                options={
                    'key': 'test_key', 'use_cache': True,
                    'callback': callback, 'error_callback': error_callback,
                },
            )

            assert isinstance(thread_manager.worker, WorkerWithCache)

            # Manually invoke the run method to simulate QRunnable execution
            thread_manager.worker.run()

            # Ensure the callback is called after the run method is invoked
            thread_manager.worker.result.emit('Cached Result', True)

        # Verify that the callback was called with the cached result
        callback.assert_called_once_with('Cached Result', True)


def test_worker_without_cache_success():
    """Test WorkerWithoutCache with a success case."""
    worker = WorkerWithoutCache(
        sample_function, args=[
            1, 2,
        ], kwargs={'key': 'value'},
    )

    worker.result = MagicMock()
    worker.error = MagicMock()
    worker.finished = MagicMock()

    worker.run()

    worker.result.emit.assert_called_once_with('Success')
    worker.error.emit.assert_not_called()
    worker.finished.emit.assert_called_once()


def test_worker_without_cache_error():
    """Test WorkerWithoutCache with an error case."""
    worker = WorkerWithoutCache(sample_error_function)

    worker.result = MagicMock()
    worker.error = MagicMock()
    worker.finished = MagicMock()

    worker.run()

    worker.result.emit.assert_not_called()
    worker.error.emit.assert_called_once()

    # Get the actual error that was emitted
    actual_error = worker.error.emit.call_args[0][0]
    assert isinstance(actual_error, ValueError)
    assert str(actual_error) == 'Test Error'

    worker.finished.emit.assert_called_once()


def test_worker_with_cache_success():
    """Test WorkerWithCache with a valid cache entry."""
    with patch('src.utils.cache.Cache.get_cache_session') as mock_cache_session:
        mock_cache = MagicMock()
        mock_cache.fetch_cache.return_value = (
            'Cached Result', True,
        )  # Simulate valid cached data
        mock_cache_session.return_value = mock_cache

        worker = WorkerWithCache(
            sample_function, key='test_key', use_cache=True,
        )
        worker.result = MagicMock()
        worker.error = MagicMock()
        worker.finished = MagicMock()

        worker.run()

        # Verify that the result signal was emitted with the cached data
        worker.result.emit.assert_called_once_with('Cached Result', True)
        worker.error.emit.assert_not_called()
        worker.finished.emit.assert_called_once()


def test_worker_with_cache_error():
    """Test WorkerWithCache when the function raises an error."""
    with patch('src.utils.cache.Cache.get_cache_session') as mock_cache_session:
        mock_cache = MagicMock()
        mock_cache.fetch_cache.return_value = (
            None, False,
        )  # Simulate no cached result
        mock_cache_session.return_value = mock_cache

        worker = WorkerWithCache(
            sample_error_function, key='test_key', use_cache=True,
        )
        worker.result = MagicMock()
        worker.error = MagicMock()
        worker.finished = MagicMock()

        worker.run()

        worker.result.emit.assert_not_called()
        worker.error.emit.assert_called_once()

        # Get the actual error that was emitted
        actual_error = worker.error.emit.call_args[0][0]
        assert isinstance(actual_error, ValueError)
        assert str(actual_error) == 'Test Error'

        worker.finished.emit.assert_called_once()


@pytest.fixture
def mock_signals():
    """Mock the signals for WorkerWithCache."""
    class MockSignals:
        """mock signal class"""
        progress = MagicMock()
        result = MagicMock()
        error = MagicMock()
        finished = MagicMock()
    return MockSignals()


def test_worker_with_valid_cache(mock_signals):
    """Test WorkerWithCache with a valid cache entry."""
    mock_cache = MagicMock()
    mock_cache.fetch_cache.return_value = (
        'cached_data', True,
    )  # Simulate valid cached data
    with patch('src.utils.cache.Cache.get_cache_session', return_value=mock_cache):
        worker = WorkerWithCache(
            func=lambda: 'fresh_data', key='test_key', use_cache=True,
        )
        worker.progress = mock_signals.progress
        worker.result = mock_signals.result
        worker.error = mock_signals.error
        worker.finished = mock_signals.finished

        worker.run()

        # Verify that the result signal was emitted with the cached data
        mock_signals.result.emit.assert_called_once_with('cached_data', True)
        mock_signals.finished.emit.assert_called_once()


def test_worker_with_invalid_cache(mock_signals):
    """Test WorkerWithCache with an invalid cache entry."""
    mock_cache = MagicMock()
    mock_cache.fetch_cache.return_value = ('cached_data', False)
    with patch('src.utils.cache.Cache.get_cache_session', return_value=mock_cache):
        worker = WorkerWithCache(
            func=lambda: 'fresh_data', key='test_key', use_cache=True,
        )
        worker.progress = mock_signals.progress
        worker.result = mock_signals.result
        worker.error = mock_signals.error
        worker.finished = mock_signals.finished

        worker.run()
        mock_signals.result.emit.assert_any_call('cached_data', False)
        mock_signals.result.emit.assert_any_call('fresh_data', True)
        mock_signals.finished.emit.assert_called_once()


def test_worker_without_cache(mock_signals):
    """Test WorkerWithCache when cache is not used."""
    with patch('src.utils.cache.Cache.get_cache_session', return_value=None):
        worker = WorkerWithCache(func=lambda: 'fresh_data', use_cache=False)
        worker.progress = mock_signals.progress
        worker.result = mock_signals.result
        worker.error = mock_signals.error
        worker.finished = mock_signals.finished

        worker.run()
        mock_signals.result.emit.assert_called_once_with('fresh_data', True)
        mock_signals.finished.emit.assert_called_once()


def test_worker_with_error():
    """Test WorkerWithCache handling of CommonException."""
    with patch('src.utils.cache.Cache.get_cache_session') as mock_cache:
        # Mock cache to return a valid cached result
        mock_cache_instance = MagicMock()
        mock_cache_instance.fetch_cache.return_value = ('cached_data', False)
        mock_cache.return_value = mock_cache_instance

        # Create a function that raises CommonException
        def error_func():
            raise CommonException('Test Error')

        worker = WorkerWithCache(
            func=error_func, key='test_key', use_cache=True,
        )
        worker.result = MagicMock()
        worker.error = MagicMock()
        worker.finished = MagicMock()

        # Run the worker
        worker.run()

        # Verify both cached result emissions
        assert worker.result.emit.call_count == 2
        worker.result.emit.assert_has_calls([
            call('cached_data', False),
            call('cached_data', True),
        ])

        # Verify error signal is emitted with correct exception
        worker.error.emit.assert_called_once()
        actual_error = worker.error.emit.call_args[0][0]
        assert isinstance(actual_error, CommonException)
        assert str(actual_error) == 'Test Error'

        # Ensure finished signal is emitted
        worker.finished.emit.assert_called_once()


def test_worker_finally(mock_signals):
    """Test WorkerWithCache to ensure the finished signal is always emitted."""
    worker = WorkerWithCache(func=lambda: 'fresh_data')
    worker.progress = mock_signals.progress
    worker.result = mock_signals.result
    worker.error = mock_signals.error
    worker.finished = mock_signals.finished

    worker.run()
    mock_signals.finished.emit.assert_called_once()
