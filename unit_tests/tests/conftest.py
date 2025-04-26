"""
Pytest fixture to ensure a QApplication instance is available for the test session.

This fixture is automatically used for the entire test session (`autouse=True`)
and ensures that a single instance of `QApplication` is created and shared
among all tests. If an instance of `QApplication` already exists, it will use
the existing one; otherwise, it creates a new instance.

The `scope="session"` parameter ensures that the `QApplication` instance is
created only once per test session, and is reused across all tests, which is
useful for tests that involve PySide6/Qt widgets.

Yields:
    QApplication: An instance of `QApplication` to be used in tests.
"""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope='session', autouse=True)
def qt_app():
    """Fixture to set up the QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
