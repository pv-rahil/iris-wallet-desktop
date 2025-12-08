"""
Module for handling receive operations in the application.
"""
from __future__ import annotations

from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations


class ReceiveOperation(MainPageObjects, BaseOperations):
    """
    Class for handling receive operations in the application.
    """

    def __init__(self, application):
        """
        Initialize the ReceiveOperation class.
        """
        super().__init__(application)

    def retry_receive_dialog(self, max_retries=2, transfer_type=None, asset_name=None):
        """
        Retry logic to ensure receive dialog shows transfer selection buttons.
        Closes any open dialog and reopens the receive dialog.
        """
        retry_count = 0
        while retry_count < max_retries:
            if self.do_is_displayed(self.wallet_transfer_page_objects.on_chain_button()) or self.do_is_displayed(self.wallet_transfer_page_objects.lightning_button()):
                if transfer_type == 'bitcoin':
                    self.wallet_transfer_page_objects.click_on_chain_button()
                elif transfer_type == 'lightning':
                    self.wallet_transfer_page_objects.click_lightning_button()
                return True  # Buttons are visible, success

            print(f"""[RETRY] Transfer buttons not visible, retrying... (attempt
            {retry_count + 1}/{max_retries})""")
            if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
                self.receive_asset_page_objects.click_receive_asset_close_button()
            elif self.do_is_displayed(self.create_ln_invoice_page_objects.close_button()):
                self.create_ln_invoice_page_objects.click_close_button()
                if transfer_type == 'bitcoin':
                    self.fungible_page_objects.click_bitcoin_frame()
            if transfer_type == 'bitcoin' and self.do_is_displayed(self.bitcoin_detail_page_objects.receive_bitcoin_button()):
                self.bitcoin_detail_page_objects.click_receive_bitcoin_button()
            if asset_name:
                self.fungible_page_objects.click_rgb20_frame(asset_name)
            retry_count += 1
        return False

    def receive(self, application, transfer_type=None, value=None):
        """
        Receive assets from the application.
        """
        address, copied_address = None, None
        self.do_focus_on_application(application)

        # Retry logic: if transfer buttons not visible, try closing and reopening (max 2 attempts)
        if transfer_type in ('bitcoin', 'lightning'):
            self.retry_receive_dialog(transfer_type=transfer_type)

        # Handle additional input for Lightning
        if transfer_type == 'lightning' and self.do_is_displayed(self.create_ln_invoice_page_objects.asset_amount()):
            self.create_ln_invoice_page_objects.enter_asset_amount(value)
            if self.do_is_displayed(self.create_ln_invoice_page_objects.create_button()):
                self.create_ln_invoice_page_objects.click_create_button()

        # Common steps for both Bitcoin,RGB and Lightning
        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            address = self.receive_asset_page_objects.get_receiver_invoice()

        if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
            self.receive_asset_page_objects.click_invoice_copy_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            copied_address = self.receive_asset_page_objects.do_get_copied_address()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        return address, copied_address

    def receive_asset_from_sidebar(self, application):
        """
        Navigate through the sidebar menu to receive an asset.
        """
        invoice = None
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.sidebar_page_objects.receive_asset_button()):
            self.sidebar_page_objects.click_receive_asset_button()
        if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
            self.receive_asset_page_objects.click_invoice_copy_button()
        if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
            invoice = self.receive_asset_page_objects.do_get_copied_address()
        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()
        if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
            self.sidebar_page_objects.click_fungibles_button()
        return invoice

    def create_wrong_ln_invoice(self, application, amount, asset_name):
        """
        Sends assets using lightning transfer with a wrong invoice.
        """
        error_label = None

        self.do_focus_on_application(application)
        self.retry_receive_dialog(transfer_type='lightning', asset_name=asset_name)


        if self.do_is_displayed(self.create_ln_invoice_page_objects.asset_amount()):
            self.create_ln_invoice_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.create_ln_invoice_page_objects.error_label()):
            error_label = self.create_ln_invoice_page_objects.get_error_label()

        if self.do_is_displayed(self.create_ln_invoice_page_objects.close_button()):
            self.create_ln_invoice_page_objects.click_close_button()

        return error_label
