# pylint: disable=too-many-arguments,too-many-branches
"""
SendOperation class provides methods for sending assets using bitcoin transfer.
"""
from __future__ import annotations

import time

from accessible_constant import BITCOIN_LEDGER_APP_NAME
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.test_helpers import handle_utxo_confirmation_dialog
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class SendOperation(MainPageObjects, BaseOperations):
    """
    Initializes the SendOperation class with the application.
    """

    def __init__(self, application):
        """
        Sends assets using bitcoin transfer.
        """
        self.hardware_wallet = None
        self.wallet_features = Wallet(application)
        super().__init__(application)

    def send(self, application, receiver_invoice, amount=None, is_hardware_wallet: bool = False, purpose: str | None = None, is_native_auth_enabled: bool = False):
        """
        Send assets

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        """
        try:
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
                self.send_asset_page_objects.enter_asset_invoice(
                    receiver_invoice,
                )
            self.do_focus_on_application(application)

            if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
                self.send_asset_page_objects.enter_asset_amount(amount)

            if self.do_is_displayed(self.send_asset_page_objects.send_button()):
                self.send_asset_page_objects.click_send_button()

            if is_native_auth_enabled is True:
                self.enter_native_password()

            if is_hardware_wallet:
                if purpose == 'send_btc':
                    self.wallet_features.confirm_transaction_on_hardware_wallet(
                        LEDGER_EMULATOR_APP_NAME,
                    )

                elif purpose == 'send_asset':
                    self.wallet_features.confirm_transaction_on_hardware_wallet(
                        LEDGER_EMULATOR_APP_NAME, is_rgb=True,
                    )
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
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
        try:

            description = None

            self.do_focus_on_application(application)
            if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
                self.send_asset_page_objects.enter_asset_invoice(
                    receiver_invoice,
                )

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
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            self.do_focus_on_application(application)
            if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
                self.toaster_page_objects.click_toaster_frame()

            if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
                description = self.toaster_page_objects.get_toaster_description()
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                self.hardware_wallet.terminate()
        return description

    def create_psbt(self, application, receiver_invoice, amount=None, fee_rate=None):
        """
        Create psbt

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)
        self.do_focus_on_application(application)

        if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if fee_rate:
            if self.do_is_displayed(self.send_asset_page_objects.fee_rate_input()):
                self.send_asset_page_objects.enter_fee_rate(fee_rate)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        try:
            if self.do_is_displayed(self.bitcoin_detail_page_objects.bitcoin_close_button()):
                self.bitcoin_detail_page_objects.click_bitcoin_close_button()
        except Exception as _:
            pass

        self.wallet_features.usb_sync()

    def create_psbt_for_multisig(self, application, receiver_invoice, amount, wallet_variant_name, utxo_required: bool = False):
        """
        Create psbt for multisig wallet

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)
        self.do_focus_on_application(application)

        if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if utxo_required:
            handle_utxo_confirmation_dialog(self, self, utxo_required=True)

        if wallet_variant_name in REQUIRE_USB_VARIANTS:
            self.wallet_features.usb_sync()

    def send_asset_for_multisig(self, application, _wallet_variant_name):
        """
        Send asset for multisig wallet
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.asset_detail_page_objects.resume_draft_frame()):
            self.asset_detail_page_objects.click_resume_draft_frame()

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()
