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
        if exc is not None:
            self.name = exc.get('name')
            self.error_message = ERROR_MAPPING.get(self.name)
            self.message = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self.error_message, None,
            )


class ServiceOperationException(Exception):
    """Exception class for errors occurring in service operations."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message  # used for localization
