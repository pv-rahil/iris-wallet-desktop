"""Unit test cases for enter wallet password page"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QWidget

from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import UnlockResponseModel
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import ToastPreset
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NETWORK_MISMATCH
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_WALLET_PASSWORD_SET
from src.utils.info_message import INFO_WALLET_UNLOCK_SUCCESSFULLY
from src.viewmodels.enter_password_view_model import EnterWalletPasswordViewModel
from src.views.components.custom_toast import ToasterManager


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def enter_wallet_password_view_model(mock_page_navigation):
    """Fixture to create an instance of the EnterWalletPasswordViewModel class."""
    return EnterWalletPasswordViewModel(mock_page_navigation)


def test_toggle_password_visibility(enter_wallet_password_view_model, mocker):
    """Test for toggle visibility working as expected"""
    line_edit_mock = mocker.MagicMock(spec=QLineEdit)

    assert (
        enter_wallet_password_view_model.toggle_password_visibility(
            line_edit_mock,
        )
        is False
    )
    line_edit_mock.setEchoMode.assert_called_once_with(QLineEdit.Normal)

    assert (
        enter_wallet_password_view_model.toggle_password_visibility(
            line_edit_mock,
        )
        is True
    )
    line_edit_mock.setEchoMode.assert_called_with(QLineEdit.Password)


# def test_on_success(enter_wallet_password_view_model, mocker):
#     """Test for on_success method"""
#     mock_message = Mock()
#     enter_wallet_password_view_model.message.connect(mock_message)

#     response = UnlockResponseModel(status=True)
#     enter_wallet_password_view_model.password = 'test_password'

#     with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network, \
#             patch('src.data.repository.setting_repository.SettingRepository.get_keyring_status') as mock_get_keyring_status, \
#             patch('src.utils.keyring_storage.set_value') as mock_set_value, \
#             patch('src.data.repository.setting_repository.SettingRepository.set_keyring_status') as mock_set_keyring_status, \
#             patch('src.data.repository.setting_repository.SettingRepository.set_wallet_initialized') as mock_set_wallet_initialized, \
#             patch('src.viewmodels.enter_password_view_model.EnterWalletPasswordViewModel.forward_to_fungibles_page') as mock_forward_to_fungibles_page:

#         mock_get_wallet_network.return_value = Mock(value='test_network')
#         mock_get_keyring_status.return_value = False
#         mock_set_value.return_value = True

#         enter_wallet_password_view_model.on_success(response)

#         mock_message.assert_called_once_with(
#             ToastPreset.SUCCESS, 'Wallet password set successfully',
#         )
#         mock_set_keyring_status.assert_called_once_with(False)
#         mock_set_wallet_initialized.assert_called_once()
#         mock_forward_to_fungibles_page.assert_called_once()


# def test_on_success_failure(enter_wallet_password_view_model, mocker):
#     """Test for on_success method when password is not set successfully"""
#     mock_message = Mock()
#     enter_wallet_password_view_model.message.connect(mock_message)

#     response = UnlockResponseModel(status=False)
#     enter_wallet_password_view_model.password = 'test_password'

#     enter_wallet_password_view_model.on_success(response)

#     mock_message.assert_called_once_with(
#         ToastPreset.ERROR, 'Unable to get password test_password',
#     )


def test_on_error(enter_wallet_password_view_model, mocker):
    """Test for on_error method"""
    exception = CommonException('Test error')

    # Ensure the main window is set properly
    ToasterManager.main_window = QWidget()

    with patch('src.utils.local_store.local_store.clear_settings') as mock_clear_settings, \
            patch('src.views.components.message_box.MessageBox') as mock_message_box, \
            patch('PySide6.QtWidgets.QApplication.instance') as mock_qt_app, \
            patch('src.views.components.toast.ToastManager.error') as mock_toast_error:

        enter_wallet_password_view_model.on_error(exception)

        mock_toast_error.assert_called_once_with(
            'Test error',
        )  # Check toast notification
        mock_clear_settings.assert_not_called()
        mock_message_box.assert_not_called()
        mock_qt_app.return_value.quit.assert_not_called()


def test_on_error_common_exception(enter_wallet_password_view_model, mocker):
    """Test for on_error method handling CommonException"""
    common_exception = CommonException('Test error')

    with patch('src.views.components.toast.ToastManager.error') as mock_toast_error:
        enter_wallet_password_view_model.on_error(common_exception)

        mock_toast_error.assert_called_once_with('Test error')


def test_on_success_with_keyring_status_false(enter_wallet_password_view_model, mocker):
    """Test for on_success method when keyring status is False"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = 'test_password'

    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network, \
            patch('src.data.repository.setting_repository.SettingRepository.get_keyring_status') as mock_get_keyring_status, \
            patch('src.utils.keyring_storage.set_value') as mock_set_value, \
            patch('src.data.repository.setting_repository.SettingRepository.set_keyring_status') as mock_set_keyring_status, \
            patch('src.data.repository.setting_repository.SettingRepository.set_wallet_initialized') as mock_set_wallet_initialized, \
            patch('src.viewmodels.enter_password_view_model.EnterWalletPasswordViewModel.forward_to_fungibles_page') as mock_forward_to_fungibles_page:

        mock_get_wallet_network.return_value = Mock(value='test_network')
        mock_get_keyring_status.return_value = False
        mock_set_value.return_value = True

        enter_wallet_password_view_model.on_success(response)

        mock_message.assert_called_once_with(
            ToastPreset.SUCCESS, 'Wallet password set successfully',
        )
        mock_set_keyring_status.assert_called_once_with(False)
        mock_set_wallet_initialized.assert_called_once()
        mock_forward_to_fungibles_page.assert_called_once()


def test_on_success_with_keyring_status_false_and_set_value_false(enter_wallet_password_view_model, mocker):
    """Test for on_success method when keyring status is False and set_value returns False"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = 'test_password'

    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network, \
            patch('src.data.repository.setting_repository.SettingRepository.get_keyring_status') as mock_get_keyring_status, \
            patch('src.utils.keyring_storage.set_value') as mock_set_value, \
            patch('src.data.repository.setting_repository.SettingRepository.set_keyring_status') as mock_set_keyring_status, \
            patch('src.data.repository.setting_repository.SettingRepository.set_wallet_initialized') as mock_set_wallet_initialized, \
            patch('src.viewmodels.enter_password_view_model.EnterWalletPasswordViewModel.forward_to_fungibles_page') as mock_forward_to_fungibles_page:

        mock_get_wallet_network.return_value = Mock(value='test_network')
        mock_get_keyring_status.return_value = False
        mock_set_value.return_value = False

        enter_wallet_password_view_model.on_success(response)

        mock_message.assert_called_once_with(
            ToastPreset.SUCCESS, 'Wallet password set successfully',
        )
        mock_set_keyring_status.assert_called_once_with(False)
        mock_set_wallet_initialized.assert_called_once()
        mock_forward_to_fungibles_page.assert_called_once()


def test_on_success_with_invalid_password(enter_wallet_password_view_model, mocker):
    """Test for on_success method with invalid password"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = None

    enter_wallet_password_view_model.on_success(response)

    mock_message.assert_called_once_with(
        ToastPreset.ERROR, 'Unable to get password None',
    )


def test_on_success_with_keyring_status_true(enter_wallet_password_view_model, mocker):
    """Test for on_success method when keyring status is True"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = 'test_password'

    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_get_wallet_network, \
            patch('src.data.repository.setting_repository.SettingRepository.get_keyring_status') as mock_get_keyring_status, \
            patch('src.data.repository.setting_repository.SettingRepository.set_wallet_initialized') as mock_set_wallet_initialized, \
            patch('src.viewmodels.enter_password_view_model.EnterWalletPasswordViewModel.forward_to_fungibles_page') as mock_forward_to_fungibles_page:

        mock_get_wallet_network.return_value = Mock(value='test_network')
        mock_get_keyring_status.return_value = True

        enter_wallet_password_view_model.on_success(response)

        mock_is_loading.assert_called_once_with(False)
        mock_forward_to_fungibles_page.assert_called_once()
        # Just mock it, no need to check actual call
        mock_set_wallet_initialized.assert_not_called()
        mock_message.assert_not_called()


def test_on_success_with_common_exception(enter_wallet_password_view_model, mocker):
    """Test for on_success method when CommonException occurs"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = 'test_password'

    error_message = 'Test error'
    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=CommonException(error_message),
    ):

        enter_wallet_password_view_model.on_success(response)

        mock_is_loading.assert_called_once_with(False)
        mock_message.assert_called_once_with(
            ToastPreset.ERROR,
            error_message,
        )


def test_on_success_with_generic_exception(enter_wallet_password_view_model, mocker):
    """Test for on_success method when generic Exception occurs"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)

    response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.password = 'test_password'

    with patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=Exception('Unexpected error'),
    ):

        enter_wallet_password_view_model.on_success(response)

        mock_is_loading.assert_called_once_with(False)
        mock_message.assert_called_once_with(
            ToastPreset.ERROR,
            'Something went wrong',
        )


# Mock MessageBox
@patch('src.viewmodels.enter_password_view_model.MessageBox', autospec=True)
def test_on_error_network_mismatch(
    mock_message_box, enter_wallet_password_view_model, mocker,
):
    """Test on_error method when network mismatch error occurs"""
    # Arrange
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)
    mock_clear_settings = mocker.patch(
        'src.utils.local_store.LocalStore.clear_settings',
    )

    error = CommonException(ERROR_NETWORK_MISMATCH)

    with patch('src.views.components.toast.ToastManager.error') as mock_toast_error:
        # Act
        enter_wallet_password_view_model.on_error(error)

        # Assert
        mock_is_loading.assert_called_once_with(False)
        mock_clear_settings.assert_called_once()
        mock_toast_error.assert_called_once_with(ERROR_NETWORK_MISMATCH)

        # Ensure MessageBox was called with the correct arguments
        mock_message_box.assert_called_once_with(
            'critical', ERROR_NETWORK_MISMATCH,
        )


def test_on_error_other_error(enter_wallet_password_view_model):
    """Test on_error method with non-network mismatch error"""
    # Arrange
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)
    error_message = 'Test error'
    error = CommonException(error_message)

    with patch('src.views.components.toast.ToastManager.error') as mock_toast_error:
        # Act
        enter_wallet_password_view_model.on_error(error)

        # Assert
        mock_is_loading.assert_called_once_with(False)
        mock_toast_error.assert_called_once_with(error_message)


def test_on_error_empty_message(enter_wallet_password_view_model):
    """Test on_error method when error message is empty"""
    # Arrange
    mock_is_loading = Mock()
    enter_wallet_password_view_model.is_loading.connect(mock_is_loading)

    error = CommonException('')

    with patch('src.views.components.toast.ToastManager.error') as mock_toast_error:
        # Act
        enter_wallet_password_view_model.on_error(error)

        # Assert
        mock_is_loading.assert_called_once_with(False)
        mock_toast_error.assert_called_once_with(ERROR_SOMETHING_WENT_WRONG)


def test_on_success_unlock_successful(enter_wallet_password_view_model, mocker):
    """Test successful unlocking with password set correctly and keyring status handling."""

    # Arrange
    enter_wallet_password_view_model.is_loading = MagicMock()
    enter_wallet_password_view_model.message = MagicMock()
    enter_wallet_password_view_model.forward_to_fungibles_page = MagicMock()

    enter_wallet_password_view_model.password = 'test_password'

    # Mock SettingRepository methods
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status',
        return_value=False,
    )  # keyring status false for this test
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_wallet_initialized',
    )

    # Mock the set_value method to return True (successful password set)
    mocker.patch(
        'src.viewmodels.enter_password_view_model.set_value', return_value=True,
    )

    # Act
    # Assuming you have the appropriate mock or actual model here
    unlock_response = UnlockResponseModel(status=True)
    enter_wallet_password_view_model.on_success(unlock_response)

    # Assert
    enter_wallet_password_view_model.is_loading.emit.assert_called_once_with(
        False,
    )
    enter_wallet_password_view_model.message.emit.assert_called_once_with(
        ToastPreset.SUCCESS, INFO_WALLET_PASSWORD_SET,
    )
    enter_wallet_password_view_model.forward_to_fungibles_page.assert_called_once()
    # In case it's needed after a successful unlock
    enter_wallet_password_view_model.forward_to_fungibles_page.assert_called_once()


def test_on_success_unlock_failed(enter_wallet_password_view_model, mocker):
    """Test failure in unlocking when password setting fails."""

    # Arrange
    enter_wallet_password_view_model.is_loading = MagicMock()
    enter_wallet_password_view_model.message = MagicMock()
    enter_wallet_password_view_model.forward_to_fungibles_page = MagicMock()

    enter_wallet_password_view_model.password = 'test_password'

    # Mock SettingRepository methods
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status',
        return_value=False,
    )  # keyring status false for this test
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_wallet_initialized',
    )

    # Mock the set_value method to return False (failed password set)
    mocker.patch(
        'src.viewmodels.enter_password_view_model.set_value', return_value=False,
    )

    # Act
    # Assuming you have the appropriate mock or actual model here
    unlock_response = UnlockResponseModel(status=False)
    enter_wallet_password_view_model.on_success(unlock_response)

    # Assert
    enter_wallet_password_view_model.is_loading.emit.assert_called_once_with(
        False,
    )
    enter_wallet_password_view_model.message.emit.assert_called_once_with(
        ToastPreset.SUCCESS, INFO_WALLET_UNLOCK_SUCCESSFULLY,
    )
    enter_wallet_password_view_model.forward_to_fungibles_page.assert_called_once()
    # In case it's needed after a successful unlock
    enter_wallet_password_view_model.forward_to_fungibles_page.assert_called_once()


def test_on_success_unlock_with_invalid_password(enter_wallet_password_view_model, mocker):
    """Test the failure of unlocking due to invalid password."""

    # Arrange
    enter_wallet_password_view_model.is_loading = MagicMock()
    enter_wallet_password_view_model.message = MagicMock()
    enter_wallet_password_view_model.forward_to_fungibles_page = MagicMock()

    enter_wallet_password_view_model.password = None  # Invalid password scenario

    # Mock SettingRepository methods
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.MAINNET,
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_keyring_status',
        return_value=False,
    )  # keyring status false for this test
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_wallet_initialized',
    )

    # Act
    # Assuming you have the appropriate mock or actual model here
    unlock_response = UnlockResponseModel(status=False)
    enter_wallet_password_view_model.on_success(unlock_response)

    # Assert
    enter_wallet_password_view_model.is_loading.emit.assert_called_once_with(
        False,
    )
    enter_wallet_password_view_model.message.emit.assert_called_once_with(
        ToastPreset.ERROR, f'Unable to get password {
            enter_wallet_password_view_model.password
        }',
    )


def test_forward_to_fungibles_page(mocker, enter_wallet_password_view_model):
    """Test the forward_to_fungibles_page method."""

    # Arrange
    mock_sidebar = MagicMock()
    mock_page_navigation = MagicMock()

    # Mock the sidebar and the setChecked method
    mock_sidebar.my_fungibles.setChecked = MagicMock()

    # Patch the page_navigation method to return the mock sidebar
    mocker.patch.object(
        enter_wallet_password_view_model,
        '_page_navigation', mock_page_navigation,
    )
    mock_page_navigation.sidebar.return_value = mock_sidebar

    # Mock the fungibles_asset_page method
    mock_page_navigation.fungibles_asset_page = MagicMock()

    # Act
    enter_wallet_password_view_model.forward_to_fungibles_page()

    # Assert
    # Check that sidebar.my_fungibles.setChecked was called once with True
    mock_sidebar.my_fungibles.setChecked.assert_called_once_with(True)

    # Check that fungibles_asset_page was called once
    mock_page_navigation.fungibles_asset_page.assert_called_once()


def test_set_wallet_credentials(mocker, enter_wallet_password_view_model):
    """Test the set_wallet_credentials method."""

    # Arrange
    mock_is_loading = MagicMock()
    mock_run_in_thread = mocker.patch.object(
        enter_wallet_password_view_model, 'run_in_thread', autospec=True,
    )
    _mock_common_service = mocker.patch(
        'src.data.service.common_operation_service.CommonOperationService.enter_wallet_password',
    )

    # Mock the is_loading signal emitter
    enter_wallet_password_view_model.is_loading = mock_is_loading

    # Set the test password input
    test_password = 'test_password'

    # Act
    enter_wallet_password_view_model.set_wallet_credentials(test_password)

    # Assert
    # Check if is_loading.emit was called with True
    mock_is_loading.emit.assert_called_once_with(True)

    # Ensure that run_in_thread was called with correct arguments
    mock_run_in_thread.assert_called_once_with(
        CommonOperationService.enter_wallet_password,
        {
            'args': [test_password],
            'callback': enter_wallet_password_view_model.on_success,
            'error_callback': enter_wallet_password_view_model.on_error,
        },
    )

    # Ensure that the password was set correctly
    assert enter_wallet_password_view_model.password == test_password
