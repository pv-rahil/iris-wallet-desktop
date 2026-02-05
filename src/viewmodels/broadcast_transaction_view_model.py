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
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.data.service.wallet_data_service import WalletDataService
from src.data.service.psbt_inspection_service import PsbtInspectionService
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.psbt_inspection_model import OperationContextModel
from src.model.psbt_inspection_model import PsbtDisplayDataModel
from src.model.psbt_inspection_model import PsbtInspectionResponseModel
from src.model.psbt_inspection_model import RgbInspectionResponseModel
from src.model.psbt_selection_model import PendingOperationDisplayModel
from src.model.psbt_selection_model import PsbtSelectionItemModel
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
from src.utils.constant import MASTER_XPUB
from src.utils.hardware_client_store import hardware_client_store
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog
from src.views.components.toast import ToastManager


class BroadcastTransactionViewModel(QObject, ThreadManager):
    """
    ViewModel for broadcasting signed PSBT transactions.
    """
    MIN_PSBT_LEN = 80
    is_loading = Signal(bool)
    tx_broadcasted = Signal(bool)
    hw_dialog_update = Signal(str, object)
    finalized_psbt = Signal(str)
    signature_count_ready = Signal(int)
    combined_psbt_ready = Signal(str)
    is_reject_loading = Signal(bool)

    # Typed model signals
    psbt_data_ready = Signal(PsbtInspectionResponseModel)
    rgb_data_ready = Signal(RgbInspectionResponseModel)
    operation_context_ready = Signal(OperationContextModel)
    display_data_ready = Signal(PsbtDisplayDataModel)
    psbt_items_ready = Signal(list)
    psbt_signed_items_ready = Signal(list)

    def __init__(self, page_navigation) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self._multisig_operation_idx: int | None = None
        self._current_signed_psbt: str | None = None
        self._current_signed_txid: str | None = None
        self._psbt_items: list[PsbtSelectionItemModel] = []
        self._psbt_signed_items: list[PsbtSelectionItemModel] = []

        # Typed model storage
        self.psbt_details: PsbtInspectionResponseModel | None = None
        self.rgb_details: RgbInspectionResponseModel | None = None
        self.operation_context: OperationContextModel | None = None
        self.display_data: PsbtDisplayDataModel | None = None

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

    def is_psbt_text_valid(self, psbt_text: str) -> bool:
        """Basic PSBT input validation used for UI enablement."""
        return bool(psbt_text) and len(psbt_text.strip()) >= self.MIN_PSBT_LEN

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

    def submit_broadcast_psbt(self, psbt_text: str, selector_index: int) -> None:
        """Parse PSBT text and dispatch to the correct broadcast handler."""
        purpose, signed_psbt = self._parse_psbt_input(psbt_text)
        purpose = self._resolve_purpose(
            explicit_purpose=purpose,
            signed=True,
            selector_index=selector_index,
        )
        purpose_map = {
            'send_btc': self.send_btc_end,
            'send_asset': self.send_end,
            'inflate_asset': self.inflate_end,
        }
        handler = purpose_map.get(purpose, self.create_utxos_end)
        handler(signed_psbt)

    def submit_sign_psbt(self, psbt_text: str, selector_index: int) -> None:
        """Parse PSBT text, set RGB mode if needed, and sign+finalize."""
        purpose, unsigned_psbt = self._parse_psbt_input(psbt_text)
        purpose = self._resolve_purpose(
            explicit_purpose=purpose,
            signed=False,
            selector_index=selector_index,
        )
        hardware_client_store.set_rgb_mode(
            purpose in ('send_asset', 'inflate_asset'),
        )
        self.sign_and_finalize_psbt(unsigned_psbt)

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

    def prepare_pending_operation(
        self, pending_operation: object | None,
    ) -> PendingOperationDisplayModel | None:
        """Extract display-safe pending operation context for the view."""
        if pending_operation is None:
            return None
        operation = getattr(pending_operation, 'operation', None)
        initiator_xpub = getattr(pending_operation, 'initiator_xpub', None)
        local_xpub = local_store.get_value(MASTER_XPUB)
        is_initiator = bool(
            initiator_xpub and local_xpub and initiator_xpub == local_xpub,
        )
        psbt = getattr(operation, 'psbt', None) if operation is not None else None
        return PendingOperationDisplayModel(
            psbt=psbt or '',
            is_initiator=is_initiator,
            operation=operation,
        )

    def get_signed_psbt_page_name(self, psbt: str) -> str:
        """Resolve page name based on signed PSBT purpose."""
        if not psbt:
            return 'NIA page'
        try:
            svc = WalletDataService.get_session()
            if svc is None:
                return 'NIA page'
            signed = svc.list_psbt(True) or []
            match = next(
                (p for p in signed if p.get('psbt') == psbt), None,
            )
            purpose = match.get('purpose') if isinstance(
                match, dict,
            ) else None
            if purpose == 'inflate_asset':
                return 'IFA secondary issuance'
        except Exception:
            return 'NIA page'
        return 'NIA page'

    def load_psbts(self, signed: bool) -> None:
        """Load PSBT drafts and emit pre-processed selection items via Service."""
        drafts = BroadcastTransactionService.load_psbts(signed)


        items = self._build_psbt_selection_items(drafts)
        if signed:
            self._psbt_signed_items = items
            self.psbt_signed_items_ready.emit(items)
        else:
            self._psbt_items = items
            self.psbt_items_ready.emit(items)

    def cleanup_secondary_draft_if_any(self, psbt_text: str) -> None:
        """Best-effort cleanup for secondary issuance drafts."""
        try:
            svc = WalletDataService.get_session()
            if svc is None:
                return
            purpose, psbt_only = self._parse_psbt_input(psbt_text)

            # If purpose is known and not inflate, do nothing
            if purpose is not None and purpose != 'inflate_asset':
                return

            if psbt_only:
                try:
                    if svc.delete_secondary_draft_by_psbt(psbt_only):
                        return
                except Exception:
                    pass

            if purpose == 'inflate_asset':
                latest = svc.get_latest_active_secondary_draft()
                if isinstance(latest, dict) and latest.get('id') is not None:
                    svc.delete_ifa_secondary_draft(int(latest['id']))
        except Exception:
            pass

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
        """Sign PSBT and post back to multisig bridge via Service."""
        self.is_loading.emit(True)
        self.run_in_thread(
            BroadcastTransactionService.multisig_sign_and_post,
            {
                'args': [unsigned_psbt, operation_idx],
                'callback': self._on_multisig_post_success,
                'error_callback': self.on_error,
            },
        )

    def submit_multisig_signature(
        self, psbt_text: str, operation_idx: int | None,
    ) -> None:
        """Validate PSBT input then sign and post back to the multisig bridge."""
        psbt_text = psbt_text.strip() if psbt_text else ''
        if not psbt_text:
            ToastManager.error(description='No PSBT to sign')
            return
        self.sign_and_post_multisig(psbt_text, operation_idx)

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
        """NACK a pending operation without signing (human disagrees) via Service."""
        if operation_idx is None:
            ToastManager.error(
                description=INFO_OPERATION_INDEX_MISSING_FOR_NACK,
            )
            return
        self.is_reject_loading.emit(True)
        self.run_in_thread(
            BroadcastTransactionService.respond_nack,
            {
                'args': [operation_idx],
                'callback': self._on_nack_post_success,
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

    def trigger_full_inspection(self, psbt_text: str, operation=None):
        """Trigger PSBT inspection with optional operation context via Service."""
        # Reset previous state
        self.reset_inspection_state()
        self.is_loading.emit(True)

        def on_success(result):
            psbt_details, operation_context, rgb_details = result
            self.is_loading.emit(False)
            
            self.psbt_details = psbt_details
            self.operation_context = operation_context
            self.rgb_details = rgb_details

            # Emit typed signals
            if self.operation_context:
                self.operation_context_ready.emit(self.operation_context)
            
            self.psbt_data_ready.emit(self.psbt_details)
            self.signature_count_ready.emit(self.psbt_details.signature_count)
            
            if self.rgb_details:
                self.rgb_data_ready.emit(self.rgb_details)

            self._try_build_display_data()

        self.run_in_thread(
            BroadcastTransactionService.inspect_transaction,
            {
                'args': [psbt_text, operation],
                'callback': on_success,
                'error_callback': self.on_error,
            },
        )

    def inspect_psbt(self, psbt: str):
        """Inspect PSBT for review details using PsbtInspectionService."""
        self.run_in_thread(
            PsbtInspectionService.inspect_psbt,
            {
                'args': [psbt],
                'callback': self._on_inspect_psbt_success,
                'error_callback': self.on_error,
            },
        )

    # REMOVED inspect_rgb_transfer as it is now handled by the Service via full inspection


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

    def _on_inspect_psbt_success(self, result: PsbtInspectionResponseModel):
        """Handle typed PSBT inspection result from service."""
        self.is_loading.emit(False)
        self.psbt_details = result
        self.psbt_data_ready.emit(self.psbt_details)
        self.signature_count_ready.emit(self.psbt_details.signature_count)
        self._try_build_display_data()

    def _on_inspect_rgb_transfer_success(self, result: RgbInspectionResponseModel):
        """Handle typed RGB inspection result from service."""
        self.is_loading.emit(False)
        self.rgb_details = result
        self.rgb_data_ready.emit(self.rgb_details)
        self._try_build_display_data()

    def _on_fetch_pending_operation_success(self, result):
        """Process operation and emit typed context model."""
        if result and result.operation:
            self.operation_context = PsbtInspectionService.extract_operation_context(
                result.operation,
            )
            self.operation_context_ready.emit(self.operation_context)
            self._try_build_display_data()

    def _try_build_display_data(self):
        """Build and emit complete display data when PSBT details are ready."""
        if self.psbt_details is None:
            return

        self.display_data = PsbtInspectionService.build_display_data(
            self.psbt_details,
            self.operation_context,
            self.rgb_details,
        )
        self.display_data_ready.emit(self.display_data)

    def reset_inspection_state(self):
        """Reset all inspection state for a new PSBT."""
        self.psbt_details = None
        self.rgb_details = None
        self.operation_context = None
        self.display_data = None

    def _build_psbt_selection_items(
        self, drafts: list[dict],
    ) -> list[PsbtSelectionItemModel]:
        items: list[PsbtSelectionItemModel] = []
        for item in drafts:
            purpose = item.get('purpose') or 'psbt'
            psbt_id = item.get('id', '')
            display_title = (
                f"{purpose} ({psbt_id[:8]})" if psbt_id else purpose
            )
            items.append(
                PsbtSelectionItemModel(
                    id=str(psbt_id) if psbt_id is not None else '',
                    purpose=purpose,
                    psbt=item.get('psbt', ''),
                    display_title=display_title,
                ),
            )
        return items

    def _parse_psbt_input(self, psbt_text: str) -> tuple[str | None, str]:
        purpose = None
        signed_psbt = psbt_text.strip()
        if signed_psbt.startswith('psbt:'):
            parts = signed_psbt.split(':', 2)
            if len(parts) == 3:
                purpose, signed_psbt = parts[1], parts[2]
            elif len(parts) == 2:
                signed_psbt = parts[1]
        return purpose, signed_psbt

    def _resolve_purpose(
        self,
        explicit_purpose: str | None,
        signed: bool,
        selector_index: int,
    ) -> str | None:
        if explicit_purpose is not None:
            return explicit_purpose
        items = self._psbt_signed_items if signed else self._psbt_items
        if 0 <= selector_index < len(items):
            return items[selector_index].purpose
        return None
