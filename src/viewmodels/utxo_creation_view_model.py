# pylint: disable=too-many-function-args
"""
This module contains the UtxoCreationViewModel class, which manages the creation of UTXOs using a hardware wallet.
Provides a singleton interface and emits signals for UI updates and error handling during the UTXO creation process.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import CreateUtxosRequestModel
from src.model.setting_model import DefaultFeeRate
from src.utils.constant import NO_OF_UTXO
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_POST_TO_BRIDGE
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.logging import logger
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class UtxoCreationViewModel(QObject, ThreadManager):
    """
    ViewModel for creating UTXOs using a hardware wallet.
    Provides a singleton interface and emits signals for UI updates and error handling.
    """
    hw_dialog_update = Signal(str, object)
    utxo_created = Signal(bool)
    unsigned_psbt = Signal(str)
    psbt_posted_to_bridge = Signal()

    def __init__(self, parent=None):
        """
        Initializes the UtxoCreationViewModel.
        Sets up hardware wallet detection and Qt object for signal/slot functionality.
        """
        super().__init__(parent)
        self.param: CreateUtxosRequestModel = None
        self.current_purpose: str | None = None

    def _is_multisig(self) -> bool:
        """Check if current wallet is multisig."""
        return SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET

    def create_utxos_begin(self, purpose: str | None = None, num: int = NO_OF_UTXO):
        """
        Create unsigned PSBT for UTXO creation in a worker thread.
        Generates an unsigned PSBT that will be used to create new UTXOs.
        """
        default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        self.current_purpose = purpose
        self.param = CreateUtxosRequestModel(
            online=colored_wallet.online,
            fee_rate=default_fee_rate.fee_rate,
            num=num,
        )
        self.run_in_thread(
            BtcRepository.create_utxos_begin,
            {
                'args': [self.param, purpose],
                'callback': self.on_utxo_begin_done,
                'error_callback': self.on_error,
            },
        )

    def on_utxo_begin_done(self, unsigned_psbt):
        """Callback when unsigned PSBT is created. Updates dialog and starts signing process."""
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET and \
                SettingRepository.get_wallet_type() == WalletType.ONLINE_TYPE_WALLET or self._is_multisig():
            self.hw_dialog_update.emit(
                INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
            )
            if self._is_multisig():
                self.sign_psbt_for_multisig(unsigned_psbt)
            else:
                self.sign_and_finalize_psbt(unsigned_psbt)
        else:
            self.unsigned_psbt.emit(unsigned_psbt)

    def sign_psbt_for_multisig(self, unsigned_psbt):
        """
        Sign the PSBT for multisig wallet (partial signature, not finalized).
        """
        self.run_in_thread(
            CommonOperationRepository.sign_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self.on_multisig_psbt_signed,
                'error_callback': self.on_error,
            },
        )

    def on_multisig_psbt_signed(self, signed_psbt):
        """
        Post signed PSBT to multisig bridge for other signers to approve.
        """
        self.hw_dialog_update.emit(
            INFO_POST_TO_BRIDGE, PsbtStatus.BROADCASTING,
        )
        self.run_in_thread(
            BtcRepository.post_create_utxos,
            {
                'args': [signed_psbt],
                'callback': self.on_psbt_posted_to_bridge,
                'error_callback': self.on_error,
            },
        )

    def on_psbt_posted_to_bridge(self):
        """Callback when PSBT is posted to bridge. Emits signal for UI to show waiting state."""
        self.psbt_posted_to_bridge.emit()

    def sign_and_finalize_psbt(self, unsigned_psbt):
        """
        Sign and finalize the PSBT in a worker thread.
        Signs the PSBT with hardware wallet and finalizes the transaction.
        """
        self.run_in_thread(
            CommonOperationRepository.sign_and_finalize_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self.on_utxo_signed_done,
                'error_callback': self.on_error,
            },
        )

    def on_utxo_signed_done(self, finalized_psbt):
        """Callback when PSBT is signed. Updates dialog and starts broadcasting or emits PSBT for offline wallets."""
        self.hw_dialog_update.emit(
            INFO_TX_BROADCAST, PsbtStatus.BROADCASTING,
        )
        self.create_utxos_end(
            finalized_psbt=finalized_psbt,
        )

    def create_utxos_end(self, finalized_psbt):
        """
        Broadcast/finalize UTXO creation in a worker thread.
        Broadcasts the finalized PSBT to complete UTXO creation.
        """
        request = BroadcastPsbtRequestModel(
            online=self.param.online,
            signed_psbt=finalized_psbt,
            skip_sync=self.param.skip_sync,
        )
        self.run_in_thread(
            BtcRepository.create_utxos_end,
            {
                'args': [request],
                'callback': self.on_utxo_end_done,
                'error_callback': self.on_error,
            },
        )

    def on_utxo_end_done(self):
        """Callback when UTXO creation is completed. Emits utxo_created signal."""
        self.utxo_created.emit(True)

    def on_error(self, error: Exception) -> None:
        """Handles errors during UTXO creation. Updates dialog for hardware wallets or shows toast for others."""
        logger.error(
            'Exception occurred while utxo operation: %s, Message: %s',
            type(error).__name__, str(error),
        )
        if SettingRepository.get_key_storage_type() != KeyStorageType.HARDWARE_WALLET and not self._is_multisig():
            description = error.message if isinstance(
                error, CommonException,
            ) else ERROR_SOMETHING_WENT_WRONG
            ToastManager.error(description=description)
        else:
            self.hw_dialog_update.emit(
                str(error), PsbtStatus.ERROR,
            )
