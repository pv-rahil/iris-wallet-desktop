"""Unit tests for keyring toggle validate method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, unused-import
from __future__ import annotations

from unittest.mock import patch

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING_STORE_NOT_ACCESSIBLE
from unit_tests.repository_fixture.setting_repository_mocked import mock_get_wallet_network
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_password
from unit_tests.service_test_resources.mocked_fun_return_values.faucet_service import mocked_network
from unit_tests.service_test_resources.service_fixture.common_operation_service_mock import mock_set_value_keyring_helper


@patch('src.data.service.common_operation_service.handle_exceptions')
def test_when_keyring_accessible(mock_handle_exceptions, mock_get_wallet_network, mock_set_value_keyring_helper):
    """Test when password is successfully stored in keyring"""
    get_network_obj = mock_get_wallet_network(mocked_network)
    mock_set_value_keyring_helper(True)

    CommonOperationService.keyring_toggle_enable_validation(
        password=mocked_password,
    )

    keyring_status = SettingRepository.get_keyring_status()
    assert keyring_status is False
    get_network_obj.assert_called_once()
    mock_handle_exceptions.assert_not_called()


@patch('src.data.service.common_operation_service.handle_exceptions')
@patch('src.data.service.common_operation_service.set_value')
def test_when_keyring_not_accessible(mock_set_value, mock_handle_exceptions, mock_get_wallet_network, mock_set_value_keyring_helper):
    """Test when password cannot be stored in keyring"""
    get_network_obj = mock_get_wallet_network(mocked_network)
    mock_set_value_keyring_helper(False)
    # Configure the mock to raise the exception when called directly in the method
    mock_set_value.side_effect = CommonException(
        ERROR_KEYRING_STORE_NOT_ACCESSIBLE,
    )

    # The exception is caught inside the method, so we don't expect it to be raised
    CommonOperationService.keyring_toggle_enable_validation(
        password=mocked_password,
    )

    # Verify the keyring status remains False when storage fails
    keyring_status = SettingRepository.get_keyring_status()
    assert keyring_status is False

    get_network_obj.assert_called_once()


@patch('src.data.service.common_operation_service.handle_exceptions')
def test_keyring_toggle_exception_handling(mock_handle_exceptions, mock_get_wallet_network):
    """Test exception handling in keyring toggle validation"""
    get_network_obj = mock_get_wallet_network(mocked_network)
    get_network_obj.side_effect = Exception('Test exception')
    mock_handle_exceptions.return_value = 'Error response'

    # The method doesn't return the result of handle_exceptions
    CommonOperationService.keyring_toggle_enable_validation(
        password=mocked_password,
    )

    # Don't assert on return value, just verify handle_exceptions was called
    mock_handle_exceptions.assert_called_once()
