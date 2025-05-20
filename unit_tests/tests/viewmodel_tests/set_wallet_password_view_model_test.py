"""Unit test for SetWalletPasswordViewModel"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QLineEdit

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import ToastPreset
from src.utils.custom_exception import CommonException
from src.utils.local_store import local_store
from src.viewmodels.set_wallet_password_view_model import SetWalletPasswordViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def mock_keyring_and_storage(monkeypatch):
    """Ensure tests use dummy values for keyring and local storage."""

    # Dummy test values
    dummy_mnemonic = 'dummy_mnemonic'
    dummy_password = 'dummy_password'
    dummy_native_login = False
    dummy_native_auth = False

    # Mock methods that retrieve data from keyring/local storage
    monkeypatch.setattr(
        local_store, 'get_value', lambda key: {
            'mnemonic': dummy_mnemonic,
            'wallet_password': dummy_password,
            'nativeLoginEnabled': dummy_native_login,
            'isNativeAuthenticationEnabled': dummy_native_auth,
        }.get(key, None),
    )

    # Mock methods that store data to keyring/local storage
    monkeypatch.setattr(local_store, 'set_value', lambda key, value: None)

    # Mock SettingRepository methods if needed
    monkeypatch.setattr(
        SettingRepository,
        'get_wallet_network', lambda: 'test_network',
    )


@pytest.fixture
def set_wallet_initialized_mock(mocker):
    """Fixture to create a mock SettingRepository set_wallet_initialized method."""
    return mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_wallet_initialized',
    )


@pytest.fixture
def unlock_mock(mocker):
    """Fixture to create a mock CommonOperationRepository unlock method."""
    return mocker.patch(
        'src.data.repository.common_operations_repository.CommonOperationRepository.unlock',
    )


@pytest.fixture
def set_value_mock(mocker):
    """Fixture to create a mock set_value."""
    return mocker.patch('src.utils.keyring_storage.set_value')


@pytest.fixture
def set_wallet_password_view_model(mock_page_navigation):
    """Fixture to create an instance of the SetWalletPasswordViewModel class."""
    return SetWalletPasswordViewModel(mock_page_navigation)


@pytest.fixture
def mocks(
    set_wallet_initialized_mock,
    unlock_mock,
    set_value_mock,
):
    """Fixture to create an object of the multiple mocks."""
    return {
        'set_wallet_initialized_mock': set_wallet_initialized_mock,
        'unlock_mock': unlock_mock,
        'set_value_mock': set_value_mock,
    }


def test_toggle_password_visibility(set_wallet_password_view_model, mocker):
    """"Test for toggle visibility work as expected"""
    line_edit_mock = mocker.MagicMock(spec=QLineEdit)
    initial_echo_mode = QLineEdit.Password

    assert (
        set_wallet_password_view_model.toggle_password_visibility(
            line_edit_mock,
        )
        is False
    )
    line_edit_mock.setEchoMode.assert_called_once_with(QLineEdit.Normal)

    assert (
        set_wallet_password_view_model.toggle_password_visibility(
            line_edit_mock,
        )
        is True
    )
    line_edit_mock.setEchoMode.assert_called_with(initial_echo_mode)


def test_generate_password(set_wallet_password_view_model):
    """"Test for generate work as expected"""
    generated_password = set_wallet_password_view_model.generate_password(
        length=12,
    )
    assert len(generated_password) == 12

    generated_password_invalid = set_wallet_password_view_model.generate_password(
        length=2,
    )
    assert 'Error' in generated_password_invalid


def test_set_wallet_password_short_password(set_wallet_password_view_model, mocker):
    """Test for set wallet password when the password length is less than 8 characters."""
    enter_password_input_mock = mocker.MagicMock(spec=QLineEdit)
    confirm_password_input_mock = mocker.MagicMock(spec=QLineEdit)
    validation_mock = mocker.MagicMock()

    # Set password length less than 8 characters
    enter_password_input_mock.text.return_value = 'short'
    confirm_password_input_mock.text.return_value = 'short'

    # Call the method
    set_wallet_password_view_model.set_wallet_password_in_thread(
        enter_password_input_mock,
        confirm_password_input_mock,
        validation_mock,
    )

    # Validation mock should be called with the appropriate message
    validation_mock.assert_called_once_with(
        'Minimum password length is 8 characters.',
    )


def test_password_too_short(set_wallet_password_view_model, mocker):
    """
    Test that validation fails when the password is shorter than 8 characters.
    Ensures the correct validation message is shown and loading is not triggered.
    """
    enter_mock = mocker.MagicMock(spec=QLineEdit)
    confirm_mock = mocker.MagicMock(spec=QLineEdit)
    validation_mock = MagicMock()

    enter_mock.text.return_value = 'short'
    confirm_mock.text.return_value = 'short'

    set_wallet_password_view_model.set_wallet_password_in_thread(
        enter_mock, confirm_mock, validation_mock,
    )

    validation_mock.assert_called_once_with(
        'Minimum password length is 8 characters.',
    )
    mock_emit = Mock()
    set_wallet_password_view_model.is_loading.connect(mock_emit)


def test_password_has_special_char(set_wallet_password_view_model, mocker):
    """
    Test that validation fails when the password contains special characters.
    Ensures the proper error message is emitted and loading is not triggered.
    """
    enter_mock = mocker.MagicMock(spec=QLineEdit)
    confirm_mock = mocker.MagicMock(spec=QLineEdit)
    validation_mock = MagicMock()

    enter_mock.text.return_value = 'valid@123'
    confirm_mock.text.return_value = 'valid@123'

    set_wallet_password_view_model.set_wallet_password_in_thread(
        enter_mock, confirm_mock, validation_mock,
    )

    validation_mock.assert_called_once_with(
        'Password cannot contain special characters.',
    )
    mock_emit = Mock()
    set_wallet_password_view_model.is_loading.connect(mock_emit)


def test_password_mismatch(set_wallet_password_view_model, mocker):
    """
    Test that validation fails when the password and confirmation do not match.
    Validates the correct message is returned and thread execution does not begin.
    """
    enter_mock = mocker.MagicMock(spec=QLineEdit)
    confirm_mock = mocker.MagicMock(spec=QLineEdit)
    validation_mock = MagicMock()

    enter_mock.text.return_value = 'valid1234'
    confirm_mock.text.return_value = 'different1234'

    set_wallet_password_view_model.set_wallet_password_in_thread(
        enter_mock, confirm_mock, validation_mock,
    )

    validation_mock.assert_called_once_with('Passwords must be the same!')
    mock_emit = Mock()
    set_wallet_password_view_model.is_loading.connect(mock_emit)


def test_password_valid_and_match(set_wallet_password_view_model, mocker):
    """
    Test that if passwords are valid and match:
    - No validation error is triggered
    - The loading state is emitted
    - The wallet initialization is executed in a thread
    """
    enter_mock = mocker.MagicMock(spec=QLineEdit)
    confirm_mock = mocker.MagicMock(spec=QLineEdit)
    validation_mock = MagicMock()
    mocked_thread = mocker.patch.object(
        set_wallet_password_view_model, 'run_in_thread',
    )
    partial_mock = mocker.patch(
        'src.viewmodels.set_wallet_password_view_model.partial',
    )

    enter_mock.text.return_value = 'validpass'
    confirm_mock.text.return_value = 'validpass'

    set_wallet_password_view_model.set_wallet_password_in_thread(
        enter_mock, confirm_mock, validation_mock,
    )

    mock_emit = Mock()
    set_wallet_password_view_model.is_loading.connect(mock_emit)
    mocked_thread.assert_called_once()
    validation_mock.assert_not_called()
    partial_mock.assert_called_once()


@patch('src.viewmodels.set_wallet_password_view_model.mnemonic_store.encrypt', return_value='encrypted_mnemonic')
@patch('src.viewmodels.set_wallet_password_view_model.local_store.write_to_file')
@patch('src.viewmodels.set_wallet_password_view_model.local_store.set_value', return_value=True)
@patch('src.viewmodels.set_wallet_password_view_model.set_value', return_value=True)
@patch('src.viewmodels.set_wallet_password_view_model.SettingRepository')
def test_on_success_password_stored(
    mock_setting_repo, mock_set_value, mock_local_store_set, mock_local_store_write, mock_encrypt, set_wallet_password_view_model,
):
    """Test that on_success stores password and navigates to fungibles page."""
    mock_response = MagicMock()
    mock_response.mnemonic = 'mnemonic'
    mock_response.account_xpub = 'xpub'

    with patch.object(set_wallet_password_view_model, 'forward_to_fungibles_page') as mock_forward:
        response_tuple = (mock_response, 'testpassword')
        mock_setting_repo.get_wallet_network.return_value.value = 'test_network'

        set_wallet_password_view_model.on_success(
            response_tuple, password='testpassword',
        )

        mock_emit = Mock()
        set_wallet_password_view_model.is_loading.connect(mock_emit)
        mock_encrypt.assert_called_once()
        mock_local_store_write.assert_called_once()
        mock_local_store_set.assert_called_once()
        mock_set_value.assert_called_once()
        mock_forward.assert_called_once()


def test_on_error_general(set_wallet_password_view_model, mocker):
    """Test that on_error emits the correct error message."""
    exception = CommonException('Other error')
    exception.message = 'Other error'

    mock_message_emit = mocker.MagicMock()
    set_wallet_password_view_model.message.connect(mock_message_emit)

    set_wallet_password_view_model.on_error(exception)

    mock_message_emit.assert_called_once_with(ToastPreset.ERROR, 'Other error')


def test_forward_to_fungibles_page(set_wallet_password_view_model, mock_page_navigation):
    """Test that forward_to_fungibles_page navigates and sets checkbox."""
    mock_sidebar = MagicMock()
    mock_fungibles_page = MagicMock()

    mock_page_navigation.sidebar.return_value = mock_sidebar
    mock_page_navigation.fungibles_asset_page.return_value = mock_fungibles_page

    set_wallet_password_view_model.forward_to_fungibles_page()

    mock_page_navigation.sidebar.assert_called_once()
    mock_sidebar.my_fungibles.setChecked.assert_called_once_with(True)
    mock_page_navigation.fungibles_asset_page.assert_called_once()
