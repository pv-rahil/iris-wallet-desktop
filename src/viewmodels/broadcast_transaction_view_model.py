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
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.rgb_model import SendAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_BITCOIN_SENT
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
    signature_count_ready = Signal(int)
    combined_psbt_ready = Signal(str)

    def __init__(self, page_navigation) -> None:
        super().__init__()
        self._page_navigation = page_navigation

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
        """After signing, post the signed PSBT back to the bridge."""
        operation_idx = getattr(self, '_multisig_operation_idx', None)

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
        # Result is an Operation enum variant or int (if from post_create_utxos?)
        # post_create_utxos returns int (operation_idx) or similar? 
        # Actually RgbRepository.post_create_utxos likely returns the operation index or Operation object?
        
        res_str = str(result)
        # Check for Initiator success (might be just an ID or object)
        # Check for Signer success (Operation enum)
        if 'CREATE_UTXOS_COMPLETED' in res_str:
            ToastManager.success(description='Operation completed and finalized!')
        elif 'CREATE_UTXOS_PENDING' in res_str:
            ToastManager.success(description='Signed successfully. Waiting for other signers.')
        elif 'SEND_BTC_COMPLETED' in res_str:
            ToastManager.success(description='Bitcoin sent successfully!')
        elif 'SEND_BTC_PENDING' in res_str:
            ToastManager.success(description='Signed successfully. Waiting for other signers.')
        elif 'INFLATION_COMPLETED' in res_str:
            ToastManager.success(description='Asset issued/inflated successfully!')
        elif 'INFLATION_PENDING' in res_str:
            ToastManager.success(description='Signed successfully. Waiting for other signers.')
        elif 'SEND_COMPLETED' in res_str:  # For Asset Send
            ToastManager.success(description='Asset sent successfully!')
        elif 'SEND_PENDING' in res_str:    # For Asset Send
            ToastManager.success(description='Signed successfully. Waiting for other signers.')
        else:
            # Generic success for initiator or other cases
            ToastManager.success(description='Operation posted to bridge successfully.')
            logger.info('Multisig post result: %s', res_str)
