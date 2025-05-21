"""Sets up the logging configuration for the application."""
from __future__ import annotations

import logging
import os
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from src.utils.constant import APP_DIR
from src.utils.constant import LOG_FILE_MAX_BACKUP_COUNT
from src.utils.constant import LOG_FILE_MAX_SIZE
from src.utils.constant import LOG_FOLDER_NAME
from src.utils.local_store import local_store


def setup_logger(logger_name: str, log_file_name: str, application_status: str | None = None) -> logging.Logger:
    """
    Sets up the logging configuration for the application.

    Depending on the application status (production or development), it configures
    different logging handlers. For production, it logs to a file with a defined
    size limit and backup count. For development, it logs both to a file and the console.

    Args:
        logger_name (str): Name of the logger.
        log_file_name (str): Log file name.
        application_status (str | None, optional): The current status of the application, either 'production',
            'development', or None. If None, it defaults to 'development'.
    Returns:
        logging.Logger: Configured logger instance.
    """
    log_directory = os.path.join(APP_DIR, LOG_FOLDER_NAME)
    path = local_store.create_folder(log_directory)

    # Create a logger
    logger_instance = logging.getLogger(logger_name)
    # Set to debug to capture all levels of messages
    logger_instance.setLevel(logging.DEBUG)
    # Prevent logging from propagating to the root logger
    logger_instance.propagate = False

    # Define formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_name = os.path.join(path, log_file_name)

    # Define and add handlers based on network
    file_handler = RotatingFileHandler(
        file_name,
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=LOG_FILE_MAX_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)
    logger_instance.addHandler(file_handler)

    if application_status == 'production':
        file_handler.setLevel(logging.ERROR)  # Capture info and error messages
    else:
        # Capture debug, info, warnings, and errors
        file_handler.setLevel(logging.DEBUG)

        console_handler = StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger_instance.addHandler(console_handler)

    return logger_instance


# Determine the application status based on the execution environment
APPLICATION_STATUS = 'production' if getattr(
    sys, 'frozen', False,
) else 'development'

# Set up loggers using the refactored function and capturing all logs without applying `APPLICATION_STATUS`
logger = setup_logger(
    'iris-wallet', 'iris_wallet_vault.log',
)
