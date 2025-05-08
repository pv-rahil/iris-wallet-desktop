# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access, too-many-arguments
"""
This module contains unit tests for the SplashViewModel class from the
src.viewmodels.splash_view_model module. It tests the behavior of various methods
including authentication, error handling, and application startup flows.
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NATIVE_AUTHENTICATION
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.splash_view_model import SplashViewModel
from src.views.components.message_box import MessageBox
from src.views.components.toast import ToastManager


@pytest.fixture
def splash_viewmodel():
    """Fixture to create a SplashViewModel instance with necessary mock attributes."""
    mock_navigation = MagicMock()
    model = SplashViewModel(mock_navigation)
    model.error_dialog_box = MagicMock()
    model.render_timer = MagicMock()
    model._page_navigation = MagicMock()
    model.is_error_handled = False
    model.is_from_retry = False
    return model


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_on_success_response_false(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the on_success method with a False response."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)

    view_model.on_success(False)

    page_navigation.fungibles_asset_page.assert_not_called()
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_NATIVE_AUTHENTICATION,
    )


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_on_error_common_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the on_error method with a CommonException."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    exception = CommonException('Custom error message')

    view_model.on_error(exception)

    mock_toast_manager.error.assert_called_once_with(
        description='Custom error message',
    )
    mock_qapp.instance().exit.assert_called_once()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_on_error_general_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the on_error method with a general Exception."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    exception = Exception('General error message')

    view_model.on_error(exception)

    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    mock_qapp.instance().exit.assert_called_once()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_is_login_authentication_enabled_true(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the is_login_authentication_enabled method when native login is enabled."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.native_login_enabled.return_value = Mock(
        is_enabled=True,
    )

    with patch.object(view_model, 'run_in_thread') as mock_run_in_thread:
        view_model.is_login_authentication_enabled()

    mock_run_in_thread.assert_called_once()
    mock_toast_manager.show_toast.assert_not_called()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_is_login_authentication_enabled_false(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the is_login_authentication_enabled method when native login is not enabled."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.native_login_enabled.return_value = False

    view_model.is_login_authentication_enabled()
    # mock_toast_manager.show_toast.assert_not_called()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_is_login_authentication_enabled_common_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the is_login_authentication_enabled method with a CommonException."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.native_login_enabled.side_effect = CommonException(
        'Custom error message',
    )

    view_model.is_login_authentication_enabled()

    page_navigation.fungibles_asset_page.assert_not_called()
    mock_toast_manager.error.assert_called_once_with(
        description='Custom error message',
    )


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_is_login_authentication_enabled_general_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests the is_login_authentication_enabled method with a general Exception."""
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.native_login_enabled.side_effect = Exception(
        'General error message',
    )

    view_model.is_login_authentication_enabled()

    page_navigation.fungibles_asset_page.assert_not_called()
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch.object(ToastManager, 'error')
@patch.object(MessageBox, '__init__', return_value=None)
@patch.object(QApplication, 'instance', return_value=MagicMock(exit=MagicMock()))
@patch('src.viewmodels.splash_view_model.PageNavigationEventManager')
@patch('src.viewmodels.splash_view_model.ErrorReportDialog')
def test_on_error_of_unlock_api(
    mock_error_dialog, mock_event_manager, mock_qapp, mock_msgbox, mock_toast, splash_viewmodel,
):
    """Test SplashViewModel.on_error_of_unlock_api with various error cases."""

    # Set up PageNavigationEventManager mock
    mock_instance = MagicMock()
    mock_instance.enter_wallet_password_page_signal = MagicMock(
        emit=MagicMock(),
    )
    mock_instance.set_wallet_password_page_signal = MagicMock(emit=MagicMock())
    mock_event_manager.get_instance.return_value = mock_instance

    # Mock `on_success_of_unlock_api`
    splash_viewmodel.on_success_of_unlock_api = MagicMock()

    # Mock ErrorReportDialog to prevent GUI popup
    mock_error_dialog_instance = MagicMock(exec=MagicMock())
    mock_error_dialog.return_value = mock_error_dialog_instance

    # Test Case: ERROR_PASSWORD_INCORRECT (Navigate to enter password)
    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message=ERROR_PASSWORD_INCORRECT),
    )
    mock_instance.enter_wallet_password_page_signal.emit.assert_called_once()
    mock_toast.assert_called_with(description=ERROR_PASSWORD_INCORRECT)

    # Reset mocks for next test
    mock_instance.enter_wallet_password_page_signal.emit.reset_mock()
    mock_toast.reset_mock()

    # Test Case: Generic error (should just show toast)
    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message='Some other error'),
    )
    mock_toast.assert_called_with(description='Some other error')

    # Test Case: Non-CommonException error
    splash_viewmodel.on_error_of_unlock_api(
        Exception('Regular exception'),
    )
    mock_toast.assert_called_with(description=None)

    # Verify ErrorReportDialog was created for all test cases
    assert mock_error_dialog.call_count == 3
    for call in mock_error_dialog.call_args_list:
        assert call[1]['initiated_from_splash'] is True


@patch('src.viewmodels.splash_view_model.CommonOperationRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
@patch('src.utils.local_store.LocalStore.set_value')
def test_on_success_of_unlock_api(mock_set_value, mock_qapp, mock_toast_manager, mock_common_repo):
    """Tests the on_success_of_unlock_api method."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.render_timer = Mock()

    # Act
    view_model.on_success_of_unlock_api()

    # Assert
    view_model.render_timer.stop.assert_called_once()
    page_navigation.fungibles_asset_page.assert_called_once()


@patch('src.viewmodels.splash_view_model.CommonOperationRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
@patch('src.utils.local_store.LocalStore.set_value')
def test_on_success_of_unlock_api_no_node_info(mock_set_value, mock_qapp, mock_toast_manager, mock_common_repo):
    """Tests the on_success_of_unlock_api method when node_info returns None."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.render_timer = Mock()

    # Act
    view_model.on_success_of_unlock_api()

    # Assert
    view_model.render_timer.stop.assert_called_once()
    page_navigation.fungibles_asset_page.assert_called_once()
    mock_set_value.assert_not_called()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_handle_application_open_keyring_enabled(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests handle_application_open method when keyring is enabled."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.get_keyring_status.return_value = True

    # Act
    view_model.handle_application_open()

    # Assert
    mock_setting_repo.get_keyring_status.assert_called_once()
    page_navigation.enter_wallet_password_page.assert_called_once()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
@patch('src.viewmodels.splash_view_model.get_value')
@patch('src.viewmodels.splash_view_model.mnemonic_store')
@patch('src.viewmodels.splash_view_model.get_bitcoin_network_from_enum')
@patch('src.viewmodels.splash_view_model.local_store')
@patch('src.viewmodels.splash_view_model.app_paths')
@patch('src.viewmodels.splash_view_model.QCoreApplication')
def test_handle_application_open_keyring_disabled(
    mock_qcore, mock_app_paths, mock_local_store, mock_get_network,
    mock_mnemonic_store, mock_get_value, mock_qapp, mock_toast_manager, mock_setting_repo,
):
    """Tests handle_application_open method when keyring is disabled."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.splash_screen_message = Mock()
    view_model.sync_chain_info_label = Mock()

    # Setup mocks
    mock_setting_repo.get_keyring_status.return_value = False
    mock_setting_repo.get_wallet_network.return_value = Mock(value='testnet')
    mock_wallet_password = 'test_password'
    mock_get_value.return_value = mock_wallet_password
    mock_mnemonic_store.decrypt.return_value = 'test_mnemonic'
    mock_local_store.get_value.return_value = 'test_xpub'
    mock_qcore.translate.return_value = 'wait_message'
    mock_app_paths.mnemonic_file_path = 'test_path'
    mock_app_paths.app_path = 'test_app_path'
    mock_get_network.return_value = 'testnet_network'

    # Act
    with patch.object(view_model, 'run_in_thread') as _mock_run_in_thread:
        view_model.handle_application_open()

        # Assert
        mock_setting_repo.get_keyring_status.assert_called_once()
        mock_setting_repo.get_wallet_network.assert_called_once()
        mock_get_value.assert_called_once()
        mock_mnemonic_store.decrypt.assert_called_once_with(
            password=mock_wallet_password, path='test_path',
        )
        view_model.splash_screen_message.emit.assert_called_once()
        view_model.sync_chain_info_label.emit.assert_called_once_with(True)
        mock_local_store.get_value.assert_called_once()
