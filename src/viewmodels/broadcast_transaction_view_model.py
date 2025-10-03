"""
ViewModel for handling the broadcasting of signed PSBT transactions (Bitcoin and RGB) in the application.
Provides methods for broadcasting, error handling, and UI feedback for transaction-related operations.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

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
from src.utils.info_message import INFO_ASSET_SENT, INFO_BITCOIN_SENT
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
        ToastManager.success(description=INFO_BITCOIN_SENT.format(response.tx_id))

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

    # def analyze_signature_count(self, psbt: str):
    #     """Count signatures in psbt in a worker thread and emit a signal when ready."""
    #     self.run_in_thread(
    #         CommonOperationRepository.count_partial_signatures,
    #         {
    #             'args': [psbt],
    #             'callback': lambda count: self.signature_count_ready.emit(count),
    #             'error_callback': self.on_error,
    #         },
    #     )

    # def combine_psbts(self, psbts: list[str]):
    #     """Combine multiple PSBTs and emit the combined PSBT when ready."""
    #     self.is_loading.emit(True)
    #     self.run_in_thread(
    #         CommonOperationRepository.combine_psbts,
    #         {
    #             'args': [psbts],
    #             'callback': self.on_combine_success,
    #             'error_callback': self.on_error,
    #         },
    #     )

    # def on_combine_success(self, combined: str):
    #     self.is_loading.emit(False)
    #     self.combined_psbt_ready.emit(combined)
