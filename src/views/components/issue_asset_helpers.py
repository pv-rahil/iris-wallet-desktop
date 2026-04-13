"""Helper functions for asset issue operations."""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.decorators.check_colorable_available import get_unspent_utxo_count
from src.utils.info_message import INFO_UTXO_CREATION_REQUIRED_FOR_ISSUING
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.toast import ToastManager


def get_wallet_type_flags() -> tuple[bool, bool]:
    """
    Get wallet type flags for issue asset pages.

    Returns:
        tuple of (is_multisig_wallet, is_offline_wallet).
    """
    is_multisig_wallet = SettingRepository.get_wallet_signature_type(
    ) == WalletSignatureType.MULTI_SIG_WALLET
    is_offline_wallet = SettingRepository.get_wallet_type(
    ) == WalletType.OFFLINE_TYPE_WALLET
    return is_multisig_wallet, is_offline_wallet


def show_multisig_psbt_toast_and_close(close_callback) -> None:
    """
    Show PSBT created toast for multisig wallet and close the page.

    Args:
        close_callback: The close callback function to execute.
    """
    ToastManager.success(
        QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_created_successfully', 'PSBT created successfully',
        ),
    )
    close_callback()


def show_utxo_confirmation_dialog(
    parent,
    dialog_active: bool,
    set_dialog_active,
) -> tuple[bool, bool]:
    """
    Show confirmation dialog for UTXO creation in multisig/watch-only wallets.

    Args:
        parent: The parent widget for the dialog.
        dialog_active: Whether a dialog is already active (skip if True).
        set_dialog_active: Callback to set dialog active state (bool) -> None.

    Returns:
        tuple of (should_proceed, dialog_was_shown):
            - should_proceed: True if the operation should continue
            - dialog_was_shown: True if a dialog was displayed
    """
    if dialog_active:
        return False, False

    if not (
        SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
    ):
        return True, False

    # Set flag to prevent dialog stacking
    set_dialog_active(True)

    dialog = ConfirmationDialog(
        message=INFO_UTXO_CREATION_REQUIRED_FOR_ISSUING,
        parent=parent,
        icon_type='info',
    )
    accepted = dialog.exec() == QDialog.Accepted

    # Reset flag after dialog closes
    set_dialog_active(False)

    return accepted, True


def create_utxos_for_issue(
    parent,
    purpose: str,
    utxo_viewmodel,
    dialog_active: bool,
    set_dialog_active,
    needed: int = 1,
) -> bool:
    """
    Create UTXOs for asset issuing with confirmation dialog for multisig/watch-only wallets.

    Args:
        parent: The parent widget.
        purpose: The purpose string (e.g., 'issue_asset_cfa', 'issue_asset_nia').
        utxo_viewmodel: The UTXO creation viewmodel.
        dialog_active: Whether a dialog is already active.
        set_dialog_active: Callback to set dialog active state.
        needed: Number of UTXOs needed.

    Returns:
        True if UTXO creation was initiated, False if dialog was rejected.
    """
    accepted, _ = show_utxo_confirmation_dialog(
        parent, dialog_active, set_dialog_active,
    )
    if not accepted:
        return False
    utxo_viewmodel.create_utxos_begin(purpose, needed)
    return True


def compute_needed_utxos(current_count: int, required: int = 1) -> int:
    """
    Compute the number of UTXOs needed.

    Args:
        current_count: Current number of unspent UTXOs.
        required: Required number of UTXOs.

    Returns:
        Number of UTXOs to create (minimum 1).
    """
    needed = required - current_count
    return needed if needed > 0 else 1


def compute_needed_utxos_for_ifa() -> int:
    """
    Compute the number of UTXOs needed for IFA operations.
    For single-sig online wallets, creates only 1 UTXO.
    For other wallet types, creates UTXOs based on current count and needed amount.

    Args:
        needed_utxos: Number of UTXOs needed for the operation (2 for issue, 3 for inflate).

    Returns:
        Number of UTXOs to create (minimum 1).
    """
    # For single-sig online wallets, create only 1 UTXO
    is_single_sig_online = (
        SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.STANDARD_TYPE_WALLET
        and SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET and 
        not SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
    )
    if is_single_sig_online:
        return 1
    current = get_unspent_utxo_count()
    needed = 2 - max(0, current)
    return needed if needed > 0 else 1
