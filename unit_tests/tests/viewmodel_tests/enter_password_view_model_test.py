"""Unit test cases for enter wallet password page"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QWidget

from src.model.common_operation_model import UnlockResponseModel
from src.model.enums.enums_model import ToastPreset
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NETWORK_MISMATCH
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
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


def test_on_success(enter_wallet_password_view_model, mocker):
    """Test for on_success method"""
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


def test_on_success_failure(enter_wallet_password_view_model, mocker):
    """Test for on_success method when password is not set successfully"""
    mock_message = Mock()
    enter_wallet_password_view_model.message.connect(mock_message)

    response = UnlockResponseModel(status=False)
    enter_wallet_password_view_model.password = 'test_password'

    enter_wallet_password_view_model.on_success(response)

    mock_message.assert_called_once_with(
        ToastPreset.ERROR, 'Unable to get password test_password',
    )


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
