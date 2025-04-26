# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for Google Drive operations."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from src.utils.error_message import ERROR_WHEN_DRIVE_STORAGE_FULL
from src.utils.gdrive_operation import GoogleDriveManager

# Test constants
TEST_FILE_ID = 'test123'
TEST_FILE_NAME = 'test.txt'
TEST_FILE_PATH = '/tmp/test.txt'
TEST_CONTENT = b'test content'


@pytest.fixture
def gdrive_manager():
    """Create GoogleDriveManager instance for testing."""
    with patch('src.utils.gdrive_operation.QApplication'):
        return GoogleDriveManager()


@pytest.fixture
def mock_service():
    """Mock Google Drive service with common methods."""
    service = MagicMock()
    service.files.return_value.get.return_value.execute.return_value = {
        'id': TEST_FILE_ID,
        'name': TEST_FILE_NAME,
    }
    return service


@pytest.fixture
def mock_authenticate():
    """Mock authenticate function."""
    with patch('src.utils.gdrive_operation.authenticate') as mock:
        mock.return_value = MagicMock()
        yield mock


def test_init(gdrive_manager):
    """Test initialization."""
    assert gdrive_manager.service is None


def test_get_service(gdrive_manager, mock_authenticate):
    """Test service initialization."""
    service = gdrive_manager._get_service()
    assert service is not None
    mock_authenticate.assert_called_once()


def test_get_storage_quota_success(gdrive_manager, mock_service):
    """Test successful storage quota retrieval."""
    gdrive_manager.service = mock_service
    mock_service.about.return_value.get.return_value.execute.return_value = {
        'storageQuota': {'limit': '1000', 'usage': '500'},
    }

    quota = gdrive_manager._get_storage_quota()

    assert quota == {'limit': '1000', 'usage': '500'}
    mock_service.about.return_value.get.assert_called_once_with(
        fields='storageQuota',
    )


def test_get_storage_quota_error(gdrive_manager, mock_service):
    """Test storage quota retrieval with error."""
    gdrive_manager.service = mock_service
    mock_service.about.return_value.get.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=403), content=b'Error',
    )

    with pytest.raises(HttpError):
        gdrive_manager._get_storage_quota()


def test_search_file_found(gdrive_manager, mock_service):
    """Test file search when file exists."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': [{'id': TEST_FILE_ID, 'name': TEST_FILE_NAME}],
    }

    file_id = gdrive_manager._search_file(TEST_FILE_NAME)
    assert file_id == TEST_FILE_ID


def test_search_file_not_found(gdrive_manager, mock_service):
    """Test file search when file doesn't exist."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.list.return_value.execute.return_value = {
        'files': [],
    }

    file_id = gdrive_manager._search_file(TEST_FILE_NAME)
    assert file_id is None


def test_upload_file_success(gdrive_manager, mock_service):
    """Test successful file upload."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.create.return_value.execute.return_value = {
        'id': TEST_FILE_ID,
    }

    with patch('src.utils.gdrive_operation.MediaFileUpload') as mock_upload:
        file_id = gdrive_manager._upload_file(TEST_FILE_PATH, TEST_FILE_NAME)
        assert file_id == TEST_FILE_ID
        mock_upload.assert_called_once_with(TEST_FILE_PATH, resumable=True)


def test_upload_file_error(gdrive_manager, mock_service):
    """Test file upload with error."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.create.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=500), content=b'Error',
    )

    with patch('src.utils.gdrive_operation.MediaFileUpload'), pytest.raises(HttpError):
        gdrive_manager._upload_file(TEST_FILE_PATH, TEST_FILE_NAME)


def test_verify_upload_success(gdrive_manager, mock_service):
    """Test successful upload verification."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.get.return_value.execute.return_value = {
        'name': TEST_FILE_NAME,
    }

    result = gdrive_manager._verify_upload(TEST_FILE_NAME, TEST_FILE_ID)
    assert result is True


def test_verify_upload_name_mismatch(gdrive_manager, mock_service):
    """Test upload verification with name mismatch."""
    gdrive_manager.service = mock_service
    mock_service.files.return_value.get.return_value.execute.return_value = {
        'name': 'different.txt',
    }

    result = gdrive_manager._verify_upload(TEST_FILE_NAME, TEST_FILE_ID)
    assert result is False


def test_upload_to_drive_full_storage(gdrive_manager):
    """Test upload when storage is full."""
    with patch.object(gdrive_manager, '_get_service'), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '1000', 'limit': '1000'}), \
            patch.object(gdrive_manager, 'error_reporter') as mock_error, \
            patch('src.utils.gdrive_operation.MessageBox') as mock_message_box:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

        assert result is False
        mock_error.assert_called_once_with(ERROR_WHEN_DRIVE_STORAGE_FULL)
        mock_message_box.assert_called_once_with(
            'warning', 'Google Drive storage is full. Cannot upload the file.',
        )


def test_upload_to_drive_success(gdrive_manager, mock_service):
    """Test successful drive upload."""
    gdrive_manager.service = mock_service
    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch.object(gdrive_manager, '_search_file', return_value=None), \
            patch.object(gdrive_manager, '_upload_file', return_value=TEST_FILE_ID), \
            patch.object(gdrive_manager, '_verify_upload', return_value=True), \
            patch('os.path.exists', return_value=True):

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)
        assert result is True


def test_download_from_drive_success(gdrive_manager, mock_service):
    """Test successful file download."""
    gdrive_manager.service = mock_service

    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_search_file', return_value=TEST_FILE_ID), \
            patch.object(gdrive_manager, '_download_file', return_value=True), \
            patch('os.path.isdir', return_value=True):

        result = gdrive_manager.download_from_drive(TEST_FILE_NAME, '/tmp')
        assert result is True


def test_download_from_drive_file_not_found(gdrive_manager):
    """Test download when file doesn't exist."""
    with patch.object(gdrive_manager, '_get_service'), \
            patch.object(gdrive_manager, '_search_file', return_value=None), \
            patch('os.path.isdir', return_value=True):

        result = gdrive_manager.download_from_drive(TEST_FILE_NAME, '/tmp')
        assert result is None


def test_restore_backup_success(gdrive_manager, mock_service):
    """Test successful backup restoration."""
    gdrive_manager.service = mock_service
    backup_name = 'backup.txt'

    with patch.object(gdrive_manager, '_search_file', return_value=TEST_FILE_ID):
        gdrive_manager._restore_backup(backup_name, TEST_FILE_NAME)
        mock_service.files.return_value.update.assert_called_once()


def test_handle_specific_error(gdrive_manager):
    """Test specific error handling."""
    with patch.object(gdrive_manager, 'error_reporter') as mock_error:
        gdrive_manager._handle_specific_error(FileNotFoundError('test error'))
        mock_error.assert_called_once()


def test_handle_generic_error(gdrive_manager):
    """Test generic error handling."""
    with patch.object(gdrive_manager, '_restore_backup') as mock_restore:
        gdrive_manager._handle_generic_error(
            Exception('test'), 'backup.txt', TEST_FILE_NAME,
        )
        mock_restore.assert_called_once_with('backup.txt', TEST_FILE_NAME)


def test_delete_file_complete_coverage(gdrive_manager, mock_service):
    """Test delete_file method with complete coverage."""
    gdrive_manager.service = mock_service

    # Test successful deletion
    mock_service.files.return_value.delete.return_value.execute.return_value = None
    result = gdrive_manager._delete_file(TEST_FILE_ID)
    assert result is True
    mock_service.files.return_value.delete.assert_called_with(
        fileId=TEST_FILE_ID,
    )

    # Test HttpError
    mock_service.files.return_value.delete.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=404), content=b'File not found',
    )
    with pytest.raises(HttpError):
        gdrive_manager._delete_file(TEST_FILE_ID)

    # Test generic exception
    mock_service.files.return_value.delete.return_value.execute.side_effect = Exception(
        'Generic error',
    )
    with pytest.raises(Exception):
        gdrive_manager._delete_file(TEST_FILE_ID)


def test_upload_to_drive_file_not_exists(gdrive_manager):
    """Test upload when file doesn't exist."""
    with patch.object(gdrive_manager, '_get_service', return_value=MagicMock()), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch('os.path.exists', return_value=False), \
            patch.object(gdrive_manager, 'error_reporter') as mock_error:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

    assert result is False
    mock_error.assert_called_once_with(
        f'File path does not exist: {TEST_FILE_PATH}',
    )


def test_upload_to_drive_with_existing_file(gdrive_manager, mock_service):
    """Test upload when file already exists."""
    gdrive_manager.service = mock_service
    existing_file_id = 'existing123'

    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch('os.path.exists', return_value=True), \
            patch.object(gdrive_manager, '_search_file', return_value=existing_file_id), \
            patch.object(gdrive_manager, '_rename_file') as mock_rename, \
            patch.object(gdrive_manager, '_upload_file', return_value=TEST_FILE_ID), \
            patch.object(gdrive_manager, '_verify_upload', return_value=True), \
            patch.object(gdrive_manager, '_delete_file') as mock_delete:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

        assert result is True
        mock_rename.assert_called_once()
        mock_delete.assert_called_once_with(existing_file_id)


def test_upload_to_drive_verification_failed(gdrive_manager, mock_service):
    """Test upload when verification fails."""
    gdrive_manager.service = mock_service

    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch('os.path.exists', return_value=True), \
            patch.object(gdrive_manager, '_search_file', return_value=None), \
            patch.object(gdrive_manager, '_upload_file', return_value=TEST_FILE_ID), \
            patch.object(gdrive_manager, '_verify_upload', return_value=False), \
            patch('src.utils.logging.logger.error') as mock_logger:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

    assert result is False
    mock_logger.assert_called_once_with(
        'Unexpected error occurred during file upload: %s, Message: %s',
        'ValueError', 'Uploaded file verification failed.',
    )


def test_upload_to_drive_specific_error(gdrive_manager, mock_service):
    """Test upload with specific error types."""
    gdrive_manager.service = mock_service

    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch('os.path.exists', return_value=True), \
            patch.object(gdrive_manager, '_search_file', side_effect=FileNotFoundError('Test error')), \
            patch.object(gdrive_manager, '_handle_specific_error') as mock_handle_error:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

        assert result is False
        mock_handle_error.assert_called_once()


def test_upload_to_drive_generic_error(gdrive_manager, mock_service):
    """Test upload with generic error and backup restoration."""
    gdrive_manager.service = mock_service

    with patch.object(gdrive_manager, '_get_service', return_value=mock_service), \
            patch.object(gdrive_manager, '_get_storage_quota', return_value={'usage': '500', 'limit': '1000'}), \
            patch('os.path.exists', return_value=True), \
            patch.object(gdrive_manager, '_search_file', return_value='existing123'), \
            patch.object(gdrive_manager, '_rename_file'), \
            patch.object(gdrive_manager, '_upload_file', side_effect=Exception('Test error')), \
            patch.object(gdrive_manager, '_handle_generic_error') as mock_handle_error:

        result = gdrive_manager.upload_to_drive(TEST_FILE_PATH, TEST_FILE_NAME)

    assert result is False
    mock_handle_error.assert_called_once()


def test_download_file_complete_coverage(gdrive_manager, mock_service):
    """Test download_file method with complete coverage."""
    gdrive_manager.service = mock_service

    # Mock successful download
    mock_downloader = MagicMock()
    mock_downloader.next_chunk.return_value = (
        MagicMock(progress=lambda: 0.5), False,
    )
    mock_downloader.next_chunk.side_effect = [
        (MagicMock(progress=lambda: 0.5), False),
        (MagicMock(progress=lambda: 1.0), True),
    ]

    with patch('src.utils.gdrive_operation.MediaIoBaseDownload', return_value=mock_downloader), \
            patch('io.FileIO') as mock_file:

        result = gdrive_manager._download_file(TEST_FILE_ID, TEST_FILE_PATH)
        assert result is True
        mock_file.assert_called_once_with(TEST_FILE_PATH, 'wb')
        assert mock_downloader.next_chunk.call_count == 2

    # Test HttpError
    mock_downloader.next_chunk.side_effect = HttpError(
        resp=MagicMock(status=404), content=b'File not found',
    )
    with patch('src.utils.gdrive_operation.MediaIoBaseDownload', return_value=mock_downloader), \
            patch('io.FileIO'):
        with pytest.raises(HttpError):
            gdrive_manager._download_file(TEST_FILE_ID, TEST_FILE_PATH)

    # Test generic exception
    mock_downloader.next_chunk.side_effect = Exception('Download failed')
    with patch('src.utils.gdrive_operation.MediaIoBaseDownload', return_value=mock_downloader), \
            patch('io.FileIO'):
        with pytest.raises(Exception):
            gdrive_manager._download_file(TEST_FILE_ID, TEST_FILE_PATH)


def test_rename_file_complete_coverage(gdrive_manager, mock_service):
    """Test rename_file method with complete coverage."""
    gdrive_manager.service = mock_service
    new_name = 'new_test.txt'

    # Test successful rename
    mock_service.files.return_value.update.return_value.execute.return_value = {
        'id': TEST_FILE_ID,
        'name': new_name,
    }

    gdrive_manager._rename_file(TEST_FILE_ID, new_name)
    mock_service.files.return_value.update.assert_called_with(
        fileId=TEST_FILE_ID,
        body={'name': new_name},
    )

    # Test HttpError
    mock_service.files.return_value.update.return_value.execute.side_effect = HttpError(
        resp=MagicMock(status=404), content=b'File not found',
    )
    with pytest.raises(HttpError):
        gdrive_manager._rename_file(TEST_FILE_ID, new_name)

    # Test generic exception
    error = Exception('Rename failed')
    mock_service.files.return_value.update.return_value.execute.side_effect = error
    with patch('src.utils.logging.logger.error') as mock_logger:
        gdrive_manager._rename_file(TEST_FILE_ID, new_name)
        mock_logger.assert_called_with(
            'Unexpected error occurred during file',
        )


def test_download_file_with_progress(gdrive_manager, mock_service, capsys):
    """Test download_file with progress updates."""
    gdrive_manager.service = mock_service

    # Mock downloader with multiple progress updates
    mock_downloader = MagicMock()
    progress_values = [0.25, 0.5, 0.75, 1.0]

    # Create status objects with fixed progress values
    status_objects = []
    for val in progress_values:
        status = MagicMock()
        status.progress.return_value = val  # Use return_value instead of lambda
        status_objects.append(status)

    # Set up the side effect to return each status object in sequence
    mock_downloader.next_chunk.side_effect = [
        (status, i == len(progress_values) - 1)
        for i, status in enumerate(status_objects)
    ]

    with patch('src.utils.gdrive_operation.MediaIoBaseDownload', return_value=mock_downloader), \
            patch('io.FileIO'):

        result = gdrive_manager._download_file(TEST_FILE_ID, TEST_FILE_PATH)
        assert result is True

        # Verify progress output
        captured = capsys.readouterr()
        # Print the actual output for debugging
        # Check each progress value
        for value in progress_values:
            expected_message = f"Download {int(value * 100)}%"
            assert expected_message in captured.out, f"Missing progress message: {
                expected_message
            }"
