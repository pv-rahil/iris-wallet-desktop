"""Helper functions for viewmodel operations."""
from __future__ import annotations

import json
import os

from rgb_lib import RespondToOperation

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.hardware_client_store import hardware_client_store
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_POST_TO_BRIDGE
from src.utils.info_message import INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.views.components.toast import ToastManager


def restore_multisig_config_from_file(file_path: str) -> bool:
    """
    Restore multisig configuration from a JSON file.

    Args:
        file_path: Path to the multisig configuration JSON file.

    Returns:
        True if configuration was restored successfully, False otherwise.
    """
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, encoding='utf-8') as mf:
            multisig_data = json.load(mf)

        SettingRepository.set_wallet_signature_type(
            WalletSignatureType.MULTI_SIG_WALLET,
        )
        SettingRepository.set_multisig_config(
            multisig_data.get('required_signers'),
            multisig_data.get('total_signers'),
        )
        SettingRepository.set_cosigners(
            multisig_data.get('cosigners', []),
        )
        SettingRepository.set_threshold_confirmed(True)
        return True
    except Exception:
        return False


def extract_psbt_result(result, is_multisig: bool) -> tuple:
    """
    Extract PSBT and operation index from result based on wallet type.

    Args:
        result: The result object from PSBT creation.
        is_multisig: Whether the wallet is multisig.

    Returns:
        tuple of (unsigned_psbt, operation_idx).
    """
    if is_multisig:
        return result.psbt, result.operation_idx
    return result, None


def extract_psbt_and_operation_idx(result, is_multisig: bool) -> tuple:
    """
    Extract PSBT and operation index from result based on wallet type.

    Args:
        result: The result object from PSBT creation.
        is_multisig: Whether the wallet is multisig.

    Returns:
        tuple of (unsigned_psbt, operation_idx).
    """
    if is_multisig:
        return result.psbt, result.operation_idx
    return result.psbt, None


def handle_hardware_wallet_signing(
    viewmodel, is_hw: bool, is_online: bool,
    is_multisig: bool, is_on_device: bool,
    button_signal=None,
):
    """
    Handle hardware wallet signing setup.

    Args:
        viewmodel: The viewmodel instance.
        is_hw: Whether hardware wallet is used.
        is_online: Whether wallet is online.
        is_multisig: Whether wallet is multisig.
        is_on_device: Whether key storage is on device.
        button_signal: Optional signal to emit when button clicked.
    """

    if is_hw and is_online and not is_multisig or is_multisig and is_on_device:
        viewmodel.hw_dialog_update.emit(
            INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
        )
        if button_signal:
            button_signal.emit(True)
        hardware_client_store.set_rgb_mode(True)
    elif is_hw and is_multisig:
        viewmodel.hw_dialog_update.emit(
            INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
        )
        if button_signal:
            button_signal.emit(True)
        hardware_client_store.set_rgb_mode(True)


def sign_psbt_for_multisig(viewmodel, unsigned_psbt: str, _operation_idx: str):
    """
    Sign PSBT for multisig wallet and post to bridge.

    Args:
        viewmodel: The viewmodel instance.
        unsigned_psbt: The unsigned PSBT.
        operation_idx: The operation index.
    """

    viewmodel.run_in_thread(
        CommonOperationRepository.sign_psbt,
        {
            'args': [unsigned_psbt],
            'callback': viewmodel.on_multisig_psbt_signed,
            'error_callback': viewmodel.on_error,
        },
    )


def sign_and_finalize_psbt(viewmodel, unsigned_psbt: str, callback_name: str = 'on_psbt_signed_and_finalized_success'):
    """
    Sign and finalize PSBT for standard wallet.

    Args:
        viewmodel: The viewmodel instance.
        unsigned_psbt: The unsigned PSBT.
        callback_name: Name of the callback method on viewmodel.
    """
    callback = getattr(viewmodel, callback_name)
    viewmodel.run_in_thread(
        CommonOperationRepository.sign_and_finalize_psbt,
        {
            'args': [unsigned_psbt],
            'callback': callback,
            'error_callback': viewmodel.on_error,
        },
    )


def post_signed_psbt_to_bridge(viewmodel, signed_psbt: str, operation_idx: str | None):
    """
    Post signed PSBT to bridge for multisig.

    Args:
        viewmodel: The viewmodel instance.
        signed_psbt: The signed PSBT.
        operation_idx: The operation index.
    """

    viewmodel.hw_dialog_update.emit(
        INFO_POST_TO_BRIDGE, PsbtStatus.BROADCASTING,
    )
    viewmodel.run_in_thread(
        RgbRepository.respond_to_operation,
        {
            'args': [operation_idx, RespondToOperation.ACK(signed_psbt)],
            'callback': viewmodel.on_success_multisig_post,
            'error_callback': viewmodel.on_error,
        },
    )


def process_psbt_result(viewmodel, result, is_multisig: bool, button_signal=None):
    """
    Process PSBT result: extract data, check watch-only, handle HW signing, and sign/finalize.

    Args:
        viewmodel: The viewmodel instance.
        result: The result object from PSBT creation.
        is_multisig: Whether the wallet is multisig.
        button_signal: Optional signal to emit when processing (e.g., send_button_clicked).

    Returns:
        tuple of (unsigned_psbt, should_continue) where should_continue is False if watch-only.
    """
    unsigned_psbt, operation_idx = extract_psbt_result(result, is_multisig)
    viewmodel.operation_idx = operation_idx

    if button_signal:
        button_signal.emit(True)

    if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
        viewmodel.unsigned_psbt.emit(unsigned_psbt)
        return unsigned_psbt, False

    is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
    is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
    is_on_device = SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE

    handle_hardware_wallet_signing(
        viewmodel, is_hw, is_online, is_multisig, is_on_device,
    )

    if is_multisig:
        sign_psbt_for_multisig(viewmodel, unsigned_psbt, operation_idx)
    else:
        sign_and_finalize_psbt(viewmodel, unsigned_psbt)

    return unsigned_psbt, True


def handle_viewmodel_error(viewmodel, error) -> None:
    """
    Handle errors in viewmodels consistently.

    Args:
        viewmodel: The viewmodel instance.
        error: The error that occurred.
    """

    if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET or \
            SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
        viewmodel.hw_dialog_update.emit(
            str(error), PsbtStatus.ERROR,
        )
    else:
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)


def on_success_multisig_post_base(viewmodel, success_callback=None):
    """
    Base implementation for handling success of multisig post.

    Args:
        viewmodel: The viewmodel instance with hw_dialog_update signal and run_in_thread method.
        success_callback: Optional callback to run after sync (receives sync result).
    """
    viewmodel.hw_dialog_update.emit(None, PsbtStatus.SUCCESS)
    ToastManager.success(INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE)

    # Sync with bridge again
    viewmodel.run_in_thread(
        RgbRepository.sync_with_hub,
        {
            'callback': success_callback or (lambda _: None),
            'error_callback': success_callback or (lambda _: None),
        },
    )
