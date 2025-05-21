""""This module defines a repository class for managing settings related to wallet initialization.
"""
from __future__ import annotations

import os
import subprocess
import sys

import src.flavour as bitcoin_network
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.setting_model import IsBackupConfiguredModel
from src.model.setting_model import IsHideExhaustedAssetEnabled
from src.model.setting_model import IsNativeLoginIntoAppEnabled
from src.model.setting_model import IsShowHiddenAssetEnabled
from src.model.setting_model import IsWalletInitialized
from src.model.setting_model import NativeAuthenticationStatus
from src.model.setting_model import SetWalletInitialized
from src.utils.constant import IS_NATIVE_AUTHENTICATION_ENABLED
from src.utils.constant import NATIVE_LOGIN_ENABLED
from src.utils.constant import RGB_LIB_VERSION_KEY
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_KEYRING_STATUS
from src.utils.handle_exception import handle_exceptions
from src.utils.keyring_storage import get_value
from src.utils.keyring_storage import set_value
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.native_windows_auth import WindowNativeAuthentication


class SettingRepository:
    """
    A repository class for handling wallet initialization settings.
    """
    @staticmethod
    def get_wallet_network() -> NetworkEnumModel:
        """
        Get the network type for the wallet.
        """
        return NetworkEnumModel(bitcoin_network.__network__)

    @staticmethod
    def is_wallet_initialized() -> IsWalletInitialized:
        """
        Checks if the wallet is initialized.

        Returns:
            IsWalletInitialized: A model indicating whether the wallet is initialized.
        """
        try:
            wallet_status = local_store.get_value('isWalletCreated')
            if wallet_status is None:
                wallet_status = False
            return IsWalletInitialized(is_wallet_initialized=wallet_status)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_wallet_initialized() -> SetWalletInitialized:
        """
        Sets the wallet as initialized.

        Returns:
            SetWalletInitialized: A model indicating the status of the operation.
        """
        try:
            local_store.set_value('isWalletCreated', True)
            # Verify the setting was applied
            if local_store.get_value('isWalletCreated', value_type=bool):
                return SetWalletInitialized(status=True)
            return SetWalletInitialized(status=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def is_backup_configured() -> IsBackupConfiguredModel:
        """
        Checks if the backup is configured.

        Returns:
            IsBackupConfiguredModel: A model indicating whether the backup is configured.
        """
        try:
            backup_status = local_store.get_value('isBackupConfigured')
            if backup_status is None:
                backup_status = False
            return IsBackupConfiguredModel(is_backup_configured=backup_status)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_backup_configured(status: bool) -> IsBackupConfiguredModel:
        """
        Sets the backup configuration status.

        Args:
            status (bool): The status to set.

        Returns:
            IsBackupConfiguredModel: A model indicating the status of the operation.
        """
        try:
            local_store.set_value('isBackupConfigured', status)
            # Verify the setting was applied
            if local_store.get_value('isBackupConfigured', value_type=bool):
                return IsBackupConfiguredModel(is_backup_configured=True)
            return IsBackupConfiguredModel(is_backup_configured=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def unset_wallet_initialized():
        """
        Unsets the wallet as initialized.
        """
        try:
            local_store.set_value('isWalletCreated', False)
            return True
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_keyring_status(status: bool):
        """
        set keyring status mean keyring accessible or not
        """
        try:
            local_store.set_value('isKeyringDisable', status)
            stored_keyring_status = local_store.get_value('isKeyringDisable')
            if stored_keyring_status is None or stored_keyring_status == '' or stored_keyring_status != status:
                raise CommonException(ERROR_KEYRING_STATUS)
        except Exception as exc:
            handle_exceptions(exc=exc)

    @staticmethod
    def get_keyring_status() -> bool:
        """Give status of keyring accessible or not"""
        stored_keyring_status = local_store.get_value('isKeyringDisable')
        if stored_keyring_status is None or stored_keyring_status == '':
            return False
        if isinstance(stored_keyring_status, str):
            stored_keyring_status = SettingRepository.str_to_bool(
                stored_keyring_status,
            )
        return stored_keyring_status

    @staticmethod
    def get_native_authentication_status() -> NativeAuthenticationStatus:
        """
        Checks native authentication status.

        Returns:
            NativeAuthenticationStatus: A model indicating whether native authentication is enabled.
        """
        try:
            status: bool = SettingRepository.get_keyring_status()
            native_status: str = 'false'
            if status is False:
                native_status = get_value(
                    IS_NATIVE_AUTHENTICATION_ENABLED,
                )
            native_status_casted: bool = SettingRepository.str_to_bool(
                native_status,
            )
            return NativeAuthenticationStatus(is_enabled=native_status_casted)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def set_native_authentication_status(status: bool) -> bool:
        """
        Sets native authentication status.

        Args:
            status (bool): The status to set.

        Returns:
            NativeAuthenticationStatus: A model indicating the status of the operation.
        """
        try:
            status = set_value(
                IS_NATIVE_AUTHENTICATION_ENABLED,
                SettingRepository.bool_to_str(status),
            )
            return status
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def native_login_enabled() -> IsNativeLoginIntoAppEnabled:
        """
        Checks native authentication status for logging into the app.

        Returns:
            IsNativeLoginIntoAppEnabled: A model indicating whether native login is enabled.
        """
        try:
            # It is get status from keyring not local storage
            status: bool = SettingRepository.get_keyring_status()
            is_enabled: str = 'false'
            if status is False:
                is_enabled = get_value(NATIVE_LOGIN_ENABLED)
            is_enabled_casted: bool = SettingRepository.str_to_bool(is_enabled)
            return IsNativeLoginIntoAppEnabled(is_enabled=is_enabled_casted)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def enable_logging_native_authentication(status: bool) -> bool:
        """
        Sets native authentication status for logging into the app.

        Args:
            status (bool): The status to set.

        Returns:
            IsNativeLoginIntoAppEnabled: A model indicating the status of the operation.
        """
        try:
            # It is store status in keyring to make secure
            status = set_value(
                NATIVE_LOGIN_ENABLED,
                SettingRepository.bool_to_str(status),
            )
            return status
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def is_show_hidden_assets_enabled() -> IsShowHiddenAssetEnabled:
        """
        Checks if hidden assets are enabled.

        Returns:
            IsShowHiddenAssetEnabled: A model indicating whether hidden assets are enabled.
        """
        try:
            is_enabled = local_store.get_value('isShowHiddenAssetEnable')
            if is_enabled is None:
                is_enabled = False
            return IsShowHiddenAssetEnabled(is_enabled=is_enabled)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def enable_show_hidden_asset(status: bool) -> IsShowHiddenAssetEnabled:
        """
        Enables or disables hidden assets.

        Args:
            status (bool): The status to set.

        Returns:
            IsShowHiddenAssetEnabled: A model indicating the status of the operation.
        """
        try:
            local_store.set_value('isShowHiddenAssetEnable', status)
            # Verify the setting was applied
            if local_store.get_value('isShowHiddenAssetEnable', value_type=bool):
                return IsShowHiddenAssetEnabled(is_enabled=True)
            return IsShowHiddenAssetEnabled(is_enabled=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def is_exhausted_asset_enabled() -> IsHideExhaustedAssetEnabled:
        """
        Checks if exhausted assets are enabled.

        Returns:
            IsHideExhaustedAssetEnabled: A model indicating whether exhausted assets are enabled.
        """
        try:
            is_enabled = local_store.get_value('isExhaustedAssetEnable')
            if is_enabled is None:
                is_enabled = False
            return IsHideExhaustedAssetEnabled(is_enabled=is_enabled)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def enable_exhausted_asset(status: bool) -> IsHideExhaustedAssetEnabled:
        """
        Enables or disables exhausted assets.

        Args:
            status (bool): The status to set.

        Returns:
            IsHideExhaustedAssetEnabled: A model indicating the status of the operation.
        """
        try:
            local_store.set_value('isExhaustedAssetEnable', status)
            # Verify the setting was applied
            if local_store.get_value('isShowHiddenAssetEnable', value_type=bool):
                return IsHideExhaustedAssetEnabled(is_enabled=True)
            return IsHideExhaustedAssetEnabled(is_enabled=False)
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def native_authentication(auth_type: NativeAuthType, msg='Please verify your identity to proceed') -> bool:
        """
        Perform native authentication based on the given authentication type and platform.

        Args:
            auth_type (NativeAuthType): The type of native authentication to perform.

        Returns:
            bool: True if authentication is successful or not required, False otherwise.

        Raises:
            CommonException: If the operating system is unsupported or authentication fails.
        """
        try:
            authentication_status: bool = False
            if NativeAuthType.LOGGING_TO_APP.value == auth_type.value:
                is_enabled_loggin: IsNativeLoginIntoAppEnabled = SettingRepository.native_login_enabled()
                if not is_enabled_loggin.is_enabled:
                    return True

            if NativeAuthType.MAJOR_OPERATION.value == auth_type.value:
                is_enabled_auth: NativeAuthenticationStatus = SettingRepository.get_native_authentication_status()
                if not is_enabled_auth.is_enabled:
                    return True

            if sys.platform == 'linux':
                authentication_status = SettingRepository._linux_native_authentication()
            elif sys.platform == 'darwin':
                authentication_status = SettingRepository._macos_native_authentication()
            elif sys.platform in ('win32', 'cygwin'):
                win_auth = WindowNativeAuthentication(msg)
                authentication_status = win_auth.start_windows_native_auth()
            else:
                raise CommonException('Unsupported operating system.')

            if not authentication_status:
                raise CommonException('Authentication failed or canceled.')
            return authentication_status
        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def _linux_native_authentication() -> bool:
        """
        Perform native authentication on Linux using 'pkexec'.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        try:
            subprocess.run(['pkexec', 'true'], check=True)
            logger.info('User native authenticated successfully.')
            return True
        except subprocess.CalledProcessError as exc:
            logger.error(
                'Native Authentication failed on Linux: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return False

    @staticmethod
    def _macos_native_authentication() -> bool:
        """
        Perform native authentication on macOS using AppleScript.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        try:
            applescript = '''
            tell application "System Events"
                display dialog "Authentication required" default answer "" with hidden answer
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript], check=True)
            logger.info('User native authenticated successfully.')
            return True
        except subprocess.CalledProcessError as exc:
            logger.error(
                'Native Authentication failed on macos: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return False

    @staticmethod
    def _windows_native_authentication() -> bool:
        """
        Perform native authentication on Windows (currently under development).

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        try:
            path_exe_of_windows_native: str = SettingRepository._get_path_windows_native_executable()
            response = subprocess.run(
                [path_exe_of_windows_native], check=True, capture_output=True,
            )
            stdout = response.stdout.decode('utf-8').strip()

            if 'User not verified.' in stdout:
                return False
            if 'User  verified.' in stdout:
                return True
            return False
        except subprocess.CalledProcessError as exc:
            logger.error(
                'Native Authentication failed on windows: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return False

    @staticmethod
    def str_to_bool(value: str | None) -> bool:
        """
        Convert a string representation of a boolean to an actual boolean value.

        Args:
            s (str | None): The string to convert.

        Returns:
            bool: The corresponding boolean value.

        Raises:
            ValueError: If the string cannot be converted to a boolean.
        """
        if value is None:
            return False
        if value.lower() in ['true', '1', 't', 'yes', 'y']:
            return True
        if value.lower() in ['false', '0', 'f', 'no', 'n']:
            return False
        raise ValueError('Cannot convert string to boolean: invalid input')

    @staticmethod
    def bool_to_str(value: bool) -> str:
        """
        Convert a boolean value to its string representation.

        Args:
            s (bool): The boolean value to convert.

        Returns:
            str: The string representation of the boolean value.
        """
        return 'true' if value else 'false'

    @staticmethod
    def _get_path_windows_native_executable() -> str:
        """Return frozen path of window executable and normal execution path of windows_native_executable"""
        if getattr(sys, 'frozen', False):
            base_path = getattr(
                sys,
                '_MEIPASS',
                os.path.dirname(
                    os.path.abspath(__file__),
                ),
            )
            return os.path.join(base_path, 'binary', 'native_auth_windows.exe')
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../', 'binary', 'native_auth_windows.exe'))

    @staticmethod
    def get_config_value(key: str, value, value_type=None):
        """
        Retrieve a configuration value from the local store. If the value does not exist, set it with the provided default value.

        Args:
            key (str): The key for the configuration value in the local store.
            value (Any, optional): The value to be set if the key does not exist. Defaults to None.
            value_type (Type, optional): The expected data type of the value. Defaults to None.

        Returns:
            Any: The current value associated with the key from the local store, or the newly set value if the key did not exist.

        Raises:
            Exception: If an error occurs during the retrieval or setting process.
        """
        try:
            current_value = local_store.get_value(key, value_type=value_type)
            if current_value is None and value is not None:
                local_store.set_value(key, value)
                if local_store.get_value(key) == value:
                    return value
                logger.error('Failed to set %s in local_store.', key)
                return None
            return current_value
        except Exception as exe:
            return handle_exceptions(exe)

    @staticmethod
    def get_rgb_lib_version():
        """This method gets the version of the rgb lib"""
        try:
            rgb_lib_version = local_store.get_value(RGB_LIB_VERSION_KEY)
            return rgb_lib_version
        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def set_rgb_lib_version(version: str):
        """This method sets the version of the rgb lib in the wallet's .ini file"""
        try:
            local_store.set_value(RGB_LIB_VERSION_KEY, version)
        except Exception as exc:
            handle_exceptions(exc)
