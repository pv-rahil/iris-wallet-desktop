"""
Provides a globally accessible `colored_wallet` object that manages
the RGB wallet and online state using the `rgb-lib` library.

This module exposes a singleton-like instance of `ColoredWallet`,
allowing centralized access and control of the wallet lifecycle,
online connectivity, and initialization data (such as for backup/restore).
It behaves similarly to the `app_paths` pattern used for file paths.
"""
from __future__ import annotations

import rgb_lib
from rgb_lib import RgbLibError
from src.flavour import __app_name_suffix__

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletSignatureType
from src.utils.constant import MULTISIG_BRIDGE_URL,MULTISIG_1_TOKEN,MULTISIG_2_TOKEN,MULTISIG_3_TOKEN
from src.utils.custom_exception import CommonException
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.logging import logger


class ColoredWallet:
    """
    Manages the RGB wallet and online session state, including secure
    loading/saving of initialization data.

    Attributes:
        wallet (rgb_lib.Wallet | rgb_lib.MultisigWallet): The active RGB wallet instance.
        online (rgb_lib.Online): The current online session.
    """

    def __init__(self):
        self._wallet: rgb_lib.Wallet | rgb_lib.MultisigWallet | None = None
        self.online_wallet: rgb_lib.Online | None = None
        self.is_multisig = (
                SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET
            )

    @property
    def wallet(self) -> rgb_lib.Wallet | rgb_lib.MultisigWallet:
        """
        Returns the initialized wallet instance (standard or multisig).

        Raises:
            RuntimeError: If the wallet is not yet set.
        """
        if self._wallet is None:
            raise CommonException('Wallet not initialized')
        return self._wallet

    def set_wallet(self, wallet: rgb_lib.Wallet | rgb_lib.MultisigWallet):
        """Sets the wallet instance (standard or multisig)."""
        self._wallet = wallet

    @property
    def online(self) -> rgb_lib.Online:
        """
        Lazily initializes and returns the online session for the current wallet.

        This method ensures the wallet is initialized, fetches the appropriate
        indexer URL based on the network, and establishes the online session.
        Subsequent calls return the already-initialized session.

        Returns:
            rgb_lib.Online: The active online session.

        Raises:
            RuntimeError: If the wallet is not initialized.
        """
        if self.online_wallet is None:
            if self._wallet is None:
                raise CommonException(
                    'Wallet must be initialized before going online.',
                )

            try:
                network = get_bitcoin_network_from_enum(
                    SettingRepository.get_wallet_network(),
                )
                indexer_url = get_bitcoin_config(network, '').indexer_url
                if self.is_multisig:
                    bridge_token = self.get_multisig_bridge_token()
                    self.online_wallet = self._wallet.go_online(indexer_url, MULTISIG_BRIDGE_URL, bridge_token)
                else:
                    self.online_wallet = self._wallet.go_online(False, indexer_url)
            except Exception as exc:
                logger.error(
                    'Failed to go online: %s, Message: %s',
                    type(exc).__name__,
                    str(exc),
                )
                raise CommonException(
                    'Failed to initialize online session', {
                        'name': type(exc).__name__,
                        'original_exception': str(exc),
                    },
                ) from exc
        return self.online_wallet

    def go_online_again(self, indexer_url: str) -> None:
        """
        Calls `go_online` with a new indexer URL, and if successful,
        updates the online session.

        Args:
            indexer_url (str): The new indexer URL to use.
        """
        if self._wallet:
            try:
                self.online_wallet = self._wallet.go_online(True, indexer_url)
            except RgbLibError.InvalidIndexer:
                raise
            except Exception as exc:
                logger.error(
                    'Failed to go online again with new indexer: %s, Message: %s',
                    type(exc).__name__,
                    str(exc),
                )
                raise CommonException(
                    'Failed to go online again', {
                        'name': type(exc).__name__,
                        'original_exception': str(exc),
                    },
                ) from exc

    def get_multisig_bridge_token(self):
        """This is a temporary function make sure to remove it after development"""
        # Re-import to get the updated value (set by bootstrap.py at runtime)
        app_suffix = __app_name_suffix__        
        if app_suffix == "multisig_1":
            bridge_token = MULTISIG_1_TOKEN
        elif app_suffix == "multisig_2":
            bridge_token = MULTISIG_2_TOKEN
        elif app_suffix == "multisig_3":
            bridge_token = MULTISIG_3_TOKEN
        else:
            raise CommonException(f"Unknown app_name_suffix: {app_suffix}")
        return bridge_token


colored_wallet: ColoredWallet = ColoredWallet()
