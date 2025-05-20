"""This module contains the CommonException class, which represents
an exception for repository operations.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.error_mapping import ERROR_MAPPING


class CommonException(Exception):
    """This is common exception class handler which handle repository and service errors."""

    def __init__(self, message: str, exc=None):
        super().__init__(message)
        self.message = message
        self.error_message = self._get_error_message(exc)

        if self.error_message:
            self.message = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self.error_message, None,
            )

    def _get_error_message(self, exc):
        """Helper method to get error message based on the exception."""
        if exc is not None:
            name = exc.get('name')
            return ERROR_MAPPING.get(name)
        return ERROR_MAPPING.get(self.message)


class ServiceOperationException(Exception):
    """Exception class for errors occurring in service operations."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message  # used for localization
