"""Unit tests for build_app_paths function in build_app_path.py"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.model.common_operation_model import AppPathsModel
from src.utils.build_app_path import build_app_paths
from src.utils.constant import APP_DIR
from src.utils.constant import APP_NAME
from src.utils.constant import CACHE_FOLDER_NAME
from src.utils.constant import LOG_FOLDER_NAME
from src.utils.custom_exception import CommonException

# Store the real os.path.join before mocking
_real_os_path_join = os.path.join


def test_build_app_paths():
    """Test build_app_paths function"""
    base_path = '/mock/base/path'
    mock_network = 'testnet'
    mock_temp_dir = '/mock/temp/dir'

    # Expected paths
    expected_app_path = os.path.join(base_path, APP_DIR)
    expected_app_name_with_network = f"{APP_NAME}_{mock_network}"
    expected_temp_folder_path = os.path.join(
        mock_temp_dir, expected_app_name_with_network,
    )

    with patch('src.utils.build_app_path.__network__', mock_network), \
            patch('tempfile.gettempdir', return_value=mock_temp_dir):
        app_paths = build_app_paths(base_path)

    # Assert the constructed paths
    assert isinstance(app_paths, AppPathsModel)
    assert app_paths.app_path == expected_app_path
    assert app_paths.iriswallet_temp_folder_path == expected_temp_folder_path
    assert app_paths.cache_path == os.path.join(
        expected_app_path, CACHE_FOLDER_NAME,
    )
    assert app_paths.app_logs_path == os.path.join(
        expected_app_path, LOG_FOLDER_NAME,
    )
    assert app_paths.pickle_file_path == os.path.join(
        expected_app_path, 'token.pickle',
    )
    assert app_paths.config_file_path == os.path.join(
        expected_app_path, f"{APP_NAME}-{mock_network}.ini",
    )
    assert app_paths.backup_folder_path == os.path.join(
        expected_temp_folder_path, 'backup',
    )
    assert app_paths.restore_folder_path == os.path.join(
        expected_temp_folder_path, 'restore',
    )


def conditional_join(*args):
    """
    A helper function that conditionally joins paths.

    Raises a CommonException when specific test input is detected,
    otherwise delegates to the real os.path.join function.
    """
    # Only raise on specific test input
    if '/mock/base/path' in args:
        raise CommonException('Mock error')
    return _real_os_path_join(*args)


def test_build_app_paths_exception_handling():
    """Test exception handling in build_app_paths function"""
    base_path = '/mock/base/path'

    with patch('src.utils.build_app_path.os.path.join', side_effect=conditional_join), \
            patch('logging.error', return_value=None):

        with pytest.raises(CommonException, match='Mock error'):
            build_app_paths(base_path)
