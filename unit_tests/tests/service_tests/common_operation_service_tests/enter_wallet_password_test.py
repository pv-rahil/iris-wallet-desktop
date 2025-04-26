"""Unit tests for enter wallet password method  in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests  function
# pylint: disable=redefined-outer-name, unused-argument, protected-access, unused-import
from __future__ import annotations

import pytest

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import UnlockResponseModel
from src.utils.custom_exception import CommonException
from unit_tests.repository_fixture.common_operations_repository_mock import mock_lock
from unit_tests.repository_fixture.common_operations_repository_mock import mock_network_info
from unit_tests.repository_fixture.common_operations_repository_mock import mock_unlock
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_network_info_api_res
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_network_info_diff
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_password
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_unlock_api_res
from unit_tests.service_test_resources.service_fixture.common_operation_service_mock import mock_is_node_locked


@pytest.fixture(autouse=True)
def reset_network():
    """Reset network to mainnet before each test"""
    SettingRepository.get_wallet_network()
    yield
    SettingRepository.get_wallet_network()


def test_enter_wallet_password_locked_same_network(mock_unlock, mock_network_info, mock_is_node_locked):
    """Case 1 : When ln node locked and build and ln node network same"""
    lock_obj = mock_is_node_locked(True)
    mock_unlock(UnlockResponseModel(status=True))
    network_info_obj = mock_network_info(mocked_network_info_api_res)
    result = CommonOperationService.enter_node_password(password='Random@123')
    assert isinstance(result, UnlockResponseModel)
    assert result.status is True
    lock_obj.assert_called_once()
    network_info_obj.assert_called_once()


def test_enter_wallet_password_unlocked_same_network(mock_unlock, mock_network_info, mock_is_node_locked, mock_lock):
    """Case 2 : When ln node unlocked and build and ln node network same"""
    lock_obj = mock_is_node_locked(False)
    mock_unlock(UnlockResponseModel(status=True))
    lock_api_obj = mock_lock(True)
    network_info_obj = mock_network_info(mocked_network_info_api_res)
    result = CommonOperationService.enter_node_password(password='Random@123')
    assert isinstance(result, UnlockResponseModel)
    assert result.status is True
    lock_obj.assert_called_once()
    lock_api_obj.assert_called_once()
    network_info_obj.assert_called_once()


def test_enter_wallet_password_locked_diff_network(mock_unlock, mock_network_info, mock_is_node_locked, mock_lock):
    """Case 3 : When ln node locked and build and ln node network diff"""
    lock_obj = mock_is_node_locked(True)
    mock_unlock(UnlockResponseModel(status=False))
    network_info_obj = mock_network_info(mocked_network_info_diff)
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.enter_node_password(password='Random@123')
    assert str(exc_info.value) == 'Network configuration does not match.'
    lock_obj.assert_called_once()
    network_info_obj.assert_called_once()


def test_enter_wallet_password_unlocked_diff_network(mock_unlock, mock_network_info, mock_is_node_locked, mock_lock):
    """Case 4 : When ln node unlocked and build and ln node network diff"""
    lock_obj = mock_is_node_locked(False)
    mock_unlock(UnlockResponseModel(status=False))
    _lock_api_obj = mock_lock(True)
    network_info_obj = mock_network_info(mocked_network_info_diff)
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.enter_node_password(password='Random@123')
    assert str(exc_info.value) == 'Network configuration does not match.'
    lock_obj.assert_called_once()
    network_info_obj.assert_called_once()
