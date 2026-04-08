"""
Module for handling receive operations in the application.
"""
from __future__ import annotations

from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import ONLINE_CREATE_HARDWARE
from accessible_constant import ONLINE_LOAD_HARDWARE
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class ReceiveOperation(MainPageObjects, BaseOperations):
    """
    Class for handling receive operations in the application.
    """

    def __init__(self, application):
        """
        Initialize the ReceiveOperation class.
        """
        self.hardware_wallet_emulator = None
        self.wallet_feature = Wallet(application)
        super().__init__(application)

    def receive(self, application):
        """
        Receive assets from the application.
        """
        address, copied_address = None, None
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            address = self.receive_asset_page_objects.get_receiver_invoice()

        if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
            self.receive_asset_page_objects.click_invoice_copy_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            copied_address = self.receive_asset_page_objects.do_get_copied_address()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        return address, copied_address

    def receive_asset_from_sidebar(self, application, variant_name=None):
        """
        Navigate through the sidebar menu to receive an asset.
        """
        try:
            invoice = None
            if variant_name in (ONLINE_CREATE_HARDWARE, ONLINE_LOAD_HARDWARE):
                self.hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)
            if self.do_is_displayed(self.sidebar_page_objects.receive_asset_button()):
                self.sidebar_page_objects.click_receive_asset_button()
            if self.hardware_wallet_emulator:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )
            if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
                self.receive_asset_page_objects.click_invoice_copy_button()
            if self.do_is_displayed(self.receive_asset_page_objects.invoice_copy_button()):
                invoice = self.receive_asset_page_objects.do_get_copied_address()
            if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
                self.receive_asset_page_objects.click_receive_asset_close_button()
            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()
            return invoice
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet_emulator:
                self.hardware_wallet_emulator.terminate()
