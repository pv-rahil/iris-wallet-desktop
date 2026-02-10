"""
ViewModel for handling the broadcasting of signed PSBT transactions (Bitcoin and RGB) in the application.
Provides methods for broadcasting, error handling, and UI feedback for transaction-related operations.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import OperationResult
from rgb_lib import RespondToOperation

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType, WalletType
from src.model.enums.enums_model import PsbtStatus
from src.model.rgb_model import SendAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_ASSET_ISSUED_INFLATED_SUCCESSFULLY
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_ASSET_SENT_SUCCESSFULLY
from src.utils.info_message import INFO_BITCOIN_SENT
from src.utils.info_message import INFO_BITCOIN_SENT_SUCCESSFULLY
from src.utils.info_message import INFO_OPERATION_COMPLETED_AND_FINALIZED
from src.utils.info_message import INFO_OPERATION_INDEX_MISSING_FOR_NACK
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_PSBT_SIGN_SUCCESSFULLY
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_SIGNED_SUCCESSFULLY_WAITING_FOR_COSIGNERS
from src.utils.local_store import local_store
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

    def __init__(self, page_navigation) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self._multisig_operation_idx: int | None = None
        self._current_signed_psbt: str | None = None
        self._current_signed_txid: str | None = None

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
        purpose = BroadcastTransactionService.resolve_purpose(parsed, selector_purpose)
        action = BroadcastTransactionService.action_key(can_broadcast=can_broadcast, purpose=purpose)

        if action == "sign":
            BroadcastTransactionService.set_rgb_mode_for_purpose(purpose)
            self.sign_and_finalize_psbt(parsed.psbt)
            return
        if action == "send_btc":
            self.send_btc_end(parsed.psbt)
            return
        if action == "send_asset":
            self.send_end(parsed.psbt)
            return
        if action == "inflate_asset":
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
        print(error)
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

    def on_success_inflate_end(self, response: OperationResult):
        """Handle success message for broadcast"""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)
        ToastManager.success(description=INFO_ASSET_SENT.format(response.txid))

    # ========== Multisig Signer Flow ==========

    def sign_and_post_multisig(self, unsigned_psbt: str, operation_idx: int | None):
        """Sign PSBT and post back to multisig bridge."""
        self.is_loading.emit(True)
        # Store operation_idx for use in callback
        self._multisig_operation_idx = operation_idx
        self.run_in_thread(
            CommonOperationRepository.sign_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self._on_multisig_sign_success,
                'error_callback': self.on_error,
            },
        )

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
        signed_psbt = self._current_signed_psbt or ""

        # SIGNER FLOW: Existing operation, so we are responding
        response = RespondToOperation.ACK(signed_psbt)

        # Post back to bridge using respond_to_operation
        self.run_in_thread(
            RgbRepository.respond_to_operation,
            {
                'args': [operation_idx, response],
                'callback': self._on_multisig_post_success,
                'error_callback': self.on_error,
            },
        )

    def _on_multisig_post_success(self, result):
        """Handle successful post to bridge."""
        self.is_loading.emit(False)
        self.tx_broadcasted.emit(True)
        # Combine pending checks to reduce complexity
        is_pending = (
            result.is_create_utxos_pending() or
            result.is_send_btc_pending() or
            result.is_inflation_pending() or
            result.is_send_pending()
        )

        if is_pending:
            ToastManager.success(
                description=INFO_SIGNED_SUCCESSFULLY_WAITING_FOR_COSIGNERS,
            )
        elif result.is_create_utxos_completed():
            ToastManager.success(
                description=INFO_OPERATION_COMPLETED_AND_FINALIZED,
            )
        elif result.is_send_btc_completed():
            ToastManager.success(description=INFO_BITCOIN_SENT_SUCCESSFULLY)
        elif result.is_inflation_completed():
            ToastManager.success(
                description=INFO_ASSET_ISSUED_INFLATED_SUCCESSFULLY,
            )
        elif result.is_send_completed():
            ToastManager.success(description=INFO_ASSET_SENT_SUCCESSFULLY)
        else:
            # Generic success for initiator or other cases
            ToastManager.success(
                description=INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE,
            )
            logger.info('Multisig post result: %s', str(result))

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

    def post_psbt_to_bridge_by_purpose(self, purpose: str, signed_psbt: str) -> None:
        """Initiator flow (watch-only): post a signed PSBT to bridge based on purpose."""
        if not signed_psbt:
            self.on_error(CommonException('No PSBT to post'))
            return
        self.is_loading.emit(True)

        if purpose == 'send_btc':
            self.run_in_thread(
                BtcRepository.post_send_btc,
                {
                    'args': [signed_psbt],
                    'callback': lambda *_: self._on_multisig_post_success(None),
                    'error_callback': self.on_error,
                },
            )
            return

        if purpose in ['create_utxos', 'issue_asset_nia', 'issue_asset_cfa', 'issue_asset_ifa']:
            self.run_in_thread(
                BtcRepository.post_create_utxos,
                {
                    'args': [signed_psbt],
                    'callback': lambda *_: self._on_multisig_post_success(None),
                    'error_callback': self.on_error,
                },
            )
            return

        self.on_error(CommonException(f'Unsupported purpose: {purpose}'))

    def respond_psbt_to_operation(self, signed_psbt: str, operation_idx: int | None) -> None:
        """Cosigner flow (watch-only): respond to operation with ACK(signed_psbt)."""
        if operation_idx is None:
            self.on_error(CommonException('Operation index missing'))
            return
        if not signed_psbt:
            self.on_error(CommonException('No PSBT to respond with'))
            return
        self.is_loading.emit(True)
        response = RespondToOperation.ACK(signed_psbt)
        self.run_in_thread(
            RgbRepository.respond_to_operation,
            {
                'args': [operation_idx, response],
                'callback': self._on_multisig_post_success,
                'error_callback': self.on_error,
            },
        )

    def _on_nack_post_success(self, result):
        """Handle successful NACK post to the multisig bridge."""
        self.is_reject_loading.emit(False)
        # Close the dialog like other flows and show a specific success toast
        self.tx_broadcasted.emit(True)
        ToastManager.success(
            description='Operation rejected and posting to the bridge',
        )

    def inspect_psbt(self, psbt: str):
        """Inspect PSBT for review details."""
        self.run_in_thread(
            RgbRepository.inspect_psbt,
            {
                'args': [psbt],
                'callback': self._on_inspect_psbt_success,
                'error_callback': self.on_error,
            },
        )

    def inspect_rgb_transfer(self, consignment: list[str], psbt: str, entropy: int):
        """Inspect RGB transfer for review details."""
        self.run_in_thread(
            RgbRepository.inspect_rgb_transfer,
            {
                'args': [consignment, psbt, entropy],
                'callback': self._on_inspect_rgb_transfer_success,
                'error_callback': self.on_error,
            },
        )

    def fetch_pending_operation(self):
        """Fetch pending operation from bridge to check against current PSBT."""
        self.run_in_thread(
            RgbRepository.sync_with_bridge,
            {
                'args': [],
                'callback': self._on_fetch_pending_operation_success,
                'error_callback': self.on_error,
            },
        )

    def _on_inspect_psbt_success(self, result):
        """Handle success message for inspect psbt"""
        self.is_loading.emit(False)
        self.psbt_inspection_ready.emit(result)

    def _on_inspect_rgb_transfer_success(self, result):
        """Handle success message for inspect rgb transfer"""
        self.is_loading.emit(False)
        self.rgb_transfer_inspection_ready.emit(result)

    def _on_fetch_pending_operation_success(self, result):
        """Handle success message for fetch pending operation"""
        self.pending_operation_ready.emit(result)
