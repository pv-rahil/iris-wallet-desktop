"""Wallet mode summary dialog page objects module."""
from __future__ import annotations

from dogtail.tree import root
from accessible_constant import WALLET_MODE_SUMMARY_DIALOG, WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON, WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class WalletModeSummaryDialogPageObjects(BaseOperations):
    """
    Wallet mode summary dialog page objects class.
    """

    def __init__(self, application):
        """
        Initializes the WalletModeSummaryDialogPageObjects class.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        # Lazy evaluation of elements using lambdas
        self.wallet_mode_summary_dialog = lambda: root.child(
            roleName='dialog', name=WALLET_MODE_SUMMARY_DIALOG,
        )
        self.cancel_button = lambda: self.wallet_mode_summary_dialog().child(
            roleName='push button', name=WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON,
        )
        self.continue_button = lambda: self.wallet_mode_summary_dialog().child(
            roleName='push button', name=WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON,
        )

    def click_wallet_mode_summary_dialog(self):
        """
        Clicks the wallet mode summary dialog if it is displayed.
        """
        return self.do_click(self.wallet_mode_summary_dialog()) if self.do_is_displayed(self.wallet_mode_summary_dialog()) else None

    def click_cancel_button(self):
        """
        Clicks the cancel button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.cancel_button()) if self.do_is_displayed(self.cancel_button()) else None

    def click_continue_button(self):
        """
        Clicks the continue button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        return self.do_click(self.continue_button()) if self.do_is_displayed(self.continue_button()) else None
