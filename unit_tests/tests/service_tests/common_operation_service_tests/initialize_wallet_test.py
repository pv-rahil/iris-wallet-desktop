"""Unit tests for initialize wallet method  in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests  function
# pylint: disable=redefined-outer-name, unused-argument, unused-import
from __future__ import annotations

import pytest

from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import InitRequestModel
from src.model.common_operation_model import InitResponseModel
from src.model.common_operation_model import UnlockRequestModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NETWORK_MISMATCH
from unit_tests.repository_fixture.common_operations_repository_mock import mock_init
from unit_tests.repository_fixture.common_operations_repository_mock import mock_network_info
from unit_tests.repository_fixture.common_operations_repository_mock import mock_unlock
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_data_init_api_response
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_network_info_api_res
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_network_info_diff
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_password
from unit_tests.service_test_resources.mocked_fun_return_values.common_operation_service import mocked_unlock_api_res


def test_initialize_wallet(mock_unlock, mock_init, mock_network_info):
    """Case 1 : Positive case or when build network and ln node network same"""
    mock_unlock(mocked_unlock_api_res)
    mock_init(mocked_data_init_api_response)
    mock_network_info(mocked_network_info_api_res)
    result = CommonOperationService.initialize_wallet('Random@123')
    assert isinstance(result, InitResponseModel)
    assert result.mnemonic == 'skill lamp please gown put season degree collect decline account monitor insane'


def test_initialize_wallet_network_diff(mock_unlock, mock_init, mock_network_info):
    """Case 2 : when build network and ln node network diff"""
    mock_unlock(mocked_unlock_api_res)
    mock_init(mocked_data_init_api_response)
    mock_network_info(mocked_network_info_diff)
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.initialize_wallet('Random@123')
    assert str(exc_info.value) == 'Network configuration does not match.'
