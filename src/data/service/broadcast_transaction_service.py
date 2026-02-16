from __future__ import annotations

from src.data.service.wallet_data_service import WalletDataService
from src.data.repository.setting_repository import SettingRepository
from src.data.repository.colored_wallet import colored_wallet
from src.model.broadcast_transaction_model import MultisigPendingContext
from src.model.broadcast_transaction_model import PsbtDraftItem
from src.model.broadcast_transaction_model import PsbtParsed
from src.model.broadcast_transaction_model import RgbTransferInspectionSummary
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.utils.constant import MASTER_XPUB
from src.utils.logging import logger
from src.utils.hardware_client_store import hardware_client_store
from src.utils.local_store import local_store


class BroadcastTransactionService:
    @staticmethod
    def list_psbt_drafts(is_signed: bool) -> list[PsbtDraftItem]:
        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return []
        rows = wallet_service.list_psbt(is_signed)
        items: list[PsbtDraftItem] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            psbt_id = row["id"]
            psbt = row["psbt"]
            signed = bool(row["signed"])
            purpose = row["purpose"]
            items.append(
                PsbtDraftItem(id=psbt_id, psbt=psbt, signed=signed, purpose=purpose),
            )
        return items

    @staticmethod
    def selector_titles(items: list[PsbtDraftItem]) -> list[str]:
        titles: list[str] = []
        for item in items:
            purpose = item.purpose or "psbt"
            psbt_id = item.id
            titles.append(f"{purpose} ({psbt_id[:8]})" if psbt_id else purpose)
        return titles

    @staticmethod
    def parse_psbt_input(text: str) -> PsbtParsed:
        psbt_text = (text or '').strip()
        purpose: str | None = None

        if psbt_text.startswith("psbt:"):
            parts = psbt_text.split(":", 2)
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
        if parsed.purpose:
            return parsed.purpose
        if selector_purpose:
            return selector_purpose
        return None

    @staticmethod
    def action_key(can_broadcast: bool, purpose: str | None) -> str:
        if not can_broadcast:
            return "sign"

        if purpose == "send_btc":
            return "send_btc"
        if purpose == "send_asset":
            return "send_asset"
        if purpose == "inflate_asset":
            return "inflate_asset"
        return "create_utxos"

    @staticmethod
    def selected_purpose(items: list[PsbtDraftItem], idx: int) -> str | None:
        if idx < 0 or idx >= len(items):
            return None
        return items[idx].purpose

    @staticmethod
    def receive_page_name_for_signed_psbt(psbt: str) -> str:
        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return "NIA page"
        signed = wallet_service.list_psbt(True)
        for row in signed:
            if not isinstance(row, dict):
                continue
            if row["psbt"] != psbt:
                continue
            if row["purpose"] == "inflate_asset":
                return "IFA secondary issuance"
            break
        return "NIA page"

    @staticmethod
    def cleanup_secondary_draft_if_any(psbt_text: str) -> None:
        wallet_service = WalletDataService.get_session()
        if wallet_service is None:
            return

        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        purpose = parsed.purpose
        psbt_only = parsed.psbt

        if purpose is not None and purpose != "inflate_asset":
            return

        if psbt_only:
            if wallet_service.delete_secondary_draft_by_psbt(psbt_only):
                return

        if purpose == "inflate_asset":
            latest = wallet_service.get_latest_active_secondary_draft()
            if latest is None:
                return
            draft_id = int(latest["id"])
            wallet_service.delete_ifa_secondary_draft(draft_id)

    @staticmethod
    def multisig_pending_context(operation_info: object) -> MultisigPendingContext | None:
        if operation_info is None:
            return None
        operation = operation_info.operation
        initiator_xpub = operation_info.initiator_xpub
        if operation is None:
            return None

        psbt = operation.psbt
        if psbt is None or psbt == "":
            return None

        local_xpub = local_store.get_value(MASTER_XPUB)
        is_initiator = bool(initiator_xpub and local_xpub and initiator_xpub == local_xpub)
        return MultisigPendingContext(psbt=psbt, is_initiator=is_initiator, operation=operation)

    @staticmethod
    def match_pending_operation(op_info: object, current_psbt: str) -> MultisigPendingContext | None:
        if op_info is None:
            return None
        if current_psbt is None or current_psbt == "":
            return None
        current_psbt_only = BroadcastTransactionService.parse_psbt_input(current_psbt).psbt
        if not current_psbt_only:
            return None
        pending = BroadcastTransactionService.multisig_pending_context(op_info)
        if pending is None:
            return None
        if pending.psbt != current_psbt_only:
            return None
        return pending

    @staticmethod
    def operation_transfer_type_key(operation: object) -> str | None:
        if operation.is_inflation_to_review():
            return "inflation"
        # RGB send (asset transfer)
        if operation.is_send_to_review():
            return "asset_transfer"
        # BTC send
        if operation.is_send_btc_to_review():
            return "btc_transfer"
        if operation.is_create_utxos_to_review():
            return "internal"
        return None

    @staticmethod
    def should_enable_action(has_input: bool, is_multisig: bool, is_psbt_validated: bool, pending_operation_present: bool) -> bool:
        if not has_input:
            return False
        if not is_multisig:
            return True
        return is_psbt_validated and pending_operation_present

    @staticmethod
    def is_rgb_purpose(purpose: str | None) -> bool:
        return purpose in ("send_asset", "inflate_asset")

    @staticmethod
    def set_rgb_mode_for_purpose(purpose: str | None) -> None:
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
                transfer_type_key = "asset_transfer"
            elif total_inflation_amount > 0:
                transfer_type_key = "inflation"

        return RgbTransferInspectionSummary(
            asset_id=str(asset_id) if asset_id else None,
            amount=int(amount_value),
            transfer_type_key=transfer_type_key,
        )

    @staticmethod
    def check_for_pending_multisig_navigation(view_model):
        """
        Checks if a multisig operation is pending (from latest sync) and navigates to the broadcast page
        if the wallet is watch-only and the operation is actionable (signed/pending).
        """
        if not colored_wallet.is_multisig:
            return

        # Check if watch-only
        if SettingRepository.get_wallet_access_type() != WalletAccessType.WATCH_ONLY:
            return

        # Use cached sync result from auto_sync_multisig.
        # Note: We rely on auto_sync_multisig having run recently (e.g. during page load).
        # auto_sync_multisig stores result in colored_wallet.latest_operation_info
        # If we removed that, we should probably manually sync here or restore it.
        # Given the task.md status "Use cached sync result", I should probably keep the 
        # storage in auto_sync_multisig or fetch it here.
        # Since I reverted auto_sync_multisig, I need to decide:
        # A) Re-add the cache line to auto_sync_multisig (safest for performance)
        # B) Call sync_with_bridge here (safer for "correctness" but slower)
        
        # User said "helper cant use colored wallet", implying the logic should be here.
        # Let's perform a lightweight check or rely on the cache if I restore it.
        # I WILL RESTORE THE CACHE FIELD IN auto_sync_multisig separately.
        
        op_info = getattr(colored_wallet, 'latest_operation_info', None)
        if not op_info or not getattr(op_info, 'operation', None):
            return

        # Check if already on broadcast page to avoid loops
        try:
            current_page = view_model.page_navigation.current_stack.get('name')
            if current_page == 'BroadcastTransactionWidget':
                return
        except Exception:
            pass

        # Navigate
        try:
            view_model.page_navigation.broadcast_transaction_page(pending_operation=op_info)

        except Exception as e:
            logger.error(f"Failed to navigate to broadcast page: {e}")

    @staticmethod
    def validate_multisig_post_condition(signed_psbt: str, expected_purpose: str) -> None:
        """
        Validates if the signed PSBT can be posted while a multisig operation is pending.
        Ensures the pending operation type matches the expected purpose.
        
        Args:
            signed_psbt (str): The signed PSBT base64.
            expected_purpose (str): The expected purpose of this PSBT (e.g. 'send_btc').
            
        Raises:
            CommonException: If validation fails (mismatch or blocking op with no match).
        """
        if not colored_wallet.is_multisig:
            return

        # 1. Check for pending operation
        op_info = getattr(colored_wallet, 'latest_operation_info', None)
        if not op_info or not getattr(op_info, 'operation', None):
            return

        if not is_blocking_operation(op_info.operation):
            return

        # 2. Pending Op Exists. Validate Matching Purpose.
        # Find the purpose of the pending operation (RGB Lib -> our keys)
        pending_key = BroadcastTransactionService.operation_transfer_type_key(op_info.operation)
        
        # Map expected_purpose to internal keys
        expected_key = None
        if expected_purpose == 'send_btc':
            expected_key = 'btc_transfer'
        elif expected_purpose == 'send_asset':
            expected_key = 'asset_transfer'
        elif expected_purpose == 'inflate_asset':
            expected_key = 'inflation'
        elif expected_purpose == 'create_utxos':
            expected_key = 'internal'
            
        if pending_key != expected_key:
            logger.warning(
                "Blocked post attempt: Pending op '%s' does not match expected '%s' ('%s')",
                pending_key, expected_key, expected_purpose
            )
            raise CommonException(
                "A different multisig operation is already pending or under review. "
                "Please complete it before proceeding."
            )
