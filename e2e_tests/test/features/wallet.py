"""
Wallet class for creating and funding a wallet.
"""
from __future__ import annotations

from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.executable_shell_script import mine
from e2e_tests.test.utilities.executable_shell_script import send_to_address


class Wallet(MainPageObjects, BaseOperations):
    """
    Initializes the Wallet class.
    """

    def __init__(self, application):
        super().__init__(application)

        self.address = None

    def create_wallet(self, application):
        """
        Creates an embedded wallet.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()

        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()

        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()

        if self.do_is_displayed(self.set_password_page_objects.password_input()):
            self.set_password_page_objects.enter_password('walletpassword')

        if self.do_is_displayed(self.set_password_page_objects.confirm_password_input()):
            self.set_password_page_objects.enter_confirm_password(
                'walletpassword',
            )

        if self.do_is_displayed(self.set_password_page_objects.proceed_button()):
            self.set_password_page_objects.click_proceed_button()

    def fund_wallet(self, application):
        """
        Funds the wallet.
        """

        self.do_focus_on_application(application)

        if self.do_is_displayed(self.fungible_page_objects.bitcoin_frame()):
            self.fungible_page_objects.click_bitcoin_frame()

        if self.do_is_displayed(self.bitcoin_detail_page_objects.receive_bitcoin_button()):
            self.bitcoin_detail_page_objects.click_receive_bitcoin_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            self.receive_asset_page_objects.click_invoice_copy_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            self.address = self.receive_asset_page_objects.do_get_copied_address()

        send_to_address(self.address, 1)
        mine(1)

        # Close the "Receive Bitcoin" dialog
        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        if self.do_is_displayed(self.bitcoin_detail_page_objects.bitcoin_close_button()):
            self.bitcoin_detail_page_objects.click_bitcoin_close_button()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

    def create_and_fund_wallet(self, application, fund=True):
        """
        Create a new wallet and fund it.
        """
        self.create_wallet(application)
        if fund:
            self.fund_wallet(application)
