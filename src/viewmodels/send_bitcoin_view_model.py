"""This module contains the SendBitcoinViewModel class, which represents the view model
for the send bitcoin page activities.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.hardware_client_store import hardware_client_store
from src.utils.info_message import INFO_BITCOIN_SENT
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_POST_TO_BRIDGE
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class SendBitcoinViewModel(QObject, ThreadManager):
    """This class represents the activities of the send bitcoin page."""
    send_button_clicked = Signal(bool)
    hw_dialog_update = Signal(object, Enum)
    unsigned_psbt = Signal(str)

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
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                None,
                PsbtStatus.SUCCESS,
            )
        ToastManager.success(
            description=INFO_BITCOIN_SENT.format(str(response.tx_id)),
        )
        self._page_navigation.bitcoin_page()

    def on_error(self, error: Exception) -> None:
        """This method is used  handle onerror for the send bitcoin page."""
        self.send_button_clicked.emit(False)
        logger.error(
            'Exception occurred while sending btc: %s, Message: %s',
            type(error).__name__, str(error),
        )
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                str(error), PsbtStatus.ERROR,
            )
        else:
            description = error.message if isinstance(
                error, CommonException,
            ) else ERROR_SOMETHING_WENT_WRONG
            ToastManager.error(description=description)

    def send_btc_begin(self, address: str, amount: int, fee_rate: int, skip_sync: bool = False):
        """
        Begin the process of sending BTC by creating a PSBT.
        Calls BtcRepository.send_btc_begin and expects a PSBT to be signed externally.
        """
        self.address = address
        self.amount = amount
        self.fee_rate = fee_rate
        self.send_button_clicked.emit(True)
        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
        if is_hw and is_online or SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTISIG:
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
        request = SendBtcRequestModel(
            address=address, amount=amount, fee_rate=fee_rate, skip_sync=skip_sync,
        )
        self.run_in_thread(
            BtcRepository.send_btc_begin,
            {
                'args': [request],
                'callback': self.on_psbt_created,
                'error_callback': self.on_error,
            },
        )

    def on_psbt_created(self, unsigned_psbt: str):
        """
        Handle the PSBT created by send_btc_begin.
        Run signing and finalization in a background thread.
        """
        self.send_button_clicked.emit(True)
        if SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
            self.unsigned_psbt.emit(unsigned_psbt)
            return

        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET

        if is_hw and is_online:
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )

        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTISIG:
            self.run_in_thread(
                CommonOperationRepository.sign_psbt,
                {
                    'args': [unsigned_psbt],
                    'callback': self.on_multisig_psbt_signed,
                    'error_callback': self.on_error,
                },
            )
        else:
            self.run_in_thread(
                CommonOperationRepository.sign_and_finalize_psbt,
                {
                    'args': [unsigned_psbt],
                    'callback': self.on_psbt_signed_and_finalized,
                    'error_callback': self.on_error,
                },
            )

    def on_multisig_psbt_signed(self, signed_psbt: str):
        """
        Callback after multisig PSBT is signed (partially).
        Now post to bridge.
        """
        self.hw_dialog_update.emit(
            INFO_POST_TO_BRIDGE, PsbtStatus.BROADCASTING,
        )
        self.run_in_thread(
            BtcRepository.post_send_btc,
            {
                'args': [signed_psbt],
                'callback': self.on_success_multisig_post,
                'error_callback': self.on_error,
            },
        )

    def on_success_multisig_post(self, _=None):
        """Handle success of multisig post"""
        # Close the dialog
        self.hw_dialog_update.emit(None, PsbtStatus.SUCCESS)
        
        ToastManager.success(INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE)
        
        # Sync with bridge again as requested
        self.run_in_thread(
            RgbRepository.sync_with_bridge,
            {
                'callback': lambda _: self._page_navigation.bitcoin_page(),
                'error_callback': lambda _: self._page_navigation.bitcoin_page(), 
            }
        )

    def on_psbt_signed_and_finalized(self, finalized_psbt: str):
        """
        Callback after PSBT is signed and finalized.
        Now broadcast the transaction.
        """
        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
        
        if is_hw and is_online:
            self.hw_dialog_update.emit(
                INFO_TX_BROADCAST, PsbtStatus.BROADCASTING,
            )
            self.send_btc_end(finalized_psbt)

    def send_btc_end(self, signed_psbt: str, skip_sync: bool = False):
        """
        Finalize and broadcast the signed PSBT.
        Calls BtcRepository.send_btc_end to broadcast the transaction.
        """
        self.send_button_clicked.emit(True)
        request = BroadcastPsbtRequestModel(
            signed_psbt=signed_psbt, skip_sync=skip_sync,
        )
        self.run_in_thread(
            BtcRepository.send_btc_end,
            {
                'args': [request],
                'callback': self.on_success,
                'error_callback': self.on_error,
            },
        )

    def cancel_operation(self):
        """
        Called when the user clicks Cancel on the hardware wallet dialog.
        Sets a cancel flag and emits stop_sign_tx_loader to close the dialog.
        """
        self.send_button_clicked.emit(False)
        hardware_client_store.stop_client()
