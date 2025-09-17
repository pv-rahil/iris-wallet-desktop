# pylint : disable = possibly-used-before-assignment
"""
SendOperation class provides methods for sending assets using bitcoin transfer.
"""
from __future__ import annotations

import time

from accessible_constant import BITCOIN_LEDGER_APP_NAME
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class SendOperation(MainPageObjects, BaseOperations):
    """
    Initializes the SendOperation class with the application.
    """

    def __init__(self, application):
        """
        Sends assets using bitcoin transfer.
        """
        super().__init__(application)

    def send(self, application, receiver_invoice, amount=None, is_hardware_wallet: bool = False, purpose: str = None, is_native_auth_enabled: bool = False):
        """
        Send assets

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        """
        if is_hardware_wallet and purpose:
            if purpose == 'send_btc':
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=BITCOIN_LEDGER_APP_NAME,
                )
            elif purpose == 'send_asset':
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)
        self.do_focus_on_application(application)

        if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if is_native_auth_enabled is True:
            self.enter_native_password()

        if is_hardware_wallet:
            self.do_focus_on_application(
                LEDGER_EMULATOR_APP_NAME,
            )
            if purpose == 'send_btc':
                time.sleep(2)
                for _ in range(2):
                    self.hw_emulator_page_objects.click_right_arrow_key(4)
                    self.hw_emulator_page_objects.press_left_and_right()
                self.hw_emulator_page_objects.click_right_arrow_key(1)
                self.hw_emulator_page_objects.press_left_and_right()

            elif purpose == 'send_asset':
                time.sleep(2)
                self.hw_emulator_page_objects.click_right_arrow_key(5)
                self.hw_emulator_page_objects.press_left_and_right()
            time.sleep(2)
            self.hardware_wallet.terminate()

    def send_with_no_fund(self, application, receiver_invoice, amount):
        """
        Send assets without sufficient funds.
        """
        validation = None
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.amount_validation()):
            validation = self.send_asset_page_objects.get_amount_validation()

        if self.do_is_displayed(self.send_asset_page_objects.send_asset_close_button()):
            self.send_asset_page_objects.click_send_asset_close_button()

        return validation

    def send_with_custom_fee_rate(self, application, receiver_invoice, amount, fee_rate, is_hardware_wallet: bool = False):
        """
        Sends assets using bitcoin with a custom fee rate.
        """

        description = None

        self.do_focus_on_application(application)
        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.fee_rate_input()):
            self.send_asset_page_objects.enter_fee_rate(fee_rate)

        if is_hardware_wallet:
            self.hardware_wallet = handle_hardware_wallet(
                app_name=BITCOIN_LEDGER_APP_NAME,
            )

        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if is_hardware_wallet:
            self.do_focus_on_application(
                LEDGER_EMULATOR_APP_NAME,
            )
            time.sleep(2)
            for _ in range(2):
                self.hw_emulator_page_objects.click_right_arrow_key(4)
                self.hw_emulator_page_objects.press_left_and_right()
            self.hw_emulator_page_objects.click_right_arrow_key(1)
            self.hw_emulator_page_objects.press_left_and_right()

        self.do_focus_on_application(application)
        if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
            self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
            description = self.toaster_page_objects.get_toaster_description()

        if self.hardware_wallet:
            self.hardware_wallet.terminate()
        return description
