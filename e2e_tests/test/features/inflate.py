# pylint: disable=too-many-arguments,too-many-branches, too-many-arguments
"""
This module contains the Inflate class, which provides methods for secondary issuance (inflate) of IFA assets.
"""
from __future__ import annotations

from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import REQUIRE_USB_VARIANTS
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_issue_asset import BaseIssueAsset
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.multisig_send_flow_helpers import click_issue_button_get_toaster_and_close
from e2e_tests.test.utilities.multisig_send_flow_helpers import handle_success_home_button
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_dialog
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_with_hardware_wallet


class Inflate(MainPageObjects, BaseOperations, BaseIssueAsset):
    """
    This class provides methods for secondary issuance (inflate) of IFA assets.
    """

    def __init__(self, application):
        """
        Initialize Inflate for secondary IFA issuance.
        """
        super().__init__(application)
        self._init_ifa_features(application)

    def _get_issue_page_objects(self):
        """Return IFA page objects for inflate operations."""
        return self.issue_ifa_page_objects

    def inflate_ifa_asset(
        self, application, asset_name, inflate_amount, variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Perform secondary issuance (inflate) on an existing IFA asset with sufficient sats and UTXO.
        """
        with self._asset_operation_context(variant_name):
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            self.inflatable_page_objects.click_ifa_frame(asset_name)

            if self.do_is_displayed(self.asset_detail_page_objects.secondary_issuance_button()):
                self.asset_detail_page_objects.click_secondary_issuance_button()

            self._enter_asset_amount_if_displayed(inflate_amount)
            self._click_issue_button_if_displayed()

            is_online = self._is_online_hardware(variant_name)
            self._handle_issue_confirmation_and_success(
                application, is_native_auth_enabled, is_inflate=True,
                is_online=is_online,
            )

    def inflate_ifa_asset_without_sufficient_sats(self, application, asset_name, inflate_amount):
        """
        Attempt to inflate IFA asset without sufficient sats and capture toaster message.
        """
        self.do_focus_on_application(application)

        # Navigate to IFA asset detail page
        if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
            self.sidebar_page_objects.click_inflatable_button()

        if self.do_is_displayed(self.inflatable_page_objects.ifa_asset_name):
            self.inflatable_page_objects.click_ifa_frame(asset_name)

        # Click secondary issuance button
        if self.do_is_displayed(self.asset_detail_page_objects.secondary_issuance_button()):
            self.asset_detail_page_objects.click_secondary_issuance_button()

        # Enter inflate amount
        if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
            self.issue_ifa_page_objects.enter_asset_amount(inflate_amount)

        # Click issue button to inflate, get toaster, close and navigate
        return click_issue_button_get_toaster_and_close(self)

    def inflate_ifa_asset_begin(
        self, application, asset_name, inflate_amount, variant_name: str | None = None, is_native_auth_enabled: bool = False, utxo_required: bool = False,
    ):
        """
        Create PSBT for secondary issuance (inflate) for watch-only/offline/hardware/multisig wallets.
        """
        with self._asset_operation_context(variant_name):
            self.do_focus_on_application(application)

            # Navigate to IFA asset detail page
            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            self.inflatable_page_objects.click_ifa_frame(asset_name)

            # Click secondary issuance button
            if self.do_is_displayed(self.asset_detail_page_objects.secondary_issuance_button()):
                self.asset_detail_page_objects.click_secondary_issuance_button()

            # Enter inflate amount
            if self.do_is_displayed(self.issue_ifa_page_objects.asset_amount()):
                self.issue_ifa_page_objects.enter_asset_amount(inflate_amount)

            # Native auth if required
            if is_native_auth_enabled is True:
                self.enter_native_password()

            # Click issue button to create PSBT
            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            if utxo_required:
                handle_utxo_confirmation_dialog(self, self, utxo_required=True)

            is_online = self._is_online_hardware(variant_name)
            self._confirm_on_hardware_wallet(
                self.wallet_feature, is_inflate=True, is_online=is_online,
            )
            try:
                if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
                    self.receive_asset_page_objects.click_receive_asset_close_button()
            except Exception as _:
                pass
            if variant_name in REQUIRE_USB_VARIANTS:
                if self.wallet_feature:
                    self.wallet_feature.usb_sync()

    def inflate_ifa_asset_for_multisig(
        self, application, asset_name, inflate_amount, wallet_variant_name: str | None = None, utxo_required: bool = False, is_native_auth_enabled: bool = False,
    ):
        """
        Perform secondary issuance (inflate) for multisig wallet.
        """
        is_hardware = self._is_multisig_hardware(wallet_variant_name)
        with self._multisig_asset_operation_context(wallet_variant_name, utxo_required):
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            self.inflatable_page_objects.click_ifa_frame(asset_name)

            if self.do_is_displayed(self.asset_detail_page_objects.secondary_issuance_button()):
                self.asset_detail_page_objects.click_secondary_issuance_button()

            self._enter_asset_amount_if_displayed(inflate_amount)

            if is_native_auth_enabled:
                self.enter_native_password()

            self._click_issue_button_if_displayed()

            if utxo_required:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=True, is_hardware=is_hardware,
                )
            else:
                handle_success_home_button(self)

    def inflate_ifa_asset_from_draft(self, application, asset_name, wallet_variant_name: str | None = None):
        """
        Finalize inflation from draft after PSBT is signed and broadcast.
        """
        is_hardware = self._is_multisig_hardware(wallet_variant_name)
        with self._multisig_asset_operation_context(wallet_variant_name, utxo_required=True):
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.inflatable_button()):
                self.sidebar_page_objects.click_inflatable_button()

            self.inflatable_page_objects.click_ifa_frame(asset_name)

            self.asset_detail_page_objects.click_resume_secondary_issuance_draft_frame()

            self._click_issue_button_if_displayed()

            if is_hardware:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=False, is_hardware=is_hardware,
                )

            handle_success_home_button(self)
