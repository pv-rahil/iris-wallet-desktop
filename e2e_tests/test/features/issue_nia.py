# pylint: disable=too-many-arguments,too-many-branches
"""
This module contains the IssueNia class, which provides methods for issuing NIA assets.
"""
from __future__ import annotations


from accessible_constant import BITCOIN_LEDGER_APP_NAME
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class IssueNia(MainPageObjects, BaseOperations):
    """
    This class provides methods for issuing NIA assets.
    """

    def __init__(self, application):
        """
        Initializes the IssuenNa class.
        """
        self.hardware_wallet = None
        self.wallet_features = Wallet(application)
        super().__init__(application)

    def issue_nia_with_sufficient_sats_and_no_utxo(self, application, asset_ticker, asset_name, asset_amount, variant_name):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=BITCOIN_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()

            if self.do_is_displayed(self.fungible_page_objects.issue_nia_button()):
                self.fungible_page_objects.click_issue_nia_button()

            if self.do_is_displayed(self.issue_nia_page_objects.asset_ticker()):
                self.issue_nia_page_objects.enter_asset_ticker(asset_ticker)

            if self.do_is_displayed(self.issue_nia_page_objects.asset_name()):
                self.issue_nia_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_nia_page_objects.asset_amount()):
                self.issue_nia_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
                self.issue_nia_page_objects.click_issue_nia_button()

            if self.hardware_wallet:
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                self.hardware_wallet.terminate()

    def issue_nia_asset_without_sat(self, application, asset_ticker, asset_name, asset_amount):
        """
        Issues an NIA asset without sufficient sats.
        """
        description = None
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.fungible_page_objects.issue_nia_button()):
            self.fungible_page_objects.click_issue_nia_button()

        if self.do_is_displayed(self.issue_nia_page_objects.asset_ticker()):
            self.issue_nia_page_objects.enter_asset_ticker(asset_ticker)

        if self.do_is_displayed(self.issue_nia_page_objects.asset_name()):
            self.issue_nia_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_nia_page_objects.asset_amount()):
            self.issue_nia_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
            self.issue_nia_page_objects.click_issue_nia_button()

        if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
            self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
            description = self.toaster_page_objects.get_toaster_description()

        if self.do_is_displayed(self.issue_nia_page_objects.close_button()):
            self.issue_nia_page_objects.click_close_button()

        return description

    def issue_nia_with_sufficient_sats_and_utxo(self, application, asset_ticker, asset_name, asset_amount, variant_name: str, is_native_auth_enabled: bool = False):
        """
        Issues an NIA asset with sufficient sats and UTXO.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=BITCOIN_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)
            if self.do_is_displayed(self.fungible_page_objects.issue_nia_button()):
                self.fungible_page_objects.click_issue_nia_button()

            self.do_focus_on_application(application)
            if self.do_is_displayed(self.issue_nia_page_objects.asset_ticker()):
                self.issue_nia_page_objects.enter_asset_ticker(asset_ticker)

            if self.do_is_displayed(self.issue_nia_page_objects.asset_name()):
                self.issue_nia_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_nia_page_objects.asset_amount()):
                self.issue_nia_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
                self.issue_nia_page_objects.click_issue_nia_button()

            if self.hardware_wallet:
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            if is_native_auth_enabled is True:
                self.enter_native_password()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                self.hardware_wallet.terminate()

    def issue_nia_with_sufficient_sats_and_no_utxo_watch_only_wallet(self, application, asset_ticker):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        self.fungible_page_objects.click_nia_frame(asset_ticker)

        if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
            self.issue_nia_page_objects.click_issue_nia_button()

        self.do_focus_on_application(application)

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
            self.fungible_page_objects.click_usb_sync_frame()

        if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
            self.usb_sync_dialog_page_objects.click_continue_button()

    def issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(self, application, asset_ticker, asset_name, asset_amount):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.fungible_page_objects.issue_nia_button()):
            self.fungible_page_objects.issue_nia_button()

        if self.do_is_displayed(self.fungible_page_objects.issue_nia_button()):
            self.fungible_page_objects.click_issue_nia_button()

        if self.do_is_displayed(self.issue_nia_page_objects.asset_ticker()):
            self.issue_nia_page_objects.enter_asset_ticker(asset_ticker)

        if self.do_is_displayed(self.issue_nia_page_objects.asset_name()):
            self.issue_nia_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_nia_page_objects.asset_amount()):
            self.issue_nia_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
            self.issue_nia_page_objects.click_issue_nia_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
            self.fungible_page_objects.click_usb_sync_frame()

        if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
            self.usb_sync_dialog_page_objects.click_continue_button()
