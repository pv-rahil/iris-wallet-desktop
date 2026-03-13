"""
Provides a globally accessible `hardware_client_store` object that manages
and stores the hardware wallet client instance (ledger-bitcoin client).

This module exposes a singleton-like instance of `HardwareClientStore`,
allowing centralized access and control of the hardware client lifecycle.
It behaves similarly to the `colored_wallet` pattern used for wallet management.
"""
from __future__ import annotations


class HardwareClientStore:
    """
    Manages the hardware wallet client instance.

    Attributes:
        _client: The active hardware wallet client instance (ledger-bitcoin).
    """

    def __init__(self):
        self._client = None
        self._is_rgb_mode: bool | None = None

    @property
    def client(self):
        """Returns the stored hardware wallet client instance, or None if not set."""
        return self._client

    def set_client(self, client):
        """Sets the hardware wallet client instance."""
        self._client = client

    def clear_client(self):
        """Clears the stored hardware wallet client instance."""
        self._client = None

    def stop_client(self):
        """Stops the running client."""
        if self._client:
            self._client.stop()
            self._client = None

    # -------- Mode controls --------
    def set_rgb_mode(self, enabled: bool) -> None:
        """Enable or disable RGB signing mode for the next operation."""
        self._is_rgb_mode = enabled

    def get_rgb_mode(self) -> bool:
        """Return the RGB signing mode flag; defaults to False if unset."""
        return bool(self._is_rgb_mode)

    def clear_rgb_mode(self) -> None:
        """Clear the RGB signing mode flag back to unspecified (None)."""
        self._is_rgb_mode = None


hardware_client_store: HardwareClientStore = HardwareClientStore()
