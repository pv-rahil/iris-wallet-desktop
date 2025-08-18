"""View model to handle network connectivity check or other logic for header"""
from __future__ import annotations

import socket

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import QThread
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from rgb_lib import RgbLibError

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import USBDrive
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import PING_DNS_ADDRESS_FOR_NETWORK_CHECK
from src.utils.constant import PING_DNS_SERVER_CALL_INTERVAL
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.local_store import local_store
from src.utils.usb_sync_manager import USBSyncManager
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class NetworkCheckerThread(QThread):
    """Thread to handle network connectivity checking."""
    network_status_signal = Signal(bool)

    def run(self):
        """Run the network check once."""
        is_connected = self.check_internet_conn()
        self.network_status_signal.emit(is_connected)

    def check_internet_conn(self):
        """Check internet connection and return status."""
        try:
            socket.create_connection(
                (PING_DNS_ADDRESS_FOR_NETWORK_CHECK, 53), timeout=3,
            )
            return True
        except OSError:
            return False


class HeaderFrameViewModel(QObject, ThreadManager):
    """Handles network connectivity in the UI."""
    network_status_signal = Signal(bool)
    sync_process_started = Signal()
    sync_process_ended = Signal()

    def __init__(self):
        super().__init__()
        self.network_checker = None
        self.password = None
        self.usb_sync_manager = USBSyncManager()

        # Use QTimer in the main thread for network checking
        self.timer = QTimer(self)
        self.timer.setInterval(PING_DNS_SERVER_CALL_INTERVAL)
        self.timer.timeout.connect(self.start_network_check)

        # Start network checking
        self.timer.start()

    def start_network_check(self):
        """Start a new network check using a separate thread."""
        self.network_checker = NetworkCheckerThread()
        self.network_checker.network_status_signal.connect(
            self.handle_network_status,
        )
        self.network_checker.start()

    def handle_network_status(self, is_connected):
        """Emit network status signal."""
        self.network_status_signal.emit(is_connected)

    def stop_network_checker(self):
        """Stop network checking when no longer needed."""
        self.timer.stop()

    def perform_sync(self, selected_drive: USBDrive, password: str):
        """Perform sync process."""
        self.password = password
        self.sync_process_started.emit()

        self.run_in_thread(
            self.usb_sync_manager.perform_sync,
            {
                'args': [selected_drive],
                'callback': self.on_sync_process_ended,
                'error_callback': self.on_error,
            },
        )

    def on_sync_process_ended(self, direction):
        """Emit sync process ended signal."""
        if direction == 'from_usb':
            self.run_in_thread(
                CommonOperationService.enter_wallet_password,
                {
                    'args': [self.password],
                    'callback': self.on_success,
                    'error_callback': self.on_error,
                },
            )
        elif direction == 'to_usb':
            self.sync_process_ended.emit()
            ToastManager.success(description=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_success'))
        elif direction == 'no_sync':
            self.sync_process_ended.emit()
            ToastManager.success(description=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'No sync needed - data is up to date'))

    def on_error(self, error):
        """Handle sync error."""
        self.sync_process_ended.emit()
        ToastManager.error(description=str(error))

    def on_success(self, response):
        """Handle sync success."""
        try:
            colored_wallet.set_wallet(response)
            network = get_bitcoin_network_from_enum(
                SettingRepository.get_wallet_network(),
            )
            indexer_url = get_bitcoin_config(network, '').indexer_url
            colored_wallet.go_online_again(indexer_url)
            self.sync_process_ended.emit()
            ToastManager.success(description=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_from_success'))
        except RgbLibError.Inconsistency as exc:
            self.usb_sync_manager.restore_local_folder_from_backup()
            self.sync_process_ended.emit()
            ToastManager.error(
                description='Due to inconsistency, wallet data has been restored to the previous state')
