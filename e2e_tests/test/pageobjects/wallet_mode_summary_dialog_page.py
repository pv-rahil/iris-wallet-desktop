"""Wallet mode summary dialog page objects module."""
from __future__ import annotations

from accessible_constant import WALLET_MODE_SUMMARY_DIALOG
from accessible_constant import WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON
from accessible_constant import WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON
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
        self.wallet_mode_summary_dialog = lambda: self._safe_find_dialog(
            'dialog', WALLET_MODE_SUMMARY_DIALOG,
        )
        self.cancel_button = lambda: self._safe_find_child(
            self.wallet_mode_summary_dialog(),
            'push button', WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON,
        )
        self.continue_button = lambda: self._safe_find_child(
            self.wallet_mode_summary_dialog(),
            'push button', WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON,
        )

    def _safe_find_child(self, parent, role_name, name):
        """
        Safely find a child element, returning None if parent is None or child not found.
        """
        if parent is None:
            return None
        try:
            return parent.findChild(
                lambda x: x.roleName == role_name and x.name == name,
                retry=False, requireResult=False,
            )
        except Exception:
            return None

    def click_wallet_mode_summary_dialog(self):
        """
        Clicks the wallet mode summary dialog if it is displayed.
        """
        dialog = self.wallet_mode_summary_dialog()
        return self.do_click(dialog) if dialog and self.do_is_displayed(dialog) else None

    def click_cancel_button(self):
        """
        Clicks the cancel button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        button = self.cancel_button()
        return self.do_click(button) if button and self.do_is_displayed(button) else None

    def click_continue_button(self):
        """
        Clicks the continue button if it is displayed.

        Returns:
            The result of the click action or None if the button is not displayed.
        """
        button = self.continue_button()
        return self.do_click(button) if button and self.do_is_displayed(button) else None
