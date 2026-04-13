"""Hardware wallet helpers for IFA asset operations."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog

from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.utils.error_message import ERROR_NOT_ENOUGH_UNCOLORED
from src.utils.info_message import INFO_UTXO_CREATION_REQUIRED_FOR_ISSUING
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.issue_asset_helpers import compute_needed_utxos_for_ifa


def handle_utxo_error(
    message: str,
    parent_widget,
    utxo_dialog_active: bool,
    secondary_issuance: bool,
    utxo_creation_view_model,
) -> tuple[bool, bool]:
    """Handle UTXO error case.

    Args:
        message: The error message.
        parent_widget: The parent widget for dialogs.
        utxo_dialog_active: Whether UTXO dialog is already active.
        secondary_issuance: Whether this is secondary issuance.
        utxo_creation_view_model: The UTXO creation view model.

    Returns:
        Tuple of (handled, retry_after_utxo_inflate).
    """

    if 'NoAvailableUtxos' not in message and ERROR_NOT_ENOUGH_UNCOLORED not in message:
        return False, False
    # Show confirmation dialog for multisig/watch-only wallets
    if (
        SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
    ):
        if utxo_dialog_active:
            return True, False
        utxo_dialog_active = True
        dialog = ConfirmationDialog(
            message=INFO_UTXO_CREATION_REQUIRED_FOR_ISSUING,
            parent=parent_widget,
            icon_type='info',
        )
        accepted = dialog.exec() == QDialog.Accepted
        if not accepted:
            return True, False
    retry_after_utxo_inflate = bool(secondary_issuance)
    utxo_purpose = 'inflation_utxo' if secondary_issuance else 'issue_asset_ifa'
    # 3 UTXOs needed for inflate, 2 for issue
    needed = compute_needed_utxos_for_ifa()
    utxo_creation_view_model.create_utxos_begin(
        purpose=utxo_purpose, num=needed,
    )
    return True, retry_after_utxo_inflate


def handle_success_dialog(
    ifa_hw_dialog: HardwareWalletOperationDialog,
    secondary_issuance: bool,
    params,
) -> bool:
    """Handle success dialog case.

    Args:
        ifa_hw_dialog: The hardware wallet dialog instance.
        secondary_issuance: Whether this is secondary issuance.
        params: The RgbAssetPageLoadModel params.

    Returns:
        True if handled.
    """
    if ifa_hw_dialog.isVisible():
        ifa_hw_dialog.accept()
    try:
        if secondary_issuance and params is not None:
            svc = WalletDataService.get_session()
            if svc is not None:
                active = None
                if params.asset_id:
                    active = svc.get_active_secondary_draft_for_asset(
                        params.asset_id,
                    )
                if active and active.get('id'):
                    draft_id = active.get('id')
                    svc.delete_ifa_secondary_draft(
                        int(draft_id) if draft_id else 0,
                    )
    except Exception:
        pass
    return True


def close_hw_dialog_if_open(
    parent_widget,
) -> None:
    """Close the hardware wallet dialog if it is currently visible.

    Args:
        parent_widget: The parent widget.
    """
    ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
        parent=parent_widget,
    )
    if ifa_hw_dialog.isVisible():
        ifa_hw_dialog.accept()


def delete_active_secondary_draft_on_success(
    secondary_issuance: bool,
    params,
) -> None:
    """Delete active secondary draft on success.

    Args:
        secondary_issuance: Whether this is secondary issuance.
        params: The RgbAssetPageLoadModel params.
    """
    if not secondary_issuance:
        return
    if not params or not params.asset_id:
        return
    svc = WalletDataService.get_session()
    if svc is None:
        return
    active = svc.get_active_secondary_draft_for_asset(
        params.asset_id,
    )
    if isinstance(active, dict):
        draft_id = active.get('id')
        if draft_id is not None:
            svc.delete_ifa_secondary_draft(int(draft_id))
