"""Unit tests for restore method of restore service"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import os
import shutil
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.data.service.restore_service import RestoreService
from src.model.common_operation_model import RestoreResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NOT_BACKUP_FILE
from src.utils.error_message import ERROR_UNABLE_GET_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_HASHED_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_PASSWORD
from src.utils.error_message import ERROR_WHILE_RESTORE_DOWNLOAD_FROM_DRIVE
from unit_tests.service_test_resources.mocked_fun_return_values.backup_service import mock_password
from unit_tests.service_test_resources.mocked_fun_return_values.backup_service import mock_valid_mnemonic

# Setup function


@pytest.fixture(scope='function')
def setup_directory():
    """Set up method for test"""
    test_dir = os.path.join(os.path.dirname(__file__), 'iris-wallet-test')

    restore_dir = os.path.join(test_dir, 'restore')

    # Create the iris-wallet-test directory
    os.makedirs(test_dir, exist_ok=True)

    # Create the restore directory inside iris-wallet-test
    os.makedirs(restore_dir, exist_ok=True)

    return test_dir, restore_dir

# Teardown function


@pytest.fixture(scope='function', autouse=True)
def teardown_directory_after_test():
    """Clean up function after test"""
    yield
    demo_dir = os.path.join(os.path.dirname(__file__), 'iris-wallet-test')
    if os.path.exists(demo_dir):
        shutil.rmtree(demo_dir)
    assert not os.path.exists(demo_dir)

# Test function


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.restore')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.service.restore_service.read_rgb_lib_version_file')
def test_restore(mock_read_version, mock_google_drive_manager, mock_restore, mock_get_path, mock_get_hashed_mnemonic, setup_directory):
    """Case 1: Test restore service"""
    test_dir, _ = setup_directory

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = test_dir
    mock_read_version.return_value = '0.3.0a14.dev1'

    mock_restore_instance = MagicMock()
    mock_restore.return_value = RestoreResponseModel(status=True)
    mock_restore_instance.return_value = None
    mock_google_drive_manager.return_value = mock_restore_instance
    mock_restore_instance.download_from_drive.return_value = True

    result = RestoreService.restore(mock_valid_mnemonic, mock_password)

    # Assert the result
    assert result.status is True

# Test function


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.restore')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.service.restore_service.app_paths')
@patch('src.data.service.restore_service.read_rgb_lib_version_file')
def test_restore_when_file_not_exists(mock_read_version, mock_app_paths, mock_google_drive_manager, mock_restore, mock_get_path, mock_get_hashed_mnemonic, setup_directory):
    """Case 2: When restore file does not exist after download"""
    test_dir, restore_dir = setup_directory

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = test_dir
    mock_read_version.return_value = '0.3.0a14.dev1'

    # Mock app_paths to avoid FileNotFoundError during cleanup
    mock_app_paths.restore_folder_path = restore_dir
    mock_app_paths.app_path = test_dir
    mock_app_paths.iriswallet_temp_folder_path = os.path.join(test_dir, 'temp')

    # Create temp folder to avoid FileNotFoundError during cleanup
    os.makedirs(mock_app_paths.iriswallet_temp_folder_path, exist_ok=True)

    mock_restore_instance = MagicMock()
    mock_restore.return_value = RestoreResponseModel(status=True)
    mock_google_drive_manager.return_value = mock_restore_instance
    mock_restore_instance.download_from_drive.return_value = None

    error_message = ERROR_NOT_BACKUP_FILE
    with pytest.raises(CommonException, match=error_message):
        RestoreService.restore(mock_valid_mnemonic, mock_password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.restore')
def test_restore_no_mnemonic(mock_restore, mock_google_drive_manager, mock_get_path, mock_get_hashed_mnemonic):
    """Case 3: Test restore service with missing mnemonic"""
    # Setup mocks
    mock_get_hashed_mnemonic.side_effect = CommonException(
        ERROR_UNABLE_GET_MNEMONIC,
    )
    mock_get_path.return_value = os.path.join(
        os.path.dirname(__file__), 'some_path',
    )
    mock_google_drive_manager.return_value = MagicMock()
    mock_google_drive_manager.return_value.download_from_drive.return_value = True
    mock_restore.return_value = RestoreResponseModel(status=True)

    # Call the RestoreService.restore method
    mnemonic = None
    password = 'test_password'

    with pytest.raises(CommonException, match=ERROR_UNABLE_GET_MNEMONIC):
        RestoreService.restore(mnemonic, password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
def test_restore_no_password(mock_get_path, mock_get_hashed_mnemonic):
    """Case 4: Test restore service with missing password"""

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = os.path.join(
        os.path.dirname(__file__), 'some_path',
    )

    # Call the RestoreService.restore method
    mnemonic = 'test_mnemonic'
    password = None

    with pytest.raises(CommonException, match=ERROR_UNABLE_TO_GET_PASSWORD):
        RestoreService.restore(mnemonic, password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.restore')
@patch('src.data.service.restore_service.app_paths')
def test_restore_no_hashed_value(mock_app_paths, mock_restore, mock_google_drive_manager, mock_get_hashed_mnemonic):
    """Case 5: Test restore service with missing hashed value"""

    # Setup mocks
    mock_get_hashed_mnemonic.side_effect = CommonException(
        ERROR_UNABLE_TO_GET_HASHED_MNEMONIC,
    )
    mock_google_drive_manager.return_value = MagicMock()
    mock_google_drive_manager.return_value.download_from_drive.return_value = True
    mock_restore.return_value = RestoreResponseModel(status=True)

    # Mock app_paths to prevent FileNotFoundError during cleanup
    mock_app_paths.iriswallet_temp_folder_path = '/tmp/iriswallet_regtest'
    mock_app_paths.restore_folder_path = '/tmp/restore'

    # Call the RestoreService.restore method with actual values from error trace
    mnemonic = 'skill lamp please gown put season degree collect decline account monitor insane'
    password = 'random@123'

    with pytest.raises(CommonException, match=ERROR_UNABLE_TO_GET_HASHED_MNEMONIC):
        RestoreService.restore(mnemonic, password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.service.restore_service.read_rgb_lib_version_file')
def test_restore_download_error(mock_read_version, mock_google_drive_manager, mock_get_hashed_mnemonic):
    """Case 6: Test restore service with download failure"""

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_read_version.return_value = '0.3.0a14.dev1'
    mock_google_drive_manager.return_value = MagicMock()
    mock_google_drive_manager.return_value.download_from_drive.return_value = False

    # Call the RestoreService.restore method
    with pytest.raises(CommonException, match=ERROR_WHILE_RESTORE_DOWNLOAD_FROM_DRIVE):
        RestoreService.restore(mock_valid_mnemonic, mock_password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.service.restore_service.read_rgb_lib_version_file')
def test_restore_incompatible_version(mock_read_version, mock_google_drive_manager, mock_get_hashed_mnemonic):
    """Case 7: Test restore service with incompatible version."""
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_read_version.return_value = 'incompatible_version'
    mock_google_drive_manager.return_value = MagicMock()
    with pytest.raises(CommonException, match='RGB_LIB_INCOMPATIBLE'):
        RestoreService.restore(mock_valid_mnemonic, mock_password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.restore_service.read_rgb_lib_version_file')
@patch('src.data.service.restore_service.GoogleDriveManager')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.restore')
@patch('src.data.service.restore_service.SettingRepository')
@patch('src.data.service.restore_service.os.path.exists')
@patch('src.data.service.restore_service.os.remove')
@patch('src.data.service.restore_service.open', create=True)
@patch('src.data.service.restore_service.json.load')
@patch('src.data.service.restore_service.app_paths')
def test_restore_multisig(
    mock_app_paths, mock_json_load, mock_open, mock_remove,
    mock_os_exists, mock_setting_repo, mock_restore_repo,
    mock_google_drive, mock_read_version, mock_hashed,
):
    """Case 8: Test restore service with multisig restoration."""
    mock_hashed.return_value = 'e23ddff3cc'
    mock_read_version.return_value = '0.3.0a14.dev1'
    # folder exists, old file exists, multisig file exists, temp folder exists (finally block)
    mock_os_exists.side_effect = [
        True, True, True,
        True, True, True, True, True, True, True,
    ]
    mock_restore_repo.return_value = RestoreResponseModel(status=True)

    mock_app_paths.iriswallet_temp_folder_path = '/tmp/dummy_temp'
    mock_app_paths.restore_folder_path = '/tmp/restore'
    mock_app_paths.app_path = '/tmp/app'

    mock_drive_instance = MagicMock()
    mock_drive_instance.download_from_drive.return_value = True
    mock_google_drive.return_value = mock_drive_instance

    mock_json_load.return_value = {
        'required_signers': 2,
        'total_signers': 3,
        'cosigners': [],
    }

    with patch('src.data.service.restore_service.shutil.rmtree') as mock_rmtree:
        result = RestoreService.restore(mock_valid_mnemonic, mock_password)
        assert result.status is True
        mock_setting_repo.set_wallet_signature_type.assert_called_once()
        mock_remove.assert_called_once()
        mock_rmtree.assert_called_once_with('/tmp/dummy_temp')
