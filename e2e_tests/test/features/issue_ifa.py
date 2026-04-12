# pylint: disable=too-many-arguments,too-many-branches, too-many-arguments
"""
This module contains the IssueIfa class, which provides methods for issuing IFA assets.
"""
from __future__ import annotations

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.test_helpers import BaseIssueAsset
from e2e_tests.test.utilities.test_helpers import handle_confirmation_dialog_and_usb_sync
from e2e_tests.test.utilities.test_helpers import handle_native_auth_and_focus
from e2e_tests.test.utilities.test_helpers import handle_native_auth_utxo_and_success
from e2e_tests.test.utilities.test_helpers import handle_offline_multisig_utxo_confirmation_and_usb_sync
from e2e_tests.test.utilities.test_helpers import handle_success_home_button
from e2e_tests.test.utilities.test_helpers import handle_utxo_confirmation_with_hardware_wallet
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

            if self.do_is_displayed(self.inflatable_page_objects.refresh_button()):
                self.inflatable_page_objects.click_refresh_button()

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
                    LEDGER_EMULATOR_APP_NAME,
                )

            # IFA-specific: native auth and success flow
            handle_native_auth_and_focus(
                self, application, is_native_auth_enabled)
            handle_success_home_button(self)
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

        if self.do_is_displayed(self.success_page_objects.home_button()):
            self.success_page_objects.click_home_button()

        self.do_focus_on_application(application)

        self.wallet_feature.usb_sync(is_receive=False)

    def issue_ifa_with_sufficient_sats_and_no_utxo_offline_wallet(self, application, asset_ticker, asset_name, asset_amount, total_supply):
        """
        Issues an IFA asset with sufficient sats and no UTXO.
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

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
            self.issue_ifa_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
            self.issue_ifa_page_objects.enter_asset_total_supply(total_supply)

        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        handle_confirmation_dialog_and_usb_sync(self, self.wallet_feature)

    def issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(self, application, asset_ticker, wallet_variant_name: str | None = None, utxo_required: bool = False, is_native_auth_enabled: bool = False):
        """
        Issues an IFA asset with sufficient sats and no UTXO.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        hardware_wallet_emulator = None
        try:
            if is_hardware and utxo_required:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            self.inflatable_page_objects.click_ifa_frame(asset_ticker)

            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            handle_native_auth_utxo_and_success(
                self, application, self.wallet_feature,
                is_native_auth_enabled=is_native_auth_enabled,
                utxo_required=utxo_required,
                is_hardware=is_hardware,
            )
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def issue_ifa_for_offline_multisig_wallet(self, application, asset_ticker, asset_name, total_supply, asset_amount, _wallet_variant_name: str | None = None, is_native_auth_enabled: bool = False):
        """
        Issues an IFA asset for offline multisig wallet.
        Creates PSBT on watch-only coordinator, then USB syncs to pass PSBT to offline signer.
        No hardware signing happens here - signing is done separately via sign_psbt.
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

        handle_offline_multisig_utxo_confirmation_and_usb_sync(
            self, application, self.wallet_feature, is_native_auth_enabled,
        )

    def issue_ifa_with_sufficient_sats_for_multisig_wallet(self, application, asset_ticker, asset_name, total_supply, asset_amount, wallet_variant_name: str | None = None, is_native_auth_enabled: bool = False):
        """
        Issues an IFA asset with sufficient sats for multisig wallet.
        This triggers UTXO creation which requires PSBT signing by cosigner.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        hardware_wallet_emulator = None
        try:
            if is_hardware:
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

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
                self.issue_ifa_page_objects.enter_asset_total_supply(
                    total_supply,
                )

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
                self.issue_ifa_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            if is_native_auth_enabled:
                self.enter_native_password()

            handle_utxo_confirmation_with_hardware_wallet(
                self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                utxo_required=True, is_hardware=is_hardware,
            )
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()
