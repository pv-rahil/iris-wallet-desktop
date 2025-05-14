"""Unit tests for get_hashed_mnemonic method in common operation service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.data.service.common_operation_service import CommonOperationService
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_UNABLE_GET_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_HASHED_MNEMONIC


@patch('src.data.service.common_operation_service.hash_mnemonic')
def test_get_hashed_mnemonic_success(mock_hash_mnemonic):
    """Test successful hashing of mnemonic"""
    # Setup mock
    mock_hash_mnemonic.return_value = 'hashed_test_mnemonic'

    # Execute
    result = CommonOperationService.get_hashed_mnemonic(
        mnemonic='test mnemonic',
    )

    # Assert
    assert result == 'hashed_test_mnemonic'
    mock_hash_mnemonic.assert_called_once_with(mnemonic_phrase='test mnemonic')


@patch('src.data.service.common_operation_service.hash_mnemonic')
def test_get_hashed_mnemonic_empty_mnemonic(mock_hash_mnemonic):
    """Test exception when mnemonic is empty"""
    # Execute and Assert
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.get_hashed_mnemonic(mnemonic='')

    assert str(exc_info.value) == ERROR_UNABLE_GET_MNEMONIC
    mock_hash_mnemonic.assert_not_called()


@patch('src.data.service.common_operation_service.hash_mnemonic')
def test_get_hashed_mnemonic_none_mnemonic(mock_hash_mnemonic):
    """Test exception when mnemonic is None"""
    # Execute and Assert
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.get_hashed_mnemonic(mnemonic=None)

    assert str(exc_info.value) == ERROR_UNABLE_GET_MNEMONIC
    mock_hash_mnemonic.assert_not_called()


@patch('src.data.service.common_operation_service.hash_mnemonic')
def test_get_hashed_mnemonic_hash_failure(mock_hash_mnemonic):
    """Test exception when hash_mnemonic returns empty result"""
    # Setup mock
    mock_hash_mnemonic.return_value = ''

    # Execute and Assert
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.get_hashed_mnemonic(mnemonic='test mnemonic')

    assert str(exc_info.value) == ERROR_UNABLE_TO_GET_HASHED_MNEMONIC
    mock_hash_mnemonic.assert_called_once_with(mnemonic_phrase='test mnemonic')


@patch('src.data.service.common_operation_service.hash_mnemonic')
def test_get_hashed_mnemonic_hash_returns_none(mock_hash_mnemonic):
    """Test exception when hash_mnemonic returns None"""
    # Setup mock
    mock_hash_mnemonic.return_value = None

    # Execute and Assert
    with pytest.raises(CommonException) as exc_info:
        CommonOperationService.get_hashed_mnemonic(mnemonic='test mnemonic')

    assert str(exc_info.value) == ERROR_UNABLE_TO_GET_HASHED_MNEMONIC
    mock_hash_mnemonic.assert_called_once_with(mnemonic_phrase='test mnemonic')
