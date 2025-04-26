"""
This module contains custom decorator to check node initialized.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.page_navigation_events import PageNavigationEventManager


def is_node_initialized(func):
    """This decorator handle situation when node is already initialized"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CommonException as exc:
            if exc.message == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'node_is_already_initialized', None):
                PageNavigationEventManager.get_instance().enter_wallet_password_page_signal.emit()
            raise exc
    return wrapper
