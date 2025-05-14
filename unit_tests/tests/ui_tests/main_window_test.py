"""This module contains unit tests for the MainWindow class, which represents the main window of the application."""
# pylint: disable=redefined-outer-name,protected-access,unused-argument
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


def test_show_main_window_loading_screen_shows_and_hides(qtbot, main_window, mocker):
    """Test show_main_window_loading_screen shows and hides the loading screen."""

    # Patch LoadingTranslucentScreen and LoaderDisplayModel
    mock_loading_screen_cls = mocker.patch(
        'src.views.main_window.LoadingTranslucentScreen', autospec=True,
    )
    mock_loader_display_model = mocker.patch(
        'src.views.main_window.LoaderDisplayModel',
    )
    mock_loader_display_model.FULL_SCREEN = 'FULL_SCREEN'

    # Mock stacked_widget.currentWidget().objectName()
    mock_current_widget = MagicMock()
    mock_current_widget.objectName.return_value = 'main_page'
    main_window.stacked_widget.currentWidget = MagicMock(
        return_value=mock_current_widget,
    )

    # Test showing the loading screen
    main_window.show_main_window_loading_screen(True)
    mock_loading_screen_cls.assert_called_once_with(
        parent=main_window.main_window,
        loader_type='FULL_SCREEN',
    )
    loading_screen_instance = main_window._loading_translucent_screen
    loading_screen_instance.start.assert_called_once()
    loading_screen_instance.make_parent_disabled_during_loading.assert_called_with(
        True,
    )

    # Test hiding the loading screen
    # Ensure _loading_translucent_screen is set and has stop method
    loading_screen_instance.reset_mock()
    main_window._loading_translucent_screen = loading_screen_instance
    main_window.show_main_window_loading_screen(False)
    loading_screen_instance.stop.assert_called_once()
    loading_screen_instance.make_parent_disabled_during_loading.assert_called_with(
        False,
    )


def test_show_main_window_loading_screen_noop_on_splash(qtbot, main_window, mocker):
    """Test show_main_window_loading_screen does nothing if current widget is splash_page."""
    # Patch stacked_widget.currentWidget().objectName() to return 'splash_page'
    mock_current_widget = MagicMock()
    mock_current_widget.objectName.return_value = 'splash_page'
    main_window.stacked_widget.currentWidget = MagicMock(
        return_value=mock_current_widget,
    )

    # Patch LoadingTranslucentScreen to ensure it is not called
    mock_loading_screen_cls = mocker.patch(
        'src.views.main_window.LoadingTranslucentScreen', autospec=True,
    )

    main_window.show_main_window_loading_screen(True)
    mock_loading_screen_cls.assert_not_called()


def test_set_app_icon_sets_correct_icon_based_on_network(mocker, main_window):
    """Test set_app_icon sets the correct icon according to the network."""
    # Patch SettingRepository.get_wallet_network and QIcon
    mock_network_enum = mocker.patch('src.views.main_window.NetworkEnumModel')
    mock_setting_repo = mocker.patch('src.views.main_window.SettingRepository')
    mock_qicon = mocker.patch('src.views.main_window.QIcon')

    # Prepare network enum values
    mock_network_enum.REGTEST.value = 'regtest'
    mock_network_enum.TESTNET.value = 'testnet'
    mock_network_enum.MAINNET.value = 'mainnet'

    # Test for REGTEST
    mock_network = mocker.Mock()
    mock_network.value = 'regtest'
    mock_setting_repo.get_wallet_network.return_value = mock_network
    main_window.main_window = mocker.Mock()
    main_window.set_app_icon()
    mock_qicon.assert_called_with(':/assets/icons/regtest-icon.ico')
    main_window.main_window.setWindowIcon.assert_called_with(
        mock_qicon.return_value,
    )

    # Test for TESTNET
    mock_qicon.reset_mock()
    main_window.main_window.setWindowIcon.reset_mock()
    mock_network.value = 'testnet'
    main_window.set_app_icon()
    mock_qicon.assert_called_with(':/assets/icons/testnet-icon.ico')
    main_window.main_window.setWindowIcon.assert_called_with(
        mock_qicon.return_value,
    )

    # Test for MAINNET
    mock_qicon.reset_mock()
    main_window.main_window.setWindowIcon.reset_mock()
    mock_network.value = 'mainnet'
    main_window.set_app_icon()
    mock_qicon.assert_called_with(':/assets/icons/mainnet-icon.ico')
    main_window.main_window.setWindowIcon.assert_called_with(
        mock_qicon.return_value,
    )
