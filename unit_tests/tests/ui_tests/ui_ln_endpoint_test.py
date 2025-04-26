"""Unit test for LN endpoint UI."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from typing import Literal
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.constant import BACKED_URL_LIGHTNING_NETWORK
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_ln_endpoint import LnEndpointWidget


@pytest.fixture
def ln_endpoint_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_ln_endpoint_view_model(ln_endpoint_page_navigation: MagicMock):
    """Fixture to create a MainViewModel instance with mocked page navigation."""
    return MainViewModel(ln_endpoint_page_navigation)


@pytest.fixture
def ln_endpoint_originating_page():
    """Fixture to provide the originating page name for testing."""
    return 'wallet_selection_page'  # or 'settings_page'


@pytest.fixture
def ln_endpoint_widget(mock_ln_endpoint_view_model: MagicMock, ln_endpoint_originating_page: Literal['wallet_selection_page']):
    """Fixture to create an instance of LnEndpointWidget with mocked view model and originating page."""
    return LnEndpointWidget(mock_ln_endpoint_view_model, ln_endpoint_originating_page)


def test_initial_ui_state(ln_endpoint_widget: LnEndpointWidget):
    """Test the initial UI state of the LnEndpointWidget."""
    # Test initial UI state
    assert ln_endpoint_widget.enter_ln_node_url_input.placeholderText(
    ) == 'enter_lightning_node_url'
    assert ln_endpoint_widget.proceed_button.text() == 'proceed'
    assert ln_endpoint_widget.ln_node_connection.text() == 'lightning_node_connection'


def test_set_ln_url(ln_endpoint_widget: LnEndpointWidget):
    """Test the set_ln_url method."""

    # Mock the enter_ln_node_url_input.text() method to return a specific URL
    with patch.object(ln_endpoint_widget.enter_ln_node_url_input, 'text', return_value='http://example.com') as _mock_text:

        # Mock the ln_endpoint_view_model.set_ln_endpoint method to track calls
        mock_set_ln_endpoint = MagicMock()
        ln_endpoint_widget.view_model.ln_endpoint_view_model.set_ln_endpoint = mock_set_ln_endpoint

        # Call the method to set the Lightning Node URL
        ln_endpoint_widget.set_ln_url()

        # Assert that set_ln_endpoint was called with the correct arguments
        mock_set_ln_endpoint.assert_called_once_with(
            'http://example.com', ln_endpoint_widget.set_validation,
        )


def test_set_validation(ln_endpoint_widget: LnEndpointWidget):
    """Test setting validation for the LnEndpointWidget."""
    # Test setting validation
    ln_endpoint_widget.set_validation()
    assert ln_endpoint_widget.label.text() == 'invalid_url'


def test_start_loading_connect(ln_endpoint_widget: LnEndpointWidget):
    """Test the behavior of starting the loading state."""
    # Test starting the loading state
    ln_endpoint_widget.proceed_button.start_loading = MagicMock()
    ln_endpoint_widget.start_loading_connect()
    ln_endpoint_widget.proceed_button.start_loading.assert_called_once()


def test_stop_loading_connect(ln_endpoint_widget: LnEndpointWidget):
    """Test the behavior of stopping the loading state."""
    # Test stopping the loading state
    ln_endpoint_widget.proceed_button.stop_loading = MagicMock()
    ln_endpoint_widget.stop_loading_connect()
    ln_endpoint_widget.proceed_button.stop_loading.assert_called_once()


def test_set_ln_placeholder_text_settings_page(ln_endpoint_widget: LnEndpointWidget):
    """Test setting the placeholder text when originating page is 'settings_page'."""
    # Test setting the placeholder text when originating page is 'settings_page'
    with patch('src.data.repository.setting_repository.SettingRepository.get_ln_endpoint', return_value='http://settings.com'):
        ln_endpoint_widget.originating_page = 'settings_page'
        ln_endpoint_widget.set_ln_placeholder_text()
        assert ln_endpoint_widget.enter_ln_node_url_input.text() == 'http://settings.com'


def test_set_ln_placeholder_text_other_page(ln_endpoint_widget: LnEndpointWidget):
    """Test setting the placeholder text when originating page is not 'settings_page'."""
    # Test setting the placeholder text when originating page is not 'settings_page'
    ln_endpoint_widget.originating_page = 'other_page'
    ln_endpoint_widget.set_ln_placeholder_text()
    assert ln_endpoint_widget.enter_ln_node_url_input.text() == BACKED_URL_LIGHTNING_NETWORK


def test_close_button_navigation(ln_endpoint_widget: LnEndpointWidget):
    """Test the close button navigation behavior."""
    # Mock the page navigation methods
    ln_endpoint_widget.view_model.page_navigation.wallet_method_page = MagicMock()

    # Test wallet selection page navigation
    ln_endpoint_widget.originating_page = 'wallet_selection_page'
    ln_endpoint_widget.close_button.clicked.emit()
    ln_endpoint_widget.view_model.page_navigation.wallet_method_page.assert_called_once()
