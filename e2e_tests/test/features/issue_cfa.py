# pylint: disable=too-many-arguments,too-many-branches
"""
Module for testing CFA asset issuance.
"""
from __future__ import annotations

import os

from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.asset_copy import copy_cfa_image_to_home_directory
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.test_helpers import handle_utxo_confirmation_with_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class IssueCfa(MainPageObjects, BaseOperations):
    """
    Class for testing CFA asset issuance.
    """

    def __init__(self, application):
        """
        Initialize the IssueCfa class.
        """
        self.hardware_wallet_emulator = None
        self.wallet_features = Wallet(application)
        super().__init__(application)

    def issue_cfa_with_sufficient_sats_and_utxo(
        self, application, asset_name, asset_description,
        asset_amount, variant_name: str | None = None, is_native_auth: bool = False,
    ):
        """
        Issue CFA asset with sufficient sats and utxo.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)
            copy_cfa_image_to_home_directory(os.getcwd())

            if self.do_is_displayed(self.sidebar_page_objects.collectibles_button()):
                self.sidebar_page_objects.click_collectibles_button()
                
            if self.do_is_displayed(self.collectible_page_objects.refresh_button()):
                self.collectible_page_objects.click_refresh_button()

            if self.do_is_displayed(self.collectible_page_objects.issue_cfa_button()):
                self.collectible_page_objects.click_issue_cfa_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_name()):
                self.issue_cfa_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_description()):
                self.issue_cfa_page_objects.enter_asset_description(
                    asset_description,
                )

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_amount()):
                self.issue_cfa_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_cfa_page_objects.upload_file_button()):
                self.issue_cfa_page_objects.click_upload_file_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.cfa_asset_media()):
                self.issue_cfa_page_objects.click_cfa_asset_media()

            if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
                self.issue_cfa_page_objects.click_issue_cfa_button()

            if self.hardware_wallet_emulator:
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            if is_native_auth is True:
                self.enter_native_password()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()

        except Exception as err:
            raise err
        finally:
            if self.hardware_wallet_emulator:
                self.hardware_wallet_emulator.terminate()

    def issue_cfa_asset_without_sat(self, application, asset_name, asset_description, asset_amount):
        """
        Issue CFA asset without sat.
        """
        description = None
        self.do_focus_on_application(application)
        copy_cfa_image_to_home_directory(os.getcwd())

        if self.do_is_displayed(self.sidebar_page_objects.collectibles_button()):
            self.sidebar_page_objects.click_collectibles_button()

        if self.do_is_displayed(self.collectible_page_objects.issue_cfa_button()):
            self.collectible_page_objects.click_issue_cfa_button()

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_name()):
            self.issue_cfa_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_description()):
            self.issue_cfa_page_objects.enter_asset_description(
                asset_description,
            )

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_amount()):
            self.issue_cfa_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_cfa_page_objects.upload_file_button()):
            self.issue_cfa_page_objects.click_upload_file_button()

        if self.do_is_displayed(self.issue_cfa_page_objects.cfa_asset_media()):
            self.issue_cfa_page_objects.click_cfa_asset_media()

        if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
            self.issue_cfa_page_objects.click_issue_cfa_button()

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.issue_cfa_page_objects.close_button()):
            self.issue_cfa_page_objects.click_close_button()

        if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
            self.sidebar_page_objects.click_fungibles_button()

        return description

    def issue_cfa_with_sufficient_sats_and_no_utxo(self, application, asset_name, asset_description, asset_amount, variant_name):
        """
        Issue CFA asset with sufficient sats and no utxo.
        """
        try:
            if variant_name in HARDWARE_WALLET_VARIANTS:
                self.hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)
            copy_cfa_image_to_home_directory(os.getcwd())

            if self.do_is_displayed(self.sidebar_page_objects.view_unspents_button()):
                self.sidebar_page_objects.click_view_unspents_button()

            if self.do_is_displayed(self.sidebar_page_objects.collectibles_button()):
                self.sidebar_page_objects.click_collectibles_button()

            if self.do_is_displayed(self.collectible_page_objects.issue_cfa_button()):
                self.collectible_page_objects.click_issue_cfa_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_name()):
                self.issue_cfa_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_description()):
                self.issue_cfa_page_objects.enter_asset_description(
                    asset_description,
                )

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_amount()):
                self.issue_cfa_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_cfa_page_objects.upload_file_button()):
                self.issue_cfa_page_objects.click_upload_file_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.cfa_asset_media()):
                self.issue_cfa_page_objects.click_cfa_asset_media()

            if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
                self.issue_cfa_page_objects.click_issue_cfa_button()

            if self.hardware_wallet_emulator:
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.success_page_objects.home_button()):
                self.success_page_objects.click_home_button()
        except Exception as err:
            raise err
        finally:
            if self.hardware_wallet_emulator:
                self.hardware_wallet_emulator.terminate()

    def issue_cfa_with_sufficient_sats_and_no_utxo_watch_only_wallet(self, application, asset_name):
        """
        Issues an CFA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)

        self.collectible_page_objects.click_cfa_frame(f"{asset_name} (Draft)")

        if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
            self.issue_cfa_page_objects.click_issue_cfa_button()

        self.do_focus_on_application(application)

        self.wallet_features.usb_sync(is_receive=True)

    def issue_cfa_with_sufficient_sats_and_no_utxo_offline_wallet(self, application, asset_name, asset_description, asset_amount):
        """
        Issues an CFA asset with sufficient sats and no UTXO.
        """
        self.do_focus_on_application(application)
        copy_cfa_image_to_home_directory(os.getcwd())

        if self.do_is_displayed(self.collectible_page_objects.issue_cfa_button()):
            self.collectible_page_objects.click_issue_cfa_button()

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_name()):
            self.issue_cfa_page_objects.enter_asset_name(asset_name)

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_description()):
            self.issue_cfa_page_objects.enter_asset_description(
                asset_description,
            )

        if self.do_is_displayed(self.issue_cfa_page_objects.asset_amount()):
            self.issue_cfa_page_objects.enter_asset_amount(asset_amount)

        if self.do_is_displayed(self.issue_cfa_page_objects.upload_file_button()):
            self.issue_cfa_page_objects.click_upload_file_button()

        if self.do_is_displayed(self.issue_cfa_page_objects.cfa_asset_media()):
            self.issue_cfa_page_objects.click_cfa_asset_media()

        if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
            self.issue_cfa_page_objects.click_issue_cfa_button()

        self.wallet_features.usb_sync(is_receive=True)

    def issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(self, application, asset_name, wallet_variant_name: str | None = None, utxo_required: bool = False, is_native_auth_enabled: bool = False):
        """
        Issues an CFA asset with sufficient sats and no UTXO.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        hardware_wallet_emulator = None
        try:
            if is_hardware and utxo_required:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.collectibles_button()):
                self.sidebar_page_objects.click_collectibles_button()

            self.collectible_page_objects.click_cfa_frame(f"{asset_name} (Draft)")

            if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
                self.issue_cfa_page_objects.click_issue_cfa_button()

            if is_native_auth_enabled:
                self.enter_native_password()

            if not utxo_required:
                if self.do_is_displayed(self.success_page_objects.home_button()):
                    self.success_page_objects.click_home_button()
            else:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_features, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=True, is_hardware=is_hardware,
                )
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def issue_cfa_with_sufficient_sats_for_multisig_wallet(self, application, asset_name, asset_description, asset_amount, wallet_variant_name: str | None = None, is_native_auth_enabled: bool = False):
        """
        Issues a CFA asset with sufficient sats for multisig wallet.
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
            copy_cfa_image_to_home_directory(os.getcwd())

            if self.do_is_displayed(self.sidebar_page_objects.collectibles_button()):
                self.sidebar_page_objects.click_collectibles_button()

            if self.do_is_displayed(self.collectible_page_objects.issue_cfa_button()):
                self.collectible_page_objects.click_issue_cfa_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_name()):
                self.issue_cfa_page_objects.enter_asset_name(asset_name)

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_description()):
                self.issue_cfa_page_objects.enter_asset_description(
                    asset_description,
                )

            if self.do_is_displayed(self.issue_cfa_page_objects.asset_amount()):
                self.issue_cfa_page_objects.enter_asset_amount(asset_amount)

            if self.do_is_displayed(self.issue_cfa_page_objects.upload_file_button()):
                self.issue_cfa_page_objects.click_upload_file_button()

            if self.do_is_displayed(self.issue_cfa_page_objects.cfa_asset_media()):
                self.issue_cfa_page_objects.click_cfa_asset_media()

            if self.do_is_displayed(self.issue_cfa_page_objects.issue_cfa_button()):
                self.issue_cfa_page_objects.click_issue_cfa_button()

            if is_native_auth_enabled:
                self.enter_native_password()

            handle_utxo_confirmation_with_hardware_wallet(
                self, self, self.wallet_features, LEDGER_EMULATOR_APP_NAME,
                utxo_required=True, is_hardware=is_hardware,
            )
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()
