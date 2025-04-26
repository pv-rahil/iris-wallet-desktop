"""
Local storage utility for application settings and data.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QDir
from PySide6.QtCore import QSettings
from PySide6.QtCore import QStandardPaths

from src.flavour import __network__
from src.utils.constant import APP_DIR
from src.utils.constant import APP_NAME
from src.utils.constant import ORGANIZATION_DOMAIN


class LocalStore:
    """
    Manages persistent storage of application settings and data.

    This class provides an interface to store and retrieve application settings
    and create network-specific directories for data storage.

    """

    def __init__(self, app_name, org_domain):
        """
        Initialize the LocalStore with application name and organization domain.

        Args:
            app_name (str): The name of the application.
            org_domain (str): The organization domain.
        """
        # Set application-wide properties
        QCoreApplication.setApplicationName(app_name)
        QCoreApplication.setOrganizationDomain(org_domain)

        # Adjust the base path to include directory like 'iriswallet/network'
        self.base_path = QDir(
            QStandardPaths.writableLocation(
                QStandardPaths.AppDataLocation,
            ),
        ).filePath(__network__)

        # Initialize settings with a custom location
        self.config_file_path = QDir(self.base_path).filePath(
            os.path.join(APP_DIR, f'{app_name}-{__network__}.ini'),
        )
        self.settings = QSettings(self.config_file_path, QSettings.IniFormat)

    def set_value(self, key, value):
        """
        Store a value in the settings.

        Args:
            key (str): The key to store the value under.
            value: The value to store.
        """
        self.settings.setValue(key, value)

    def get_value(self, key, value_type=None):
        """
        Retrieve a value from the settings.

        Args:
            key (str): The key to retrieve the value for.
            value_type (type, optional): The type to convert the value to.
                                         Defaults to None.

        Returns:
            The value associated with the key, or None if conversion fails.
        """
        value = self.settings.value(key)
        if value_type and value is not None:
            try:
                return value_type(value)
            except (TypeError, ValueError):
                return None
        return value

    def remove_key(self, key):
        """
        Remove a key-value pair from the settings.

        Args:
            key (str): The key to remove.
        """
        self.settings.remove(key)

    def clear_settings(self):
        """Clear all settings."""
        self.settings.clear()

    def all_keys(self):
        """
        Get all keys in the settings.

        Returns:
            list: A list of all keys in the settings.
        """
        return self.settings.allKeys()

    def get_path(self):
        """
        Get the base path for application data.

        Returns:
            str: The base path.
        """
        return self.base_path

    def create_folder(self, folder_name):
        """
        Create a folder in the network-specific directory.

        Args:
            folder_name (str): The name of the folder to create.

        Returns:
            str: The full path to the created folder.
        """
        print('Base path', self.base_path)
        folder_path = QDir(self.base_path).filePath(folder_name)
        QDir().mkpath(folder_path)
        print('after', folder_path)
        return folder_path


# Create a singleton instance of LocalStore
local_store = LocalStore(APP_NAME, ORGANIZATION_DOMAIN)
