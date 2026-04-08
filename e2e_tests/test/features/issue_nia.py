# pylint: disable=too-many-arguments,too-many-branches
"""
This module contains the IssueNia class, which provides methods for issuing NIA assets.
"""
from __future__ import annotations

from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.test_helpers import BaseIssueAsset
from e2e_tests.test.utilities.test_helpers import handle_utxo_confirmation_dialog
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class IssueNia(MainPageObjects, BaseOperations, BaseIssueAsset):
    """
    This class provides methods for issuing NIA assets.
    """

    def __init__(self, application):
        """
        Initialize the IssueNia class with the application.
        """
        self.hardware_wallet_emu = None
        self.wallet_feature = Wallet(application)
        super().__init__(application)

    def issue_nia_with_sufficient_sats_and_no_utxo(self, application, asset_ticker, asset_name, asset_amount, variant_name):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet_emu = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
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

            if self.hardware_wallet_emu:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            # NIA-specific: focus and success flow
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            # NIA: cleanup using helper method
            self._cleanup_hardware_wallet()

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

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.issue_nia_page_objects.close_button()):
            self.issue_nia_page_objects.click_close_button()

        return description

    def issue_nia_with_sufficient_sats_and_utxo(self, application, asset_ticker, asset_name, asset_amount, variant_name: str, is_native_auth_enabled: bool = False):
        """
        Issues an NIA asset with sufficient sats and UTXO.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet_emu = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
                self.fungible_page_objects.click_refresh_button()
                
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

            if self.hardware_wallet_emu:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            # NIA with native auth: password entry and success flow
            if is_native_auth_enabled is True:
                self.enter_native_password()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            # NIA: terminate hardware wallet emulator directly
            if self.hardware_wallet_emu:
                self.hardware_wallet_emu.terminate()

    def issue_nia_with_sufficient_sats_and_no_utxo_watch_only_wallet(self, application, asset_ticker):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        self.fungible_page_objects.click_nia_frame(asset_ticker)

        if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
            self.issue_nia_page_objects.click_issue_nia_button()

        self.do_focus_on_application(application)

        self.wallet_feature.usb_sync(is_receive=True)

    def issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(self, application, asset_ticker, asset_name, asset_amount):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
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

        self.wallet_feature.usb_sync(is_receive=True)

    def issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(self, application, asset_ticker, utxo_required: bool = False, is_native_auth_enabled: bool = False):
        """
        Issues an NIA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        self.fungible_page_objects.click_nia_frame(asset_ticker)

        if self.do_is_displayed(self.issue_nia_page_objects.issue_nia_button()):
            self.issue_nia_page_objects.click_issue_nia_button()
        if is_native_auth_enabled:
            self.enter_native_password()
        if utxo_required:
            handle_utxo_confirmation_dialog(self, self, utxo_required=True)
        else:
            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()

    def issue_nia_with_sufficient_sats_for_multisig_wallet(self, application, asset_ticker, asset_name, asset_amount, is_native_auth_enabled: bool = False):
        """
        Issues an NIA asset with sufficient sats for multisig wallet.
        """
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

        if is_native_auth_enabled:
            self.enter_native_password()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
            self.confirmation_dialog_page_objects.click_confirmation_dialog()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
            self.confirmation_dialog_page_objects.click_confirmation_continue_button()
