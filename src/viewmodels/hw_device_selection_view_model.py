# pylint: disable=too-few-public-methods
"""ViewModel handling hardware device connection logic off the UI thread.

Encapsulates the background task to fetch Ledger xpubs/fingerprint and exposes
signals for the view/dialog to react to start, success and error.
"""
from __future__ import annotations

from hwilib.common import Chain
from hwilib.devices.ledger import LedgerClient
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MASTER_XPUB
from src.utils.local_store import local_store
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class HWDeviceSelectionViewModel(QObject, ThreadManager):
    """Runs hardware device connect in background and emits results."""

    connect_succeeded = Signal()
    connect_failed = Signal(object)

    def __init__(self) -> None:
        super().__init__()

    def connect_to_device(self, device_path: str, network: NetworkEnumModel, is_multisig: bool = False) -> None:
        """Start background job to fetch xpubs/fingerprint for the given device."""
        self.run_in_thread(
            self._fetch_ledger_xpubs,
            {
                'args': [device_path, network, is_multisig],
                'callback': self.on_ledger_success,
                'error_callback': self.on_ledger_error,
            },
        )

    def _fetch_ledger_xpubs(self, device_path: str, network: NetworkEnumModel, is_multisig: bool = False):
        """Worker method executed off the UI thread.

        Returns: tuple (vanilla_xpub, colored_xpub, fingerprint)
        """
        try:
            if network == NetworkEnumModel.MAINNET:
                chain = Chain.MAIN
                # BIP-48: m/48'/0'/0'/2' for Mainnet Native Segwit Multisig
                multisig_path = 'm/48h/0h/0h/2h'
            elif network == NetworkEnumModel.TESTNET:
                chain = Chain.TEST
                # BIP-48: m/48'/1'/0'/2' for Testnet Native Segwit Multisig
                multisig_path = 'm/48h/1h/0h/2h'
            else:
                chain = Chain.REGTEST
                # BIP-48: m/48'/1'/0'/2' for Regtest Native Segwit Multisig (using testnet coin type)
                multisig_path = 'm/48h/1h/0h/2h'

            client = LedgerClient(device_path, None, True, chain)

            if is_multisig:

                multisig_colored_path = multisig_path.replace(
                    '0h/2h', '827167h/2h',
                )

                vanilla = client.get_pubkey_at_path(multisig_path).to_string()
                colored = client.get_pubkey_at_path(
                    multisig_colored_path,
                ).to_string()
            else:
                vanilla = client.get_pubkey_at_path('m/86h/1h/0h').to_string()
                colored = client.get_pubkey_at_path(
                    'm/86h/827167h/0h',
                ).to_string()

            fingerprint = client.get_master_fingerprint().hex()

            # Fetch Master XPUB (required for biscuit auth / bridge token)
            # Only required for multisig setups where we need the master xpub for authentication
            master_xpub = None
            if is_multisig:
                # Path 'm' corresponds to the root extended public key of the device's seed.
                master_xpub = client.get_pubkey_at_path('m').to_string()

            return vanilla, colored, fingerprint, master_xpub
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
