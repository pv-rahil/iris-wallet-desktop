# pylint: disable=too-few-public-methods
"""
This module contains the method to execute
blocking methods in a thread using QThread provided by Qt.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtCore import QRunnable
from PySide6.QtCore import QThreadPool
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from src.utils.cache import Cache
from src.utils.custom_exception import CommonException


class ThreadManager:
    """
    Manages the execution of functions in separate threads using QThreadPool.

    Methods:
        run_in_thread(func, args=None, kwargs=None, callback=None, error_callback=None):
            Executes a given function in a separate thread.
        _handle_error(error):
            Handles any errors that occur during the execution of the function.
        print_output(output):
            Prints the output.
        thread_complete():
            Notifies when the thread execution is complete.
    """

    def __init__(self):
        self.threadpool = QThreadPool()
        self.worker: WorkerWithoutCache | None = None

    def run_in_thread(self, func: Callable, options: dict | None = None):
        """
        Executes the given function in a separate thread.

        Args:
            func (Callable): The function to be executed.
            options (Optional[dict]): Options including 'args', 'kwargs', 'callback', 'error_callback',
                                    'key', 'page', and 'use_cache'. Defaults to None.
        """
        options = options or {}
        args = options.get('args', [])
        kwargs = options.get('kwargs', {})
        callback = options.get('callback')
        error_callback = options.get('error_callback')
        key = options.get('key')
        use_cache = options.get('use_cache', False)

        if use_cache:
            self.worker = WorkerWithCache(
                func, key, use_cache, args=args, kwargs=kwargs,
            )
        else:
            self.worker = WorkerWithoutCache(func, args=args, kwargs=kwargs)

        if callback:
            self.worker.result.connect(callback)

        if error_callback:
            self.worker.error.connect(error_callback)

        self.worker.finished.connect(self.thread_complete)

        self.threadpool.start(self.worker)

    def thread_complete(self):
        """
        Notifies that the thread execution is complete.
        """
        # Might be useful in future
        pass    # pylint:disable=unnecessary-pass


class WorkerSignalsWithoutCache(QObject):
    """
    Defines the signals available from a running worker thread.

    Attributes:
        finished (Signal): Emitted when the worker has finished processing.
        error (Signal): Emitted when an error occurs.
        result (Signal): Emitted with the result of the function execution.
        progress (Signal): Emitted to report progress (not used in this implementation).
    """
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(object)


class WorkerSignalsWithCache(WorkerSignalsWithoutCache):
    """
    Defines the signals available from a running worker thread.

    Attributes:
        finished (Signal): Emitted when the worker has finished processing.
        error (Signal): Emitted when an error occurs.
        result (Signal): Emitted with the result of the function execution.
        progress (Signal): Emitted to report progress (not used in this implementation).
    """
    result = Signal(object, bool)


class WorkerWithoutCache(QRunnable, WorkerSignalsWithoutCache):
    """
    Worker thread for executing a function with optional arguments and keyword arguments.

    Methods:
        run():
            Executes the function in the thread and emits signals based on the outcome.
    """

    def __init__(self, func: Callable, args: list | None = None, kwargs: dict | None = None):
        super().__init__()
        self.func = func
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}

    @Slot()
    def run(self):
        """
        Runs the function with the provided arguments and keyword arguments.
        Emits result or error signals based on the outcome.
        """
        try:
            self.progress.emit(True)
            result = self.func(*self.args, **self.kwargs)
        except (TypeError, ValueError, RuntimeError, CommonException) as exc:
            self.error.emit(exc)
        else:
            self.result.emit(result)
        finally:
            self.finished.emit()


class WorkerWithCache(QRunnable, WorkerSignalsWithCache):
    """
    Worker thread for executing a function with optional arguments and keyword arguments.
    Includes logic for caching method responses.
    """

    def __init__(self, func: Callable, key: str | None = None, use_cache: bool = False, args: list | None = None, kwargs: dict | None = None):
        super().__init__()
        self.func = func
        self.key = key
        self.use_cache = use_cache
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}

    @Slot()
    def run(self):
        """
        Runs the function with the provided arguments and keyword arguments.
        Incorporates caching logic:
        - Displays cached data immediately if available.
        - Calls the API in parallel to fetch fresh data.
        - Updates the cache and UI once the fresh data is fetched.
        """
        try:
            # Emit progress signal to indicate task has started
            self.progress.emit(True)
            cache: Cache | None = Cache.get_cache_session()

            # Step 1: Check and emit cached result (if available)
            if self.use_cache and self.key and cache is not None:
                cached_result, valid = cache.fetch_cache(self.key)
                if cached_result:
                    # Display cached data immediately
                    self.result.emit(cached_result, valid)
                    if valid:
                        return
            # Step 2: Call the API to fetch fresh data
            result = self.func(*self.args, **self.kwargs)
        except (TypeError, ValueError, RuntimeError, CommonException) as exc:
            # Handle any errors encountered during execution
            if cached_result:
                self.result.emit(cached_result, True)
            self.error.emit(exc)
        else:
            self.result.emit(result, True)
            if cache is not None:
                cache.on_success(self.key, result)
        # make customize except error for cache
        finally:
            # Signal that the thread has finished execution
            self.finished.emit()
