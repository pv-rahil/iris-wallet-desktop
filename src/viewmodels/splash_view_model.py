"""This module contains the SplashViewModel class, which represents the view model
for splash page.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import QProcess
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication

from src.data.repository.wallet_holder import WalletHolder
from src.data.service.common_operation_service import CommonOperationService
import src.flavour as bitcoin_network
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import NodeInfoResponseModel, WalletRequestModel
from src.model.common_operation_model import UnlockRequestModel
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import WalletType
from src.utils.constant import COMPATIBLE_RLN_NODE_COMMITS
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import NODE_PUB_KEY
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_CONNECTION_FAILED_WITH_LN
from src.utils.error_message import ERROR_NATIVE_AUTHENTICATION
from src.utils.error_message import ERROR_NODE_INCOMPATIBILITY
from src.utils.error_message import ERROR_NODE_WALLET_NOT_INITIALIZED
from src.utils.error_message import ERROR_PASSWORD_INCORRECT
from src.utils.error_message import ERROR_REQUEST_TIMEOUT
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG_WHILE_UNLOCKING_LN_ON_SPLASH
from src.utils.helpers import get_bitcoin_config
from src.utils.info_message import INFO_RESTARTING_RLN_NODE
from src.utils.info_message import INFO_STARTING_RLN_NODE
from src.utils.info_message import INFO_WALLET_RESET
from src.utils.keyring_storage import get_value
from src.utils.ln_node_manage import LnNodeServerManager
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager
from src.utils.render_timer import RenderTimer
from src.utils.reset_app import delete_app_data
from src.utils.worker import ThreadManager
from src.viewmodels.wallet_and_transfer_selection_viewmodel import WalletTransferSelectionViewModel
from src.views.components.error_report_dialog_box import ErrorReportDialog
from src.views.components.message_box import MessageBox
from src.views.components.node_crash_dialog import CrashDialogBox
from src.views.components.node_incompatibility import NodeIncompatibilityDialog
from src.views.components.toast import ToastManager
from src.utils.build_app_path import app_paths

class SplashViewModel(QObject, ThreadManager):
    """This class represents splash page"""

    accept_button_clicked = Signal(str)  # Signal to update in the view
    decline_button_clicked = Signal(str)
    splash_screen_message = Signal(str)
    sync_chain_info_label = Signal(bool)
    show_main_window_loader = Signal(bool, str)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.wallet_transfer_selection_view_model: WalletTransferSelectionViewModel = None
        self.render_timer = RenderTimer(task_name='SplashScreenWidget')
        self.is_from_retry: bool = False
        self.is_error_handled = False
        self.ln_node_manager = LnNodeServerManager.get_instance()
        self.ln_node_manager.process.finished.connect(self.on_node_failure)
        self.error_dialog_box = None

    def load_wallet_transfer_selection_view_model(self, view_model: WalletTransferSelectionViewModel):
        """
        Loads the WalletTransferSelectionViewModel into the splash view.

        This method assigns the provided WalletTransferSelectionViewModel instance to the splash view model.
        preventing duplicate instances and maintaining consistency across the application.

        Args:
            view_model (WalletTransferSelectionViewModel): The singleton instance of WalletTransferSelectionViewModel.
        """
        self.wallet_transfer_selection_view_model = view_model

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
        node_pub_key: NodeInfoResponseModel = CommonOperationRepository.node_info()
        if node_pub_key is not None:
            local_store.set_value(NODE_PUB_KEY, node_pub_key.pubkey)
        self.show_main_window_loader.emit(False, INFO_RESTARTING_RLN_NODE)

    def on_error_of_unlock_api(self, error: Exception):
        """Handle error of unlock API."""
        self.error_dialog_box = ErrorReportDialog(initiated_from_splash=True)
        error_message = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG_WHILE_UNLOCKING_LN_ON_SPLASH

        ToastManager.error(
            description=error_message,
        )

        if error_message == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'already_unlocked', None):
            # Node is already unlocked, treat it as a success
            self.on_success_of_unlock_api()
            return

        if error_message == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'not_initialized', None):
            self.render_timer.stop()
            self._page_navigation.term_and_condition_page()
            return

        if error_message is ERROR_REQUEST_TIMEOUT:
            MessageBox('critical', message_text=ERROR_CONNECTION_FAILED_WITH_LN)
            QApplication.instance().exit()

        if error_message == ERROR_CONNECTION_FAILED_WITH_LN and not self.is_error_handled:
            if self.ln_node_manager.process.state() == QProcess.ProcessState.NotRunning:
                self.restart_ln_node_after_crash()
            else:
                self.is_error_handled = True
                self.error_dialog_box.exec()
            return

        if error_message == ERROR_PASSWORD_INCORRECT:
            PageNavigationEventManager.get_instance().enter_wallet_password_page_signal.emit()
            return

        if error_message == ERROR_NODE_WALLET_NOT_INITIALIZED:
            PageNavigationEventManager.get_instance().set_wallet_password_page_signal.emit()
            return

        # Log the error and display a toast message
        logger.error(
            'Error while unlocking node on splash page: %s, Message: %s',
            type(error).__name__, str(error),
        )
        if not self.is_from_retry and not self.is_error_handled:
            self.is_error_handled = True
            self.error_dialog_box.exec()
            return

        self.show_main_window_loader.emit(False, INFO_RESTARTING_RLN_NODE)

        self.is_from_retry = False

    def handle_application_open(self):
        """This method handle application start"""
        try:
            print(1)
            self.show_main_window_loader.emit(True, INFO_RESTARTING_RLN_NODE)
            keyring_status = SettingRepository.get_keyring_status()
            if keyring_status is True:
                self._page_navigation.enter_wallet_password_page()
            else:

                self.splash_screen_message.emit(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'wait_for_node_to_unlock', None,
                    ),
                )
                self.sync_chain_info_label.emit(True)
                init = WalletHolder.get_init_response()
                network = CommonOperationService.get_bitcoin_network_from_enum(bitcoin_network.__network__)
                print('----------------->',network)
                wallet = WalletRequestModel(data_dir=app_paths.app_path,bitcoin_network=network,pubkey=init.account_xpub,mnemonic=init.mnemonic)
                self.run_in_thread(
                    CommonOperationRepository.unlock, {
                        'args': wallet,
                        'callback': self.on_success_of_unlock_api,
                        'error_callback': self.on_error_of_unlock_api,
                    },
                )
        except CommonException as error:
            self.show_main_window_loader.emit(False, INFO_RESTARTING_RLN_NODE)
            logger.error(
                'Exception occurred at handle_application_open: %s, Message: %s',
                type(error).__name__, str(error),
            )
            ToastManager.error(
                description=error.message,
            )
        except Exception as error:
            self.show_main_window_loader.emit(False, INFO_RESTARTING_RLN_NODE)
            logger.error(
                'Exception occurred at handle_application_open: %s, Message: %s',
                type(error).__name__, str(error),
            )
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def handle_node_incompatibility(self):
        """Handles the case when the node commit ID is incompatible."""
        node_incompatible = NodeIncompatibilityDialog()
        node_incompatible.show_node_incompatibility_dialog()
        clicked_button = node_incompatible.node_incompatibility_dialog.clickedButton()

        if clicked_button == node_incompatible.close_button:
            QApplication.instance().exit()
        elif clicked_button == node_incompatible.delete_app_data_button:
            node_incompatible.show_confirmation_dialog()
            if node_incompatible.confirmation_dialog.clickedButton() == node_incompatible.confirm_delete_button:
                self.on_delete_app_data()
            elif node_incompatible.confirmation_dialog.clickedButton() == node_incompatible.cancel:
                self.handle_application_open()

    def restart_ln_node_after_crash(self):
        """
        Attempts to restart the RGB Lightning Node after it crashes, exits, or is killed.
        If the user chooses to retry, the application will attempt to restart the node.
        Otherwise, the application will exit.
        """
        if not self.is_error_handled:
            self.is_error_handled = True

            logger.error(
                'RLN node process was KILLED or CRASHED!',
            )

            crash_dialog_box = CrashDialogBox()

            if crash_dialog_box.message_box.clickedButton() == crash_dialog_box.retry_button:
                self.is_from_retry = True

                logger.info(
                    'Restarting RGB Lightning Node',
                )

                self.handle_application_open()
            else:
                QApplication.instance().exit()

    def on_node_failure(self, exit_code, exit_status):
        """This method handles crash exits of RGB LN Node"""
        if exit_status == QProcess.ExitStatus.CrashExit:
            logger.error(
                'RLN node process was KILLED or CRASHED! Exit Code: %s', exit_code,
            )
            self.restart_ln_node_after_crash()

    def on_delete_app_data(self):
        """This function deletes the wallet data after user confirms when using an invalid RGB Lightning node"""
        basepath = local_store.get_path()
        network_type = SettingRepository.get_wallet_network()
        delete_app_data(basepath, network=network_type.value)
        logger.info(INFO_WALLET_RESET)
        self._page_navigation.welcome_page()
        self.show_main_window_loader.emit(
            True, INFO_STARTING_RLN_NODE,
        )
        self.wallet_transfer_selection_view_model.start_node_for_embedded_option()

    def is_rln_commit_valid(self) -> bool:
        """Checks if the stored commit ID is in the list of compatible commit IDs."""
        return SettingRepository.get_rln_node_commit_id() in COMPATIBLE_RLN_NODE_COMMITS
