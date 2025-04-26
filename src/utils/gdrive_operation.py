"""Helper module to upload and download backup file(zip) from google drive"""
from __future__ import annotations

import io
import os
import pickle

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from PySide6.QtWidgets import QApplication

from src.utils.error_message import ERROR_WHEN_DRIVE_STORAGE_FULL
from src.utils.gauth import authenticate
from src.utils.logging import logger
from src.views.components.message_box import MessageBox


class GoogleDriveManager:
    """
    A class to manage interactions with Google Drive API.
    """

    def __init__(self):
        """
        Initializes the GoogleDriveManager instance.
        """
        self.service = None

    def _get_service(self):
        """
        Retrieves the authenticated Google Drive service instance.
        """
        self.service = authenticate(QApplication.instance())
        return self.service

    def _get_storage_quota(self) -> dict:
        """
        Retrieves the current storage quota information.

        Returns:
            dict: A dictionary containing the storage quota information.
        """
        try:
            storage_info = self.service.about().get(fields='storageQuota').execute()
            return storage_info.get('storageQuota', {})
        except HttpError as exc:
            logger.error(
                'HttpError occurred while retrieving storage quota: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise
        except Exception as exc:
            logger.error(
                'Unexpected error occurred while retrieving storage quota: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise

    def _search_file(self, file_name: str) -> str | None:
        """
        Searches for a file by name on Google Drive.

        Args:
            file_name (str): The name of the file to search for.

        Returns:
            str | None: The ID of the file if found, None otherwise.
        """
        try:
            results = self.service.files().list(
                q=f"name='{file_name}'",
                spaces='drive',
                fields='files(id, name)',
            ).execute()
            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
        except HttpError as exc:
            logger.error(
                'HttpError occurred during file search: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during file search: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise

    def _delete_file(self, file_id: str) -> bool:
        """
        Deletes a file from Google Drive given its file ID.

        Args:
            file_id (str): The ID of the file to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as exc:
            logger.error(
                'HttpError occurred during file deletion: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during file deletion: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise

    def _download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Downloads a file from Google Drive to the specified destination path.

        Args:
            file_id (str): The ID of the file to download.
            destination_path (str): The path where the file should be saved.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        request = self.service.files().get_media(fileId=file_id)
        with io.FileIO(destination_path, 'wb') as file_io:
            downloader = MediaIoBaseDownload(file_io, request)
            done = False
            try:
                while not done:
                    status, done = downloader.next_chunk()
                    print(f'Download {int(status.progress() * 100)}%')
                return True
            except HttpError as exc:
                logger.error(
                    'HttpError occurred during file download: %s, Message: %s', type(
                        exc,
                    ).__name__, str(exc),
                )
                raise
            except Exception as exc:
                logger.error(
                    'Unexpected error occurred during file download: %s, Message: %s', type(
                        exc,
                    ).__name__, str(exc),
                )
                raise

    def upload_to_drive(self, file_path: str, file_name: str) -> bool:
        """
        Uploads a file to Google Drive.

        Args:
            file_path (str): The local path of the file to upload.
            file_name (str): The name of the file on Google Drive.

        Returns:
            bool: True if upload was successful, False otherwise.
        """
        service = self._get_service()

        storage_quota = self._get_storage_quota()
        usage = int(storage_quota.get('usage', '0'))
        limit = int(storage_quota.get('limit', '0'))
        if 0 < limit <= usage:
            self.error_reporter(ERROR_WHEN_DRIVE_STORAGE_FULL)
            MessageBox('warning', ERROR_WHEN_DRIVE_STORAGE_FULL)
            return False

        if service is None:
            self.info_reporter('Google Drive service is not initialized.')
            return False

        # Validate inputs
        if not os.path.exists(file_path):
            self.error_reporter(f'File path does not exist: {file_path}')
            return False

        try:
            existing_file_id: str | None = self._search_file(file_name)
            backup_file_name = None
            if existing_file_id:
                pubkey, file_extension = os.path.splitext(file_name)
                backup_file_name = f'{pubkey}_temp{file_extension}'
                self._rename_file(existing_file_id, backup_file_name)

            new_file_id = self._upload_file(file_path, file_name)
            if self._verify_upload(file_name, new_file_id):
                if backup_file_name and existing_file_id:
                    self._delete_file(existing_file_id)
                return True
            raise ValueError('Uploaded file verification failed.')
        except (FileNotFoundError, pickle.PickleError, HttpError) as specific_error:
            self._handle_specific_error(specific_error)

        except Exception as generic_error:
            self._handle_generic_error(
                generic_error, backup_file_name, file_name,
            )
        return False

    def download_from_drive(self, file_name: str, destination_dir: str) -> bool | None:
        """
        Downloads a file from Google Drive by name to the specified directory.

        Args:
            file_name (str): The name of the file on Google Drive to download.
            destination_dir (str): The local directory path to save the downloaded file.

        Returns:
            bool: True if download was successful.
            None: If file is not found on Google Drive.
        """
        try:
            service = self._get_service()
            if service is None:
                return False

            # Validate inputs
            if not os.path.isdir(destination_dir):
                logger.error(
                    'Destination directory does not exist: %s', destination_dir,
                )
                return False

            file_id = self._search_file(file_name)
            if file_id:
                destination_path = os.path.join(destination_dir, file_name)
                return self._download_file(file_id, destination_path)

            logger.info("File '%s' not found on Google Drive.", file_name)
            return None

        except HttpError as exc:
            logger.error(
                'HttpError occurred during file download: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during file download: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
        return False

    @staticmethod
    def error_reporter(message: str):
        """
        Default error reporter which logs the error message.

        Args:
            message (str): The error message to report.
        """
        logger.error(message)

    @staticmethod
    def info_reporter(message: str):
        """
        Default info reporter which logs the info message.

        Args:
            message (str): The info message to report.
        """
        logger.info(message)

    def _handle_specific_error(self, error: Exception):
        """
        Handles specific types of errors.

        Args:
            error (Exception): The specific error to handle.
        """
        if isinstance(error, FileNotFoundError):
            self.error_reporter(f'File not found: {str(error)}')
        elif isinstance(error, pickle.PickleError):
            self.error_reporter(f'Failed to load or dump token: {str(error)}')
        elif isinstance(error, HttpError):
            self.error_reporter(f'HTTP error occurred: {str(error)}')
        else:
            self.error_reporter(f'Unexpected error: {str(error)}')

    def _handle_generic_error(self, error: Exception, backup_file_name: str | None, original_file_name: str):
        """
        Handles generic errors and attempts to restore backup if available.

        Args:
            error (Exception): The generic error to handle.
            backup_file_name (str): The name of the backup file.
            original_file_name (str): The original name of the file.
        """
        logger.error(
            'Unexpected error occurred during file upload: %s, Message: %s', type(
                error,
            ).__name__, str(error),
        )
        if backup_file_name:
            self._restore_backup(backup_file_name, original_file_name)

    def _restore_backup(self, backup_file_name: str, original_file_name: str):
        """
        Restores a backup file to its original name.

        Args:
            backup_file_name (str): The name of the backup file.
            original_file_name (str): The original name of the file.
        """
        try:
            backup_file_id = self._search_file(backup_file_name)
            if backup_file_id:
                file_metadata = {'name': original_file_name}
                self.service.files().update(fileId=backup_file_id, body=file_metadata).execute()
                logger.info(
                    'Restored backup file to original name: %s', original_file_name,
                )
        except HttpError as exc:
            logger.error(
                'Failed to restore backup file: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during backup restoration: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )

    def _rename_file(self, file_id: str, new_name: str):
        """
        Renames a file on Google Drive.

        Args:
            file_id (str): The ID of the file to rename.
            new_name (str): The new name for the file.
        """
        try:
            file_metadata = {'name': new_name}
            self.service.files().update(fileId=file_id, body=file_metadata).execute()
            logger.info('Renamed existing file to: %s', new_name)
        except HttpError as exc:
            logger.error(
                'Failed to rename file: %s, Message: %s',
                type(exc).__name__, str(exc),
            )
            raise
        except Exception:
            logger.error('Unexpected error occurred during file')

    def _upload_file(self, file_path: str, file_name: str) -> str:
        """
        Uploads a file to Google Drive.

        Args:
            file_path (str): The path to the file to be uploaded.
            file_name (str): The name of the file on Google Drive.
            folder_id (str, optional): The ID of the folder on Google Drive to upload the file to.

        Returns:
            str: The ID of the uploaded file.
        """
        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, resumable=True)
        try:
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id',
            ).execute()
            return file.get('id')
        except HttpError as exc:
            logger.error(
                'HttpError occurred during file upload: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during file upload: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            raise

    def _verify_upload(self, expected_name: str, file_id: str) -> bool:
        """
        Verifies if the uploaded file matches the expected name and ID.

        Args:
            expected_name (str): The expected name of the file.
            file_id (str): The ID of the uploaded file.

        Returns:
            bool: True if the uploaded file matches the expected name and ID, False otherwise.
        """
        try:
            file = self.service.files().get(fileId=file_id, fields='name').execute()
            if file.get('name') == expected_name:
                logger.info(
                    "File '%s' uploaded successfully with ID: %s", expected_name, file_id,
                )
                return True

            logger.error(
                "Uploaded file name '%s' does not match expected name '%s'", file.get(
                    'name',
                ), expected_name,
            )
            return False
        except HttpError as exc:
            logger.error(
                'HttpError occurred during file verification: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return False
        except Exception as exc:
            logger.error(
                'Unexpected error occurred during file verification: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return False
