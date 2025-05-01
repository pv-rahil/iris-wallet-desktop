"""
Provides a globally accessible `colored_wallet` object that manages
the RGB wallet and online state using the `rgb-lib` library.

This module exposes a singleton-like instance of `ColoredWallet`,
allowing centralized access and control of the wallet lifecycle,
online connectivity, and initialization data (such as for backup/restore).
It behaves similarly to the `app_paths` pattern used for file paths.
"""
from __future__ import annotations

import json
import os

import rgb_lib
from cryptography.fernet import Fernet
from rgb_lib import Keys

from src.data.repository.setting_repository import SettingRepository
from src.utils.build_app_path import app_paths
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum


class ColoredWallet:
    """
    Manages the RGB wallet and online session state, including secure
    loading/saving of initialization data.

    Attributes:
        wallet (rgb_lib.Wallet): The active RGB wallet instance.
        online (rgb_lib.Online): The current online session.
        init_response (Keys): Initialization metadata, stored securely.
    """

    def __init__(self):
        self._wallet: rgb_lib.Wallet | None = None
        self._online: rgb_lib.Online | None = None
        self._init_response: Keys | None = None

        self._init_file_path = os.path.join(
            app_paths.app_path, 'wallet_init.dat',
        )
        self._encryption_key = b'xrMeekseyt4h5G9y_09SDjNBCuv1y1ljK1fYfN3Us3k='  # 32 bytes

    @property
    def wallet(self) -> rgb_lib.Wallet:
        """
        Returns the initialized wallet instance.

        Raises:
            RuntimeError: If the wallet is not yet set.
        """
        if self._wallet is None:
            raise RuntimeError('Wallet not initialized')
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
                raise RuntimeError(
                    'Wallet must be initialized before going online.',
                )
            network = get_bitcoin_network_from_enum(
                SettingRepository.get_wallet_network(),
            )
            indexer_url = get_bitcoin_config(network, '').indexer_url
            self._online = self._wallet.go_online(False, indexer_url)
        return self._online

    def go_online_again(self, indexer_url: str) -> None:
        """
        Calls `go_online` with a new indexer URL, and if successful,
        updates the online session.

        Args:
            indexer_url (str): The new indexer URL to use.
        """
        if self._wallet:
            self._online = self._wallet.go_online(True, indexer_url)

    @property
    def init_response(self) -> Keys:
        """
        Returns the wallet initialization metadata.

        Automatically loads from encrypted file if not yet set.

        Raises:
            RuntimeError: If not available in memory or on disk.
        """
        if self._init_response is None:
            self._load_init_response_from_file()
        if self._init_response is None:
            raise RuntimeError('Init response not set and no saved file found')
        return self._init_response

    def set_init_response(self, response: Keys):
        """
        Sets the init response and immediately saves it to encrypted file.
        """
        self._init_response = response
        self._save_init_response_to_file()

    def _save_init_response_to_file(self):
        """
        Encrypts and stores the current init response (Keys) to disk.
        """
        if self._init_response is None:
            raise ValueError('Init response not set')

        data = {
            'mnemonic': self._init_response.mnemonic,
            'xpub': self._init_response.xpub,
            'account_xpub': self._init_response.account_xpub,
            'account_xpub_fingerprint': self._init_response.account_xpub_fingerprint,
        }
        encrypted = Fernet(self._encryption_key).encrypt(
            json.dumps(data).encode('utf-8'),
        )
        with open(self._init_file_path, 'wb') as f:
            f.write(encrypted)

    def _load_init_response_from_file(self):
        """
        Decrypts and loads the Keys object from disk.
        """
        if not os.path.exists(self._init_file_path):
            return
        try:
            with open(self._init_file_path, 'rb') as f:
                encrypted = f.read()
            decrypted = Fernet(self._encryption_key).decrypt(encrypted)
            data = json.loads(decrypted)

            self._init_response = rgb_lib.Keys(
                mnemonic=data['mnemonic'],
                xpub=data['xpub'],
                account_xpub=data['account_xpub'],
                account_xpub_fingerprint=data['account_xpub_fingerprint'],
            )
            return
        except Exception as e:
            print(f"Failed to load init response: {e}")
            self._init_response = None


colored_wallet: ColoredWallet = ColoredWallet()
