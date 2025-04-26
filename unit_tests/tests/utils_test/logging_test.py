"""Unit test for logger class"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import logging
import os
import sys
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from src.utils.constant import APP_DIR
from src.utils.constant import LOG_FILE_MAX_BACKUP_COUNT
from src.utils.constant import LOG_FILE_MAX_SIZE
from src.utils.constant import LOG_FOLDER_NAME
from src.utils.logging import setup_logger  # Adjust import path as needed


class TestSetupLogging(unittest.TestCase):
    """Unit test for logger class """
    @patch('src.utils.logging.local_store')
    @patch('src.utils.logging.RotatingFileHandler')
    @patch('src.utils.logging.StreamHandler')
    @patch('src.utils.logging.logging.getLogger')
    def test_setup_logging_production(
        self, mock_get_logger, mock_stream_handler, mock_rotating_file_handler, mock_local_store,
    ):
        """Test logging setup in production mode."""

        # Setup mocks
        mock_local_store.create_folder.return_value = 'mock_log_path'
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        mock_rotating_file_handler_instance = MagicMock()
        mock_rotating_file_handler.return_value = mock_rotating_file_handler_instance

        # Call setup_logger with correct arguments
        setup_logger('iris-wallet', 'iris_wallet_desktop.log', 'production')

        # Assertions
        mock_local_store.create_folder.assert_called_once_with(
            os.path.join(APP_DIR, LOG_FOLDER_NAME),
        )
        mock_get_logger.assert_called_once_with('iris-wallet')
        mock_rotating_file_handler.assert_called_once_with(
            os.path.join('mock_log_path', 'iris_wallet_desktop.log'),
            maxBytes=LOG_FILE_MAX_SIZE,
            backupCount=LOG_FILE_MAX_BACKUP_COUNT,
        )
        mock_logger_instance.addHandler.assert_called_once_with(
            mock_rotating_file_handler_instance,
        )
        mock_rotating_file_handler_instance.setLevel.assert_called_once_with(
            logging.ERROR,
        )

    @patch('src.utils.logging.local_store')
    @patch('src.utils.logging.RotatingFileHandler')
    @patch('src.utils.logging.StreamHandler')
    @patch('src.utils.logging.logging.getLogger')
    def test_setup_logging_development(
        self, mock_get_logger, mock_stream_handler, mock_rotating_file_handler, mock_local_store,
    ):
        """Test logging setup in development mode."""

        # Setup mocks
        mock_local_store.create_folder.return_value = 'mock_log_path'
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        mock_rotating_file_handler_instance = MagicMock()
        mock_rotating_file_handler.return_value = mock_rotating_file_handler_instance
        mock_console_handler_instance = MagicMock()
        mock_stream_handler.return_value = mock_console_handler_instance

        # Call setup_logger with correct arguments
        setup_logger('iris-wallet', 'iris_wallet_desktop.log', 'development')

        # Assertions
        mock_local_store.create_folder.assert_called_once_with(
            os.path.join(APP_DIR, LOG_FOLDER_NAME),
        )
        mock_get_logger.assert_called_once_with('iris-wallet')
        mock_rotating_file_handler.assert_called_once_with(
            os.path.join('mock_log_path', 'iris_wallet_desktop.log'),
            maxBytes=LOG_FILE_MAX_SIZE,
            backupCount=LOG_FILE_MAX_BACKUP_COUNT,
        )
        mock_logger_instance.addHandler.assert_any_call(
            mock_rotating_file_handler_instance,
        )
        mock_rotating_file_handler_instance.setLevel.assert_called_once_with(
            logging.DEBUG,
        )

        # Additional checks for development mode
        mock_stream_handler.assert_called_once_with(sys.stdout)
        mock_console_handler_instance.setLevel.assert_called_once_with(
            logging.DEBUG,
        )
        mock_logger_instance.addHandler.assert_any_call(
            mock_console_handler_instance,
        )
