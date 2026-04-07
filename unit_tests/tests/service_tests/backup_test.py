"""Unit tests for backup method of back service"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import os
import shutil
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.data.service.backup_service import BackupService
from src.model.enums.enums_model import WalletSignatureType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_BACKUP_FILE_NOT_EXITS
from src.utils.error_message import ERROR_UNABLE_GET_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_HASHED_MNEMONIC
from src.utils.error_message import ERROR_UNABLE_TO_GET_PASSWORD
from unit_tests.service_test_resources.mocked_fun_return_values.backup_service import mock_password
from unit_tests.service_test_resources.mocked_fun_return_values.backup_service import mock_valid_mnemonic

# Setup function


@pytest.fixture(scope='function')
def setup_directory():
    """Set up method for test"""
    test_dir = os.path.join(os.path.dirname(__file__), 'iris-wallet-test')

    backup_dir = os.path.join(test_dir, 'backup')

    # Create the iris-wallet-test directory
    os.makedirs(test_dir, exist_ok=True)

    # Create the backup directory inside iris-wallet-test
    os.makedirs(backup_dir, exist_ok=True)

    return test_dir, backup_dir

# Teardown function


@pytest.fixture(scope='function', autouse=True)
def teardown_directory_after_test():
    """Clean up function after test"""
    yield
    test_dir = os.path.join(os.path.dirname(__file__), 'iris-wallet-test')
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    assert not os.path.exists(test_dir)

# Test function


@patch('src.data.service.backup_service.SettingRepository.get_rgb_lib_version')
@patch('src.data.service.backup_service.SettingRepository.get_wallet_signature_type')
@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.service.backup_service.BackupService.backup_file_exists')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.backup')
@patch('src.data.service.backup_service.GoogleDriveManager')
def test_backup(mock_google_drive_manager, mock_backup, mock_backup_file_exits, mock_get_path, mock_get_hashed_mnemonic, mock_wallet_signature_type, mock_rgb_lib_version, setup_directory):
    """Case 1 : Test backup service"""
    test_dir, _ = setup_directory

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = test_dir

    mock_backup_instance = MagicMock()
    mock_backup.return_value = None
    mock_backup_file_exits.return_value = True
    mock_backup_instance.return_value = None
    mock_google_drive_manager.return_value = mock_backup_instance
    mock_backup_instance.upload_to_drive.return_value = True
    mock_rgb_lib_version.return_value = '0.3.0'
    mock_wallet_signature_type.return_value = WalletSignatureType.SINGLE_SIG_WALLET

    result = BackupService.backup(mock_valid_mnemonic, mock_password)

    # Assert the result
    assert result is True

# Test function


@patch('src.data.service.backup_service.SettingRepository.get_wallet_signature_type')
@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.service.backup_service.BackupService.backup_file_exists')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.backup')
@patch('src.data.service.backup_service.GoogleDriveManager')
def test_backup_when_backup_file_not_exits(mock_google_drive_manager, mock_backup, mock_backup_file_exits, mock_get_path, mock_get_hashed_mnemonic, mock_wallet_signature_type, setup_directory):
    """Case  2: When backup not exits after api call"""
    test_dir, _ = setup_directory

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = test_dir

    mock_backup_instance = MagicMock()
    mock_backup.return_value = None
    mock_backup_file_exits.return_value = False
    mock_backup_instance.return_value = None
    mock_google_drive_manager.return_value = mock_backup_instance
    mock_backup_instance.upload_to_drive.return_value = True
    mock_wallet_signature_type.return_value = WalletSignatureType.SINGLE_SIG_WALLET
    error_message = ERROR_BACKUP_FILE_NOT_EXITS
    with pytest.raises(CommonException, match=error_message):
        BackupService.backup(mock_valid_mnemonic, mock_password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
@patch('src.data.service.backup_service.BackupService.backup_file_exists')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.backup')
def test_backup_no_mnemonic(mock_backup, mock_backup_file_exits, mock_get_path, mock_get_hashed_mnemonic):
    """Case 3 : Test backup service with missing mnemonic"""
    # Setup mocks
    mock_get_hashed_mnemonic.side_effect = CommonException(
        ERROR_UNABLE_GET_MNEMONIC,
    )
    mock_get_path.return_value = os.path.join(
        os.path.dirname(__file__), 'some_path',
    )
    mock_backup.return_value = None
    mock_backup_file_exits.return_value = True

    # Call the BackupService.backup method
    mnemonic = None
    password = 'demo_password'

    with pytest.raises(CommonException, match=ERROR_UNABLE_GET_MNEMONIC):
        BackupService.backup(mnemonic, password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.utils.local_store.local_store.get_path')
def test_backup_no_password(mock_get_path, mock_get_hashed_mnemonic):
    """Case 4 : Test backup service with missing password"""

    # Setup mocks
    mock_get_hashed_mnemonic.return_value = 'e23ddff3cc'
    mock_get_path.return_value = os.path.join(
        os.path.dirname(__file__), 'some_path',
    )

    # Call the BackupService.backup method
    mnemonic = 'demo_mnemonic'
    password = None

    with pytest.raises(CommonException, match=ERROR_UNABLE_TO_GET_PASSWORD):
        BackupService.backup(mnemonic, password)


@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.backup_service.BackupService.backup_file_exists')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.backup')
def test_backup_no_hashed_value(mock_backup, mock_backup_file_exits, mock_get_hashed_mnemonic):
    """Case 5 : Test backup service with missing hashed value"""

    # Setup mocks
    mock_get_hashed_mnemonic.side_effect = CommonException(
        ERROR_UNABLE_TO_GET_HASHED_MNEMONIC,
    )
    mock_backup.return_value = None
    mock_backup_file_exits.return_value = True

    # Call the BackupService.backup method
    with pytest.raises(CommonException, match=ERROR_UNABLE_TO_GET_HASHED_MNEMONIC):
        BackupService.backup(mock_valid_mnemonic, mock_password)


def test_backup_file_exists():
    """Case 6 : test backup_file_exists"""
    result = BackupService.backup_file_exists('./random_path')
    assert result is False


@patch('src.data.service.backup_service.write_rgb_lib_version_file')
@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.backup_service.BackupService.backup_file_exists')
@patch('src.data.repository.common_operations_repository.CommonOperationRepository.backup')
@patch('src.data.service.backup_service.GoogleDriveManager')
@patch('src.data.service.backup_service.SettingRepository')
@patch('src.data.service.backup_service.os.path.exists')
def test_backup_multisig_wallet(
    mock_os_exists, mock_setting_repo, mock_google_drive,
    mock_backup_repo, mock_backup_exists, mock_hashed,
    mock_version_file, setup_directory,
):
    """Case 7: Test backup for multisig wallet - should backup multisig config."""

    mock_os_exists.return_value = False  # No existing backup file
    mock_hashed.return_value = 'hashed_mnemonic_123'
    mock_backup_exists.return_value = True

    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_setting_repo.get_multisig_config.return_value = (2, 3)
    mock_setting_repo.get_cosigners.return_value = [
        {'master_fingerprint': 'FP1'},
    ]

    mock_drive_instance = MagicMock()
    mock_drive_instance.upload_to_drive.return_value = True
    mock_google_drive.return_value = mock_drive_instance

    mock_version_file.return_value = ('/tmp/version.txt', 'version.txt')

    result = BackupService.backup('mnemonic words', 'password123')

    assert result is True
    # Verify multisig config was backed up
    # backup, version, multisig
    assert mock_drive_instance.upload_to_drive.call_count == 3


@patch('src.data.service.backup_service.BackupService._upload_multisig_config', return_value=True)
@patch('src.data.service.backup_service.BackupService._upload_backup_to_drive', return_value=(True, True))
@patch('src.data.service.backup_service.BackupService._prepare_backup_file')
@patch('src.data.service.backup_service.GoogleDriveManager')
@patch('src.data.service.backup_service.app_paths')
@patch('src.data.service.common_operation_service.CommonOperationService.get_hashed_mnemonic')
@patch('src.data.service.backup_service.os.remove')
@patch('src.data.service.backup_service.os.makedirs')
@patch('src.data.service.backup_service.os.path.exists', return_value=True)
def test_backup_removes_old_file(
    mock_os_exists, mock_makedirs, mock_remove, mock_hashed, mock_app_paths,
    mock_google_drive, mock_prepare, mock_upload_backup, mock_multisig_upload,
):
    """Case 8: Test backup removes old backup file if exists."""
    # Mock app_paths
    mock_app_paths.backup_folder_path = '/tmp/backup'
    mock_app_paths.iriswallet_temp_folder_path = '/tmp/iriswallet_temp'

    mock_hashed.return_value = 'hashed_mnemonic'

    result = BackupService.backup('mnemonic', 'password')

    assert result is True
    mock_remove.assert_called_once()  # Old backup file removed
