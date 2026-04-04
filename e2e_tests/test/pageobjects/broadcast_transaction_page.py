"""
Broadcast/Sign PSBT page objects for interacting with the broadcast transaction page.
"""
from __future__ import annotations

from accessible_constant import BROADCAST_TRANSACTION_METHOD_SELECTOR
from accessible_constant import BROADCAST_TRANSACTION_PAGE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PSBT_INPUT
from accessible_constant import CLEAR_PSBT_BUTTON
from accessible_constant import EXPORT_PSBT_BUTTON
from accessible_constant import IMPORT_PSBT_BUTTON
from accessible_constant import REJECT_PSBT_BUTTON
from accessible_constant import SIGN_PSBT_PAGE_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class BroadcastTransactionPageObjects(BaseOperations):
    """Page object for the Broadcast/Sign PSBT page."""

    def __init__(self, application):
        super().__init__(application)

        # Elements
        self.close_button = lambda: self.perform_action_on_element(
            role_name='push button', name=BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON,
        )
        self.psbt_input = lambda: self.perform_action_on_element(
            role_name='text', name=BROADCAST_TRANSACTION_PSBT_INPUT,
        )
        self.method_selector = lambda: self.perform_action_on_element(
            role_name='combo box', name=BROADCAST_TRANSACTION_METHOD_SELECTOR,
        )
        self.broadcast_button = lambda: self.perform_action_on_element(
            role_name='push button', name=BROADCAST_TRANSACTION_PAGE_BUTTON,
        )
        self.sign_psbt_button = lambda: self.perform_action_on_element(
            role_name='push button', name=SIGN_PSBT_PAGE_BUTTON,
        )
        self.import_psbt_button = lambda: self.perform_action_on_element(
            role_name='push button', name=IMPORT_PSBT_BUTTON,
        )
        self.export_psbt_button = lambda: self.perform_action_on_element(
            role_name='push button', name=EXPORT_PSBT_BUTTON,
        )
        self.clear_psbt_button = lambda: self.perform_action_on_element(
            role_name='push button', name=CLEAR_PSBT_BUTTON,
        )
        self.reject_psbt_button = lambda: self.perform_action_on_element(
            role_name='push button', name=REJECT_PSBT_BUTTON,
        )

    def enter_psbt(self, psbt_text: str):
        """Enter PSBT text into the input field."""
        return self.do_set_text(self.psbt_input(), psbt_text) if self.do_is_displayed(self.psbt_input()) else None

    def click_close(self):
        """Click the close button."""
        return self.do_click(self.close_button()) if self.do_is_displayed(self.close_button()) else None

    def click_broadcast_button(self):
        """Click the broadcast button."""
        return self.do_click(self.broadcast_button()) if self.do_is_displayed(self.broadcast_button()) else None

    def click_sign_psbt_button(self):
        """Click the sign psbt button."""
        return self.do_click(self.sign_psbt_button()) if self.do_is_displayed(self.sign_psbt_button()) else None

    def click_import_psbt_button(self):
        """Click the import psbt button."""
        return self.do_click(self.import_psbt_button()) if self.do_is_displayed(self.import_psbt_button()) else None

    def click_export_psbt_button(self):
        """Click the export psbt button."""
        return self.do_click(self.export_psbt_button()) if self.do_is_displayed(self.export_psbt_button()) else None

    def click_clear_psbt_button(self):
        """Click the clear psbt button."""
        return self.do_click(self.clear_psbt_button()) if self.do_is_displayed(self.clear_psbt_button()) else None

    def click_reject_psbt_button(self):
        """Click the reject psbt button."""
        return self.do_click(self.reject_psbt_button()) if self.do_is_displayed(self.reject_psbt_button()) else None
