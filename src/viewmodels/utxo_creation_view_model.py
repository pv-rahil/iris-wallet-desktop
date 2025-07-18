# pylint: disable=too-many-function-args
"""
This module contains the UtxoCreationViewModel class, which manages the creation of UTXOs using a hardware wallet.
Provides a singleton interface and emits signals for UI updates and error handling during the UTXO creation process.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.rgb_model import CreateUtxosRequestModel
from src.utils.custom_exception import CommonException
from src.utils.decorators.require_hardware_wallet_connected import require_hardware_wallet_connected
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
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
    utxo_created = Signal()
    psbt_finalized = Signal(str)
    utxo_required = Signal()
    utxo_creation_started = Signal()

    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        """
        Returns the singleton instance of UtxoCreationViewModel.
        Ensures only one instance exists throughout the application lifecycle.
        """
        if cls._instance is None:
            cls._instance = UtxoCreationViewModel(parent)
        return cls._instance

    def __init__(self, parent=None):
        """
        Initializes the UtxoCreationViewModel.
        Sets up hardware wallet detection and Qt object for signal/slot functionality.
        """
        super().__init__(parent)
        self.param: CreateUtxosRequestModel = None

    @require_hardware_wallet_connected()
    def create_utxos_with_hardware_wallet(self, param: CreateUtxosRequestModel):
        """
        Initiates UTXO creation using the hardware wallet PSBT flow.
        Starts the PSBT creation process or emits utxo_required signal if hardware wallet not connected.
        """
        try:
            self.param = param
            if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
                self.create_utxos_begin()
            else:
                self.utxo_required.emit()
        except Exception as e:
            self.hw_dialog_update.emit(str(e), PsbtStatus.ERROR)
            self.error.emit(str(e))
            raise

    def create_utxos_begin(self):
        """
        Create unsigned PSBT for UTXO creation in a worker thread.
        Generates an unsigned PSBT that will be used to create new UTXOs.
        """
        self.run_in_thread(
            BtcRepository.create_utxos_begin,
            {
                'args': [self.param],
                'callback': self.on_utxo_begin_done,
                'error_callback': self.on_error,
            },
        )

    def on_utxo_begin_done(self, unsigned_psbt):
        """Callback when unsigned PSBT is created. Updates dialog and starts signing process."""
        self.hw_dialog_update.emit(
            INFO_SIGN_FROM_HARDWARE_WALLET, PsbtStatus.SIGNING,
        )
        self.sign_and_finalize_psbt(unsigned_psbt)

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
        if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET:
            self.hw_dialog_update.emit(
                INFO_TX_BROADCAST, PsbtStatus.BROADCASTING,
            )
            self.create_utxos_end(
                finalized_psbt=finalized_psbt,
            )
        else:
            self.utxo_created.emit()
            self.psbt_finalized.emit(finalized_psbt)

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
        self.utxo_created.emit()

    def on_error(self, error: Exception) -> None:
        """Handles errors during UTXO creation. Updates dialog for hardware wallets or shows toast for others."""
        logger.error(
            'Exception occurred while utxo operation: %s, Message: %s',
            type(error).__name__, str(error),
        )
        if SettingRepository.get_key_storage_type() != KeyStorageType.HARDWARE_WALLET:
            description = error.message if isinstance(
                error, CommonException,
            ) else ERROR_SOMETHING_WENT_WRONG
            ToastManager.error(description=description)
        else:
            self.hw_dialog_update.emit(
                str(error), PsbtStatus.ERROR,
            )
