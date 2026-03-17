# pylint: disable=too-few-public-methods
"""ViewModel handling hardware device connection logic off the UI thread.

Encapsulates the background task to fetch Ledger xpubs/fingerprint and exposes
signals for the view/dialog to react to start, success and error.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MASTER_XPUB
from src.utils.ledger_hw_client import create_ledger_client
from src.utils.local_store import local_store
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class HWDeviceSelectionViewModel(QObject, ThreadManager):
    """Runs hardware device connect in background and emits results."""

    connect_succeeded = Signal()
    connect_failed = Signal(object)

    def __init__(self) -> None:
        super().__init__()

    def connect_to_device(self, device_info: dict, network: NetworkEnumModel) -> None:
        """Start background job to fetch xpubs/fingerprint for the given device."""
        self.run_in_thread(
            self._fetch_ledger_xpubs,
            {
                'args': [device_info, network],
                'callback': self.on_ledger_success,
                'error_callback': self.on_ledger_error,
            },
        )

    def _fetch_ledger_xpubs(self, device_info: dict, network: NetworkEnumModel):
        """Worker method executed off the UI thread.

        Returns: tuple (vanilla_xpub, colored_xpub, fingerprint, master_xpub)
        """
        try:
            if network == NetworkEnumModel.MAINNET:
                derivation_path = "m/86'/0'/0'"
                rgb_coin_type = "827166'"
            elif network == NetworkEnumModel.TESTNET:
                derivation_path = "m/86'/1'/0'"
                rgb_coin_type = "827167'"
            else:
                derivation_path = "m/86'/1'/0'"
                rgb_coin_type = "827167'"

            if network == NetworkEnumModel.MAINNET:
                replace_target = "0'/0'"
            else:
                replace_target = "1'/0'"

            vanilla = None
            colored = None
            fingerprint = None
            master_xpub = None

            try:
                client = create_ledger_client(device_info)
                vanilla = client.get_extended_pubkey(
                    derivation_path, display=True,
                )

                colored_path = derivation_path.replace(
                    replace_target,
                    rgb_coin_type + "/0'",
                )
                colored = client.get_extended_pubkey(
                    colored_path, display=True,
                )
                fingerprint = client.get_master_fingerprint().hex()
                return vanilla, colored, fingerprint, master_xpub
            finally:
                client.stop()
        except Exception as e:
            self.connect_failed.emit(str(e))
            return None, None, None, None

    def on_ledger_success(self, result):
        """
        Handle successful retrieval of xpubs and fingerprint from Ledger.
        """
        if result:
            vanilla, colored, fingerprint, master_xpub = result
            local_store.set_value(ACCOUNT_XPUB_VANILLA, vanilla)
            local_store.set_value(ACCOUNT_XPUB_COLORED, colored)
            local_store.set_value(MASTER_FINGERPRINT, fingerprint)

            # Only set master_xpub if it was fetched (multisig case)
            if master_xpub:
                local_store.set_value(MASTER_XPUB, master_xpub)

            self.connect_succeeded.emit()

    def on_ledger_error(self, error):
        """
        Handle error during Ledger xpub/fingerprint retrieval.
        """
        ToastManager.error(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'failed_to_fetch_xpubs',
            ).format(error),
        )
        self.connect_failed.emit(error)
