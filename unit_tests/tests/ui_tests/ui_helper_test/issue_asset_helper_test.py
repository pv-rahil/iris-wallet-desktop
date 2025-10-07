"""Unit tests for issue asset helper"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


def assert_success_page_called(widget, asset_name):
    """Helper function to assert the success page was called with correct parameters."""
    widget._view_model.page_navigation.show_success_page.assert_called_once()

    params = widget._view_model.page_navigation.show_success_page.call_args[0][0]
    assert params.header == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_new_ticker',
    )
    assert params.title == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'you_are_all_set',
    )
    assert params.description == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_issued',
    ).format(asset_name)
    assert params.button_text == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'home',
    )
