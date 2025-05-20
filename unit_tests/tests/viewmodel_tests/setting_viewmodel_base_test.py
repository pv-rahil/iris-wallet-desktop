"""Unit test for setting view model base functionality.

This module contains unit tests for the base functionality of the SettingViewModel class.
The SettingViewModel handles user preferences and application settings including:

- Native authentication and login settings
- Asset visibility preferences (hidden/exhausted assets)
- Default values for network parameters:
  - Fee rates
  - Expiry times
  - Indexer URLs
  - Minimum confirmations
- Error handling and user notifications via toast messages
- Navigation between setting pages and sections

The tests verify the proper behavior of settings management, error cases,
and interaction with the underlying repositories and UI components.
"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultIndexerUrl
from src.model.setting_model import DefaultMinConfirmation
from src.model.setting_model import DefaultProxyEndpoint
from src.model.setting_model import IsHideExhaustedAssetEnabled
from src.model.setting_model import IsNativeLoginIntoAppEnabled
from src.model.setting_model import IsShowHiddenAssetEnabled
from src.model.setting_model import NativeAuthenticationStatus
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.setting_view_model import SettingViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def setting_view_model(mock_page_navigation):
    """Fixture to create an instance of the SettingViewModel class."""
    return SettingViewModel(mock_page_navigation)


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.SettingRepository.native_authentication')
def test_enable_native_logging(mock_native_auth, mock_toast_manager, mock_setting_repository):
    """Test the enable_native_logging method."""
    page_navigation = MagicMock()

    view_model = SettingViewModel(page_navigation=page_navigation)
    mock_setting_repository.native_login_enabled.return_value = IsNativeLoginIntoAppEnabled(
        is_enabled=True,
    )
    mock_native_auth.return_value = True
    # Connect the signal to a mock slot
    native_auth_logging_event_slot = Mock()
    view_model.native_auth_logging_event.connect(
        native_auth_logging_event_slot,
    )

    view_model.enable_native_logging(True)

    # Test exception handling
    mock_setting_repository.enable_logging_native_authentication.side_effect = CommonException(
        'Error',
    )
    view_model.enable_native_logging(False)

    mock_setting_repository.enable_logging_native_authentication.side_effect = Exception
    view_model.enable_native_logging(False)


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.SettingRepository.native_authentication')
def test_enable_native_authentication(mock_native_auth, mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test the enable_native_authentication method."""
    mock_setting_repository.get_native_authentication_status.return_value = NativeAuthenticationStatus(
        is_enabled=True,
    )

    mock_native_auth.return_value = True

    # Connect the signal to a mock slot
    native_auth_enable_event_slot = Mock()
    setting_view_model.native_auth_enable_event.connect(
        native_auth_enable_event_slot,
    )

    setting_view_model.enable_native_authentication(True)

    # Test exception handling
    mock_setting_repository.set_native_authentication_status.side_effect = CommonException(
        'Error',
    )
    setting_view_model.enable_native_authentication(False)

    mock_setting_repository.set_native_authentication_status.side_effect = Exception
    setting_view_model.enable_native_authentication(False)


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_enable_exhausted_asset_true(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test the enable_exhausted_asset method when set (true)."""
    mock_setting_repository.enable_exhausted_asset.return_value = IsHideExhaustedAssetEnabled(
        is_enabled=True,
    )

    # Connect the signal to a mock slot
    exhausted_asset_event_slot = Mock()
    setting_view_model.exhausted_asset_event.connect(
        exhausted_asset_event_slot,
    )
    setting_view_model.enable_exhausted_asset(True)

    mock_setting_repository.enable_exhausted_asset.assert_called_once_with(
        True,
    )
    exhausted_asset_event_slot.assert_called_once_with(True)

    # Test exception handling
    mock_setting_repository.enable_exhausted_asset.side_effect = CommonException(
        'Error',
    )
    setting_view_model.enable_exhausted_asset(False)
    exhausted_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description='Error',
    )

    mock_setting_repository.enable_exhausted_asset.side_effect = Exception
    setting_view_model.enable_exhausted_asset(False)
    exhausted_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_enable_exhausted_asset_false(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test the enable_exhausted_asset method when not set (false)."""
    mock_setting_repository.enable_exhausted_asset.return_value = IsHideExhaustedAssetEnabled(
        is_enabled=False,
    )

    # Connect the signal to a mock slot
    exhausted_asset_event_slot = Mock()
    setting_view_model.exhausted_asset_event.connect(
        exhausted_asset_event_slot,
    )

    setting_view_model.enable_exhausted_asset(True)

    mock_setting_repository.enable_exhausted_asset.assert_called_once_with(
        True,
    )
    exhausted_asset_event_slot.assert_called_once_with(False)

    # Test exception handling
    mock_setting_repository.enable_exhausted_asset.side_effect = CommonException(
        'Error',
    )
    setting_view_model.enable_exhausted_asset(False)
    exhausted_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description='Error',
    )

    mock_setting_repository.enable_exhausted_asset.side_effect = Exception
    setting_view_model.enable_exhausted_asset(False)
    exhausted_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_enable_hide_asset_true(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test the enable_hide_asset method when set(True)."""
    mock_setting_repository.enable_show_hidden_asset.return_value = IsShowHiddenAssetEnabled(
        is_enabled=True,
    )

    # Connect the signal to a mock slot
    hide_asset_event_slot = Mock()
    setting_view_model.hide_asset_event.connect(hide_asset_event_slot)

    setting_view_model.enable_hide_asset(True)

    mock_setting_repository.enable_show_hidden_asset.assert_called_once_with(
        True,
    )
    hide_asset_event_slot.assert_called_once_with(True)
    # Test exception handling
    mock_setting_repository.enable_show_hidden_asset.side_effect = CommonException(
        'Error',
    )
    setting_view_model.enable_hide_asset(False)
    hide_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(description='Error')

    mock_setting_repository.enable_show_hidden_asset.side_effect = Exception
    setting_view_model.enable_hide_asset(False)
    hide_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_enable_hide_asset_false(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test the enable_hide_asset method when not set(false)."""
    mock_setting_repository.enable_show_hidden_asset.return_value = IsShowHiddenAssetEnabled(
        is_enabled=False,
    )

    # Connect the signal to a mock slot
    hide_asset_event_slot = Mock()
    setting_view_model.hide_asset_event.connect(hide_asset_event_slot)

    setting_view_model.enable_hide_asset(True)

    mock_setting_repository.enable_show_hidden_asset.assert_called_once_with(
        True,
    )
    hide_asset_event_slot.assert_called_once_with(False)
    # Test exception handling
    mock_setting_repository.enable_show_hidden_asset.side_effect = CommonException(
        'Error',
    )
    setting_view_model.enable_hide_asset(False)
    hide_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description='Error',
    )

    mock_setting_repository.enable_show_hidden_asset.side_effect = Exception
    setting_view_model.enable_hide_asset(False)
    hide_asset_event_slot.assert_called_with(True)
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.SettingCardRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_page_load(mock_toast_manager, mock_setting_card_repository, mock_setting_repository, setting_view_model):
    """Test the on_page_load method."""

    # Patch the on_page_load_event signal so we can track the emit calls
    with patch.object(setting_view_model, 'on_page_load_event', new_callable=MagicMock) as mock_on_page_load_event:

        # Arrange mock responses from the repository
        mock_setting_repository.get_native_authentication_status.return_value = NativeAuthenticationStatus(
            is_enabled=True,
        )
        mock_setting_repository.native_login_enabled.return_value = IsNativeLoginIntoAppEnabled(
            is_enabled=True,
        )
        mock_setting_repository.is_show_hidden_assets_enabled.return_value = IsShowHiddenAssetEnabled(
            is_enabled=True,
        )
        mock_setting_repository.is_exhausted_asset_enabled.return_value = IsHideExhaustedAssetEnabled(
            is_enabled=True,
        )
        mock_setting_card_repository.get_default_fee_rate.return_value = DefaultFeeRate(
            fee_rate=5,
        )
        mock_setting_card_repository.get_default_indexer_url.return_value = DefaultIndexerUrl(
            url='http://localhost:8080',
        )
        mock_setting_card_repository.get_default_proxy_endpoint.return_value = DefaultProxyEndpoint(
            endpoint='http://localhost:8080',
        )
        mock_setting_card_repository.get_default_min_confirmation.return_value = DefaultMinConfirmation(
            min_confirmation=6,
        )

        # Act
        setting_view_model.on_page_load()

        # Verify that the emit method was called
        mock_on_page_load_event.emit.assert_called_once()

        # Get the actual model that was emitted
        actual_model = mock_on_page_load_event.emit.call_args[0][0]

        # Verify the model properties
        assert actual_model.status_of_native_auth.is_enabled is True
        assert actual_model.status_of_native_logging_auth.is_enabled is True
        assert actual_model.status_of_exhausted_asset.is_enabled is True
        assert actual_model.status_of_hide_asset.is_enabled is True
        assert actual_model.value_of_default_fee.fee_rate == 5
        assert actual_model.value_of_default_indexer_url.url == 'http://localhost:8080'
        assert actual_model.value_of_default_proxy_endpoint.endpoint == 'http://localhost:8080'
        assert actual_model.value_of_default_min_confirmation.min_confirmation == 6

        # Test exception handling for CommonException
        mock_setting_repository.get_native_authentication_status.side_effect = CommonException(
            'Error',
        )
        setting_view_model.on_page_load()
        mock_toast_manager.error.assert_called_with(description='Error')
        setting_view_model._page_navigation.fungibles_asset_page.assert_called_once()

        # Reset the mock for the next test
        setting_view_model._page_navigation.fungibles_asset_page.reset_mock()

        # Test exception handling for general Exception
        mock_setting_repository.get_native_authentication_status.side_effect = Exception()
        setting_view_model.on_page_load()
        mock_toast_manager.error.assert_called_with(
            description=ERROR_SOMETHING_WENT_WRONG,
        )
        setting_view_model._page_navigation.fungibles_asset_page.assert_called_once()


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_of_keyring_validation(mock_toast_manager, setting_view_model):
    """Test the on_success_of_keyring_validation method."""
    # Mock signals
    setting_view_model.loading_status = MagicMock()
    setting_view_model.on_success_validation_keyring_event = MagicMock()

    # Call the method
    setting_view_model.on_success_of_keyring_validation()

    # Assert that loading_status.emit was called with False
    setting_view_model.loading_status.emit.assert_called_once_with(False)

    # Assert that on_success_validation_keyring_event.emit was called
    setting_view_model.on_success_validation_keyring_event.emit.assert_called_once()


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_of_keyring_enable_validation_with_common_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_of_keyring_enable_validation method with a CommonException."""
    # Mock signals
    setting_view_model.loading_status = MagicMock()
    setting_view_model.on_error_validation_keyring_event = MagicMock()

    # Create a CommonException
    error = CommonException(message='Test Error')

    # Call the method with the CommonException
    setting_view_model.on_error_of_keyring_enable_validation(error)

    # Assert that loading_status.emit was called with False
    setting_view_model.loading_status.emit.assert_called_once_with(False)

    # Assert that on_error_validation_keyring_event.emit was called
    setting_view_model.on_error_validation_keyring_event.emit.assert_called_once()

    # Assert that the ToastManager.show_toast was called with the expected arguments
    mock_toast_manager.error.assert_called_once_with(description='Test Error')


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_of_keyring_enable_validation_with_general_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_of_keyring_enable_validation method with a general exception."""
    # Mock signals
    setting_view_model.loading_status = MagicMock()
    setting_view_model.on_error_validation_keyring_event = MagicMock()

    # Create a general Exception
    error = Exception('General Error')

    # Call the method with the general Exception
    setting_view_model.on_error_of_keyring_enable_validation(error)

    # Assert that loading_status.emit was called with False
    setting_view_model.loading_status.emit.assert_called_once_with(False)

    # Assert that on_error_validation_keyring_event.emit was called
    setting_view_model.on_error_validation_keyring_event.emit.assert_called_once()

    # Assert that the ToastManager.show_toast was called with the expected arguments
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository.enable_logging_native_authentication')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_native_login_fail_to_set(mock_toast_manager, mock_enable_logging, setting_view_model):
    """Test the on_success_native_login method when native login is successful but setting fails."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_logging_event = MagicMock()
    setting_view_model.login_toggle = True

    # Set the mock return value
    mock_enable_logging.return_value = False

    # Call the method
    setting_view_model.on_success_native_login(True)

    # Check that enable_logging_native_authentication was called with the correct parameter
    mock_enable_logging.assert_called_once_with(True)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_logging_event.emit.assert_called_once_with(
        False,
    )

    # Check that ToastManager.error was called with the correct parameters
    mock_toast_manager.info.assert_called_once_with(description=ERROR_KEYRING)


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_native_login_failure(mock_toast_manager, setting_view_model):
    """Test the on_success_native_login method when native login fails."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_logging_event = MagicMock()
    setting_view_model.login_toggle = True

    # Call the method
    setting_view_model.on_success_native_login(False)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_logging_event.emit.assert_called_once_with(
        False,
    )

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository.set_native_authentication_status')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_native_auth_success(mock_toast_manager, mock_set_auth, setting_view_model):
    """Test the on_success_native_auth method when native auth is successful."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_enable_event = MagicMock()
    setting_view_model.auth_toggle = True

    # Set the mock return value
    mock_set_auth.return_value = True

    # Call the method
    setting_view_model.on_success_native_auth(True)

    # Check that set_native_authentication_status was called with the correct parameter
    mock_set_auth.assert_called_once_with(True)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_enable_event.emit.assert_called_once_with(
        True,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository.set_native_authentication_status')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_native_auth_fail_to_set(mock_toast_manager, mock_set_auth, setting_view_model):
    """Test the on_success_native_auth method when native auth is successful but setting fails."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_enable_event = MagicMock()
    setting_view_model.auth_toggle = True

    # Set the mock return value
    mock_set_auth.return_value = False

    # Call the method
    setting_view_model.on_success_native_auth(True)

    # Check that set_native_authentication_status was called with the correct parameter
    mock_set_auth.assert_called_once_with(True)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_enable_event.emit.assert_called_once_with(
        False,
    )

    # Check that ToastManager.info was called with the correct parameters
    mock_toast_manager.info.assert_called_once_with(description=ERROR_KEYRING)


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_success_native_auth_failure(mock_toast_manager, setting_view_model):
    """Test the on_success_native_auth method when native auth fails."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_enable_event = MagicMock()
    setting_view_model.auth_toggle = True

    # Call the method
    setting_view_model.on_success_native_auth(False)

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_native_login_common_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_native_login method when a CommonException is raised."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_logging_event = MagicMock()
    setting_view_model.login_toggle = True

    # Create a CommonException
    error = CommonException('Test error message')

    # Call the method
    setting_view_model.on_error_native_login(error)

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(description=error.message)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_logging_event.emit.assert_called_once_with(
        False,
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_native_login_generic_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_native_login method when a generic Exception is raised."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_logging_event = MagicMock()
    setting_view_model.login_toggle = True

    # Create a generic Exception
    error = Exception('Generic error')

    # Call the method
    setting_view_model.on_error_native_login(error)

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )

    # Check that the correct signal was emitted
    setting_view_model.native_auth_logging_event.emit.assert_called_once_with(
        False,
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_native_auth_common_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_native_auth method when a CommonException is raised."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_enable_event = MagicMock()
    setting_view_model.auth_toggle = True

    # Create a CommonException
    error = CommonException('Test error message')

    # Call the method
    setting_view_model.on_error_native_auth(error)

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(description=error.message)

    # Check that the correct signal was emitted
    setting_view_model.native_auth_enable_event.emit.assert_called_once_with(
        False,
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_native_auth_generic_exception(mock_toast_manager, setting_view_model):
    """Test the on_error_native_auth method when a generic Exception is raised."""
    # Mock the signal and other attributes
    setting_view_model.native_auth_enable_event = MagicMock()
    setting_view_model.auth_toggle = True

    # Create a generic Exception
    error = Exception('Generic error')

    # Call the method
    setting_view_model.on_error_native_auth(error)

    # Check that ToastManager.show_toast was called with the correct parameters
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )

    # Check that the correct signal was emitted
    setting_view_model.native_auth_enable_event.emit.assert_called_once_with(
        False,
    )


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_page_load_common_exception(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test on_page_load when CommonException occurs."""
    setting_view_model._page_navigation = Mock()
    mock_setting_repository.get_native_authentication_status.side_effect = CommonException(
        'Test error',
    )

    setting_view_model.on_page_load()

    mock_toast_manager.error.assert_called_once_with(description='Test error')
    setting_view_model._page_navigation.fungibles_asset_page.assert_called_once()


@patch('src.viewmodels.setting_view_model.SettingRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_page_load_generic_exception(mock_toast_manager, mock_setting_repository, setting_view_model):
    """Test on_page_load when generic Exception occurs."""
    setting_view_model._page_navigation = Mock()
    mock_setting_repository.get_native_authentication_status.side_effect = Exception()

    setting_view_model.on_page_load()

    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    setting_view_model._page_navigation.fungibles_asset_page.assert_called_once()


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_of_keyring_enable_validation_common_exception(mock_toast_manager, setting_view_model):
    """Test on_error_of_keyring_enable_validation with CommonException."""
    setting_view_model.on_error_validation_keyring_event = Mock()
    setting_view_model.loading_status = Mock()
    error = CommonException('Test error')

    setting_view_model.on_error_of_keyring_enable_validation(error)

    setting_view_model.on_error_validation_keyring_event.emit.assert_called_once()
    setting_view_model.loading_status.emit.assert_called_once_with(False)
    mock_toast_manager.error.assert_called_once_with(description='Test error')


@patch('src.viewmodels.setting_view_model.ToastManager')
def test_on_error_of_keyring_enable_validation_generic_exception(mock_toast_manager, setting_view_model):
    """Test on_error_of_keyring_enable_validation with generic Exception."""
    setting_view_model.on_error_validation_keyring_event = Mock()
    setting_view_model.loading_status = Mock()
    error = Exception()

    setting_view_model.on_error_of_keyring_enable_validation(error)

    setting_view_model.on_error_validation_keyring_event.emit.assert_called_once()
    setting_view_model.loading_status.emit.assert_called_once_with(False)
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.CommonOperationService')
def test_enable_keyring(mock_common_operation_service, setting_view_model):
    """Test enable_keyring method."""
    setting_view_model.loading_status = Mock()
    setting_view_model.run_in_thread = Mock()

    password = 'test password'

    setting_view_model.enable_keyring(password)

    setting_view_model.loading_status.emit.assert_called_once_with(True)
    setting_view_model.run_in_thread.assert_called_once()
    call_args = setting_view_model.run_in_thread.call_args[0][1]
    assert call_args['args'] == [password]
    assert call_args['callback'] == setting_view_model.on_success_of_keyring_validation
    assert call_args['error_callback'] == setting_view_model.on_error_of_keyring_enable_validation
