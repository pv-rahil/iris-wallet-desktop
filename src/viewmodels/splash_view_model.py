"""This module contains the SplashViewModel class, which represents the view model
for splash page.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication

import src.flavour as bitcoin_network
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import WalletRequestModel
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_NATIVE_AUTHENTICATION
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.keyring_storage import get_value
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.render_timer import RenderTimer
from src.utils.wallet_credential_encryption import mnemonic_store
from src.utils.worker import ThreadManager
from src.views.components.error_report_dialog_box import ErrorReportDialog
from src.views.components.toast import ToastManager


class SplashViewModel(QObject, ThreadManager):
    """This class represents splash page"""

    accept_button_clicked = Signal(str)  # Signal to update in the view
    decline_button_clicked = Signal(str)
    splash_screen_message = Signal(str)
    sync_chain_info_label = Signal(bool)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.render_timer = RenderTimer(task_name='SplashScreenWidget')
        self.error_dialog_box = None

    def on_success(self, response):
        """Callback after successful of native login authentication"""
        if response:
            self.handle_application_open()
        else:
            ToastManager.error(
                description=ERROR_NATIVE_AUTHENTICATION,
            )

    def on_error(self, error: Exception):
        """
        Callback after unsuccessful of native login authentication.

        Args:
            exc (Exception): The exception that was raised.
        """
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)
        QApplication.instance().exit()

    def is_login_authentication_enabled(self):
        """Check login authentication enabled"""
        try:
            if SettingRepository.native_login_enabled().is_enabled:
                self.splash_screen_message.emit(
                    'Please authenticate the application..',
                )
            self.run_in_thread(
                SettingRepository.native_authentication,
                {
                    'args': [NativeAuthType.LOGGING_TO_APP],
                    'callback': self.on_success,
                    'error_callback': self.on_error,
                },
            )
        except CommonException as exc:
            ToastManager.error(
                description=exc.message,
            )
        except Exception:
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def on_success_of_unlock_api(self):
        """On success of unlock api it is forward the user to main page"""
        self.render_timer.stop()
        self._page_navigation.fungibles_asset_page()

    def on_error_of_unlock_api(self, error: Exception):
        """Handle error of unlock API."""
        self.error_dialog_box = ErrorReportDialog(initiated_from_splash=True)
        error_message = error.message if isinstance(
            error, CommonException,
        ) else None
        # else ERROR_SOMETHING_WENT_WRONG_WHILE_UNLOCKING_LN_ON_SPLASH

        ToastManager.error(
            description=error_message,
        )

        # if error_message == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'already_unlocked', None):
        #     # Node is already unlocked, treat it as a success
        #     self.on_success_of_unlock_api()
        #     return

        # if error_message == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'not_initialized', None):
        #     self.render_timer.stop()
        #     self._page_navigation.term_and_condition_page()
        #     return

        # if error_message is ERROR_REQUEST_TIMEOUT:
        #     MessageBox('critical', message_text=ERROR_CONNECTION_FAILED_WITH_LN)
        #     QApplication.instance().exit()

        if error_message == ERROR_PASSWORD_INCORRECT:
            PageNavigationEventManager.get_instance().enter_wallet_password_page_signal.emit()
            return

        # if error_message == ERROR_NODE_WALLET_NOT_INITIALIZED:
        #     PageNavigationEventManager.get_instance().set_wallet_password_page_signal.emit()
        #     return

        # Log the error and display a toast message
        logger.error(
            'Error while unlocking wallet on splash page: %s, Message: %s',
            type(error).__name__, str(error),
        )
        # if not self.is_from_retry and not self.is_error_handled:
        #     self.is_error_handled = True
        #     self.error_dialog_box.exec()
        #     return

        # self.is_from_retry = False

    def handle_application_open(self):
        """This method handle application start"""
        try:
            keyring_status = SettingRepository.get_keyring_status()
            network: NetworkEnumModel = SettingRepository.get_wallet_network()
            wallet_password: str = get_value(
                WALLET_PASSWORD_KEY, network.value,
            )
            if keyring_status is True or wallet_password is None:
                self._page_navigation.enter_wallet_password_page()
            else:
                decrypted_mnemonic = mnemonic_store.decrypt(
                    password=wallet_password, path=app_paths.mnemonic_file_path,
                )
                self.splash_screen_message.emit(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'wait_for_node_to_unlock', None,
                    ),
                )
                self.sync_chain_info_label.emit(True)
                network = get_bitcoin_network_from_enum(
                    bitcoin_network.__network__,
                )
                account_xpub = local_store.get_value(ACCOUNT_XPUB)
                wallet = WalletRequestModel(
                    data_dir=app_paths.app_path, bitcoin_network=network, account_xpub=account_xpub, mnemonic=decrypted_mnemonic,
                )
                self.run_in_thread(
                    CommonOperationRepository.unlock, {
                        'args': [wallet],
                        'callback': self.on_success_of_unlock_api,
                        'error_callback': self.on_error_of_unlock_api,
                    },
                )
        except CommonException as error:
            logger.error(
                'Exception occurred at handle_application_open: %s, Message: %s',
                type(error).__name__, str(error),
            )
            ToastManager.error(
                description=error.message,
            )
        except Exception as error:
            logger.error(
                'Exception occurred at handle_application_open: %s, Message: %s',
                type(error).__name__, str(error),
            )
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )
