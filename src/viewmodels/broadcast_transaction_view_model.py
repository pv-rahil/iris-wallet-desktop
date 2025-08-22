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
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.rgb_model import SendAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_BTC_SENT
from src.utils.info_message import INFO_UTXO_CREATED
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class BroadcastTransactionViewModel(QObject, ThreadManager):
    """
    ViewModel for broadcasting signed PSBT transactions.
    """
    is_loading = Signal(bool)
    tx_broadcasted = Signal(bool)

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

    def finalized_psbt(self, signed_psbt):
        """finalize psbt"""
        self.run_in_thread(
            CommonOperationRepository.sign_and_finalize_psbt,
            {
                'args': [signed_psbt],
                'error_callback': self.on_error,
            },
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
        ToastManager.success(description=INFO_UTXO_CREATED)

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
        ToastManager.success(description=INFO_BTC_SENT.format(response.tx_id))
