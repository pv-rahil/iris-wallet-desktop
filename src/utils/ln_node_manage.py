"""
This module provides a class to manage the lifecycle of an LN node server process.
It uses PySide6's QProcess for starting and stopping the server, and includes
methods to check the server's status and handle process-related events.

Classes:
    LnNodeServerManager: Manages the LN node server process, including starting,
                         stopping, and monitoring the server.

Constants:
    INTERVAL: Time interval in seconds to check the server status.
    LN_BINARY_NAME: The name of the LN node binary.
    MAX_ATTEMPTS_TO_WAIT_FOR_NODE: Maximum number of attempts to wait for the server to start.
    NODE_INFO_ENDPOINT: The endpoint to check the server's status.
    PageNameEnum: Enum for different page names in the application.
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QObject
from PySide6.QtCore import QProcess
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from requests import HTTPError
from requests.exceptions import ConnectionError as RequestsConnectionError

from src.utils.constant import INTERVAL
from src.utils.constant import LN_BINARY_NAME
from src.utils.constant import MAX_ATTEMPTS_FOR_CLOSE
from src.utils.constant import MAX_ATTEMPTS_TO_WAIT_FOR_NODE
from src.utils.constant import NODE_CLOSE_INTERVAL
from src.utils.endpoints import NODE_INFO_ENDPOINT
from src.utils.request import Request


class LnNodeServerManager(QObject):
    """
    Manages the LN node server process, including starting, stopping, and monitoring the server.

    Attributes:
        process_started (Signal): Signal emitted when the server process starts.
        process_terminated (Signal): Signal emitted when the server process terminates.
        process_error (Signal): Signal emitted when an error occurs in the server process.
        process_already_running (Signal): Signal emitted when attempting to start an already running server.
        _instance (LnNodeServerManager): Singleton instance of the manager.
    """

    process_started = Signal()
    process_terminated = Signal()
    process_error = Signal(int, str)
    process_already_running = Signal()
    process_finished_on_request_app_close = Signal()
    process_finished_on_request_app_close_error = Signal()
    main_window_loader = Signal(bool)
    _instance = None

    def __init__(self):
        """
        Initializes the LnNodeServerManager instance.
        """
        super().__init__()
        self.executable_path = self._get_ln_path()
        self.process = QProcess(self)
        self.process.started.connect(self.on_process_started)
        self.process.finished.connect(self.on_process_terminated)
        self.process.errorOccurred.connect(self.on_process_error)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_node_status)
        self.attempts = 0
        self.attempts_for_close = 0
        self.is_stop = False
        self._timer_for_on_close = QTimer(self)

    def start_server(self, arguments: list):
        """
        Starts the LN node server process with the given arguments.

        Args:
            arguments (list): The arguments to pass to the server executable.
            page_name (PageNameEnum): The name of the page initiating the server start.
        """
        if self.process.state() == QProcess.NotRunning:
            self.process.start(self.executable_path, arguments)
        else:
            self.process_already_running.emit()

    def stop_server_from_close_button(self):
        """
        Stops the LN node server process if it is running.
        """
        if self.process.state() == QProcess.Running:
            self.is_stop = True
            self.process.terminate()
            self.attempts_for_close = 0
            self._timer_for_on_close.timeout.connect(
                self._check_process_on_close_button_click,
            )
            self._timer_for_on_close.start(NODE_CLOSE_INTERVAL * 1000)
        self.timer.stop()

    def _check_process_on_close_button_click(self):
        if self.attempts_for_close >= MAX_ATTEMPTS_FOR_CLOSE:
            self._timer_for_on_close.stop()
            self.process_finished_on_request_app_close_error.emit()
        if self.process.state() == QProcess.NotRunning:
            self._timer_for_on_close.stop()
            self.timer.stop()
            self.process_finished_on_request_app_close.emit()
        else:
            self.attempts_for_close += 1

    def on_process_started(self):
        """
        Slot called when the server process starts. Starts a timer to check the server status.
        """
        if self.process.state() == QProcess.Running:
            self.attempts = 0
            # Convert seconds to milliseconds
            self.timer.start(INTERVAL * 1000)
        else:
            self.process_error.emit(500, 'Unable to start server')

    def check_node_status(self):
        """
        Checks the status of the LN node server by making a request to the NODE_INFO_ENDPOINT.
        Emits process_started if the server is running, or process_error if the server fails to start.
        """
        if self.attempts >= MAX_ATTEMPTS_TO_WAIT_FOR_NODE:
            self.process_error.emit(500, 'Unable to start server')
            self.timer.stop()
            self.main_window_loader.emit(False)
            return

        try:
            response = Request.get(NODE_INFO_ENDPOINT)
            response.raise_for_status()
            self.process_started.emit()
            self.timer.stop()
            self.main_window_loader.emit(False)
        except HTTPError:
            self.process_started.emit()
            self.timer.stop()
        except (RequestsConnectionError, Exception):
            self.attempts += 1

    def on_process_terminated(self):
        """
        Slot called when the server process terminates. Emits the process_terminated signal.
        """
        if self.is_stop:
            self.process_terminated.emit()

    def on_process_error(self, error):
        """
        Slot called when an error occurs in the server process. Emits the process_error signal and stops the server.

        Args:
            error: The error code or exception.
        """
        self.process_error.emit(
            self.process.errorString(),
            error,
        )

    def on_process_already_running(self):
        """
        Slot called when attempting to start a server that is already running. Emits the process_already_running signal.
        """
        self.process_already_running.emit()

    def _get_ln_path(self):
        """
        Returns the path to the LN node binary executable.

        Returns:
            str: The path to the LN node binary.
        """
        ln_binary_name = LN_BINARY_NAME
        if sys.platform.startswith('win'):
            ln_binary_name = f"{ln_binary_name}.exe"
        if getattr(sys, 'frozen', False):
            base_path = getattr(
                sys,
                '_MEIPASS',
                os.path.dirname(
                    os.path.abspath(__file__),
                ),
            )
            return os.path.join(base_path, 'ln_node_binary', ln_binary_name)
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../', 'ln_node_binary', ln_binary_name))

    @staticmethod
    def get_instance():
        """
        Returns the singleton instance of LnNodeServerManager.

        Returns:
            LnNodeServerManager: The singleton instance of the manager.
        """
        if LnNodeServerManager._instance is None:
            LnNodeServerManager._instance = LnNodeServerManager()
        return LnNodeServerManager._instance
