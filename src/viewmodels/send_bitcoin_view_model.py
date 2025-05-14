"""This module contains the SendBitcoinViewModel class, which represents the view model
for the send bitcoin page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.enums.enums_model import NativeAuthType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_BITCOIN_SENT
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class SendBitcoinViewModel(QObject, ThreadManager):
    """This class represents the activities of the send bitcoin page."""
    send_button_clicked = Signal(bool)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.address = None
        self.amount = None
        self.fee_rate = None

    def on_send_click(self, address: str, amount: int, fee_rate: int):
        """"
        Executes the send_bitcoin method in a separate thread.
        This method starts a thread to execute the send_bitcoin function with the provided arguments.
        It emits a signal to indicate loading state and defines a callback for when the operation is successful.
        """
        self.address = address
        self.amount = amount
        self.fee_rate = fee_rate
        self.send_button_clicked.emit(True)
        self.run_in_thread(
            SettingRepository.native_authentication,
            {
                'args': [NativeAuthType.MAJOR_OPERATION],
                'callback': self.on_success_authentication_btc_send,
                'error_callback': self.on_error,
            },
        )

    def on_success_authentication_btc_send(self):
        """call back which send btc to address after success of authentication"""
        try:
            self.run_in_thread(
                BtcRepository.send_btc,
                {
                    'args': [
                        SendBtcRequestModel(
                            amount=self.amount, address=self.address, fee_rate=self.fee_rate,
                        ),
                    ],
                    'callback': self.on_success,
                    'error_callback': self.on_error,
                },
            )
        except Exception as exc:
            logger.error(
                'Exception occurred while sending btc: %s, Message: %s',
                type(exc).__name__, str(exc),
            )
            ToastManager.error(
                description=ERROR_SOMETHING_WENT_WRONG,
            )

    def on_success(self, response: SendBtcResponseModel) -> None:
        """This method is used  handle onsuccess for the send bitcoin page."""
        self.send_button_clicked.emit(False)
        ToastManager.success(
            description=INFO_BITCOIN_SENT.format(str(response.txid)),
        )
        self._page_navigation.bitcoin_page()

    def on_error(self, error: Exception) -> None:
        """This method is used  handle onerror for the send bitcoin page."""
        self.send_button_clicked.emit(False)
        logger.error(
            'Exception occurred while sending btc: %s, Message: %s',
            type(error).__name__, str(error),
        )
        description = error.message if isinstance(
            error, CommonException,
        ) else ERROR_SOMETHING_WENT_WRONG
        ToastManager.error(description=description)
