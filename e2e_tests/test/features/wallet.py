# pylint: disable=too-many-branches
"""
Wallet class for creating and funding a wallet.
"""
from __future__ import annotations

import os
import time

from dogtail.tree import root

from accessible_constant import BITCOIN_LEDGER_APP_NAME
from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import ONLINE_CREATE_ON_DEVICE
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
from e2e_tests.test.utilities.executable_shell_script import mine
from e2e_tests.test.utilities.executable_shell_script import send_to_address
from e2e_tests.test.utilities.fake_usb import clear_fake_usb_mount_all
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import map_load_to_create
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
        self.hardware_wallet = None

    def create_wallet(self, application, variant: str, is_load_wallet: bool = False):
        """
        Creates a wallet.
        """
        self.do_focus_on_application(application)

        # Second app should be watch-only when primary variant is offline
        if application == SECOND_APPLICATION:
            if is_load_wallet:
                effective_variant = variant
            else:
                if variant in REQUIRE_USB_VARIANTS:
                    effective_variant = ONLINE_WATCH_ONLY
                else:
                    effective_variant = ONLINE_CREATE_ON_DEVICE
        else:
            effective_variant = variant

        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()

        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()

        self.drive_selection_flow(application, effective_variant)

        if effective_variant in LOAD_WALLET_VARIANT:
            if self.do_is_displayed(self.welcome_page_objects.restore_button()):
                self.welcome_page_objects.click_restore_button()
            return

        if effective_variant in HARDWARE_WALLET_VARIANTS:
            self.set_up_hardware_wallet(application)

        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()

        if effective_variant == ONLINE_WATCH_ONLY:
            xpub_vanilla, xpub_colored, fingerprint,_ = self.collect_keyring_values_from_app()
            self.do_focus_on_application(application)
            self.set_up_watch_only_wallet(
                xpub_vanilla, xpub_colored, fingerprint,
            )

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
        print('wrong call')

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
        if application == FIRST_APPLICATION and variant in LOAD_WALLET_VARIANT:
            self.load_wallet(application, variant)
            return
        self.create_wallet(application, variant)
        if fund:
            self.fund_wallet(application)

    def load_wallet(self, application, variant: str):
        """
        Drive the wallet "load/restore" flow for the given variant.

        This will navigate the selection steps and open the Restore flow on the
        welcome page. The caller/test is responsible for providing credentials
        (via google_auth or USB sync flows) and any subsequent steps.
        """
        self.do_focus_on_application(application)

        self.create_wallet(application, variant)
        
        second_app = root.child(roleName='frame', name=SECOND_APPLICATION)

        if not second_app:
            return

        second_wallet = Wallet(second_app)

        create_variant = map_load_to_create(variant)

        second_wallet.create_wallet(SECOND_APPLICATION, create_variant, is_load_wallet=True)

        mnemonic = None
        password = None
        xpub_vanilla = None
        xpub_colored = None
        fingerprint = None

        second_wallet.do_focus_on_application(SECOND_APPLICATION)
        
        if variant in HARDWARE_WALLET_VARIANTS:
            xpub_vanilla, xpub_colored, fingerprint, password = second_wallet.collect_keyring_values_from_app(SECOND_APPLICATION, is_load_wallet=True)
        else:
            if second_wallet.do_is_displayed(second_wallet.sidebar_page_objects.settings_button()):
                second_wallet.sidebar_page_objects.click_settings_button()
            if second_wallet.do_is_displayed(second_wallet.settings_page_objects.keyring_toggle_button()):
                second_wallet.settings_page_objects.click_keyring_toggle_button()
            if second_wallet.do_is_displayed(second_wallet.keyring_dialog_page_objects.keyring_mnemonic_copy_button()):
                second_wallet.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
                mnemonic = second_wallet.keyring_dialog_page_objects.do_get_copied_address()
            if second_wallet.do_is_displayed(second_wallet.keyring_dialog_page_objects.keyring_password_copy_button()):
                second_wallet.keyring_dialog_page_objects.click_keyring_password_copy_button()
                password = second_wallet.keyring_dialog_page_objects.do_get_copied_address()
            if second_wallet.do_is_displayed(second_wallet.keyring_dialog_page_objects.cancel_button()):
                second_wallet.keyring_dialog_page_objects.click_cancel_button()

        # For online flows, perform Google auth and trigger backup on second app
        if variant in REQUIRE_USB_VARIANTS:
            # Trigger USB sync on second app
            second_wallet.do_focus_on_application(SECOND_APPLICATION)
            if second_wallet.do_is_displayed(second_wallet.fungible_page_objects.usb_sync_frame()):
                second_wallet.fungible_page_objects.click_usb_sync_frame()
            if second_wallet.do_is_displayed(second_wallet.usb_sync_dialog_page_objects.continue_button()):
                second_wallet.usb_sync_dialog_page_objects.click_continue_button()

        else:
            if second_wallet.do_is_displayed(second_wallet.sidebar_page_objects.backup_button()):
                second_wallet.sidebar_page_objects.click_backup_button()
            if second_wallet.do_is_displayed(second_wallet.backup_page_objects.configure_button()):
                second_wallet.backup_page_objects.click_configurable_button()
            second_wallet.google_auth()
            if second_wallet.do_is_displayed(second_wallet.toaster_page_objects.toaster_close_button()):
                second_wallet.toaster_page_objects.click_toaster_close_button()
            if second_wallet.do_is_displayed(second_wallet.backup_page_objects.backup_wallet_data_button()):
                second_wallet.backup_page_objects.click_backup_wallet_data_button()

        # Now focus back to the first app and complete the restore with collected credentials
        self.do_focus_on_application(application)

        if variant in REQUIRE_USB_VARIANTS:
            if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                self.usb_sync_dialog_page_objects.click_continue_button()
            if variant in HARDWARE_WALLET_VARIANTS:
                self.restore_with_xpubs(
                    xpub_vanilla=xpub_vanilla,
                    xpub_colored=xpub_colored,
                    fingerprint=fingerprint,
                    password=password,
                )
            else:
                self.restore_with_mnemonic(
                    mnemonic=mnemonic,
                    password=password,
                )
        else:
            # Online path: use Google auth flow
            if variant in HARDWARE_WALLET_VARIANTS:
                self.google_auth(
                    xpub_vanilla=xpub_vanilla,
                    xpub_colored=xpub_colored,
                    fingerprint=fingerprint,
                    password=password,
                )
            else:
                self.google_auth(
                    mnemonic=mnemonic,
                    password=password,
                )
        if self.do_is_displayed(self.enter_wallet_password_page_objects.password_input()):
            self.enter_wallet_password_page_objects.enter_password(password)
        if self.do_is_displayed(self.enter_wallet_password_page_objects.login_button()):
            self.enter_wallet_password_page_objects.click_login_button()
        
        clear_fake_usb_mount_all()

        from e2e_tests.test.utilities.app_setup import get_current_environment
        env = get_current_environment()
        if env:
            # If running single-instance tests, kill the temporary second instance we spawned
            if getattr(env, 'num_instances', 2) < 2:
                try:
                    env.terminate_process(getattr(env, 'second_process', None))
                    env.second_process = None
                except Exception:
                    pass
            else:
                # In multi-instance mode, simply reset the second instance to refresh state
                env.reset_second_instance()

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
            self.restore_wallet_page_objects.enter_xpub_vanilla_value(xpub_vanilla)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_xpub_colored_input()) and xpub_colored:
            self.restore_wallet_page_objects.enter_xpub_colored_value(xpub_colored)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_fingerprint_input()) and fingerprint:
            self.restore_wallet_page_objects.enter_fingerprint_value(fingerprint)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_password_input()) and password:
            self.restore_wallet_page_objects.enter_password_value(password)
        if self.do_is_displayed(self.restore_wallet_page_objects.restore_continue_button()):
            self.restore_wallet_page_objects.click_continue_button()

    def set_up_hardware_wallet(self, application):
        """
        Set up the hardware wallet.
        """
        try:
            speculos_process = handle_hardware_wallet(
                app_name=BITCOIN_LEDGER_APP_NAME, reset=True,
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
            self.hw_emulator_page_objects.click_right_arrow_key(7)
            self.hw_emulator_page_objects.press_left_and_right()
            self.do_focus_on_application(application)
            time.sleep(2)
        except Exception as e:
            raise e
        finally:
            speculos_process.terminate()

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

    def collect_keyring_values_from_app(self,app_name:str = FIRST_APPLICATION, is_load_wallet:bool = False) -> tuple[str | None, str | None, str | None]:
        """Focus the first application and read xpubs + fingerprint from About page copy buttons."""
        self.do_focus_on_application(app_name)
        try:
            first_app = root.child(roleName='frame', name=app_name)
        except Exception:
            first_app = None

        if not first_app:
            return None, None, None

        sidebar_page = SidebarPageObjects(first_app)
        about_page = AboutPageObjects(first_app)
        setting_page = SettingsPageObjects(first_app)
        keyring_dialog_page = KeyringDialogBoxPageObjects(first_app)

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

    def sign_psbt(self, application, variant_name, is_rgb: bool = False):
        """
        Sign psbt.
        """
        try:
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()

            if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
                self.fungible_page_objects.click_usb_sync_frame()

            if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                self.usb_sync_dialog_page_objects.click_continue_button()

            if self.do_is_displayed(self.fungible_page_objects.psbt_info_frame()):
                self.fungible_page_objects.click_psbt_info_frame()

            if variant_name in HARDWARE_WALLET_VARIANTS:
                if is_rgb:
                    self.hardware_wallet = handle_hardware_wallet(
                        app_name=RGB_LEDGER_APP_NAME,
                    )
                else:
                    self.hardware_wallet = handle_hardware_wallet(
                        app_name=BITCOIN_LEDGER_APP_NAME,
                    )

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.broadcast_transaction_page_objects.sign_psbt_button()):
                self.broadcast_transaction_page_objects.click_sign_psbt_button()

            self.do_focus_on_application(CONFIRMATION_DIALOG)
            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
                self.confirmation_dialog_page_objects.click_confirmation_dialog()

            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_checkbox()):
                self.confirmation_dialog_page_objects.click_confirmation_checkbox()

            if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
                self.confirmation_dialog_page_objects.click_confirmation_continue_button()

            if self.hardware_wallet:
                self.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_rgb)

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
                self.receive_asset_page_objects.click_receive_asset_close_button()

            if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
                self.fungible_page_objects.click_usb_sync_frame()

            if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                self.usb_sync_dialog_page_objects.click_continue_button()

        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                self.hardware_wallet.terminate()

    def broadcast_psbt(self, application):
        """
        Broadcast psbt.
        """
        description = None
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
            self.fungible_page_objects.click_usb_sync_frame()

        if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
            self.usb_sync_dialog_page_objects.click_continue_button()

        if self.do_is_displayed(self.fungible_page_objects.psbt_info_frame()):
            self.fungible_page_objects.click_psbt_info_frame()

        if self.do_is_displayed(self.broadcast_transaction_page_objects.broadcast_button()):
            self.broadcast_transaction_page_objects.click_broadcast_button()

        self.do_focus_on_application(CONFIRMATION_DIALOG)
        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
            self.confirmation_dialog_page_objects.click_confirmation_dialog()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_checkbox()):
            self.confirmation_dialog_page_objects.click_confirmation_checkbox()

        if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
            self.confirmation_dialog_page_objects.click_confirmation_continue_button()

        if self.do_is_displayed(self.toaster_page_objects.toaster_frame()):
            self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.toaster_page_objects.toaster_description()):
            description = self.toaster_page_objects.get_toaster_description()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

        return description

    def confirm_transaction_on_hardware_wallet(self, application, is_rgb: bool = False):
        """
        Confirm transaction on hardware wallet.
        """
        self.do_focus_on_application(application)
        time.sleep(3)
        if is_rgb:
            self.hw_emulator_page_objects.click_right_arrow_key(5)
            self.hw_emulator_page_objects.press_left_and_right()
        else:
            for _ in range(2):
                self.hw_emulator_page_objects.click_right_arrow_key(4)
                self.hw_emulator_page_objects.press_left_and_right()
            self.hw_emulator_page_objects.click_right_arrow_key(1)
            self.hw_emulator_page_objects.press_left_and_right()
