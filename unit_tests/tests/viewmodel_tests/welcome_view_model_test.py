"""Unit test for welcome view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.viewmodels.welcome_view_model import WelcomeViewModel


@pytest.fixture
def mock_page_navigation():
    """Fixture for creating a mock page navigation object."""
    return Mock()


@pytest.fixture
def welcome_view_model(mock_page_navigation):
    """Fixture for creating an instance of WelcomeViewModel with a mock page navigation object."""
    return WelcomeViewModel(mock_page_navigation)


def test_initialization(welcome_view_model):
    """Test if the WelcomeViewModel is initialized correctly."""
    assert isinstance(welcome_view_model, WelcomeViewModel)
    assert welcome_view_model._page_navigation is not None


def test_on_create_click(welcome_view_model, mock_page_navigation):
    """Test if the on_create_click method works as expected."""
    welcome_view_model.on_create_click()
    mock_page_navigation.set_wallet_password_page.assert_called_once()
