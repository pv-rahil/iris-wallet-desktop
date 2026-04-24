# pylint: disable=consider-using-with, too-many-branches, too-many-statements, too-many-nested-blocks, too-many-arguments
"""
Wallet operations mixin for transaction signing, hardware wallet, and restore operations.
"""
from __future__ import annotations

import os
import time

from dogtail.tree import root

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import MULTISIG_VARIANTS
from accessible_constant import ONLINE_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from accessible_constant import SECOND_APPLICATION
from accessible_constant import WATCH_ONLY_DIALOG
from e2e_tests.test.pageobjects.about_page import AboutPageObjects
from e2e_tests.test.pageobjects.keyring_dialog_page import KeyringDialogBoxPageObjects
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.pageobjects.settings_page_object import SettingsPageObjects
from e2e_tests.test.pageobjects.sidebar_page import SidebarPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet

BACKUP_EMAIL_ID = os.getenv('BACKUP_EMAIL_ID')
BACKUP_EMAIL_PASSWORD = os.getenv('BACKUP_EMAIL_PASSWORD')


class WalletOperationsMixin(MainPageObjects, BaseOperations):
    """
    Mixin class for wallet operations: transaction signing, hardware wallet,
    restore, and backup operations.
    """

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
                    xpub_vanilla,
                )
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_colored_input()):
                self.restore_wallet_page_objects.enter_xpub_colored_value(
                    xpub_colored,
                )
            if self.do_is_displayed(self.restore_wallet_page_objects.restore_fingerprint_input()):
                self.restore_wallet_page_objects.enter_fingerprint_value(
                    fingerprint,
                )
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

        # Retry wrong code handling up to 4 times until continue button appears
        max_retries = 4
        for _retry in range(max_retries):
            if self.do_is_displayed(self.backup_page_objects.continue_button()):
                break
            if self.backup_page_objects.is_wrong_code_label_displayed():
                code = self.backup_page_objects.get_security_otp()
                self.backup_page_objects.clear_code_field()
                self.backup_page_objects.enter_security_code(code)
                self.backup_page_objects.click_next_button()

        if self.do_is_displayed(self.backup_page_objects.continue_button()):
            self.backup_page_objects.click_continue_button()

    def restore_with_mnemonic(self, mnemonic: str | None, password: str | None):
        """Restore using mnemonic/password via restore dialog without triggering any online backup UI."""
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_mnemonic_input()) and mnemonic:
            self.restore_wallet_page_objects.enter_mnemonic_value(mnemonic)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_password_input()) and password:
            self.restore_wallet_page_objects.enter_password_value(password)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_continue_button()):
            self.restore_wallet_page_objects.click_continue_button()

    def restore_with_xpubs(self, xpub_vanilla: str | None, xpub_colored: str | None, fingerprint: str | None, password: str | None):
        """Restore using xpubs/fingerprint/password via restore dialog without triggering any online backup UI."""
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_vanilla_input()) and xpub_vanilla:
            self.restore_wallet_page_objects.enter_xpub_vanilla_value(
                xpub_vanilla,
            )
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_colored_input()) and xpub_colored:
            self.restore_wallet_page_objects.enter_xpub_colored_value(
                xpub_colored,
            )
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_fingerprint_input()) and fingerprint:
            self.restore_wallet_page_objects.enter_fingerprint_value(
                fingerprint,
            )
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_password_input()) and password:
            self.restore_wallet_page_objects.enter_password_value(password)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_continue_button()):
            self.restore_wallet_page_objects.click_continue_button()

    def navigate_to_watch_only_restore(self, application):
        """Drive selection to Watch-Only and open the Restore flow on the welcome page."""
        self.do_focus_on_application(application)
        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()
        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()
        # Drive to watch-only selection
        self.drive_selection_flow(application, ONLINE_WATCH_ONLY)
        # Open Restore on welcome (do not click Create for this flow)
        if self.do_is_displayed(self.welcome_page_objects.restore_button()):
            self.welcome_page_objects.click_restore_button()

    def set_up_hardware_wallet(
        self,
        application,
        terminate_emulator: bool = True,
        reset_regtest_flag: bool = True,
    ):
        """
        Set up the hardware wallet.

        Args:
            application: The application name.
            terminate_emulator: Whether to terminate the emulator after setup.
                For multisig, set to False to keep emulator running for later signing.
            reset_regtest_flag: Whether to reset regtest before starting emulator.
                For multisig, set to False to let the coordinator manage regtest lifecycle.
        """
        speculos_process = None
        try:
            speculos_process = handle_hardware_wallet(
                app_name=RGB_LEDGER_APP_NAME, reset=reset_regtest_flag,
            )
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
            for _ in range(2):
                time.sleep(1)
                self.hw_emulator_page_objects.click_right_arrow_key(5)
                self.hw_emulator_page_objects.press_left_and_right()
            self.do_focus_on_application(application)
            time.sleep(2)
        except Exception as e:
            if speculos_process:
                speculos_process.terminate()
            raise e
        finally:
            if terminate_emulator and speculos_process:
                speculos_process.terminate()

        return speculos_process

    def set_up_watch_only_wallet(self, xpub_vanilla: str | None, xpub_colored: str | None, fingerprint: str | None):
        """Apply provided xpubs and fingerprint to watch-only dialog in second app."""
        # Focus the watch-only dialog and populate
        self.do_focus_on_application(WATCH_ONLY_DIALOG)
        if self.do_is_displayed(self.watch_only_dialog_page_objects.watch_only_dialog()):
            self.watch_only_dialog_page_objects.click_watch_only_dialog()

        if xpub_vanilla and self.do_is_displayed(self.watch_only_dialog_page_objects.watch_only_xpub_vanilla()):
            self.watch_only_dialog_page_objects.enter_xpub_vanilla_value(
                xpub_vanilla,
            )

        if xpub_colored and self.do_is_displayed(self.watch_only_dialog_page_objects.watch_only_xpub_colored()):
            self.watch_only_dialog_page_objects.enter_xpub_colored_value(
                xpub_colored,
            )

        if fingerprint and self.do_is_displayed(self.watch_only_dialog_page_objects.watch_only_master_fingerprint()):
            self.watch_only_dialog_page_objects.enter_fingerprint_value(
                fingerprint,
            )

        # Confirm checkbox and continue
        self.do_focus_on_application(WATCH_ONLY_DIALOG)
        if self.do_is_displayed(self.watch_only_dialog_page_objects.watch_only_checkbox()):
            self.watch_only_dialog_page_objects.click_checkbox()

        if self.do_is_displayed(self.watch_only_dialog_page_objects.continue_button()):
            self.watch_only_dialog_page_objects.click_continue_button()

    def collect_keyring_values_from_app(self, app_name: str = FIRST_APPLICATION, is_load_wallet: bool = False) -> tuple[str | None, str | None, str | None, str | None]:
        """Focus the first application and read xpubs + fingerprint from About page copy buttons."""
        self.do_focus_on_application(app_name)

        # Get the app frame from the TestEnvironment to ensure correct app context
        env = self.get_current_environment()
        target_app = None
        if app_name == FIRST_APPLICATION and env and hasattr(env, 'first_application'):
            target_app = env.first_application
        elif app_name == SECOND_APPLICATION and env and hasattr(env, 'second_application'):
            target_app = env.second_application

        # Fallback to finding frame directly if not available from env
        if not target_app:
            target_app = root.child(roleName='frame', name=app_name)

        if not target_app:
            return None, None, None, None

        sidebar_page = SidebarPageObjects(target_app)
        about_page = AboutPageObjects(target_app)
        setting_page = SettingsPageObjects(target_app)
        keyring_dialog_page = KeyringDialogBoxPageObjects(target_app)

        xpub_vanilla = None
        xpub_colored = None
        fingerprint = None
        password = None

        if is_load_wallet:
            if sidebar_page.do_is_displayed(sidebar_page.settings_button()):
                sidebar_page.click_settings_button()

            if setting_page.do_is_displayed(setting_page.keyring_toggle_button()):
                setting_page.click_keyring_toggle_button()

            if keyring_dialog_page.do_is_displayed(keyring_dialog_page.keyring_xpub_vanilla_copy_button()):
                keyring_dialog_page.click_keyring_xpub_vanilla_copy_button()
                xpub_vanilla = keyring_dialog_page.do_get_copied_address()

            if keyring_dialog_page.do_is_displayed(keyring_dialog_page.keyring_xpub_colored_copy_button()):
                keyring_dialog_page.click_keyring_xpub_colored_copy_button()
                xpub_colored = keyring_dialog_page.do_get_copied_address()

            if keyring_dialog_page.do_is_displayed(keyring_dialog_page.keyring_fingerprint_copy_button()):
                keyring_dialog_page.click_keyring_fingerprint_copy_button()
                fingerprint = keyring_dialog_page.do_get_copied_address()

            if keyring_dialog_page.do_is_displayed(keyring_dialog_page.keyring_password_copy_button()):
                keyring_dialog_page.click_keyring_password_copy_button()
                password = keyring_dialog_page.do_get_copied_address()

            if keyring_dialog_page.do_is_displayed(keyring_dialog_page.cancel_button()):
                keyring_dialog_page.click_cancel_button()

        else:
            if sidebar_page.do_is_displayed(sidebar_page.about_button()):
                sidebar_page.click_about_button()

            if about_page.do_is_displayed(about_page.vanilla_xpub_copy_button()):
                about_page.click_vanilla_xpub_copy_button()
                xpub_vanilla = about_page.do_get_copied_address()

            if about_page.do_is_displayed(about_page.colored_xpub_copy_button()):
                about_page.click_colored_xpub_copy_button()
                xpub_colored = about_page.do_get_copied_address()

            if about_page.do_is_displayed(about_page.master_fingerprint_copy_button()):
                about_page.click_master_fingerprint_copy_button()
                fingerprint = about_page.do_get_copied_address()

        if sidebar_page.do_is_displayed(sidebar_page.fungibles_button()):
            sidebar_page.click_fungibles_button()
        return xpub_vanilla, xpub_colored, fingerprint, password

    def sign_psbt(self, application, variant_name, is_rgb: bool = False, is_inflate: bool = False, is_btc: bool = False, is_ifa: bool = False):
        """
        Sign psbt.
        """
        try:
            is_online = None
            if variant_name in REQUIRE_USB_VARIANTS:
                is_online = False
            else:
                is_online = True
            if variant_name in HARDWARE_WALLET_VARIANTS or variant_name in MULTISIG_HARDWARE_VARIANTS:
                # RGB Ledger app can sign both BTC and RGB transactions
                self.hw_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()

            if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
                self.fungible_page_objects.click_refresh_button()

            if variant_name == ONLINE_WATCH_ONLY or variant_name in REQUIRE_USB_VARIANTS:
                if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
                    self.fungible_page_objects.click_usb_sync_frame()

                if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                    self.usb_sync_dialog_page_objects.click_continue_button()

            if self.do_is_displayed(self.fungible_page_objects.psbt_info_frame()):
                self.fungible_page_objects.click_psbt_info_frame()

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.broadcast_transaction_page_objects.sign_psbt_button()):
                self.broadcast_transaction_page_objects.click_sign_psbt_button()

            if variant_name not in MULTISIG_VARIANTS:
                self.do_focus_on_application(CONFIRMATION_DIALOG)
                if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
                    self.confirmation_dialog_page_objects.click_confirmation_dialog()

                if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_checkbox()):
                    self.confirmation_dialog_page_objects.click_confirmation_checkbox()

                if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
                    self.confirmation_dialog_page_objects.click_confirmation_continue_button()

            if self.hw_emulator:
                if variant_name in MULTISIG_HARDWARE_VARIANTS:
                    self.sign_multisig_on_hardware_wallet(
                        LEDGER_EMULATOR_APP_NAME,
                    )
                else:
                    self.confirm_transaction_on_hardware_wallet(
                        LEDGER_EMULATOR_APP_NAME,
                        is_rgb=is_rgb,
                        is_inflate=is_inflate,
                        is_btc=is_btc,
                        is_online=is_online,
                        is_ifa=is_ifa,
                    )

                self.do_focus_on_application(application)

            if variant_name == ONLINE_WATCH_ONLY or variant_name in REQUIRE_USB_VARIANTS:
                self.usb_sync(is_receive=True)

        except Exception as e:
            raise e
        finally:
            if self.hw_emulator:
                self.hw_emulator.terminate()

    def broadcast_psbt(self, application, is_multisig: bool = False):
        """
        Broadcast psbt.
        """
        description = None
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
            self.sidebar_page_objects.click_fungibles_button()

        if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
            self.fungible_page_objects.click_usb_sync_frame()

        if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
            self.usb_sync_dialog_page_objects.click_continue_button()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

        if self.do_is_displayed(self.fungible_page_objects.psbt_info_frame()):
            self.fungible_page_objects.click_psbt_info_frame()

        if self.do_is_displayed(self.broadcast_transaction_page_objects.broadcast_button()):
            self.broadcast_transaction_page_objects.click_broadcast_button()

        if not is_multisig:
            self.do_focus_on_application(CONFIRMATION_DIALOG)
            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
                self.confirmation_dialog_page_objects.click_confirmation_dialog()

            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_checkbox()):
                self.confirmation_dialog_page_objects.click_confirmation_checkbox()

            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
                self.confirmation_dialog_page_objects.click_confirmation_continue_button()

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

        return description

    def confirm_transaction_on_hardware_wallet(
        self, application, is_rgb: bool = False,
        is_inflate: bool = False, is_online: bool = True, is_btc: bool = False,
        is_ifa: bool = False,
    ):
        """
        Confirm transaction on hardware wallet for single-sig.

        For online single-sig hardware wallet:
        - IFA issue: 2 UTXOs (4 right + both each), no final RGB signing
        - IFA inflate: 2 UTXOs (4 right + both each), then 5 right + both (RGB signing)
        - RGB send: 3 UTXOs (4 right + both each), then 5 right + both
        - BTC send: 5 right + both (no UTXOs needed)

        For offline single-sig hardware wallet (no UTXO creation needed):
        - RGB/inflate/BTC send: 4 right + both, then 5 right + both
        - NIA/CFA/IFA issue: 4 right + both

        Args:
            application: Application name.
            is_rgb: Whether this is an RGB send transaction.
            is_inflate: Whether this is an IFA inflate operation (for final RGB signing).
            is_online: Whether this is an online hardware wallet (True for online, False for offline).
            is_btc: Whether this is a BTC send transaction.
        """
        self.do_focus_on_application(application)
        # Longer delay for RGB sends to ensure Ledger is ready for UTXO signing
        initial_delay = 5 if (is_online and (is_inflate or is_rgb)) else 3
        time.sleep(initial_delay)

        # Determine UTXO count for online single-sig hardware wallet
        utxo_count = 0
        if is_online and (is_inflate or is_rgb):
            utxo_count = 2

        # Sign UTXOs first (for online hardware wallet)
        for i in range(utxo_count):
            self.do_focus_on_application(application)
            time.sleep(2)
            self.hw_emulator_page_objects.click_right_arrow_key(4)
            self.hw_emulator_page_objects.press_left_and_right()
            # Longer delay after each UTXO signing to let Ledger process
            # 2s between UTXOs, 1s before final
            time.sleep(2 if i < utxo_count - 1 else 1)

        # Final transaction signing
        if is_inflate or is_rgb:
            self.do_focus_on_application(application)
            time.sleep(1)
            self.hw_emulator_page_objects.click_right_arrow_key(5)
            self.hw_emulator_page_objects.press_left_and_right()
        elif is_btc and is_online:
            self.do_focus_on_application(application)
            time.sleep(1)
            self.hw_emulator_page_objects.click_right_arrow_key(5)
            self.hw_emulator_page_objects.press_left_and_right()
        else:
            itr = 2 if (is_ifa and is_online) else 1
            self.do_focus_on_application(application)
            for _ in range(itr):
                self.do_focus_on_application(application)
                time.sleep(2)
                self.hw_emulator_page_objects.click_right_arrow_key(4)
                self.hw_emulator_page_objects.press_left_and_right()
                time.sleep(1)

        time.sleep(2)

    def sign_multisig_on_hardware_wallet(self, application):
        """
        Sign multisig transaction on hardware wallet.
        Called after app sends SIGN_PSBT request.
        Sequence: 13 right + left+right (register policy), then 4 right + left+right (sign)
        """
        time.sleep(2)
        self.do_focus_on_application(application)
        # First sequence: 13 right arrows then left+right (register wallet policy)
        self.hw_emulator_page_objects.click_right_arrow_key(13, delay=0.8)
        self.hw_emulator_page_objects.press_left_and_right(duration=0.2)
        # Wait for sign transaction screen to appear
        self.do_focus_on_application(application)
        time.sleep(3)
        # Second sequence: 4 right arrows then left+right (sign transaction)
        self.hw_emulator_page_objects.click_right_arrow_key(4, delay=0.8)
        self.hw_emulator_page_objects.press_left_and_right(duration=0.2)
        time.sleep(2)

    def usb_sync(self, is_receive=False):
        """
        Sync wallet.
        """
        if is_receive:
            if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
                self.receive_asset_page_objects.click_receive_asset_close_button()
        else:
            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()

        if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
            self.fungible_page_objects.click_usb_sync_frame()

        if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
            self.usb_sync_dialog_page_objects.click_continue_button()
