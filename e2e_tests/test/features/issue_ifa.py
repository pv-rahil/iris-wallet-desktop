# pylint: disable=too-many-arguments,too-many-branches, too-many-arguments
"""
This module contains the IssueIfa class, which provides methods for issuing IFA assets.
"""
from __future__ import annotations

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.test_helpers import BaseIssueAsset
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class IssueIfa(MainPageObjects, BaseOperations, BaseIssueAsset):
    """
    This class provides methods for issuing IFA assets.
    """

    def __init__(self, application):
        """
        Initialize the IssueIfa class with the application.
        """
        self.wallet_feature = Wallet(application)
        super().__init__(application)

    def issue_ifa_with_sufficient_sats_and_utxo(
        self, application, asset_ticker, asset_name,
        issue_amount, total_supply, variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Issues an IFA asset with sufficient sats and UTXO.
        """
        try:
            hardware_wallet_emulator = None
            if variant_name in HARDWARE_WALLET_VARIANTS:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
                self.inflatable_page_objects.click_issue_ifa_button()

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_ticker()):
                self.issue_ifa_page_objects.enter_asset_ticker(asset_ticker)

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_name()):
                self.issue_ifa_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
                self.issue_ifa_page_objects.enter_asset_amount(issue_amount)

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
                self.issue_ifa_page_objects.enter_asset_total_supply(
                    total_supply,
                )

            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            if hardware_wallet_emulator:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_issue_ifa=True,
                )

            # IFA-specific: native auth and success flow
            if is_native_auth_enabled is True:
                self.enter_native_password()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            # IFA: cleanup local hardware wallet emulator
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def issue_ifa_asset_without_sat(self, application, asset_ticker, asset_name, issue_amount, total_supply):
        """
        Issues an IFA asset without sufficient sats and captures toaster message.
        """
        description = None
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
            self.sidebar_page_objects.click_inflatable_button()

        if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
            self.inflatable_page_objects.click_issue_ifa_button()

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_ticker()):
            self.issue_ifa_page_objects.enter_asset_ticker(asset_ticker)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_name()):
            self.issue_ifa_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
            self.issue_ifa_page_objects.enter_asset_amount(issue_amount)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
            self.issue_ifa_page_objects.enter_asset_total_supply(total_supply)

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.issue_ifa_page_objects.close_button()):
            self.issue_ifa_page_objects.click_close_button()

        if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
            self.sidebar_page_objects.click_fungibles_button()

        return description

    def issue_ifa_with_sufficient_sats_and_no_utxo_watch_only_wallet(self, application, asset_name):
        """
        Initiate IFA issuance from a draft in watch-only/offline mode to create an unsigned PSBT.
        After this, the test should sign and broadcast, then return to finalize issuance from the draft again.
        """
        self.do_focus_on_application(application)

        # Open the draft card and click issue to produce the PSBT
        self.inflatable_page_objects.click_ifa_frame(f"{asset_name} (Draft)")

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        self.do_focus_on_application(application)

        self.wallet_feature.usb_sync(is_receive=True)

    def issue_ifa_with_sufficient_sats_and_no_utxo_offline_wallet(self, application, asset_ticker, asset_name, asset_amount, total_supply):
        """
        Issues an IFA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
            self.inflatable_page_objects.issue_ifa_button()

        if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
            self.inflatable_page_objects.click_issue_ifa_button()

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_ticker()):
            self.issue_ifa_page_objects.enter_asset_ticker(asset_ticker)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_name()):
            self.issue_ifa_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
            self.issue_ifa_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
            self.issue_ifa_page_objects.enter_asset_total_supply(total_supply)

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        self.wallet_feature.usb_sync(is_receive=True)

    def issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(self, application, asset_ticker, utxo_required: bool = False, is_native_auth_enabled: bool = False):
        """
        Issues an IFA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
            self.sidebar_page_objects.click_inflatable_button()

        self.inflatable_page_objects.click_ifa_frame(asset_ticker)

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        if is_native_auth_enabled:
            self.enter_native_password()

        if utxo_required:
            self.do_focus_on_application(CONFIRMATION_DIALOG)
            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
                self.confirmation_dialog_page_objects.click_confirmation_dialog()

            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
                self.confirmation_dialog_page_objects.click_confirmation_continue_button()
        else:
            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()

    def issue_ifa_with_sufficient_sats_for_multisig_wallet(self, application, asset_ticker, asset_name, total_supply, asset_amount, is_native_auth_enabled: bool = False):
        """
        Issues an NIA asset with sufficient sats for multisig wallet.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
            self.sidebar_page_objects.click_inflatable_button()

        if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
            self.inflatable_page_objects.click_issue_ifa_button()

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_ticker()):
            self.issue_ifa_page_objects.enter_asset_ticker(asset_ticker)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_name()):
            self.issue_ifa_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
            self.issue_ifa_page_objects.enter_asset_total_supply(total_supply)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
            self.issue_ifa_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        if is_native_auth_enabled:
            self.enter_native_password()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
            self.confirmation_dialog_page_objects.click_confirmation_dialog()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
            self.confirmation_dialog_page_objects.click_confirmation_continue_button()
