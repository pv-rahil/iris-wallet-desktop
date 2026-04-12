# pylint: disable=too-few-public-methods
"""
Base class for issue asset feature classes.
"""
from __future__ import annotations

from accessible_constant import HARDWARE_WALLET_VARIANTS
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class BaseIssueAsset:
    """
    Base class for issue asset feature classes providing common hardware wallet handling.
    """

    hardware_wallet_emulator = None

    def _init_hardware_wallet(self, variant_name: str | None, app_name: str) -> bool:
        """
        Initialize hardware wallet emulator if variant requires it.

        Args:
            variant_name: Wallet variant name.
            app_name: Ledger app name.

        Returns:
            True if hardware wallet was initialized.
        """
        if variant_name in HARDWARE_WALLET_VARIANTS:
            self.hardware_wallet_emulator = handle_hardware_wallet(
                app_name=app_name,
            )
            return True
        return False

    def _cleanup_hardware_wallet(self) -> None:
        """Clean up hardware wallet emulator if it exists."""
        if self.hardware_wallet_emulator:
            self.hardware_wallet_emulator.terminate()
            self.hardware_wallet_emulator = None
