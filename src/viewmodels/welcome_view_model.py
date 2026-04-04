# pylint: disable=too-few-public-methods
"""This module contains the welcomeViewModel class, which represents the view model
for the term and conditions page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import KeyringDialogModel
from src.model.common_operation_model import USBDrive
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.utils.build_app_path import app_paths
from src.utils.constant import CURRENT_RGB_LIB_VERSION
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_RESTORE_COMPLETED
from src.utils.keyring_storage import get_value
from src.utils.keyring_storage import set_value
from src.utils.logging import logger
from src.utils.usb_sync_manager import USBSyncManager
from src.utils.worker import ThreadManager
from src.viewmodels.viewmodel_helpers import restore_multisig_config_from_file
from src.views.components.keyring_error_dialog import KeyringErrorDialog
from src.views.components.toast import ToastManager


class WelcomeViewModel(QObject, ThreadManager):
    """This class represents the activities of the welcome page."""

    create_button_clicked = Signal(bool)  # Signal to update in the view
    restore_button_clicked = Signal()
    restore_process_success = Signal()
    restore_process_failed = Signal()

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.usb_sync_manager = USBSyncManager()

    def on_create_click(self):
        """This method handles the wallet creation process."""
        network = SettingRepository.get_wallet_network()
        password = get_value(
            WALLET_PASSWORD_KEY, network.value,
        )
        is_multisig = (
            SettingRepository.get_wallet_signature_type(
            ) == WalletSignatureType.MULTI_SIG_WALLET
        )

        if is_multisig:
            self.create_button_clicked.emit(True)
            self.run_in_thread(
                CommonOperationService.initialize_wallet,
                {
                    'args': [password],
                    'callback': self._on_multisig_wallet_initialized,
                    'error_callback': self._on_multisig_init_error,
                },
            )
        else:
            self._page_navigation.set_wallet_password_page()

    def _on_multisig_wallet_initialized(self):
        """Handle successful multisig wallet initialization."""
        self.create_button_clicked.emit(False)
        SettingRepository.set_wallet_initialized()
        SettingRepository.set_rgb_lib_version(CURRENT_RGB_LIB_VERSION)
        self._page_navigation.fungibles_asset_page()

    def _on_multisig_init_error(self, error: CommonException):
        """Handle multisig wallet initialization error."""
        self.create_button_clicked.emit(False)
        ToastManager.error(error.message)

    def restore_offline_wallet(self, usb_drive: USBDrive, master_fingerprint: str, data: KeyringDialogModel):
        """This method handles the offline wallet restore process."""
        self.restore_button_clicked.emit()
        self.run_in_thread(
            self.usb_sync_manager.sync_from_usb,
            {
                'args': [usb_drive, master_fingerprint, True],
                'callback': lambda: self.handle_sync_completed(data),
                'error_callback': self.handle_sync_error,
            },
        )

    def handle_sync_completed(self, data: KeyringDialogModel):
        """This method handles the restore process completion."""
        if data.password is None:
            return
        network = SettingRepository.get_wallet_network()
        is_set_password: bool = set_value(
            WALLET_PASSWORD_KEY, data.password, network.value,
        )

        if is_set_password:
            # Restore multisig configuration if cosigners file was synced from USB
            cosigners_file_path = app_paths.multisig_cosigners_file_path
            if restore_multisig_config_from_file(cosigners_file_path):
                logger.info('Restored multisig configuration from USB')
            ToastManager.success(INFO_RESTORE_COMPLETED)
            SettingRepository.set_keyring_status(status=False)
            self._page_navigation.enter_wallet_password_page()
        else:
            if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY or SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
                keyring_warning_dialog = KeyringErrorDialog(
                    KeyringDialogModel(
                        xpub_vanilla=data.xpub_vanilla,
                        xpub_colored=data.xpub_colored,
                        master_fingerprint=data.master_fingerprint,
                        password=data.password,
                        navigate_to=self._page_navigation.enter_wallet_password_page,
                    ),
                )
            else:
                keyring_warning_dialog = KeyringErrorDialog(
                    KeyringDialogModel(
                        mnemonic=data.mnemonic,
                        password=data.password,
                        navigate_to=self._page_navigation.enter_wallet_password_page,
                    ),
                )
            keyring_warning_dialog.exec()
        self.restore_process_success.emit()

    def handle_sync_error(self, error):
        """This method handles the restore process error."""
        self.restore_process_failed.emit()
        ToastManager.error(error.message)
