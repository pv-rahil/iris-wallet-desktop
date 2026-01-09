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
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.common_operation_service import CommonOperationService
from src.model.common_operation_model import USBDrive
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import PING_DNS_ADDRESS_FOR_NETWORK_CHECK
from src.utils.constant import PING_DNS_SERVER_CALL_INTERVAL
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.logging import logger
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
    sync_process_ended = Signal(str)
    # Multisig: emits list of pending operations from bridge
    pending_operations_ready = Signal(list)

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

    def _is_multisig(self) -> bool:
        """Check if current wallet is multisig."""
        return SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET

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
                'callback': self.handle_sync_completed,
                'error_callback': self.handle_sync_error,
            },
        )

    def handle_sync_completed(self, direction: str, retry: bool = False):
        """Handle completion of sync process."""
        if direction == 'from_usb':
            self.run_in_thread(
                CommonOperationService.enter_wallet_password,
                {
                    'args': [self.password],
                    'callback': lambda *_: self.handle_sync_success(direction, retry),
                    'error_callback': self.handle_sync_error,
                },
            )
        elif direction == 'to_usb':
            self.sync_process_ended.emit('to_usb')
            ToastManager.success(
                description=QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_success',
                ),
            )
        elif direction == 'no_sync':
            self.sync_process_ended.emit('no_sync')
            ToastManager.success(
                description=QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_no_sync_needed',
                ),
            )

    def handle_sync_error(self, error: Exception):
        """Handle sync error."""
        self.sync_process_ended.emit('error')
        ToastManager.error(description=str(error))

    def handle_sync_success(self, direction: str, retry: bool):
        """Handle sync success after password entry."""
        try:
            if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
                network = get_bitcoin_network_from_enum(
                    SettingRepository.get_wallet_network(),
                )
                indexer_url = get_bitcoin_config(network, '').indexer_url
                colored_wallet.online_wallet = colored_wallet.wallet.go_online(
                    False, indexer_url,
                )
            self.sync_process_ended.emit('from_usb')
            if not retry:
                ToastManager.success(
                    description=QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_from_success',
                    ),
                )
        except RgbLibError.Inconsistency:
            self.usb_sync_manager.restore_local_folder_from_backup()
            self.handle_sync_completed(direction, retry=True)
            self.sync_process_ended.emit()
            ToastManager.error(
                description=QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'usb_sync_inconsistency_restored',
                ),
            )
        except Exception as exc:
            logger.error('Failed to sync wallet: %s', exc)
            ToastManager.error(description=str(exc))

    # ========== Multisig Bridge Sync ==========

    def sync_multisig_bridge(self):
        """Sync with multisig bridge to get pending operations for review."""
        if not self._is_multisig():
            return
        self.run_in_thread(
            RgbRepository.sync_with_bridge,
            {
                'args': [],
                'callback': self.on_multisig_sync_done,
                'error_callback': self.on_multisig_sync_error,
            },
        )

    def on_multisig_sync_done(self, operation_info):
        """Handle successful bridge sync. Emits pending operations list."""
        # operation_info is a single OperationInfo object when there's a pending operation
        # It has fields: operation_idx, initiator_xpub, operation
        pending_ops = []
        if operation_info is not None:
            # It's a single OperationInfo, wrap it in a list
            pending_ops = [operation_info]
            print('operation found')
        else:
            print('no operation found')
        self.pending_operations_ready.emit(pending_ops)

    def on_multisig_sync_error(self, error: Exception):
        """Handle bridge sync error."""
        logger.error('Failed to sync with multisig bridge: %s', error)
        # Emit empty list on error
        self.pending_operations_ready.emit([])

