"""
Service for handling broadcast transaction operations, including PSBT management,
multisig coordination, and RGB asset transfers.
"""
from __future__ import annotations

from src.data.service.wallet_data_service import WalletDataService
from src.model.broadcast_transaction_model import MultisigPendingContext
from src.model.broadcast_transaction_model import PsbtDraftItem
from src.model.broadcast_transaction_model import PsbtParsed
from src.model.broadcast_transaction_model import RgbTransferInspectionSummary
from src.utils.constant import MASTER_XPUB
from src.utils.hardware_client_store import hardware_client_store
from src.utils.local_store import local_store
from PySide6.QtCore import QCoreApplication
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.model.common_operation_model import ReceiveAssetModel
from src.model.broadcast_transaction_model import (
    MultisigPendingContext, PsbtDraftItem, PsbtParsed, RgbTransferInspectionSummary,
    PendingOperationMatchResult, InspectionContext, PsbtTextChangedContext,
    RenderInspectionResult, SignatureProgressContext,
)

class BroadcastTransactionService:
    """Service class for managing broadcast transaction logic and PSBT operations."""

    @staticmethod
    def list_psbt_drafts(is_signed: bool) -> list[PsbtDraftItem]:
        """List PSBT drafts from the wallet service."""

        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return []
        rows = wallet_service.list_psbt(is_signed)
        items: list[PsbtDraftItem] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            psbt_id = row['id']
            psbt = row['psbt']
            signed = bool(row['signed'])
            purpose = row['purpose']
            fascia_path = row.get('fascia_path')
            entropy = row.get('entropy')
            min_confirmations = row.get('min_confirmations')
            items.append(
                PsbtDraftItem(
                    id=psbt_id, psbt=psbt,
                    signed=signed, purpose=purpose,
                    fascia_path=fascia_path,
                    entropy=entropy,
                    min_confirmations=min_confirmations,
                ),
            )
        return items

    @staticmethod
    def selector_titles(items: list[PsbtDraftItem]) -> list[str]:
        """Generate display titles for the draft items."""

        titles: list[str] = []
        for item in items:
            purpose = item.purpose or 'psbt'
            psbt_id = item.id
            titles.append(f"{purpose} ({psbt_id[:8]})" if psbt_id else purpose)
        return titles

    @staticmethod
    def parse_psbt_input(text: str) -> PsbtParsed:
        """Parse raw PSBT input text (handles psbt: prefix and whitespace)."""

        psbt_text = (text or '').strip()
        purpose: str | None = None

        if psbt_text.startswith('psbt:'):
            parts = psbt_text.split(':', 2)
            if len(parts) == 3:
                purpose = parts[1] or None
                psbt_text = parts[2]
            elif len(parts) == 2:
                psbt_text = parts[1]

        # Base64 PSBTs are sometimes pasted with newlines/spaces; normalize them.
        normalized_psbt = ''.join(psbt_text.split())
        return PsbtParsed(psbt=normalized_psbt, purpose=purpose)

    @staticmethod
    def resolve_purpose(parsed: PsbtParsed, selector_purpose: str | None) -> str | None:
        """Resolve the purpose of the PSBT."""

        if parsed.purpose:
            return parsed.purpose
        if selector_purpose:
            return selector_purpose
        return None

    @staticmethod
    def action_key(can_broadcast: bool, purpose: str | None) -> str:
        """Determine the action key based on broadcast capability and purpose."""

        if not can_broadcast:
            return 'sign'

        if purpose == 'send_btc':
            return 'send_btc'
        if purpose == 'send_asset':
            return 'send_asset'
        if purpose in ('inflate_asset', 'inflation'):
            return 'inflation'
        return 'create_utxos'

    @staticmethod
    def selected_purpose(items: list[PsbtDraftItem], idx: int) -> str | None:
        """Get the purpose of the selected item."""

        if idx < 0 or idx >= len(items):
            return None
        return items[idx].purpose

    @staticmethod
    def receive_page_name_for_signed_psbt(psbt: str) -> str:
        """Determine the target page name for a signed PSBT."""

        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return 'NIA page'
        signed = wallet_service.list_psbt(True)
        for row in signed:
            if not isinstance(row, dict):
                continue
            if row['psbt'] != psbt:
                continue
            if row['purpose'] in ('inflate_asset', 'inflation'):
                return 'IFA secondary issuance'
            break
        return 'NIA page'

    @staticmethod
    def cleanup_secondary_draft_if_any(psbt_text: str, explicit_purpose: str | None = None) -> None:
        """Clean up secondary draft (IFA) if applicable."""

        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return

        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        purpose = explicit_purpose or parsed.purpose
        psbt_only = parsed.psbt

        if purpose is not None and purpose not in ('inflate_asset', 'inflation'):
            return

        if psbt_only:
            if wallet_service.delete_secondary_draft_by_psbt(psbt_only):
                return

        if purpose in ('inflate_asset', 'inflation'):
            latest = wallet_service.get_latest_active_secondary_draft()
            if latest is None:
                return
            draft_id = int(latest['id'])
            wallet_service.delete_ifa_secondary_draft(draft_id)

    @staticmethod
    def multisig_pending_context(operation_info: object) -> MultisigPendingContext | None:
        """Create a pending context from operation info."""

        if operation_info is None:
            return None
        operation = operation_info.operation
        initiator_xpub = operation_info.initiator_xpub
        if operation is None:
            return None

        psbt = operation.psbt
        if psbt is None or psbt == '':
            return None

        local_xpub = local_store.get_value(MASTER_XPUB)
        is_initiator = bool(
            initiator_xpub and local_xpub and initiator_xpub == local_xpub,
        )
        return MultisigPendingContext(psbt=psbt, is_initiator=is_initiator, operation=operation)

    @staticmethod
    def match_pending_operation(op_info: object, current_psbt: str) -> MultisigPendingContext | None:
        """Match a pending operation with a current PSBT."""

        if op_info is None:
            return None
        if current_psbt is None or current_psbt == '':
            return None
        current_psbt_only = BroadcastTransactionService.parse_psbt_input(
            current_psbt,
        ).psbt
        if not current_psbt_only:
            return None
        pending = BroadcastTransactionService.multisig_pending_context(op_info)
        if pending is None:
            return None
        if pending.psbt != current_psbt_only:
            return None
        return pending

    # Global state for pending operation (populated by HeaderFrameViewModel)
    _pending_operation_info: object | None = None
    _pending_operation_txid: str | None = None

    @classmethod
    def set_pending_operation_state(cls, op_info: object, txid: str | None) -> None:
        """Set the global pending operation state."""
        cls._pending_operation_info = op_info
        cls._pending_operation_txid = txid

    @classmethod
    def get_pending_operation_state(cls) -> tuple[object | None, str | None]:
        """Get the global pending operation state."""
        return cls._pending_operation_info, cls._pending_operation_txid

    @staticmethod
    def match_pending_operation_by_txid(op_info: object, current_psbt_txid: str) -> MultisigPendingContext | None:
        """Match a pending operation by TXID."""

        if op_info is None or not current_psbt_txid:
            return None
        pending = BroadcastTransactionService.multisig_pending_context(op_info)
        if pending is None:
            return None
        return pending

    @staticmethod
    def operation_transfer_type_key(operation: object) -> str | None:
        """Extract transfer_type_key if this is an RGB transfer operation."""
        if operation.is_INFLATION_TO_REVIEW():
            return 'inflate_asset'
        if operation.is_SEND_TO_REVIEW():
            return 'send_asset'
        # BTC send
        if operation.is_SEND_BTC_TO_REVIEW():
            return 'send_btc'
        if operation.is_CREATE_UTXOS_TO_REVIEW():
            return 'create_utxos'
        return None

    @staticmethod
    def should_enable_action(
        has_input: bool, is_multisig: bool, is_psbt_validated: bool, pending_operation_present: bool,
    ) -> bool:
        """Determine if the action button should be enabled."""

        if not has_input:
            return False
        if not is_multisig:
            return True
        return is_psbt_validated and pending_operation_present

    @staticmethod
    def is_rgb_purpose(purpose: str | None) -> bool:
        """Check if the purpose is related to RGB."""

        return purpose in ('send_asset', 'inflate_asset', 'inflation')

    @staticmethod
    def set_rgb_mode_for_purpose(purpose: str | None) -> None:
        """Set the hardware client RGB mode based on purpose."""

        hardware_client_store.set_rgb_mode(
            BroadcastTransactionService.is_rgb_purpose(purpose),
        )

    @staticmethod
    def rgb_transfer_inspection_summary(
        rgb_details: object,
        pending_transfer_type_key: str | None,
    ) -> RgbTransferInspectionSummary:
        """Extract (asset_id, amount, transfer_type_key) from an rgb-lib inspection.

        The UI should not need to understand rgb-lib internal structures.
        """
        if rgb_details is None:
            return RgbTransferInspectionSummary(
                asset_id=None,
                amount=0,
                transfer_type_key=pending_transfer_type_key,
            )

        asset_id: str | None = None
        send_amount = 0
        total_inflation_amount = 0

        try:
            operations = rgb_details.operations
            if operations:
                op_info = operations[0]
                asset_id = op_info.asset_id

                for transition in op_info.transitions:
                    for output in transition.outputs:
                        assignment = output.assignment
                        if assignment is not None and assignment.is_FUNGIBLE():
                            amt = assignment.amount
                            total_inflation_amount += amt
                            if not output.is_ours:
                                send_amount += amt
        except Exception:
            asset_id = None
            send_amount = 0
            total_inflation_amount = 0

        amount_value = 0
        if send_amount > 0:
            amount_value = send_amount
        elif total_inflation_amount > 0:
            amount_value = total_inflation_amount

        transfer_type_key = pending_transfer_type_key
        if transfer_type_key is None:
            if send_amount > 0:
                transfer_type_key = 'asset_transfer'
            elif total_inflation_amount > 0:
                transfer_type_key = 'inflation'

        return RgbTransferInspectionSummary(
            asset_id=str(asset_id) if asset_id else None,
            amount=int(amount_value),
            transfer_type_key=transfer_type_key,
        )

    @staticmethod
    def get_psbt_purpose_from_storage(psbt_base64: str) -> str | None:
        """Fetch purpose stored for this PSBT in the local wallet DB (if any)."""
        psbt_norm = (psbt_base64 or '').strip()
        if not psbt_norm:
            return None
        try:
            service = WalletDataService.get_session()
            if not service:
                return None

            # Check both unsigned and signed rows.
            for signed in (0, 1):
                cur = service.conn.cursor()
                cur.execute(
                    'SELECT purpose FROM psbt WHERE signed = ? AND psbt = ? LIMIT 1',
                    (signed, psbt_norm),
                )
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
            return None
        except Exception:
            return None

    @staticmethod
    def get_psbt_rgb_context(psbt_base64: str) -> dict | None:
        """Fetch RGB context (fascia_path, entropy, min_confirmations) for a PSBT from storage.
        
        Used by offline wallets to display RGB asset details during PSBT signing.
        """
        psbt_norm = (psbt_base64 or '').strip()
        if not psbt_norm:
            return None
        try:
            service = WalletDataService.get_session()
            if not service:
                return None
            return service.get_psbt_rgb_context(psbt_norm)
        except Exception:
            return None

    @staticmethod
    def resolve_transfer_type(
        psbt_text: str,
        is_multisig: bool,
        explicit_type: str | None = None,
        is_inflation: bool = False,
    ) -> str | None:
        """Centralized logic to determine the transfer type key for UI labeling."""
        if is_inflation:
            return 'inflation'
        if explicit_type:
            return explicit_type

        if is_multisig:
            parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
            if parsed.purpose:
                return parsed.purpose
            # Fallback to storage lookup if no purpose prefix
            storage_purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(
                parsed.psbt,
            )
            return storage_purpose or 'send_btc'

        return None

    @staticmethod
    def get_transfer_type_label(key: str | None) -> str:
        """Return translated transfer type label with fallback."""
        if key is None:
            return ''
        translated = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, key,
        )
        if translated and translated != key:
            return translated

        fallback_labels = {
            'internal': 'Internal',
            'btc_transfer': 'BTC transfer',
            'inflation': 'Inflation',
            'asset_transfer': 'Asset transfer',
            'send_btc': 'Send BTC',
            'send_asset': 'Send Asset',
            'create_utxos': 'Internal',
            'issue_asset_cfa': 'Internal',
            'issue_asset_nia': 'Internal',
            'issue_asset_ifa': 'Internal',
            'inflation_utxo': 'Internal',
            'send_rgb': 'Internal',
            'inflate_asset': 'Inflation',
        }
        return fallback_labels.get(key, key or '')

    @staticmethod
    def can_enable_primary_action(
        psbt_text: str,
        can_broadcast: bool,
        is_multisig: bool,
        is_psbt_validated: bool,
        pending_operation_present: bool,
        is_watch_only: bool,
        selector_index: int,
        selector_visible: bool,
        is_offline_mode: bool,
        min_psbt_len: int,
    ) -> bool:
        """Determine if the primary action button should be enabled."""
        has_input = bool(psbt_text) and (
            len(psbt_text.strip()) >= min_psbt_len
        )
        if not has_input:
            return False

        if can_broadcast:
            if is_multisig and is_watch_only:
                return is_psbt_validated and pending_operation_present

            method_ok = (not selector_visible) or (selector_index >= 0)
            return method_ok

        # Signer flow
        if is_multisig:
            has_purpose = False
            if is_offline_mode:
                parsed = BroadcastTransactionService.parse_psbt_input(
                    psbt_text.strip(),
                )
                has_purpose = bool(parsed.purpose) or bool(
                    BroadcastTransactionService.get_psbt_purpose_from_storage(
                        parsed.psbt,
                    ),
                )

            return (is_psbt_validated and pending_operation_present) or (
                is_offline_mode and (has_purpose or is_psbt_validated)
            )

        return True

    @staticmethod
    def can_enable_reject_action(
        can_broadcast: bool,
        is_multisig: bool,
        is_psbt_validated: bool,
        pending_operation_present: bool,
        is_watch_only: bool,
    ) -> bool:
        """Determine if the reject button should be enabled."""
        if is_multisig:
            if can_broadcast and is_watch_only:
                return is_psbt_validated and pending_operation_present
            return pending_operation_present
        return False

    @staticmethod
    def psbts_loaded_data(items: list[PsbtDraftItem], is_signed: bool) -> dict:
        """Prepare data needed for the UI after PSBTs are loaded."""
        if len(items) == 0:
            return {'has_items': False}

        if len(items) == 1:
            return {
                'has_items': True,
                'is_single': True,
                'psbt': items[0].psbt,
            }

        label_key = 'select_psbt_for_broadcast' if is_signed else 'select_psbt_for_sign'
        titles = BroadcastTransactionService.selector_titles(items)

        return {
            'has_items': True,
            'is_single': False,
            'label_key': label_key,
            'titles': titles,
        }

    @staticmethod
    def receive_asset_model_for_signed_psbt(psbt: str) -> object:
        """Create the appropriate model for navigating to the receive asset page."""
        page_name = BroadcastTransactionService.receive_page_name_for_signed_psbt(
            psbt,
        )
        return ReceiveAssetModel(
            page_name=page_name,
            address_info='psbt_info',
            psbt=psbt,
            is_signed=True,
        )

    @staticmethod
    def multisig_sign_loading_data(pending_op_ctx: object) -> dict:
        """Prepare data needed for loading multisig signed PSBTs."""
        pending = BroadcastTransactionService.multisig_pending_context(
            pending_op_ctx,
        )
        if pending is None:
            return {'has_pending': False}

        return {
            'has_pending': True,
            'is_initiator': pending.is_initiator,
            'psbt': pending.psbt,
            'operation': pending.operation,
        }

    @staticmethod
    def get_retranslate_data(can_broadcast: bool, is_multisig: bool, is_watch_only: bool = False) -> dict:
        """Get translated strings for the UI."""
        if can_broadcast:
            title = 'broadcast_transaction'
            label = 'broadcast_transaction_label'
            button = 'broadcast_transaction'
        elif is_multisig and is_watch_only:
            # Watch-only multisig can only respond/post, not sign
            title = 'respond_to_multisig'
            label = 'respond_to_multisig_label'
            button = 'post_to_multisig'
        else:
            title = 'sign_psbt'
            label = 'sign_psbt_label'
            button = 'sign_psbt'

        data = {
            'title': QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, title),
            'label': QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, label),
            'button': QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, button),
        }

        if is_multisig:
            data['subtitle'] = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'paste_or_import_psbt',
            )

        return data

    @staticmethod
    def process_pending_operation_match(
        pending: MultisigPendingContext | None,
        op_info: object,
        is_watch_only: bool,
    ) -> PendingOperationMatchResult | None:
        """Process the pending operation matching and extract context data."""
        from rgb_lib import Operation

        if pending is None:
            return None

        operation = pending.operation
        transfer_type = BroadcastTransactionService.operation_transfer_type_key(operation)
        is_inflation = (transfer_type == 'inflation')

        should_trigger_rgb_inspection = False
        fascia_path = None
        entropy = 0

        DETAILS_OPERATIONS = (
            Operation.SEND_TO_REVIEW,
            Operation.SEND_PENDING,
            Operation.SEND_COMPLETED,
            Operation.SEND_DISCARDED,
            Operation.INFLATION_TO_REVIEW,
            Operation.INFLATION_PENDING,
            Operation.INFLATION_COMPLETED,
            Operation.INFLATION_DISCARDED,
            Operation.BLIND_RECEIVE_COMPLETED,
            Operation.WITNESS_RECEIVE_COMPLETED,
        )

        if is_watch_only and isinstance(operation, DETAILS_OPERATIONS):
            op_ctx = operation.details
            if op_ctx and hasattr(op_ctx, 'fascia_path') and op_ctx.fascia_path:
                should_trigger_rgb_inspection = True
                fascia_path = op_ctx.fascia_path
                entropy = op_ctx.entropy if (hasattr(op_ctx, 'entropy') and op_ctx.entropy is not None) else 0

        ack_count = 0
        threshold = None
        if operation.status is not None and operation.status.acked_by is not None and operation.status.threshold is not None:
            ack_count = len(operation.status.acked_by)
            threshold = operation.status.threshold

        return PendingOperationMatchResult(
            operation=operation,
            pending_operation=op_info,
            transfer_type=transfer_type,
            is_inflation=is_inflation,
            should_trigger_rgb_inspection=should_trigger_rgb_inspection,
            fascia_path=fascia_path,
            entropy=entropy,
            is_initiator=pending.is_initiator,
            ack_count=ack_count,
            threshold=threshold,
        )

    @staticmethod
    def resolve_inspection_context(
        operation: object | None,
        parsed_purpose: str | None,
        psbt_body: str,
        current_rgb_expected: bool,
    ) -> InspectionContext:
        """Resolve the inspection context based on the operation and PSBT purpose."""
        is_inflation = False
        rgb_expected = False
        if operation:
            if hasattr(operation, 'is_INFLATION_TO_REVIEW'):
                is_inflation = operation.is_INFLATION_TO_REVIEW()
            if hasattr(operation, 'is_SEND_TO_REVIEW'):
                rgb_expected = operation.is_SEND_TO_REVIEW() or is_inflation
        else:
            purpose = parsed_purpose or BroadcastTransactionService.get_psbt_purpose_from_storage(psbt_body)
            is_inflation = purpose in ('inflate_asset', 'inflation')
            rgb_expected = purpose in ('send_asset', 'inflate_asset', 'inflation') or current_rgb_expected

        return InspectionContext(
            is_inflation=is_inflation,
            rgb_expected=rgb_expected,
        )

    @staticmethod
    def resolve_purpose_for_signing(
        parsed_purpose: str | None,
        operation: object | None,
        psbt: str,
    ) -> str | None:
        """Resolve the purpose for the signing action."""
        purpose = parsed_purpose
        if not purpose and operation:
            purpose = BroadcastTransactionService.operation_transfer_type_key(operation)
        if not purpose:
            purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(psbt)
        return purpose

    @staticmethod
    def prepare_psbt_text_changed_state(
        psbt_text: str,
        last_inspected_psbt: str | None,
        min_psbt_len: int,
    ) -> PsbtTextChangedContext:
        """Parse the input PSBT and prepare context variables for _on_psbt_text_changed."""
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        psbt_body = parsed.psbt
        
        is_same_as_last = (last_inspected_psbt == psbt_body)
        should_inspect = bool(psbt_body and len(psbt_body) >= min_psbt_len)
        
        is_rgb = False
        is_inflation = False
        purpose = None
        
        if should_inspect:
            is_rgb = BroadcastTransactionService.is_rgb_purpose(parsed.purpose)
            is_inflation = (parsed.purpose == 'inflation')
            purpose = parsed.purpose

        return PsbtTextChangedContext(
            is_same_as_last=is_same_as_last,
            should_inspect=should_inspect,
            psbt_body=psbt_body,
            is_rgb=is_rgb,
            is_inflation=is_inflation,
            purpose=purpose,
        )

    @staticmethod
    def prepare_render_inspection_state(
        psbt_details: object | None,
        is_multisig_rgb_expected: bool,
        rgb_details: object | None,
        is_offline_wallet: bool,
        current_psbt: str,
        min_psbt_len: int,
    ) -> RenderInspectionResult:
        """Determine if we should render the inspection details and prepare UI signals."""
        if psbt_details is None:
            return RenderInspectionResult(should_render=False, should_show_sign_status=False)

        if is_multisig_rgb_expected and rgb_details is None:
            return RenderInspectionResult(should_render=False, should_show_sign_status=False)

        if not current_psbt or len(current_psbt) < min_psbt_len:
            return RenderInspectionResult(should_render=False, should_show_sign_status=False)

        should_show_sign_status = not is_offline_wallet
        return RenderInspectionResult(
            should_render=True,
            should_show_sign_status=should_show_sign_status,
        )

    @staticmethod
    def prepare_signature_progress_ui_state(
        current_psbt: str | None,
        min_psbt_len: int,
        current_operation: object | None,
    ) -> SignatureProgressContext:
        """Context variables for rendering missing signature progress UI."""
        has_valid_psbt = current_psbt is not None and len(current_psbt) >= min_psbt_len
        should_trigger_direct = False
        
        if current_operation and current_psbt:
            if hasattr(current_operation, 'psbt') and current_operation.psbt == current_psbt:
                should_trigger_direct = True
                
        return SignatureProgressContext(
            has_valid_psbt=has_valid_psbt,
            should_trigger_direct=should_trigger_direct,
        )

    @staticmethod
    def prepare_psbt_export_content(psbt_text: str) -> tuple[str, str] | None:
        """Prepare PSBT content for export with purpose prefix.

        Args:
            psbt_text: The PSBT text to prepare

        Returns:
            Tuple of (export_text, purpose) or None if invalid
        """
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        purpose = parsed.purpose
        current_psbt = parsed.psbt
        if not current_psbt:
            return None

        if purpose is None:
            purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(current_psbt)

        export_text = current_psbt
        if purpose:
            export_text = f"psbt:{purpose}:{current_psbt}"

        return export_text, purpose

    @staticmethod
    def read_psbt_from_file(file_path: str) -> tuple[str, str | None] | None:
        """Read and parse PSBT from file.

        Args:
            file_path: Path to the PSBT file

        Returns:
            Tuple of (psbt_content, error_message) or None on success
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                text = (f.read() or '').strip()

            parsed = BroadcastTransactionService.parse_psbt_input(text)
            psbt_only = parsed.psbt
            if not psbt_only:
                return None, 'Invalid PSBT file content'
            return psbt_only, None
        except Exception as e:
            return None, f'Failed to read PSBT file: {e}'

    @staticmethod
    def write_psbt_to_file(file_path: str, content: str) -> str | None:
        """Write PSBT content to file.

        Args:
            file_path: Path to write to
            content: PSBT content to write

        Returns:
            Error message or None on success
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return None
        except Exception as e:
            return f'Failed to write PSBT file: {e}'
