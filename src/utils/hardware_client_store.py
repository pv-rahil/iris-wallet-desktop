"""
Provides a globally accessible `hardware_client_store` object that manages
and stores the hardware wallet client instance (e.g., LedgerClient).

This module exposes a singleton-like instance of `HardwareClientStore`,
allowing centralized access and control of the hardware client lifecycle.
It behaves similarly to the `colored_wallet` pattern used for wallet management.
"""
from __future__ import annotations

from hwilib.devices.ledger import LedgerClient


class HardwareClientStore:
    """
    Manages the hardware wallet client instance.

    Attributes:
        _client: The active hardware wallet client instance (e.g., LedgerClient).
    """

    def __init__(self):
        self._client = None

    @property
    def client(self) -> LedgerClient:
        """Returns the stored hardware wallet client instance, or None if not set."""
        return self._client

    def set_client(self, client):
        """Sets the hardware wallet client instance."""
        self._client = client

    def clear_client(self):
        """Clears the stored hardware wallet client instance."""
        self._client = None

    def stop_client(self):
        """Stops the running client"""
        if self._client:
            self._client.close()
            self._client = None


hardware_client_store: HardwareClientStore = HardwareClientStore()
