# pylint : disable = possibly-used-before-assignment
"""
SendOperation class provides methods for sending assets using bitcoin or lightning transfer.
"""
from __future__ import annotations

from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from src.utils.info_message import INFO_BITCOIN_SENT


class SendOperation(MainPageObjects, BaseOperations):
    """
    Initializes the SendOperation class with the application.
    """

    def __init__(self, application):
        """
        Sends assets using bitcoin or lightning transfer.
        """
        super().__init__(application)

    def retry_send_dialog(self, max_retries=2, transfer_type=None):
        """
        Retry logic to ensure send dialog shows transfer selection buttons.
        Closes any open dialog and reopens the send dialog.
        """
        retry_count = 0
        while retry_count < max_retries:
            if self.do_is_displayed(self.wallet_transfer_page_objects.on_chain_button()) or self.do_is_displayed(self.wallet_transfer_page_objects.lightning_button()):
                # Buttons are visible, click the appropriate one
                if transfer_type == 'lightning':
                    self.wallet_transfer_page_objects.click_lightning_button()
                elif transfer_type == 'bitcoin':
                    self.wallet_transfer_page_objects.click_on_chain_button()
                return True  # Success

            print(f"""[RETRY] Transfer buttons not visible, retrying... (attempt
            {retry_count + 1}/{max_retries})""")
            # Close whichever dialog is open (on-chain or lightning)
            if self.do_is_displayed(self.send_asset_page_objects.send_asset_close_button()):
                self.send_asset_page_objects.click_send_asset_close_button()
            elif self.do_is_displayed(self.send_ln_invoice_page_objects.close_button()):
                self.send_ln_invoice_page_objects.click_close_button()
                self.fungible_page_objects.click_bitcoin_frame()

            # Re-open send dialog
            if self.do_is_displayed(self.bitcoin_detail_page_objects.send_bitcoin_button()):
                self.bitcoin_detail_page_objects.click_send_bitcoin_button()
            retry_count += 1
        return False

    def send(self, application, receiver_invoice, amount=None, transfer_type=None, is_native_auth_enabled: bool = False):
        """
        Send assets using bitcoin or lightning transfer.

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        :param transfer_type: The type of transfer ('bitcoin' or 'lightning').
        """
        self.do_focus_on_application(application)

        # Retry logic: if transfer buttons not visible, try closing and reopening (max 2 attempts)
        if transfer_type in ('bitcoin', 'lightning'):
            self.retry_send_dialog(transfer_type=transfer_type)

        send_objects = self.send_asset_page_objects if transfer_type != 'lightning' else self.send_ln_invoice_page_objects

        if self.do_is_displayed(send_objects.invoice_input()):
            send_objects.enter_asset_invoice(receiver_invoice)

        if amount and hasattr(send_objects, 'asset_amount_input') and self.do_is_displayed(send_objects.asset_amount_input()):
            send_objects.enter_asset_amount(amount)

        if self.do_is_displayed(send_objects.send_button()):
            send_objects.click_send_button()

        if is_native_auth_enabled is True:
            self.enter_native_password()

    def send_with_no_fund(self, application, receiver_invoice, amount, transfer_type=None):
        """
        Send assets without sufficient funds.
        """
        validation = None
        self.do_focus_on_application(application)

        # Retry logic: if transfer buttons not visible, try closing and reopening (max 2 attempts)
        if transfer_type == 'bitcoin':
            self.retry_send_dialog(transfer_type=transfer_type)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.amount_validation()):
            validation = self.send_asset_page_objects.get_amount_validation()

        if self.do_is_displayed(self.send_asset_page_objects.send_asset_close_button()):
            self.send_asset_page_objects.click_send_asset_close_button()

        return validation

    def send_with_wrong_invoice(self, application, receiver_invoice, amount, transfer_type=None):
        """
        Send assets with a wrong invoice.
        """
        description = None
        self.do_focus_on_application(application)

        # Retry logic: if transfer buttons not visible, try closing and reopening (max 2 attempts)
        if transfer_type == 'bitcoin':
            self.retry_send_dialog(transfer_type=transfer_type)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
            self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
            description = self.toaster_page_objects.get_toaster_description()

        if self.do_is_displayed(self.send_asset_page_objects.send_asset_close_button()):
            self.send_asset_page_objects.click_send_asset_close_button()

        return description

    def send_with_custom_fee_rate(self, application, receiver_invoice, amount, fee_rate, transfer_type=None):
        """
        Sends assets using bitcoin or lightning transfer with a custom fee rate.
        """
        description = None
        self.do_focus_on_application(application)

        # Retry logic: if transfer buttons not visible, try closing and reopening (max 2 attempts)
        if transfer_type == 'bitcoin':
            self.retry_send_dialog(transfer_type=transfer_type)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.fee_rate_input()):
            self.send_asset_page_objects.enter_fee_rate(fee_rate)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
            self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
            description = self.toaster_page_objects.get_toaster_description(
                filter_pattern=INFO_BITCOIN_SENT.split('{}', maxsplit=1)[0],
            )

        return description
