"""
ViewModel for handling the broadcasting of signed PSBT transactions (Bitcoin and RGB) in the application.
Provides methods for broadcasting, error handling, and UI feedback for transaction-related operations.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import OperationInfo
from rgb_lib import RespondToOperation

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import SendAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_ASSET_ISSUED_INFLATED_SUCCESSFULLY
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_BITCOIN_SENT
from src.utils.info_message import INFO_OPERATION_COMPLETED_AND_FINALIZED
from src.utils.info_message import INFO_OPERATION_INDEX_MISSING_FOR_NACK
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_PSBT_SIGN_SUCCESSFULLY
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog
from src.views.components.toast import ToastManager


class BroadcastTransactionViewModel(QObject, ThreadManager):
    """
    ViewModel for broadcasting signed PSBT transactions.
    """
    is_loading = Signal(bool)
    tx_broadcasted = Signal(bool)
    hw_dialog_update = Signal(str, object)
    finalized_psbt = Signal(str)
    psbt_inspection_ready = Signal(object)
    rgb_transfer_inspection_ready = Signal(object)
    pending_operation_ready = Signal(object)
    is_reject_loading = Signal(bool)
    psbts_loaded = Signal(list)
    trigger_bridge_sync = Signal()

    def __init__(self, page_navigation) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self._multisig_operation_idx: int | None = None
        self._current_signed_psbt: str | None = None
        self._current_signed_txid: str | None = None
        self._pending_psbt_txid: str | None = None
        self._pending_op_info: object | None = None
        # Guard variables for preventing duplicate calls
        self._inspecting_psbt: str | None = None
        self._inspecting_rgb: tuple | None = None

    def load_psbts(self, is_signed: bool) -> None:
        """Load PSBT drafts via service and emit to the UI."""

        def _run():
            try:
                items = BroadcastTransactionService.list_psbt_drafts(is_signed)
                self.psbts_loaded.emit(items)
            except Exception as exc:
                self.on_error(CommonException(str(exc)))
                self.psbts_loaded.emit([])

        self.run_in_thread(_run, {})

    def execute_psbt_action(self, psbt_text: str, selector_purpose: str | None, can_broadcast: bool) -> None:
        """Execute sign/broadcast flow. Routing decisions are delegated to the service."""
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        purpose = BroadcastTransactionService.resolve_purpose(
            parsed, selector_purpose,
        )
        action = BroadcastTransactionService.action_key(
            can_broadcast=can_broadcast, purpose=purpose,
        )

        if action == 'sign':
            BroadcastTransactionService.set_rgb_mode_for_purpose(purpose)
            self.sign_and_finalize_psbt(parsed.psbt)
            return
        if action == 'send_btc':
            self.send_btc_end(parsed.psbt)
            return
        if action == 'send_asset':
            self.send_end(parsed.psbt)
            return
        if action == 'inflation':
            self.inflate_end(parsed.psbt)
            return
        self.create_utxos_end(parsed.psbt)

    def send_end(self, signed_psbt: str):
        """
        Broadcast a signed PSBT using the RgbRepository.
        """
        self.is_loading.emit(True)
        request = BroadcastPsbtRequestModel(signed_psbt=signed_psbt)
        self.run_in_thread(
            RgbRepository.send_end,
            {
                'args': [request],
                'callback': self.on_success_send_end,
                'error_callback': self.on_error,
            },
        )

    def on_success_send_end(self, response: SendAssetResponseModel):
        """Handle success message for broadcast"""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)
        ToastManager.success(description=INFO_ASSET_SENT.format(response.txid))

    def on_error(self, error: CommonException) -> None:
        """Handle error for broadcasting psbt."""
        self.is_loading.emit(False)
        self.is_reject_loading.emit(False)
        ToastManager.error(description=error.message)
        logger.error(
            'Exception occurred: %s, Message: %s',
            type(error).__name__, str(error),
        )

    def create_utxos_end(self, signed_psbt: str):
        """
        Broadcast a signed PSBT using the RgbRepository.
        """
        self.is_loading.emit(True)
        request = BroadcastPsbtRequestModel(signed_psbt=signed_psbt)
        self.run_in_thread(
            BtcRepository.create_utxos_end,
            {
                'args': [request],
                'callback': self.on_success_create_utxos_end,
                'error_callback': self.on_error,
            },
        )

    def on_success_create_utxos_end(self):
        """Handle success message for broadcast"""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)

    def send_btc_end(self, signed_psbt: str):
        """
        Broadcast a signed PSBT using the RgbRepository.
        """
        self.is_loading.emit(True)
        request = BroadcastPsbtRequestModel(signed_psbt=signed_psbt)
        self.run_in_thread(
            BtcRepository.send_btc_end,
            {
                'args': [request],
                'callback': self.on_success_send_btc_end,
                'error_callback': self.on_error,
            },
        )

    def on_success_send_btc_end(self, response: SendBtcResponseModel):
        """Handle success message for broadcast"""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)
        ToastManager.success(
            description=INFO_BITCOIN_SENT.format(response.tx_id),
        )

    def sign_and_finalize_psbt(self, unsigned_psbt):
        """
        Sign and finalize the PSBT in a worker thread.
        Signs the PSBT with hardware wallet and finalizes the transaction.
        """
        self.hw_dialog_update.emit(
            INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
        )
        self.run_in_thread(
            CommonOperationRepository.sign_and_finalize_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self.on_sign_and_finalize_success,
                'error_callback': self.on_sign_and_finalize_error,
            },
        )

    def on_sign_and_finalize_success(self, finalized_psbt):
        """Handle success method for signing"""
        self.finalized_psbt.emit(finalized_psbt)
        ToastManager.success(description=INFO_PSBT_SIGN_SUCCESSFULLY)

    def on_sign_and_finalize_error(self, error: CommonException) -> None:
        """Handle error for broadcasting psbt."""
        self.is_loading.emit(False)
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            hw_device = HWDeviceSelectionDialog(None)
            message = hw_device.map_hwi_error(str(error))
            self.hw_dialog_update.emit(
                str(message), PsbtStatus.ERROR,
            )
        else:
            ToastManager.error(description=error.message)
            logger.error(
                'Exception occurred: %s, Message: %s',
                type(error).__name__, str(error),
            )

    def inflate_end(self, signed_psbt: str):
        """
        Broadcast a signed PSBT using the RgbRepository.
        """
        self.is_loading.emit(True)
        self.run_in_thread(
            RgbRepository.inflate_end,
            {
                'args': [signed_psbt],
                'callback': self.on_success_inflate_end,
                'error_callback': self.on_error,
            },
        )

    def on_success_inflate_end(self, result):
        """Handle success message for broadcast"""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)
        ToastManager.success(
            description=INFO_ASSET_ISSUED_INFLATED_SUCCESSFULLY.format(
                result.txid,
            ),
        )

    def _respond_to_multisig_operation(self, operation_idx: int | None, response: RespondToOperation) -> None:
        """Post an ACK/NACK response for a multisig pending operation."""
        self.run_in_thread(
            RgbRepository.respond_to_operation,
            {
                'args': [operation_idx, response],
                'callback': self._on_multisig_post_success,
                'error_callback': self.on_error,
            },
        )

    # ========== Multisig Signer Flow ==========

    def sign_and_post_multisig(self, unsigned_psbt: str, operation_idx: int | None, purpose: str | None = None):
        """Sign PSBT and post back to multisig bridge."""
        self.is_loading.emit(True)
        # Store operation_idx for use in callback
        self._multisig_operation_idx = operation_idx

        if purpose:
            BroadcastTransactionService.set_rgb_mode_for_purpose(purpose)

        # Show hardware wallet dialog if applicable
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )

        self.run_in_thread(
            CommonOperationRepository.sign_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self._on_multisig_sign_success,
                'error_callback': self.on_multisig_sign_error,
            },
        )

    def on_multisig_sign_error(self, error: CommonException) -> None:
        """Handle error for multisig signing."""
        self.is_loading.emit(False)
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            hw_dialog = HWDeviceSelectionDialog(None)
            message = hw_dialog.map_hwi_error(str(error))
            self.hw_dialog_update.emit(
                str(message), PsbtStatus.ERROR,
            )
        else:
            self.on_error(error)

    def _on_multisig_sign_success(self, signed_psbt: str):
        """After signing, inspect to get TXID, then post back to the bridge."""
        # Store for use in next steps
        if SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET:
            self.finalized_psbt.emit(signed_psbt)
            return
        self._current_signed_psbt = signed_psbt

        # INSPECT newly signed PSBT to get TXID for filtering later
        self.run_in_thread(
            RgbRepository.inspect_psbt,
            {
                'args': [signed_psbt],
                'callback': self._on_signed_psbt_inspected,
                'error_callback': self.on_error,
            },
        )

    def _on_signed_psbt_inspected(self, details):
        """Got inspection details, extract TXID and proceed to post."""
        try:
            self._current_signed_txid = details.txid
        except AttributeError:
            self._current_signed_txid = None

        operation_idx = self._multisig_operation_idx
        signed_psbt = self._current_signed_psbt or ''

        # SIGNER FLOW: Existing operation, so we are responding
        response = RespondToOperation.ACK(signed_psbt)
        self._respond_to_multisig_operation(operation_idx, response)

    def _on_multisig_post_success(self, result: OperationInfo):
        """Handle successful post to bridge."""
        self.is_loading.emit(False)
        BroadcastTransactionService.set_pending_operation_state(None, None)
        self.trigger_bridge_sync.emit()
        self.tx_broadcasted.emit(True)
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                None, PsbtStatus.SUCCESS,
            )

        if result is None:
            ToastManager.success(
                description=INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE,
            )
            return

        if result.operation.is_create_utxos_completed():
            ToastManager.success(
                description=INFO_OPERATION_COMPLETED_AND_FINALIZED,
            )
        elif result.operation.is_send_btc_completed():
            ToastManager.success(
                description=INFO_BITCOIN_SENT.format(result.operation.txid),
            )
        elif result.operation.is_inflation_completed():
            ToastManager.success(
                description=INFO_ASSET_ISSUED_INFLATED_SUCCESSFULLY.format(
                    result.operation.txid,
                ),
            )
        elif result.operation.is_send_completed():
            ToastManager.success(
                description=INFO_ASSET_SENT.format(result.operation.txid),
            )
        else:
            # Generic success for initiator or other cases
            ToastManager.success(
                description=INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE,
            )

    def respond_nack(self, operation_idx: int | None):
        """NACK a pending operation without signing (human disagrees)."""
        if operation_idx is None:
            ToastManager.error(
                description=INFO_OPERATION_INDEX_MISSING_FOR_NACK,
            )
            return
        self.is_reject_loading.emit(True)
        response = RespondToOperation.NACK()
        self.run_in_thread(
            RgbRepository.respond_to_operation,
            {
                'args': [operation_idx, response],
                'callback': self._on_nack_post_success,
                'error_callback': self.on_error,
            },
        )

    # ========== Multisig Watch-Only USB helpers ==========

    def respond_psbt_to_operation(self, signed_psbt: str, operation_idx: int | None) -> None:
        """Cosigner flow (watch-only): respond to operation with ACK(signed_psbt)."""
        self.is_loading.emit(True)
        response = RespondToOperation.ACK(signed_psbt)
        self._respond_to_multisig_operation(operation_idx, response)

    def _on_nack_post_success(self):
        """Handle successful NACK post to the multisig bridge."""
        self.is_reject_loading.emit(False)
        # Close the dialog like other flows and show a specific success toast
        BroadcastTransactionService.set_pending_operation_state(None, None)
        self.trigger_bridge_sync.emit()
        self.tx_broadcasted.emit(True)
        ToastManager.success(
            description='Operation rejected and posting to the bridge',
        )

    def inspect_psbt(self, psbt: str):
        """Inspect PSBT for review details."""
        # Guard: skip if already inspecting this PSBT
        if self._inspecting_psbt == psbt:
            return
        self._inspecting_psbt = psbt
        self.run_in_thread(
            RgbRepository.inspect_psbt,
            {
                'args': [psbt],
                'callback': self._on_inspect_psbt_success,
                'error_callback': self._on_inspect_psbt_error,
            },
        )

    def _on_inspect_psbt_error(self, error: Exception) -> None:
        """Handle error for PSBT inspection - emit None so UI can handle failure."""
        self._inspecting_psbt = None  # Reset guard
        self.is_loading.emit(False)
        self.psbt_inspection_ready.emit(None)  # Emit None to signal failure
        msg = error.message if hasattr(error, 'message') else str(error)
        ToastManager.error(description=msg)
        logger.error(
            'PSBT inspection failed: %s, Message: %s',
            type(error).__name__, str(error),
        )

    def inspect_rgb_transfer(self, fascia_path: str, psbt: str, entropy: int):
        """Inspect RGB transfer for review details."""
        # Guard: skip if already inspecting this RGB transfer
        rebased_path = BroadcastTransactionService.rebase_fascia_path(
            fascia_path,
        )
        key = (rebased_path, psbt)
        if self._inspecting_rgb == key:
            return
        self._inspecting_rgb = key
        self.run_in_thread(
            RgbRepository.inspect_rgb_transfer,
            {
                'args': [rebased_path, psbt, entropy],
                'callback': self._on_inspect_rgb_transfer_success,
                'error_callback': self._on_inspect_rgb_transfer_error,
            },
        )

    def _on_inspect_rgb_transfer_error(self, error: Exception) -> None:
        """Handle error for RGB transfer inspection - emit None so UI can handle failure."""
        self._inspecting_rgb = None  # Reset guard
        self.is_loading.emit(False)
        self.rgb_transfer_inspection_ready.emit(
            None,
        )  # Emit None to signal failure
        msg = error.message if hasattr(error, 'message') else str(error)
        ToastManager.error(description=msg)
        logger.error(
            'RGB transfer inspection failed: %s, Message: %s',
            type(error).__name__, str(error),
        )

    def fetch_pending_operation(self):
        """Fetch pending operation from bridge to check against current PSBT."""
        if SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET:
            return

        # NEW: Check global state first (populated by Header)
        global_op_info, global_txid = BroadcastTransactionService.get_pending_operation_state()
        if global_op_info:
            self._pending_op_info = global_op_info
            self._pending_psbt_txid = global_txid
            self.pending_operation_ready.emit(global_op_info)
            return

        # Fallback if global state empty (orphan page load?)
        self.run_in_thread(
            RgbRepository.sync_with_hub,
            {
                'args': [],
                'callback': self._on_fetch_pending_operation_success,
                'error_callback': self.on_error,
            },
        )

    def _on_inspect_psbt_success(self, result):
        """Handle success message for inspect psbt"""
        self._inspecting_psbt = None  # Reset guard
        self.is_loading.emit(False)
        self.psbt_inspection_ready.emit(result)

    def _on_inspect_rgb_transfer_success(self, result):
        """Handle success message for inspect rgb transfer"""
        self._inspecting_rgb = None  # Reset guard
        self.is_loading.emit(False)
        self.rgb_transfer_inspection_ready.emit(result)

    def _on_fetch_pending_operation_success(self, result):
        """
        Handle success message for fetch pending operation (fallback path).
        """
        self._pending_op_info = result
        if result:
            # Inspect to get TXID (for fuzzy matching)
            pending_ctx = BroadcastTransactionService.multisig_pending_context(
                result,
            )
            if pending_ctx and pending_ctx.psbt:
                self.run_in_thread(
                    RgbRepository.inspect_psbt,
                    {
                        'args': [pending_ctx.psbt],
                        'callback': self._on_pending_psbt_inspected,
                        'error_callback': self.on_error,
                    },
                )
                return

        # If no result or no PSBT to inspect, emit immediately
        self._pending_psbt_txid = None
        self.pending_operation_ready.emit(result)

    def _on_pending_psbt_inspected(self, result):
        """Callback when the pending operation's PSBT has been inspected."""
        try:
            self._pending_psbt_txid = result.txid
            # Update global state too
            BroadcastTransactionService.set_pending_operation_state(
                self._pending_op_info, result.txid,
            )
        except Exception:
            self._pending_psbt_txid = None
        # Now emit the signal with the original op info
        self.pending_operation_ready.emit(self._pending_op_info)

    def get_pending_psbt_txid(self) -> str | None:
        """Return the TXID of the currently pending operation's PSBT."""
        return self._pending_psbt_txid
