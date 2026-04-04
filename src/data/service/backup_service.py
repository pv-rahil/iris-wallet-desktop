"""
This module provides the service for backup.
"""
from __future__ import annotations

import json
import os
import shutil

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import BackupRequestModel
from src.model.enums.enums_model import WalletSignatureType
from src.utils.build_app_path import app_paths
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_BACKUP_FILE_NOT_EXITS
from src.utils.error_message import ERROR_UNABLE_TO_GET_PASSWORD
from src.utils.gdrive_operation import GoogleDriveManager
from src.utils.handle_exception import handle_exceptions
from src.utils.helpers import write_rgb_lib_version_file
from src.utils.logging import logger


class BackupService:
    """
    Service class to handle the backup operations.
    """
    @staticmethod
    def backup_file_exists(file_path: str) -> bool:
        """
        Check if a file exists at the given path.

        :param file_path: Path of the file to check.
        :return: True if file exists, False otherwise.
        """
        return os.path.exists(file_path)

    @staticmethod
    def _prepare_backup_file(backup_file_path: str, password: str) -> None:
        """Prepare and verify backup file exists."""
        if not password:
            raise CommonException(ERROR_UNABLE_TO_GET_PASSWORD)

        logger.info('Calling backup api')
        CommonOperationRepository.backup(
            BackupRequestModel(
                backup_path=backup_file_path,
                password=password,
            ),
        )

        if not BackupService.backup_file_exists(backup_file_path):
            error_message = ERROR_BACKUP_FILE_NOT_EXITS + ' ' + backup_file_path
            raise CommonException(error_message)

    @staticmethod
    def _upload_backup_to_drive(backup: GoogleDriveManager, backup_file_path: str, backup_file_name: str, hashed_mnemonic: str) -> tuple:
        """Upload backup and version files to Google Drive."""
        success = backup.upload_to_drive(
            file_path=backup_file_path, file_name=backup_file_name,
        )
        version_file_path, version_file_name = write_rgb_lib_version_file(
            hashed_mnemonic,
        )
        version_success = backup.upload_to_drive(
            file_path=version_file_path, file_name=version_file_name,
        )
        return success, version_success

    @staticmethod
    def _upload_multisig_config(backup: GoogleDriveManager, hashed_mnemonic: str, backup_folder_path: str) -> bool:
        """Upload multisig configuration if applicable."""
        if SettingRepository.get_wallet_signature_type() != WalletSignatureType.MULTI_SIG_WALLET:
            return True

        req_signers, tot_signers = SettingRepository.get_multisig_config()
        cosigners = SettingRepository.get_cosigners()

        multisig_data = {
            'required_signers': req_signers,
            'total_signers': tot_signers,
            'cosigners': cosigners,
        }

        multisig_file_name = f'{hashed_mnemonic}.multisig.json'
        multisig_file_path = os.path.join(
            backup_folder_path, multisig_file_name,
        )

        with open(multisig_file_path, 'w', encoding='utf-8') as mf:
            json.dump(multisig_data, mf)

        logger.info('Uploading multisig configuration to drive')
        return backup.upload_to_drive(
            file_path=multisig_file_path, file_name=multisig_file_name,
        )

    @staticmethod
    def backup(mnemonic: str, password: str) -> bool:
        """
        Creates a temporary backup of the wallet's data, uploads it to Google Drive,
        and deletes the local backup after a successful upload.

        Returns:
            bool: True if the backup and upload were successful, False otherwise.

        Raises:
            CommonException: If any operation fails during the backup process.
        """
        try:
            logger.info('Back up process started...')

            backup_folder_path = app_paths.backup_folder_path
            hashed_mnemonic = CommonOperationService.get_hashed_mnemonic(
                mnemonic=mnemonic,
            )
            backup_file_name = f'{hashed_mnemonic}.rgb_backup'

            if not os.path.exists(backup_folder_path):
                logger.info('Creating backup folder')
                os.makedirs(backup_folder_path, exist_ok=True)

            backup_file_path = os.path.join(
                backup_folder_path, backup_file_name,
            )

            if os.path.exists(backup_file_path):
                os.remove(backup_file_path)

            BackupService._prepare_backup_file(backup_file_path, password)

            backup = GoogleDriveManager()
            success, version_success = BackupService._upload_backup_to_drive(
                backup, backup_file_path, backup_file_name, hashed_mnemonic,
            )
            multisig_success = BackupService._upload_multisig_config(
                backup, hashed_mnemonic, backup_folder_path,
            )

            return success and version_success and multisig_success

        except Exception as exc:
            return handle_exceptions(exc)
        finally:
            if os.path.exists(app_paths.iriswallet_temp_folder_path):
                shutil.rmtree(
                    app_paths.iriswallet_temp_folder_path, ignore_errors=True,
                )
                logger.info('Deleting backup folder')
