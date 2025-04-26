"""
This class measure and log the time taken for rendering or any other process.
"""
from __future__ import annotations

from PySide6.QtCore import QElapsedTimer

from src.utils.logging import logger


class RenderTimer:
    """
    Utility class to measure and log the time taken for rendering or any other process using QElapsedTimer.
    """
    _instance = None  # Class-level attribute to store the singleton instance

    def __new__(cls, *args, **kwargs):
        """
        Override __new__ to ensure only one instance of the class exists.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, task_name: str):
        """
        Initializes the RenderTimer with a task name.

        :param task_name: The name of the task being timed.
        """
        # Initialize only once (guard against multiple __init__ calls)
        self.task_name = task_name
        if not hasattr(self, 'initialized'):
            self.timer = QElapsedTimer()
            self.initialized = True  # Ensure initialization happens only once
            self.is_rendering = False  # This flag tracks whether rendering is ongoing

    def start(self):
        """Start the QElapsedTimer."""
        if not self.is_rendering:
            self.is_rendering = True  # Set the flag to True to prevent further calls
            self.timer.start()
            logger.info('%s started.', self.task_name)

    def stop(self):
        """
        Stop the timer, calculate the elapsed time and log it.

        :return: The elapsed time in milliseconds.
        """
        if not self.timer.isValid():
            logger.warning('Timer for %s was not started.', self.task_name)
        if self.is_rendering:
            self.is_rendering = False
            elapsed_time_ms = self.timer.elapsed()
            logger.info(
                '%s finished. Time taken: %d ms.',
                self.task_name, elapsed_time_ms,
            )
