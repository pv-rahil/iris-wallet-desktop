"""View model to handle network connectivity check or other logic for header"""
from __future__ import annotations

import socket

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import QThread
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from rgb_lib import Operation
from rgb_lib import OperationInfo
from rgb_lib import RgbLibError

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.colored_wallet import get_online_wallet
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.data.service.common_operation_service import CommonOperationService
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import PsbtData
from src.model.common_operation_model import USBDrive
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import PING_DNS_ADDRESS_FOR_NETWORK_CHECK
from src.utils.constant import PING_DNS_SERVER_CALL_INTERVAL
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
    # Assuming this signal exists or needs to be added
    is_loading = Signal(bool)
    multisig_pending_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.network_checker = None
        self.password = None
        self.usb_sync_manager = USBSyncManager()
        self._multisig_pending = False

        # Use QTimer in the main thread for network checking
        self.timer = QTimer(self)
        self.timer.setInterval(PING_DNS_SERVER_CALL_INTERVAL)
        self.timer.timeout.connect(self.start_network_check)

        # Start network checking
        self.timer.start()

    @property
    def is_multisig_pending(self) -> bool:
        """Check if multisig wallet has pending operations."""
        return self._multisig_pending

    def _set_multisig_pending(self, pending: bool) -> None:
        """Set multisig pending state."""
        if self._multisig_pending != pending:
            self._multisig_pending = pending
            self.multisig_pending_state_changed.emit(pending)

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
                is_multisig = SettingRepository.get_wallet_signature_type(
                ) == WalletSignatureType.MULTI_SIG_WALLET
                colored_wallet.online_wallet = get_online_wallet(
                    colored_wallet.wallet, is_multisig,
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
        """Sync with multisig bridge to check for pending operations."""
        if not self._is_multisig():
            return
        if SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET:
            return
        self.is_loading.emit(True)
        self.run_in_thread(
            RgbRepository.sync_with_hub,
            {
                'args': [],
                'callback': self.on_multisig_sync_done,
                # Assuming on_error is on_multisig_sync_error
                'error_callback': self.on_multisig_sync_error,
            },
        )

    def on_multisig_sync_done(self, operation_info: list[OperationInfo] | OperationInfo):
        """Handle successful bridge sync. Emits pending operations list."""
        # operation_info is a list of filtered operations (or single obj if from legacy path, but we changed it)
        pending_ops = []
        if operation_info:
            if isinstance(operation_info, list):
                pending_ops = operation_info
            else:
                pending_ops = [operation_info]

        has_blocking_op = False
        for op_info in pending_ops:
            if op_info is None:
                continue
            operation = op_info.operation
            if operation is None:
                continue

            is_blocking = (
                operation.is_CREATE_UTXOS_TO_REVIEW()
                or operation.is_CREATE_UTXOS_PENDING()
                or operation.is_SEND_BTC_TO_REVIEW()
                or operation.is_SEND_BTC_PENDING()
                or operation.is_SEND_TO_REVIEW()
                or operation.is_SEND_PENDING()
                or operation.is_INFLATION_TO_REVIEW()
                or operation.is_INFLATION_PENDING()
            )
            if is_blocking:
                has_blocking_op = True
                break

        self._set_multisig_pending(has_blocking_op)

        # For watch-only wallets: extract and save review PSBTs to local DB
        # so they can be transferred to offline wallet via USB sync
        if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
            self._extract_and_save_review_psbts(pending_ops)
            # Update RGB context for PSBTs where we are the initiator
            self._update_rgb_context_for_initiator_psbts(pending_ops)

        # Trigger inspection of the blocking pending operation (if any) to get its TXID
        # and store it in global service state
        self._inspect_and_set_global_pending_state(pending_ops)

        # Filter pending_ops to only include those that require action from the current wallet
        actionable_ops = []
        for op_info in pending_ops:
            if op_info is None or not hasattr(op_info, 'operation'):
                continue
            operation = op_info.operation
            if operation is None:
                continue

            is_to_review = (
                operation.is_CREATE_UTXOS_TO_REVIEW()
                or operation.is_SEND_BTC_TO_REVIEW()
                or operation.is_SEND_TO_REVIEW()
                or operation.is_INFLATION_TO_REVIEW()
            )
            if is_to_review:
                actionable_ops.append(op_info)

        self.pending_operations_ready.emit(actionable_ops)

    def _inspect_and_set_global_pending_state(self, pending_ops: list[OperationInfo]):
        """Find the relevant pending operation, inspect its PSBT to get TXID, and set global state."""

        # Reset state first
        BroadcastTransactionService.set_pending_operation_state(None, None)

        target_op_info = None
        for op_info in pending_ops:
            if op_info is None:
                continue
            operation = op_info.operation
            if operation is None:
                continue
            psbt = getattr(operation, 'psbt', None)
            if not psbt:
                continue

            # We care about operations that block new ones (Create UTXOs, Send BTC, Send RGB, Inflation)
            is_blocking = (
                operation.is_CREATE_UTXOS_TO_REVIEW() or operation.is_CREATE_UTXOS_PENDING() or
                operation.is_SEND_BTC_TO_REVIEW() or operation.is_SEND_BTC_PENDING() or
                operation.is_SEND_TO_REVIEW() or operation.is_SEND_PENDING() or
                operation.is_INFLATION_TO_REVIEW() or operation.is_INFLATION_PENDING()
            )
            if is_blocking:
                target_op_info = op_info
                break

        if not target_op_info:
            return

        # Found a target operation. Inspect its PSBT to get TXID.
        operation = target_op_info.operation
        psbt = getattr(operation, 'psbt', None)
        if not psbt:
            return

        # Store op info tentatively (without TXID yet)
        BroadcastTransactionService.set_pending_operation_state(
            target_op_info, None,
        )

        # Run inspection in thread
        self.run_in_thread(
            RgbRepository.inspect_psbt,
            {
                'args': [psbt],
                'callback': lambda result: self._on_pending_psbt_inspected(result, target_op_info),
                'error_callback': lambda e: logger.error('Header Pending Inspection Failed: %s', e),
            },
        )

    def _on_pending_psbt_inspected(self, result, op_info: OperationInfo):
        """Callback when pending PSBT is inspected."""
        try:
            txid = result.txid
            BroadcastTransactionService.set_pending_operation_state(
                op_info, txid,
            )
        except Exception as e:
            logger.error('Failed to set global pending state: %s', e)

    def _is_review_operation(self, operation: Operation) -> bool:
        """Check if operation is a review type needing signature."""
        return (
            operation.is_CREATE_UTXOS_TO_REVIEW()
            or operation.is_SEND_BTC_TO_REVIEW()
            or operation.is_SEND_TO_REVIEW()
            or operation.is_INFLATION_TO_REVIEW()
        )

    def _get_purpose_from_operation(self, operation: Operation) -> str | None:
        """Determine purpose from operation type."""
        if operation.is_CREATE_UTXOS_TO_REVIEW():
            return 'create_utxos'
        if operation.is_SEND_BTC_TO_REVIEW():
            return 'send_btc'
        if operation.is_SEND_TO_REVIEW():
            return 'send_asset'
        if operation.is_INFLATION_TO_REVIEW():
            return 'inflate_asset'
        return None

    def _check_already_signed(self, wallet_service: WalletDataService, psbt: str) -> bool:
        """Check if we already have a signed version of this PSBT."""
        existing_signed = wallet_service.list_psbt(signed=True)
        if not existing_signed:
            return False
        try:
            unsigned_txid = RgbRepository.inspect_psbt(psbt=psbt).txid
            for p in existing_signed:
                psbt_value = p.get('psbt')
                if not psbt_value:
                    continue
                try:
                    signed_txid = RgbRepository.inspect_psbt(
                        psbt=psbt_value,
                    ).txid
                    if unsigned_txid == signed_txid:
                        return True
                except Exception:
                    pass
        except Exception as e:
            logger.error('Failed to inspect PSBT for duplicate check: %s', e)
        return False

    def _extract_rgb_context(self, operation: Operation) -> tuple[str | None, int | None, int | None]:
        """Extract RGB context from operation details."""
        is_rgb = operation.is_SEND_TO_REVIEW() or operation.is_INFLATION_TO_REVIEW()
        if not is_rgb:
            return None, None, None
        op_details = operation.details
        if op_details is None:
            return None, None, None
        fascia_path = op_details.fascia_path
        entropy = op_details.entropy
        min_confirmations = op_details.min_confirmations
        return fascia_path, entropy, min_confirmations

    def _extract_and_save_review_psbts(self, pending_ops: list[OperationInfo]):
        """Extract PSBTs from review operations and save to local DB for offline signing."""

        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return

        local_xpub = SettingRepository.get_config_value(
            ACCOUNT_XPUB_COLORED, None,
        )

        for op_info in pending_ops:
            if op_info is None:
                continue
            operation = op_info.operation
            if operation is None:
                continue

            if not self._is_review_operation(operation):
                continue

            psbt = operation.psbt
            if not psbt:
                continue

            purpose = self._get_purpose_from_operation(operation)
            if not purpose:
                continue

            # Skip if we initiated this operation
            if op_info.initiator_xpub == local_xpub:
                continue

            try:
                # Check for duplicate unsigned PSBT
                existing = wallet_service.list_psbt(signed=False)
                if existing and any(p.get('psbt') == psbt for p in existing):
                    continue

                # Check if already signed
                if self._check_already_signed(wallet_service, psbt):
                    continue

                # Extract RGB context and save
                fascia_path, entropy, min_confirmations = self._extract_rgb_context(
                    operation,
                )
                wallet_service.add_psbt(
                    PsbtData(
                        psbt_base64=psbt,
                        signed=False,
                        purpose=purpose,
                        fascia_path=fascia_path,
                        entropy=entropy,
                        min_confirmations=min_confirmations,
                    ),
                )
                logger.info(
                    'Saved review operation PSBT to local DB: purpose=%s, rgb_context=%s',
                    purpose,
                    bool(fascia_path),
                )
            except Exception as exc:
                logger.error('Failed to save review PSBT to DB: %s', exc)

    def _update_rgb_context_for_initiator_psbts(self, pending_ops: list[OperationInfo]):
        """Update RGB context for PSBTs where current wallet is the initiator.

        When watch-only initiates a send/inflate operation, the PSBT is saved immediately
        but RGB context (fascia_path, entropy, min_confirmations) comes later from
        sync_with_hub. This method updates those PSBTs with the RGB context.
        """
        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return

        local_xpub = SettingRepository.get_config_value(
            ACCOUNT_XPUB_COLORED, None,
        )

        for op_info in pending_ops:
            if op_info is None or not hasattr(op_info, 'operation'):
                continue

            operation = op_info.operation
            if operation is None:
                continue

            # Only process RGB operations where we are the initiator
            is_rgb_operation = (
                operation.is_SEND_TO_REVIEW() or operation.is_SEND_PENDING() or
                operation.is_INFLATION_TO_REVIEW() or operation.is_INFLATION_PENDING()
            )
            if not is_rgb_operation:
                continue

            # Check if we are the initiator
            initiator_xpub = getattr(op_info, 'initiator_xpub', None)
            if initiator_xpub != local_xpub:
                continue

            # Extract PSBT and RGB context
            psbt = getattr(operation, 'psbt', None)
            if not psbt:
                continue

            op_details = getattr(operation, 'details', None)
            if op_details is None:
                continue

            fascia_path = getattr(op_details, 'fascia_path', None)
            entropy = getattr(op_details, 'entropy', None)
            min_confirmations = getattr(op_details, 'min_confirmations', None)

            # Only update if we have fascia_path (indicates valid RGB context)
            if not fascia_path:
                continue

            try:
                updated = wallet_service.update_psbt_rgb_context(
                    psbt,
                    fascia_path=fascia_path,
                    entropy=entropy,
                    min_confirmations=min_confirmations,
                )
                if updated:
                    logger.info(
                        'Updated RGB context for initiator PSBT: fascia_path=%s',
                        fascia_path[:20] if fascia_path else None,
                    )
            except Exception as exc:
                logger.error(
                    'Failed to update RGB context for initiator PSBT: %s', exc,
                )

    def on_multisig_sync_error(self, error: Exception):
        """Handle bridge sync error."""
        logger.error('Failed to sync with multisig bridge: %s', error)
        self._set_multisig_pending(False)
        # Emit empty list on error
        self.pending_operations_ready.emit([])
