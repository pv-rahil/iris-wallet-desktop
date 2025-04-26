"""Unit testcase for term view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication

from src.viewmodels.term_view_model import TermsViewModel


@pytest.fixture
def app(qtbot):  # Use qtbot for GUI interactions if needed
    """Fixture to create a QCoreApplication instance."""
    application = QCoreApplication.instance() or QCoreApplication([])
    return application


@pytest.fixture
def page_navigation_mock():
    """Fixture for creating a mock page navigation object."""
    return Mock()


@pytest.fixture
def terms_view_model_fixture(page_navigation_mock):
    """Fixture for creating an instance of TermsViewModel with a mock page navigation object."""
    return TermsViewModel(page_navigation_mock)


def test_initialization(terms_view_model_fixture):
    """Test if the TermsViewModel is initialized correctly."""
    assert isinstance(terms_view_model_fixture, TermsViewModel)
    assert terms_view_model_fixture._page_navigation is not None


def test_on_accept_click(terms_view_model_fixture, page_navigation_mock):
    """Test if the on_accept_click method works as expected."""
    terms_view_model_fixture.on_accept_click()
    page_navigation_mock.wallet_connection_page.assert_called_once()


def test_on_decline_click(app, terms_view_model_fixture):
    """Test if the on_decline_click method works as expected."""
    with patch.object(QCoreApplication, 'quit', autospec=True) as mock_quit:
        terms_view_model_fixture.on_decline_click()
        mock_quit.assert_called_once()
