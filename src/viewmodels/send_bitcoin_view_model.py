"""This module contains the SendBitcoinViewModel class, which represents the view model
for the send bitcoin page activities.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NativeAuthType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.hardware_client_store import hardware_client_store
from src.utils.info_message import INFO_BITCOIN_SENT
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.info_message import INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.viewmodels.viewmodel_helpers import handle_viewmodel_error
from src.viewmodels.viewmodel_helpers import post_signed_psbt_to_bridge
from src.viewmodels.viewmodel_helpers import process_psbt_result
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
        self.operation_idx: str | None = None

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

        # Check if native auth is required for multisig or on-device key variants
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        is_on_device = SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET

        # Native auth required for: multisig on-device, or online on-device (non-multisig)
        requires_native_auth = (is_multisig and is_on_device) or (
            is_online and is_on_device and not is_multisig
        )

        if requires_native_auth:
            self.run_in_thread(
                SettingRepository.native_authentication,
                {
                    'args': [NativeAuthType.MAJOR_OPERATION],
                    'callback': self.on_success_authentication_btc_send,
                    'error_callback': self.on_error,
                },
            )
        else:
            self._proceed_with_send_btc()

    def _proceed_with_send_btc(self):
        """Proceed with sending BTC after native auth or directly for non-auth variants."""
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

    def on_success_authentication_btc_send(self, success: bool):
        """call back which send btc to address after success of authentication"""
        if success:
            self._proceed_with_send_btc()
        else:
            self.send_button_clicked.emit(False)
            ToastManager.error(description=ERROR_AUTHENTICATION_CANCELLED)

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
        handle_viewmodel_error(self, error)

    def send_btc_begin(self, address: str, amount: int, fee_rate: int, skip_sync: bool = False):
        """
        Begin the process of sending BTC by creating a PSBT.
        Calls BtcRepository.send_btc_begin and expects a PSBT to be signed externally.
        """
        self.address = address
        self.amount = amount
        self.fee_rate = fee_rate
        self.send_button_clicked.emit(True)

        # Check if native auth is required for multisig or on-device key variants
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        is_on_device = SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET

        # Native auth required for: multisig on-device, or online on-device (non-multisig)
        requires_native_auth = (is_multisig and is_on_device) or (
            is_online and is_on_device and not is_multisig
        )

        if requires_native_auth:
            self.run_in_thread(
                SettingRepository.native_authentication,
                {
                    'args': [NativeAuthType.MAJOR_OPERATION],
                    'callback': self._on_success_native_auth_send_btc_begin,
                    'error_callback': self.on_error,
                },
            )
        else:
            self._proceed_with_send_btc_begin(skip_sync)

    def _on_success_native_auth_send_btc_begin(self, success: bool):
        """Callback after native auth success for send_btc_begin."""
        if success:
            self._proceed_with_send_btc_begin(skip_sync=False)
        else:
            self.send_button_clicked.emit(False)
            ToastManager.error(description=ERROR_AUTHENTICATION_CANCELLED)

    def _proceed_with_send_btc_begin(self, skip_sync: bool):
        """Proceed with PSBT creation after native auth check."""
        is_hw = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        is_online = SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET
        if (is_hw and is_online and SettingRepository.get_wallet_signature_type() == WalletSignatureType.STANDARD_TYPE_WALLET) or (
            SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET and
                SettingRepository.get_key_storage_type() == KeyStorageType.ON_DEVICE
        ):
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
        elif is_hw and SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.hw_dialog_update.emit(
                INFO_REGISTER_WALLET_AND_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
        request = SendBtcRequestModel(
            address=self.address, amount=self.amount, fee_rate=self.fee_rate, skip_sync=skip_sync,
        )
        if SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET:
            self.run_in_thread(
                BtcRepository.send_btc_init,
                {
                    'args': [request],
                    'callback': self.on_psbt_creation_success,
                    'error_callback': self.on_error,
                },
            )
        else:
            self.run_in_thread(
                BtcRepository.send_btc_begin,
                {
                    'args': [request],
                    'callback': self.on_psbt_creation_success,
                    'error_callback': self.on_error,
                },
            )

    def on_psbt_creation_success(self, result):
        """
        Handle the PSBT created by send_btc_begin.
        Run signing and finalization in a background thread.
        """
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        process_psbt_result(
            self, result, is_multisig,
            self.send_button_clicked,
        )

    def on_multisig_psbt_signed(self, signed_psbt: str):
        """
        Callback after multisig PSBT is signed (partially).
        Now post to bridge.
        """
        post_signed_psbt_to_bridge(self, signed_psbt, self.operation_idx)

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
            },
        )

    def on_psbt_signed_and_finalized_success(self, finalized_psbt: str):
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
