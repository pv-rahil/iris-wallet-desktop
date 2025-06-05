"""Unit tests for issue asset service"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments,unused-import
from __future__ import annotations

import pytest

from src.data.service.issue_asset_service import IssueAssetService
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_IMAGE_PATH_NOT_EXITS
from unit_tests.repository_fixture.rgb_repository_mock import mock_issue_asset_cfa
from unit_tests.service_test_resources.mocked_fun_return_values.issue_asset_service import mock_data_issue_cfa_asset_res
from unit_tests.service_test_resources.mocked_fun_return_values.issue_asset_service import mock_data_new_asset_issue
from unit_tests.service_test_resources.mocked_fun_return_values.issue_asset_service import mock_data_new_asset_issue_no_path_exits


def test_issue_asset_cfa(mock_issue_asset_cfa):
    """Case 1 : Issue asset CFA service method test"""
    issue_asset_obj = mock_issue_asset_cfa(mock_data_issue_cfa_asset_res)
    response = IssueAssetService.issue_asset_cfa(mock_data_new_asset_issue)
    issue_asset_obj.assert_called_once()
    assert response == mock_data_issue_cfa_asset_res


def test_issue_asset_cfa_path_not_exits():
    """Case 2 : Test when image path not exits"""
    with pytest.raises(CommonException, match=ERROR_IMAGE_PATH_NOT_EXITS):
        IssueAssetService.issue_asset_cfa(
            mock_data_new_asset_issue_no_path_exits,
        )
