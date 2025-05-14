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

from src.data.repository.setting_repository import SettingRepository
from src.utils.custom_exception import CommonException
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.logging import logger


class ColoredWallet:
    """
    Manages the RGB wallet and online session state, including secure
    loading/saving of initialization data.

    Attributes:
        wallet (rgb_lib.Wallet): The active RGB wallet instance.
        online (rgb_lib.Online): The current online session.
    """

    def __init__(self):
        self._wallet: rgb_lib.Wallet | None = None
        self._online: rgb_lib.Online | None = None

    @property
    def wallet(self) -> rgb_lib.Wallet:
        """
        Returns the initialized wallet instance.

        Raises:
            RuntimeError: If the wallet is not yet set.
        """
        if self._wallet is None:
            raise CommonException('Wallet not initialized')
        return self._wallet

    def set_wallet(self, wallet: rgb_lib.Wallet):
        """Sets the wallet instance."""
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
        if self._online is None:
            if self._wallet is None:
                raise CommonException(
                    'Wallet must be initialized before going online.',
                )

            try:
                network = get_bitcoin_network_from_enum(
                    SettingRepository.get_wallet_network(),
                )
                indexer_url = get_bitcoin_config(network, '').indexer_url
                self._online = self._wallet.go_online(False, indexer_url)
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
        return self._online

    def go_online_again(self, indexer_url: str) -> None:
        """
        Calls `go_online` with a new indexer URL, and if successful,
        updates the online session.

        Args:
            indexer_url (str): The new indexer URL to use.
        """
        if self._wallet:
            try:
                self._online = self._wallet.go_online(True, indexer_url)
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


colored_wallet: ColoredWallet = ColoredWallet()
