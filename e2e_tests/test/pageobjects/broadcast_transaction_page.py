"""
Broadcast/Sign PSBT page objects for interacting with the broadcast transaction page.
"""
from __future__ import annotations

from accessible_constant import BROADCAST_TRANSACTION_METHOD_SELECTOR
from accessible_constant import BROADCAST_TRANSACTION_PAGE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PSBT_INPUT
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
