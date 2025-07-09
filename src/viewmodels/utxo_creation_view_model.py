"""
This module contains the UtxoCreationViewModel class, which manages the creation of UTXOs using a hardware wallet.
It provides a singleton interface and emits signals for UI updates and error handling during the UTXO creation process.
"""
from __future__ import annotations
from src.data.repository.btc_repository import BtcRepository
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.logging import logger

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.colored_wallet import colored_wallet
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import KeyStorageType
from src.model.rgb_model import CreateUtxosRequestModel
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.info_message import INFO_SIGN_FROM_HARDWARE_WALLET
from src.utils.info_message import INFO_TX_BROADCAST
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class UtxoCreationViewModel(QObject,ThreadManager):
    """
    ViewModel for creating UTXOs using a hardware wallet.
    Provides a singleton interface and emits signals for UI updates and error handling.
    """
    hw_dialog_update = Signal(str, object)
    utxo_created = Signal()
    psbt_finalized = Signal(str)
    utxo_required = Signal()

    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        """
        Returns the singleton instance of UtxoCreationViewModel.

        Args:
            parent: Optional parent QObject.
        Returns:
            UtxoCreationViewModel: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = UtxoCreationViewModel(parent)
        return cls._instance

    def __init__(self, parent=None):
        """
        Initializes the UtxoCreationViewModel.
        Use get_instance() to get the singleton instance.
        """
        self.is_hardware_wallet = SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET
        super().__init__(parent)

    @require_hardware_wallet_connected()
    def create_utxos_with_hardware_wallet(self, param:CreateUtxosRequestModel):
        """
        Creates UTXOs using the hardware wallet PSBT flow.
        - Calls create_utxos_begin to get the unsigned PSBT.
        - Signs and finalizes the PSBT with CommonOperationRepository.
        - Completes UTXO creation with create_utxos_end.
        Emits signals for dialog state and result.

        Args:
            online: Whether the wallet is online.
            up_to: Optional, up to value for UTXO creation.
            num: Optional, number of UTXOs to create.
            size: Optional, size of each UTXO.
            fee_rate: Optional, fee rate for the transaction.
            skip_sync: Optional, whether to skip sync after creation.
        Returns:
            The result of UTXO creation.
        Raises:
            Exception: If any error occurs during the process.
        """
        try:
            self.param:CreateUtxosRequestModel = param
            if self.is_hardware_wallet:
                self.create_utxos_begin()
            else:
                self.utxo_required.emit()
        except Exception as e:
            self.hw_dialog_update.emit(str(e), PsbtStatus.ERROR)
            self.error.emit(str(e))
            raise

    def create_utxos_begin(self):
        """
        Step 1: Create unsigned PSBT for UTXO creation in a worker thread.
        Emits utxo_begin_done(unsigned_psbt) on success.
        """
        self.run_in_thread(
            BtcRepository.create_utxos_begin,
            {
                'args': [self.param],
                'callback': self.on_utxo_begin_done,
                'error_callback': self.on_error,
            }
        )

    def on_utxo_begin_done(self, unsigned_psbt):
        self.hw_dialog_update.emit(
                    INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
                )
        self.sign_and_finalize_psbt(unsigned_psbt=unsigned_psbt)

    def sign_and_finalize_psbt(self, unsigned_psbt):
        """
        Step 2: Sign and finalize the PSBT in a worker thread.
        Emits utxo_signed_done(finalized_psbt) on success.
        """
        self.run_in_thread(
            CommonOperationRepository.sign_and_finalize_psbt,
            {
                'args': [unsigned_psbt],
                'callback': self.on_utxo_signed_done,
                'error_callback': self.on_error,
            }
        )

    def on_utxo_signed_done(self, finalized_psbt):
        if self.is_hardware_wallet:
            self.hw_dialog_update.emit(INFO_TX_BROADCAST,PsbtStatus.BROADCASTING)
            self.create_utxos_end(online=self.param.online,finalized_psbt=finalized_psbt,skip_sync=self.param.skip_sync)
        else:
            self.utxo_created.emit()
            self.psbt_finalized.emit(finalized_psbt)

    def create_utxos_end(self, online, finalized_psbt, skip_sync):
        """
        Step 3: Broadcast/finalize UTXO creation in a worker thread.
        Emits utxo_end_done(result) on success.
        """
        self.run_in_thread(
            BtcRepository.create_utxos_end,
            {
                'args': [online, finalized_psbt, skip_sync],
                'callback': self.on_utxo_end_done,
                'error_callback': self.on_error,
            }
        )

    def on_utxo_end_done(self):
        self.utxo_created.emit()

    def on_error(self, error: Exception) -> None:
        """This method is used  handle onerror for the utxo creation."""
        logger.error(
            'Exception occurred while utxo operation: %s, Message: %s',
            type(error).__name__, str(error),
        )
        if self.is_hardware_wallet:
            self.hw_dialog_update.emit(
                str(error), PsbtStatus.ERROR,
            )
        else:
            description = error.message if isinstance(
                error, CommonException,
            ) else ERROR_SOMETHING_WENT_WRONG
            ToastManager.error(description=description)