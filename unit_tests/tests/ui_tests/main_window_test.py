"""This module contains unit tests for the MainWindow class, which represents the main window of the application."""
# pylint: disable=redefined-outer-name
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QWidget

from src.viewmodels.main_view_model import MainViewModel
from src.views.main_window import MainWindow


@pytest.fixture
def main_window_page_navigation():
    """Fixture to create a mocked page navigation object."""
    return MagicMock()


@pytest.fixture
def mock_main_window_view_model(main_window_page_navigation):
    """Fixture to create a MainViewModel instance with mocked page navigation."""
    mock_view_model = MagicMock(spec=MainViewModel)
    mock_view_model.page_navigation = main_window_page_navigation
    return mock_view_model


@pytest.fixture
def main_window(qtbot, mock_main_window_view_model):
    """Fixture to create a MainWindow instance."""
    window = MainWindow()
    window.setup_ui(QMainWindow())  # Ensure UI is set up before using it
    if isinstance(window.main_window, QWidget):
        qtbot.addWidget(window.main_window)

    # Properly mock the view model with required attributes
    mock_main_window_view_model.splash_view_model = MagicMock()
    mock_main_window_view_model.wallet_transfer_selection_view_model = MagicMock()

    # Now set the mocked view model
    window.set_ui_and_model(mock_main_window_view_model)

    return window


def test_initial_state(main_window):
    """Test the initial state of the MainWindow."""
    assert isinstance(main_window.main_window, QMainWindow)
    expected_title = f'Iris Wallet {main_window.network.value.capitalize()}'
    assert main_window.main_window.windowTitle() == expected_title
    assert not main_window.main_window.isVisible()


def test_setup_ui(main_window):
    """Test setting up the UI."""
    assert main_window.central_widget is not None
    assert main_window.grid_layout_main is not None
    assert main_window.horizontal_layout is not None
    assert main_window.stacked_widget is not None


def test_retranslate_ui(main_window):
    """Test the retranslate_ui method."""
    # Mock the app name suffix
    with patch('src.views.main_window.__app_name_suffix__', 'TestSuffix'):
        main_window.retranslate_ui()
        expected_title = f'Iris Wallet {
            main_window.network.value.capitalize()
        } TestSuffix'
        assert main_window.main_window.windowTitle() == expected_title

    # Test without app name suffix
    with patch('src.views.main_window.__app_name_suffix__', None):
        main_window.retranslate_ui()
        expected_title = f'Iris Wallet {
            main_window.network.value.capitalize()
        }'
        assert main_window.main_window.windowTitle() == expected_title
