"""This module is view model for backup"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.setting_repository import SettingRepository
from src.data.service.backup_service import BackupService
from src.model.enums.enums_model import ToastPreset
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.error_message import ERROR_BACKUP_FAILED
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.handle_exception import CommonException
from src.utils.info_message import INFO_BACKUP_COMPLETED
from src.utils.info_message import INFO_BACKUP_COMPLETED_KEYRING_LOCKED
from src.utils.keyring_storage import get_value
from src.utils.logging import logger
from src.utils.wallet_credential_encryption import mnemonic_store
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class BackupViewModel(QObject, ThreadManager):
    """
    ViewModel class handling backup operations with asynchronous handling of
    API calls and UI signals.

    Attributes:
        is_loading (Signal): Signal emitted to indicate loading state changes.
        message (Signal): Signal emitted to display toast messages to the user.
        _page_navigation: Object managing navigation between pages.

    Signals:
        is_loading(bool): Signal emitted to indicate loading state changes.
        message(ToastPreset, str): Signal emitted to display toast messages to the user.
    """
    is_loading = Signal(bool)
    message = Signal(ToastPreset, str)

    def __init__(self, page_navigation) -> None:
        """
        Initialize the BackupViewModel with the given page navigation.

        Args:
            page_navigation: Object managing navigation between pages.
        """
        super().__init__()
        self.password_validation = None
        self._page_navigation = page_navigation

    def on_error(self, error: CommonException):
        """This method is called on error from backup api call"""
        self.is_loading.emit(False)
        ToastManager.error(description=error.message)

    def _handle_error(self, error_message: str, exc: Exception) -> None:
        """Centralized method to handle logging and displaying errors."""
        self.is_loading.emit(False)
        logger.error(f"{error_message}: %s", exc)
        ToastManager.error(description=ERROR_SOMETHING_WENT_WRONG)

    def on_success(self, response: bool) -> None:
        """
        Handle actions upon successful completion of the backup API call.

        Args:
            response (bool): Flag indicating success or failure of the backup operation.
        """
        self.is_loading.emit(False)
        if response:
            ToastManager.info(description=INFO_BACKUP_COMPLETED)
        else:
            ToastManager.error(description=ERROR_BACKUP_FAILED)

    def on_success_from_backup_page(self) -> None:
        """Callback function call when backup triggered from backup UI page and keyring is not accessible."""
        ToastManager.success(description=INFO_BACKUP_COMPLETED_KEYRING_LOCKED)
        self._page_navigation.enter_wallet_password_page()

    def run_backup_service_thread(self, mnemonic: str, password: str, is_keyring_accessible: bool = True) -> None:
        """Run backup service in thread."""
        try:
            self.is_loading.emit(True)
            self.run_in_thread(
                BackupService.backup, {
                    'args': [mnemonic, password],
                    'callback': self.on_success if is_keyring_accessible else self.on_success_from_backup_page,
                    'error_callback': self.on_error,
                },
            )
        except (ConnectionError, FileNotFoundError, CommonException) as exc:
            self._handle_error('Backup service error', exc)
        except Exception as exc:
            self._handle_error('Unexpected error', exc)

    def backup_when_keyring_unaccessible(self, mnemonic: str, password: str) -> None:
        """This method is called when keyring store is not accessible."""
        self.run_backup_service_thread(
            mnemonic=mnemonic, password=password, is_keyring_accessible=False,
        )

    def backup(self) -> None:
        """
        Initiate the backup process, managing loading state and asynchronous
        execution using the BackupService.
        """
        network = SettingRepository.get_wallet_network()
        password = get_value(
            key=WALLET_PASSWORD_KEY, network=network.value,
        )
        mnemonic = mnemonic_store.decrypted_mnemonic
        if mnemonic is None:
            raise ValueError('Mnemonic is not available for backup.')

        self.run_backup_service_thread(
            mnemonic=mnemonic, password=password,
        )
