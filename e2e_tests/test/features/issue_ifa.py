# pylint: disable=too-many-arguments,too-many-branches
"""
This module contains the IssueIfa class, which provides methods for issuing IFA assets.
"""
from __future__ import annotations

from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_issue_asset import BaseIssueAsset
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.send_flow_helpers import click_issue_button_get_toaster_and_close
from e2e_tests.test.utilities.send_flow_helpers import handle_confirmation_dialog_and_usb_sync
from e2e_tests.test.utilities.send_flow_helpers import handle_offline_multisig_utxo_confirmation_and_usb_sync


class IssueIfa(MainPageObjects, BaseOperations, BaseIssueAsset):
    """
    This class provides methods for issuing IFA assets.
    """

    def __init__(self, application):
        """
        Initialize the IssueIfa class with the application.
        """
        super().__init__(application)
        self._init_ifa_features(application)

    def _get_issue_page_objects(self):
        """Get the issue page objects for IFA asset type."""
        issue_page = self.issue_ifa_page_objects
        return issue_page

    # Primary IFA issuance methods
    def issue_ifa_with_sufficient_sats_and_utxo(
        self, application, asset_ticker, asset_name,
        issue_amount, total_supply, variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Issues an IFA asset with sufficient sats and UTXO.
        """
        with self._asset_operation_context(variant_name):
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            if self.do_is_displayed(self.inflatable_page_objects.refresh_button()):
                self.inflatable_page_objects.click_refresh_button()

            if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
                self.inflatable_page_objects.click_issue_ifa_button()

            self._enter_asset_ticker_if_displayed(asset_ticker)
            self._enter_asset_name_if_displayed(asset_name)
            self._enter_asset_amount_if_displayed(issue_amount)

            if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
                self.issue_ifa_page_objects.enter_asset_total_supply(
                    total_supply,
                )

            self._click_issue_button_if_displayed()

            is_online = self._is_online_hardware(variant_name)
            self._handle_issue_confirmation_and_success(
                application, is_native_auth_enabled, is_ifa=True, is_online=is_online,
            )

    def issue_ifa_asset_without_sat(self, application, asset_ticker, asset_name, issue_amount, total_supply):
        """
        Issues an IFA asset without sufficient sats and captures toaster message.
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
            self.issue_ifa_page_objects.enter_asset_amount(issue_amount)

        if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
            self.issue_ifa_page_objects.enter_asset_total_supply(total_supply)

        # Click issue button, get toaster, close and navigate
        return click_issue_button_get_toaster_and_close(self)

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

    def issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
        self, application, asset_ticker, wallet_variant_name: str | None = None,
        utxo_required: bool = False, is_native_auth_enabled: bool = False,
    ):
        """
        Issues an IFA asset with sufficient sats and no UTXO.
        """

        def navigate_to_ifa():
            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()
            self.inflatable_page_objects.click_ifa_frame(asset_ticker)
            self._click_issue_button_if_displayed()

        self._handle_multisig_inflate_flow(
            application, wallet_variant_name, utxo_required, is_native_auth_enabled,
            pre_flow_callback=navigate_to_ifa,
        )

    def issue_ifa_for_offline_multisig_wallet(
        self, application, asset_ticker, asset_name, total_supply, asset_amount,
        _wallet_variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
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

    def issue_ifa_with_sufficient_sats_for_multisig_wallet(
        self, application, asset_ticker, asset_name, total_supply, asset_amount,
        wallet_variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Issues an IFA asset with sufficient sats for multisig wallet.
        This triggers UTXO creation which requires PSBT signing by cosigner.
        """

        def navigate_and_enter_total_supply():
            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()
            if self.do_is_displayed(self.inflatable_page_objects.issue_ifa_button()):
                self.inflatable_page_objects.click_issue_ifa_button()
            if self.do_is_displayed(self.issue_ifa_page_objects.asset_total_supply()):
                self.issue_ifa_page_objects.enter_asset_total_supply(
                    total_supply,
                )

        self._handle_multisig_issue_flow(
            application, wallet_variant_name, is_native_auth_enabled,
            asset_ticker, asset_name, asset_amount,
            pre_issue_callback=navigate_and_enter_total_supply,
        )
