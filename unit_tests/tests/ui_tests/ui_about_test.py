"""Unit test for about UI"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

import os
import shutil
import zipfile
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QDir
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.utils.common_utils import network_info
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_DOWNLOAD_CANCELED
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.toast import ToastManager
from src.views.components.toast import ToastPreset
from src.views.ui_about import AboutWidget


@pytest.fixture
def mock_about_view_model():
    """Fixture to create a MainViewModel instance."""
    return MainViewModel(MagicMock())  # Mock the page navigation


@pytest.fixture
def about_widget(mock_about_view_model, qtbot, mocker):
    """Fixture to create the AboutWidget instance with mocked dependencies."""
    mock_config_values = {
        'indexer_url': 'test_url',
        'proxy_endpoint': 'test_endpoint',
    }

    with patch('src.utils.local_store.local_store.get_value') as mock_get_value, \
            patch('src.utils.common_utils.zip_logger_folder') as mock_zip_logger_folder, \
            patch('src.utils.helpers.SettingRepository.get_config_value') as mock_get_config_value:

        mock_get_value.return_value = True
        mock_zip_logger_folder.return_value = (
            '/mock/logs.zip', '/mock/output/dir',
        )

        mock_get_config_value.side_effect = lambda key, default=None: mock_config_values.get(
            key, default,
        )

        widget = AboutWidget(mock_about_view_model)
        qtbot.addWidget(widget)

    return widget


def test_widget_initialization(about_widget):
    """Test the initialization of the widget."""
    assert isinstance(about_widget.app_version_label, QLabel)
    assert about_widget.app_version_label.text().startswith('app_version')


def test_retranslate_ui(about_widget):
    """Test the retranslate_ui method."""
    about_widget.retranslate_ui()
    assert 'privacy_policy' in about_widget.privacy_policy_label.text()
    assert 'terms_of_service' in about_widget.terms_service_label.text()


def test_download_logs_button_click(about_widget, qtbot, mocker):
    """Test the download_logs button click event."""
    mock_download_logs = mocker.patch.object(about_widget, 'download_logs')
    qtbot.mouseClick(about_widget.download_log, Qt.LeftButton)
    mock_download_logs.assert_called_once()


def test_network_info_success(about_widget, mocker):
    """Test the network_info method with successful network retrieval."""
    mock_network = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
    )
    mock_network.return_value.value = 'testnet'
    network_info(about_widget)
    assert about_widget.network == 'testnet'


def test_network_info_common_exception(about_widget, mocker):
    """Test the network_info method with a CommonException."""
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=CommonException('Test exception'),
    )

    mock_toast = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )
    network_info(about_widget)

    assert about_widget.network == 'regtest'
    mock_toast.assert_called_once_with(
        parent=None, title=None, description='Test exception',
    )


def test_network_info_generic_exception(about_widget, mocker):
    """Test the network_info method with a generic exception."""
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=Exception('Generic error'),
    )

    mock_toast = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )
    network_info(about_widget)

    assert about_widget.network == 'regtest'
    mock_toast.assert_called_once_with(
        parent=None, title=None, description='Something went wrong',
    )


def test_download_logs_with_save_path(about_widget, qtbot, mocker):
    """Test the download_logs method when a save path is provided."""
    # Mock dependencies
    base_path = '/mock/base/path'
    mock_get_path = mocker.patch(
        'src.utils.local_store.local_store.get_path', return_value=base_path,
    )

    # Mock filesystem operations
    mocker.patch('os.makedirs')
    mock_rmtree = mocker.patch('shutil.rmtree')  # Mock directly
    mocker.patch('shutil.make_archive')
    mocker.patch('os.stat')
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('shutil.copy')
    mocker.patch('os.remove')
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch(
        'os.walk', return_value=[
            ('/mock/output/dir', [], ['file1', 'file2']),
        ],
    )
    mocker.patch('zipfile.ZipFile', autospec=True)

    # Mock download_file to ensure it's called
    def mock_download_file(save_path, output_dir):
        # Simulate the behavior of the actual download_file function
        with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zip_file.write(file_path, arcname)
        # Simulate the finally block
        shutil.rmtree(output_dir)
        # Simulate success toast
        ToastManager.success(description='Logs saved successfully.')

    mocker.patch(
        'src.views.ui_about.download_file',
        side_effect=mock_download_file,
    )

    # Mock zip_logger_folder at the module level
    zip_filename = 'mock/logs.zip'
    output_dir = '/mock/output/dir'
    zip_file_path = '/mock/base/path.zip'
    mock_zip_logger = mocker.patch(
        'src.views.ui_about.zip_logger_folder', autospec=True,
    )
    mock_zip_logger.return_value = (zip_filename, output_dir, zip_file_path)

    # Mock file dialog
    save_path = '/mock/save/path.zip'
    mock_file_dialog = mocker.patch(
        'PySide6.QtWidgets.QFileDialog.getSaveFileName',
        return_value=(save_path, 'Zip Files (*.zip)'),
    )

    # Mock ToastManager
    mock_toast_success = mocker.patch(
        'src.views.components.toast.ToastManager.success',
    )
    mock_toast_error = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )

    # Call the method
    about_widget.download_logs()

    # Verify calls
    mock_get_path.assert_called_once()
    mock_zip_logger.assert_called_once_with(base_path)
    mock_file_dialog.assert_called_once_with(
        about_widget, 'Save logs File', QDir.homePath(
        )+'/'+zip_filename, 'Zip Files (*.zip)',
    )
    mock_rmtree.assert_called_once_with(output_dir)
    mock_toast_error.assert_not_called()
    mock_toast_success.assert_called_once()


def test_download_logs_cancelled(about_widget, qtbot, mocker):
    """Test the download_logs method when the user cancels the save dialog."""
    # Mock dependencies
    base_path = '/mock/base/path'
    mock_get_path = mocker.patch(
        'src.utils.local_store.local_store.get_path', return_value=base_path,
    )

    # Mock filesystem operations
    mocker.patch('os.makedirs')
    mock_rmtree = mocker.patch('shutil.rmtree')  # Mock directly
    mocker.patch('shutil.make_archive')
    mocker.patch('os.stat')
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('shutil.copy')

    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('os.remove')

    # Mock zip_logger_folder at the module level
    zip_filename = 'mock/logs.zip'
    output_dir = '/mock/output/dir'
    zip_file_path = '/mock/base/path.zip'
    mock_zip_logger = mocker.patch(
        'src.views.ui_about.zip_logger_folder', autospec=True,
    )
    mock_zip_logger.return_value = (zip_filename, output_dir, zip_file_path)

    # Mock file dialog to simulate cancellation
    mock_file_dialog = mocker.patch(
        'PySide6.QtWidgets.QFileDialog.getSaveFileName',
        return_value=('', ''),
    )

    # Mock ToastManager
    mock_toast = mocker.patch(
        'src.views.components.toast.ToastManager.show_toast',
    )

    # Call the method
    about_widget.download_logs()

    # Verify calls
    mock_get_path.assert_called_once()
    mock_zip_logger.assert_called_once_with(base_path)
    mock_file_dialog.assert_called_once_with(
        about_widget, 'Save logs File', QDir.homePath(
        )+'/'+zip_filename, 'Zip Files (*.zip)',
    )
    # rmtree should not be called if download is cancelled
    mock_rmtree.assert_not_called()
    mock_toast.assert_called_once_with(
        about_widget,
        ToastPreset.INFORMATION,
        description=INFO_DOWNLOAD_CANCELED,
    )


def test_download_logs_button_functionality(about_widget, qtbot, mocker):
    """Test that the download logs button triggers the download_logs method."""
    # Mock the download_logs method
    mock_download_logs = mocker.patch.object(about_widget, 'download_logs')

    # Click the download button
    qtbot.mouseClick(about_widget.download_log, Qt.LeftButton)

    # Verify the method was called
    mock_download_logs.assert_called_once()
