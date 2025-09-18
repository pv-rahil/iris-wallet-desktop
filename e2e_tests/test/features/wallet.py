"""
Wallet class for creating and funding a wallet.
"""
from __future__ import annotations

import os
import time

from accessible_constant import BITCOIN_LEDGER_APP_NAME
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.executable_shell_script import mine
from e2e_tests.test.utilities.executable_shell_script import send_to_address
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import resolve_steps as resolve_wallet_steps

BACKUP_EMAIL_ID = os.getenv('BACKUP_EMAIL_ID')
BACKUP_EMAIL_PASSWORD = os.getenv('BACKUP_EMAIL_PASSWORD')


class Wallet(MainPageObjects, BaseOperations):
    """
    Initializes the Wallet class.
    """

    def __init__(self, application):
        super().__init__(application)

        self.address = None

    def create_wallet(self, application, variant: str):
        """
        Creates a wallet.
        """
        self.do_focus_on_application(application)

        effective_variant = (
            'online_create_on_device' if application == SECOND_APPLICATION else variant
        )

        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()

        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()

        self.drive_selection_flow(application, effective_variant)
        if effective_variant == 'online_watch_only':
            pass

        if effective_variant in HARDWARE_WALLET_VARIANTS:
            self.set_up_hardware_wallet(application)

        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()

        if self.do_is_displayed(self.set_password_page_objects.password_input()):
            self.set_password_page_objects.enter_password('walletpassword')

        if self.do_is_displayed(self.set_password_page_objects.confirm_password_input()):
            self.set_password_page_objects.enter_confirm_password(
                'walletpassword',
            )

        if self.do_is_displayed(self.set_password_page_objects.proceed_button()):
            self.set_password_page_objects.click_proceed_button()

    def fund_wallet(self, application):
        """
        Funds the wallet.
        """

        self.do_focus_on_application(application)

        if self.do_is_displayed(self.fungible_page_objects.bitcoin_frame()):
            self.fungible_page_objects.click_bitcoin_frame()

        if self.do_is_displayed(self.bitcoin_detail_page_objects.receive_bitcoin_button()):
            self.bitcoin_detail_page_objects.click_receive_bitcoin_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            self.receive_asset_page_objects.click_invoice_copy_button()

        if self.do_is_displayed(self.receive_asset_page_objects.receiver_invoice()):
            self.address = self.receive_asset_page_objects.do_get_copied_address()

        send_to_address(self.address, 1)
        mine(1)

        # Close the "Receive Bitcoin" dialog
        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        if self.do_is_displayed(self.bitcoin_detail_page_objects.bitcoin_close_button()):
            self.bitcoin_detail_page_objects.click_bitcoin_close_button()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

    def create_and_fund_wallet(self, application, variant: str, fund=True):
        """
        Create a new wallet and fund it.
        """

        self.create_wallet(application, variant)
        if fund:
            self.fund_wallet(application)

    def drive_selection_flow(self, application, variant: str):
        """
        Drive the 4-step selection flow using option indices (1 or 2).
        """
        step1, step2, step3, step4 = resolve_wallet_steps(variant)
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step1)
            self.selection_page_objects.click_continue_button()

        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step2)
            self.selection_page_objects.click_continue_button()

        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step3)
            self.selection_page_objects.click_continue_button()

        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step4)
            self.selection_page_objects.click_continue_button()

        # Handle wallet mode summary dialog if it appears
        if self.do_is_displayed(self.wallet_mode_summary_dialog_page_objects.continue_button()):
            self.wallet_mode_summary_dialog_page_objects.click_continue_button()

    def google_auth(self, mnemonic=None, password=None, xpub_vanilla=None, xpub_colored=None, fingerprint=None):
        """
        Google authentication for backup and restore
        """
        if mnemonic and password:
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_mnemonic_input()):
                self.restore_wallet_page_objects.enter_mnemonic_value(mnemonic)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_password_input()):
                self.restore_wallet_page_objects.enter_password_value(password)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_continue_button()):
                self.restore_wallet_page_objects.click_continue_button()
        if xpub_vanilla and xpub_colored and fingerprint and password:
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_vanilla_input()):
                self.restore_wallet_page_objects.enter_xpub_vanilla_value(
                    xpub_vanilla)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_colored_input()):
                self.restore_wallet_page_objects.enter_xpub_colored_value(
                    xpub_colored)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_fingerprint_input()):
                self.restore_wallet_page_objects.enter_fingerprint_value(
                    fingerprint)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_password_input()):
                self.restore_wallet_page_objects.enter_password_value(password)
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_continue_button()):
                self.restore_wallet_page_objects.click_continue_button()

        if self.do_is_displayed(self.backup_page_objects.backup_window()):
            self.backup_page_objects.click_backup_window()

        if self.do_is_displayed(self.backup_page_objects.email_input()):
            self.backup_page_objects.enter_email(
                BACKUP_EMAIL_ID,
            )
        if self.do_is_displayed(self.backup_page_objects.next_button()):
            self.backup_page_objects.click_next_button()
        if self.do_is_displayed(self.backup_page_objects.password_input()):
            self.backup_page_objects.enter_password(
                BACKUP_EMAIL_PASSWORD,
            )
        if self.do_is_displayed(self.backup_page_objects.next_button()):
            self.backup_page_objects.click_next_button()
        try:
            if self.do_is_displayed(self.backup_page_objects.try_another_way_button()):
                self.backup_page_objects.click_try_another_way_button()
        except Exception as _:
            pass
        if self.do_is_displayed(self.backup_page_objects.google_authenticator()):
            self.backup_page_objects.click_google_authenticator_button()
        if self.do_is_displayed(self.backup_page_objects.enter_code()):
            code = self.backup_page_objects.get_security_otp()
            self.backup_page_objects.enter_security_code(
                code,
            )
        if self.do_is_displayed(self.backup_page_objects.next_button()):
            self.backup_page_objects.click_next_button()

    def set_up_hardware_wallet(self, application):
        """
        Set up the hardware wallet.
        """
        speculos_process = handle_hardware_wallet(
            app_name=BITCOIN_LEDGER_APP_NAME, reset=True)
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.hw_connect_page_objects.ledger_option()):
            self.hw_connect_page_objects.click_ledger_option()
        if self.do_is_displayed(self.hw_connect_page_objects.continue_button()):
            self.hw_connect_page_objects.click_continue_button()
        if self.do_is_displayed(self.hw_device_selection_dialog_page_objects.ledger_emulator_radio_button()):
            self.hw_device_selection_dialog_page_objects.click_ledger_emulator_radio_button()
        if self.do_is_displayed(self.hw_device_selection_dialog_page_objects.connect_button()):
            self.hw_device_selection_dialog_page_objects.click_connect_button()
        self.do_focus_on_application(LEDGER_EMULATOR_APP_NAME)
        self.hw_emulator_page_objects.click_right_arrow_key(7)
        self.hw_emulator_page_objects.press_left_and_right()
        self.do_focus_on_application(application)
        time.sleep(2)
        speculos_process.terminate()
