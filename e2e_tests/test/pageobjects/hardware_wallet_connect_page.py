# pylint:disable=too-many-instance-attributes
"""
Hardware wallet connect page objects class for interacting with the hardware wallet connect page.
"""
from __future__ import annotations

from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_CONTINUE_BUTTON
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_LEDGER_OPTION
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_TREZOR_OPTION
from e2e_tests.test.utilities.base_operation import BaseOperations


class HardwareWalletConnectPageObjects(BaseOperations):
    """
    Hardware wallet connect page objects class for interacting with the hardware wallet connect page.
    """

    def __init__(self, application):
        """
        Initializes the HardwareWalletConnectPageObjects class.

        Args:
            application: The application object.
        """
        super().__init__(application)

        self.hw_connect_window = lambda: self.get_first_element(
            role_name='filler', name=HARDWARE_WALLET_CONNECT_PAGE,
        )
        self.continue_button = lambda: self.get_first_element(
            role_name='push button', name=HARDWARE_WALLET_CONNECT_PAGE_CONTINUE_BUTTON,
        )
        self.ledger_option = lambda: self.get_first_element(
            role_name='panel', name=HARDWARE_WALLET_CONNECT_PAGE_LEDGER_OPTION,
        )
        self.trezor_option = lambda: self.get_first_element(
            role_name='panel', name=HARDWARE_WALLET_CONNECT_PAGE_TREZOR_OPTION,
        )

    def click_continue_button(self):
        """Clicks the continue button."""
        return self.do_click(self.continue_button()) if self.do_is_displayed(self.continue_button()) else None

    def click_ledger_option(self):
        """Clicks the ledger option."""
        return self.do_click(self.ledger_option()) if self.do_is_displayed(self.ledger_option()) else None

    def click_trezor_option(self):
        """Clicks the trezor option."""
        return self.do_click(self.trezor_option()) if self.do_is_displayed(self.trezor_option()) else None
