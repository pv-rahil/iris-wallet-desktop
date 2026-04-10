# pylint: disable=too-many-arguments,too-many-branches, too-many-arguments
"""
This module contains the Inflate class, which provides methods for secondary issuance (inflate) of IFA assets.
"""
from __future__ import annotations

from e2e_tests.test.utilities.test_helpers import handle_utxo_confirmation_with_hardware_wallet
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class Inflate(MainPageObjects, BaseOperations):
    """
    This class provides methods for secondary issuance (inflate) of IFA assets.
    """

    def __init__(self, application):
        """
        Initialize the Inflate class with the application.
        """
        self.wallet_feature = Wallet(application)
        super().__init__(application)

    def inflate_ifa_asset(
        self, application, asset_name, inflate_amount, variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Perform secondary issuance (inflate) on an existing IFA asset with sufficient sats and UTXO.
        """
        try:
            hardware_wallet_emulator = None
            if variant_name in HARDWARE_WALLET_VARIANTS:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
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

            # Click issue button to inflate
            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            if hardware_wallet_emulator:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_issue_ifa=True,
                )

            # Native auth if required
            if is_native_auth_enabled is True:
                self.enter_native_password()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def inflate_ifa_asset_without_sufficient_sats(self, application, asset_name, inflate_amount):
        """
        Attempt to inflate IFA asset without sufficient sats and capture toaster message.
        """
        description = None
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

        # Click issue button to inflate
        if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
            self.issue_ifa_page_objects.click_issue_ifa_button()

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.issue_ifa_page_objects.close_button()):
            self.issue_ifa_page_objects.click_close_button()

        if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
            self.sidebar_page_objects.click_fungibles_button()

        return description

    def inflate_ifa_asset_begin(
        self, application, asset_name, inflate_amount, variant_name: str | None = None, is_native_auth_enabled: bool = False,
    ):
        """
        Create PSBT for secondary issuance (inflate) for watch-only/offline/hardware/multisig wallets.
        """
        try:
            hardware_wallet_emulator = None
            if variant_name in HARDWARE_WALLET_VARIANTS:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
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

            if hardware_wallet_emulator:
                self.wallet_feature.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_issue_ifa=True,
                )
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def inflate_ifa_asset_for_multisig(
        self, application, asset_name, inflate_amount, wallet_variant_name: str | None = None, utxo_required: bool = False, is_native_auth_enabled: bool = False,
    ):
        """
        Perform secondary issuance (inflate) for multisig wallet.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        hardware_wallet_emulator = None
        try:
            if is_hardware and utxo_required:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
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

            # Click issue button to inflate
            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()

            if utxo_required:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=True, is_hardware=is_hardware,
                )
            else:
                if self.do_is_displayed(self.success_page_objects.home_button()):
                    self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def inflate_ifa_asset_from_draft(self, application, asset_name, wallet_variant_name: str | None = None):
        """
        Finalize inflation from draft after PSBT is signed and broadcast.
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

            # Click on the draft frame
            self.inflatable_page_objects.click_ifa_frame(asset_name)

            self.asset_detail_page_objects.click_resume_secondary_issuance_draft_frame()

            if self.do_is_displayed(self.issue_ifa_page_objects.issue_ifa_button()):
                self.issue_ifa_page_objects.click_issue_ifa_button()
                
            if is_hardware:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=False, is_hardware=is_hardware,
                )

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()
