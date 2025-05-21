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

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NATIVE_AUTHENTICATION
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.splash_view_model import ACCOUNT_XPUB
from src.viewmodels.splash_view_model import ERROR_RGB_LIB_INCOMPATIBILITY
from src.viewmodels.splash_view_model import SplashViewModel
from src.viewmodels.splash_view_model import WALLET_PASSWORD_KEY
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
    # Simulate valid RGB commit
    view_model.is_rgb_lib_version_valid = Mock(return_value=True)
    mock_setting_repo.get_keyring_status.return_value = True
    mock_setting_repo.get_wallet_network.return_value = Mock(value='testnet')

    # Act
    view_model.handle_application_open()

    # Assert
    mock_setting_repo.get_keyring_status.assert_called_once()
    page_navigation.enter_wallet_password_page.assert_called_once()


@patch('src.viewmodels.splash_view_model.WalletRequestModel')
@patch('src.viewmodels.splash_view_model.get_bitcoin_network_from_enum')
@patch('src.viewmodels.splash_view_model.local_store')
@patch('src.viewmodels.splash_view_model.app_paths')
@patch('src.viewmodels.splash_view_model.QCoreApplication')
@patch('src.viewmodels.splash_view_model.mnemonic_store')
@patch('src.viewmodels.splash_view_model.get_value')
@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.logger')
def test_handle_application_open_main_flow(
    mock_logger,
    mock_setting_repo,
    mock_get_value,
    mock_mnemonic_store,
    mock_qcore,
    mock_app_paths,
    mock_local_store,
    mock_get_network,
    mock_wallet_request_model,
):
    """Test handle_application_open for main flows (valid/invalid RGB, keyring, password present/missing)."""

    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.splash_screen_message = Mock()
    view_model.sync_chain_info_label = Mock()
    view_model.handle_node_incompatibility = Mock()
    view_model.run_in_thread = Mock()

    # --- Case 1: Valid RGB commit, keyring enabled ---
    mock_setting_repo.get_keyring_status.return_value = True
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_value.return_value = None
    view_model.is_rgb_lib_version_valid = Mock(return_value=True)

    view_model.handle_application_open()
    mock_setting_repo.get_keyring_status.assert_called()
    page_navigation.enter_wallet_password_page.assert_called_once()
    # Reset for next case
    page_navigation.enter_wallet_password_page.reset_mock()

    # --- Case 2: Valid RGB commit, keyring disabled, wallet_password present ---
    mock_setting_repo.get_keyring_status.return_value = False
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.TESTNET
    mock_get_value.return_value = 'test_password'
    mock_mnemonic_file_path = 'test_path'
    mock_app_path = 'test_app_path'
    mock_app_paths.mnemonic_file_path = mock_mnemonic_file_path
    mock_app_paths.app_path = mock_app_path
    mock_mnemonic_store.decrypt.return_value = 'decrypted_mnemonic'
    mock_qcore.translate.return_value = 'wait_for_node_to_unlock'
    mock_get_network.return_value = 'bitcoin_network'
    mock_local_store.get_value.return_value = 'account_xpub'
    mock_wallet_instance = Mock()
    mock_wallet_request_model.return_value = mock_wallet_instance

    view_model.handle_application_open()
    mock_setting_repo.get_keyring_status.assert_called()
    mock_setting_repo.get_wallet_network.assert_called()
    mock_get_value.assert_called_with(
        WALLET_PASSWORD_KEY, NetworkEnumModel.TESTNET.value,
    )
    mock_mnemonic_store.decrypt.assert_called_with(
        password='test_password', path=mock_mnemonic_file_path,
    )
    view_model.splash_screen_message.emit.assert_called_with(
        'wait_for_node_to_unlock',
    )
    view_model.sync_chain_info_label.emit.assert_called_with(True)
    mock_get_network.assert_called()
    mock_local_store.get_value.assert_called_with(ACCOUNT_XPUB)
    mock_wallet_request_model.assert_called_with(
        data_dir=mock_app_path,
        bitcoin_network='bitcoin_network',
        account_xpub='account_xpub',
        mnemonic='decrypted_mnemonic',
    )
    view_model.run_in_thread.assert_called()
    # Reset for next case
    view_model.splash_screen_message.emit.reset_mock()
    view_model.sync_chain_info_label.emit.reset_mock()
    view_model.run_in_thread.reset_mock()

    # --- Case 3: Valid RGB commit, keyring disabled, wallet_password is None ---
    mock_setting_repo.get_keyring_status.return_value = False
    mock_get_value.return_value = None
    view_model.handle_application_open()
    page_navigation.enter_wallet_password_page.assert_called()

    # --- Case 4: Invalid RGB commit ---
    view_model.is_rgb_lib_version_valid = Mock(return_value=False)
    view_model.handle_application_open()
    mock_logger.error.assert_any_call(ERROR_RGB_LIB_INCOMPATIBILITY)
    view_model.handle_node_incompatibility.assert_called_once()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.ToastManager')
@patch('src.viewmodels.splash_view_model.logger')
def test_handle_application_open_error_handling(
    mock_logger,
    mock_toast_manager,
    mock_setting_repo,
):
    """Test handle_application_open for error handling (CommonException, generic Exception)."""

    # Arrange
    page_navigation = Mock()
    view_model = SplashViewModel(page_navigation)
    view_model.splash_screen_message = Mock()
    view_model.sync_chain_info_label = Mock()
    view_model.handle_node_incompatibility = Mock()
    view_model.run_in_thread = Mock()

    # --- Case 5: CommonException is raised ---
    mock_setting_repo.get_keyring_status.side_effect = CommonException(
        'common error',
    )
    view_model.is_rgb_lib_version_valid = Mock(return_value=True)
    view_model.handle_node_incompatibility.reset_mock()
    view_model.run_in_thread.reset_mock()
    page_navigation.enter_wallet_password_page.reset_mock()
    mock_logger.reset_mock()
    mock_toast_manager.reset_mock()
    view_model.splash_screen_message.emit.reset_mock()
    view_model.sync_chain_info_label.emit.reset_mock()
    try:
        view_model.handle_application_open()
    except Exception:
        pass
    mock_logger.error.assert_any_call(
        'Exception occurred at handle_application_open: %s, Message: %s',
        'CommonException', 'common error',
    )
    mock_toast_manager.error.assert_called_with(description='common error')
    mock_setting_repo.get_keyring_status.side_effect = None

    # --- Case 6: Generic Exception is raised ---
    mock_setting_repo.get_keyring_status.side_effect = Exception(
        'generic error',
    )
    view_model.is_rgb_lib_version_valid = Mock(return_value=True)
    try:
        view_model.handle_application_open()
    except Exception:
        pass
    mock_logger.error.assert_any_call(
        'Exception occurred at handle_application_open: %s, Message: %s',
        'Exception', 'generic error',
    )
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    mock_setting_repo.get_keyring_status.side_effect = None


@patch('src.viewmodels.splash_view_model.RgbLibIncompatibilityDialog', autospec=True)
@patch('src.viewmodels.splash_view_model.delete_app_data')
@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.local_store')
def test_delete_app_data(
    mock_local_store, mock_setting_repo, mock_delete_app_data, mock_node_incompatibility, splash_viewmodel,
):
    """Test delete_app_data method to ensure the correct flow when a node is incompatible."""

    # Mock local_store.get_path()
    mock_local_store.get_path.return_value = 'test/path'

    # Mock SettingRepository.get_wallet_network() to return a proper enum value
    mock_setting_repo.get_wallet_network.return_value = NetworkEnumModel.MAINNET

    # Create a mock instance of the dialog
    mock_dialog_instance = MagicMock()
    mock_node_incompatibility.return_value = mock_dialog_instance

    # Prevent the dialog from being shown
    mock_dialog_instance.exec_ = MagicMock()

    # Simulate button clicks
    mock_dialog_instance.node_incompatibility_dialog.clickedButton.return_value = (
        mock_dialog_instance.on_delete_app_data_button
    )
    mock_dialog_instance.confirmation_dialog.clickedButton.return_value = (
        mock_dialog_instance.confirm_delete_button
    )

    # Call the method under test
    splash_viewmodel.on_delete_app_data()

    # Ensure delete_app_data() was called with correct arguments
    mock_delete_app_data.assert_called_once_with(
        'test/path', network=NetworkEnumModel.MAINNET.value,
    )

    # Ensure navigation to welcome page
    splash_viewmodel._page_navigation.welcome_page.assert_called_once()


@patch('src.viewmodels.splash_view_model.RgbLibIncompatibilityDialog')
@patch('src.viewmodels.splash_view_model.QApplication')
def test_handle_node_incompatibility(mock_qapp, mock_rgb_lib_incompatibility, splash_viewmodel):
    """Test handle_node_incompatibility method ensuring correct flow without GUI pop-ups."""

    # Create a mock instance of RgbLibIncompatibilityDialog
    mock_rgb_lib_instance = mock_rgb_lib_incompatibility.return_value

    # Mock delete app data button click
    mock_rgb_lib_instance.node_incompatibility_dialog.clickedButton.return_value = (
        mock_rgb_lib_instance.delete_app_data_button
    )
    mock_rgb_lib_instance.confirmation_dialog.clickedButton.return_value = (
        mock_rgb_lib_instance.confirm_delete_button
    )

    # Mock necessary methods
    splash_viewmodel.on_delete_app_data = MagicMock()
    splash_viewmodel.handle_application_open = MagicMock()

    # Act - Simulate handling node incompatibility
    splash_viewmodel.handle_node_incompatibility()

    # Assert - Ensure correct methods are called
    mock_rgb_lib_instance.show_confirmation_dialog.assert_called_once()
    splash_viewmodel.on_delete_app_data.assert_called_once()
    splash_viewmodel.handle_application_open.assert_not_called()
    mock_qapp.instance().exit.assert_not_called()

    # Test case where cancel is clicked instead
    mock_rgb_lib_instance.confirmation_dialog.clickedButton.return_value = (
        mock_rgb_lib_instance.cancel
    )

    splash_viewmodel.handle_node_incompatibility()

    # Assert cancel behavior
    splash_viewmodel.handle_application_open.assert_called_once()
    splash_viewmodel.on_delete_app_data.assert_called_once()


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.COMPATIBLE_RGB_LIB_VERSION', new=['version1', 'version2'])
def test_is_rgb_lib_version_valid(mock_setting_repo, splash_viewmodel):
    """Test is_rgb_commit_valid returns True when commit is compatible."""
    mock_setting_repo.get_rgb_lib_version.return_value = 'version1'
    assert splash_viewmodel.is_rgb_lib_version_valid() is True


@patch('src.viewmodels.splash_view_model.SettingRepository')
@patch('src.viewmodels.splash_view_model.COMPATIBLE_RGB_LIB_VERSION', new=['version1', 'version2'])
def test_is_rgb_lib_version_invalid(mock_setting_repo, splash_viewmodel):
    """Test is_rgb_commit_valid returns False when commit is not compatible."""
    mock_setting_repo.get_rgb_lib_version.return_value = 'invalid_commit'
    assert splash_viewmodel.is_rgb_lib_version_valid() is False
