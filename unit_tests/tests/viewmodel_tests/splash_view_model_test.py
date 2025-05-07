# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
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
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication

from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_CONNECTION_FAILED_WITH_PROVIDED_URL
from src.utils.error_message import ERROR_NATIVE_AUTHENTICATION
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.error_message import ERROR_REQUEST_TIMEOUT
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

    # Test Case: 'already_unlocked'
    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message='already_unlocked'),
    )
    splash_viewmodel.on_success_of_unlock_api.assert_called_once()

    # Reset mock for next test
    splash_viewmodel.on_success_of_unlock_api.reset_mock()

    # Test Case: 'not_initialized'
    splash_viewmodel.render_timer = MagicMock(stop=MagicMock())
    splash_viewmodel._page_navigation = MagicMock(
        term_and_condition_page=MagicMock(),
    )

    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message='not_initialized'),
    )

    # Assert that `stop()` was called
    splash_viewmodel.render_timer.stop.assert_called_once()

    # Assert page navigation was triggered
    splash_viewmodel._page_navigation.term_and_condition_page.assert_called_once()

    # Reset QApplication mock for next test
    mock_qapp.return_value.exit.reset_mock()

    # Test Case: ERROR_REQUEST_TIMEOUT (App should exit)
    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message=ERROR_REQUEST_TIMEOUT),
    )
    mock_qapp.return_value.exit.assert_called_once()

    # Reset QApplication mock for next test
    mock_qapp.return_value.exit.reset_mock()

    # Test Case: ERROR_PASSWORD_INCORRECT (Navigate to enter password)
    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message=ERROR_PASSWORD_INCORRECT),
    )
    mock_instance.enter_wallet_password_page_signal.emit.assert_called_once()

    # Reset mocks for next test
    mock_instance.enter_wallet_password_page_signal.emit.reset_mock()

    mock_instance.set_wallet_password_page_signal.emit.assert_called_once()

    # Reset mocks for next test
    mock_instance.set_wallet_password_page_signal.emit.reset_mock()

    # Test Case: ERROR_CONNECTION_FAILED_WITH_LN (Node is NOT running)
    with patch.object(splash_viewmodel, 'restart_ln_node_after_crash') as mock_restart:
        # Reset error handled state
        splash_viewmodel.is_error_handled = False

        # Set up node manager mock
        splash_viewmodel.ln_node_manager = MagicMock()
        splash_viewmodel.ln_node_manager.process = MagicMock()
        splash_viewmodel.ln_node_manager.process.state = MagicMock(
            return_value=QProcess.ProcessState.NotRunning,
        )

        # Call with exact error message
        splash_viewmodel.on_error_of_unlock_api(
            CommonException(message=ERROR_CONNECTION_FAILED_WITH_PROVIDED_URL),
        )
        mock_restart.assert_called_once()

    # Test Case: ERROR_CONNECTION_FAILED_WITH_LN (Node is running)
    # Reset all state and create fresh mock instance
    splash_viewmodel.is_error_handled = False
    splash_viewmodel.is_from_retry = False
    mock_error_dialog_instance = MagicMock(exec=MagicMock())
    mock_error_dialog.return_value = mock_error_dialog_instance
    splash_viewmodel.ln_node_manager.process.state.return_value = QProcess.ProcessState.Running

    splash_viewmodel.on_error_of_unlock_api(
        CommonException(message=ERROR_CONNECTION_FAILED_WITH_PROVIDED_URL),
    )
    mock_error_dialog_instance.exec.assert_called_once()
    assert splash_viewmodel.is_error_handled is True


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
    mock_node_info = Mock()
    mock_node_info.pubkey = 'test_pubkey'
    mock_common_repo.node_info.return_value = mock_node_info

    # Act
    view_model.on_success_of_unlock_api()

    # Assert
    view_model.render_timer.stop.assert_called_once()
    page_navigation.fungibles_asset_page.assert_called_once()
    mock_common_repo.node_info.assert_called_once()
    mock_set_value.assert_called_once_with('node_pub_key', 'test_pubkey')


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
    mock_common_repo.node_info.return_value = None

    # Act
    view_model.on_success_of_unlock_api()

    # Assert
    view_model.render_timer.stop.assert_called_once()
    page_navigation.fungibles_asset_page.assert_called_once()
    mock_common_repo.node_info.assert_called_once()
    mock_set_value.assert_not_called()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_handle_application_open_common_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests handle_application_open method when CommonException occurs."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    error_message = 'Test error'
    mock_setting_repo.get_wallet_type.side_effect = CommonException(
        error_message,
    )

    # Act
    view_model.handle_application_open()

    # Assert
    mock_setting_repo.get_wallet_type.assert_called_once()
    mock_toast_manager.error.assert_called_once_with(description=error_message)


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_handle_application_open_generic_exception(mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests handle_application_open method when generic Exception occurs."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    mock_setting_repo.get_wallet_type.side_effect = Exception(
        'Unexpected error',
    )

    # Act
    view_model.handle_application_open()

    # Assert
    mock_setting_repo.get_wallet_type.assert_called_once()
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


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
@patch('src.viewmodels.splash_view_model.get_bitcoin_config')
@patch('src.viewmodels.splash_view_model.CommonOperationRepository')
def test_handle_application_open_keyring_disabled(mock_common_repo, mock_bitcoin_config, mock_get_value, mock_qapp, mock_toast_manager, mock_setting_repo):
    """Tests handle_application_open method when keyring is disabled."""
    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.splash_screen_message = Mock()
    view_model.sync_chain_info_label = Mock()
    mock_setting_repo.get_keyring_status.return_value = False
    mock_wallet_password = 'test_password'
    mock_get_value.return_value = mock_wallet_password
    mock_bitcoin_config.return_value = 'test_config'

    # Act
    view_model.handle_application_open()

    # Assert
    mock_setting_repo.get_keyring_status.assert_called_once()
    view_model.splash_screen_message.emit.assert_called_once()
    view_model.sync_chain_info_label.emit.assert_called_once_with(True)
    mock_get_value.assert_called_once()
    mock_bitcoin_config.assert_called_once()
    assert hasattr(view_model, 'worker')
