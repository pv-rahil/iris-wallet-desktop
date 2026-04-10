# pylint: disable=consider-using-with, too-many-branches, too-many-lines, too-many-statements
"""
Wallet class for creating and funding a wallet.
"""
from __future__ import annotations

import os
import subprocess
import time

from dogtail.tree import root

from accessible_constant import APP2_NAME
from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import MULTISIG_VARIANTS
from accessible_constant import OFFLINE_CREATE_ON_DEVICE
from accessible_constant import OFFLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_WATCH_ONLY
from accessible_constant import ONLINE_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from accessible_constant import SECOND_APPLICATION
from accessible_constant import SECOND_APPLICATION_PATH
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
from e2e_tests.test.utilities.multisig_coordinator import get_multisig_coordinator
from e2e_tests.test.utilities.reset_app import delete_app_data
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import map_load_to_create
from e2e_tests.test.utilities.wallet_variants import map_to_load_variant
from e2e_tests.test.utilities.wallet_variants import resolve_steps as resolve_wallet_steps
from src.utils.constant import APP_NAME
from src.utils.local_store import local_store
from src.version import __version__

BACKUP_EMAIL_ID = os.getenv('BACKUP_EMAIL_ID')
BACKUP_EMAIL_PASSWORD = os.getenv('BACKUP_EMAIL_PASSWORD')


class Wallet(MainPageObjects, BaseOperations):
    """
    Initializes the Wallet class.
    """

    def __init__(self, application):
        super().__init__(application)

        self.address = None
        self.hw_emulator = None

    def _refresh_application(self, application_name: str | None = None):
        """
        Refresh the application node and reinitialize all page objects.
        Call this after the application is reset/relaunched to get fresh element references.

        Args:
            application_name: The name of the application to find. If None, uses self.application.name.
        """
        # Get the application name from parameter or existing application
        name = application_name
        if name:
            try:
                # Search through all iris applications to find the showing frame
                frame = None
                for app in root.applications():
                    if 'iris' in app.name.lower():
                        try:
                            found_frame = app.child(
                                roleName='frame', name=name,
                            )
                            if found_frame and found_frame.showing:
                                frame = found_frame
                                break
                        except Exception:
                            continue

                # Fallback to direct search if not found
                if not frame:
                    frame = root.child(
                        roleName='frame', name=name, showingOnly=True,
                    )

                self.application = frame
                # Reinitialize all page objects with fresh application
                super().__init__(self.application)
                print(f"[REFRESH] Successfully refreshed application: {name}")
            except Exception as e:
                print(f"[WARN] Failed to refresh application '{name}': {e}")

    def _resolve_effective_variant(self, application: str, variant: str, is_load_wallet: bool) -> str | None:
        """
        Resolve the effective variant based on application role and instance mode.
        Returns None if single-instance watch-only flow should be used.
        """
        env = self.get_current_environment()
        multi_instance = bool(env and getattr(env, 'num_instances', 1) >= 2)
        result: str | None = variant

        if variant == ONLINE_WATCH_ONLY:
            result = self._handle_online_watch_only_variant(
                application, multi_instance,
            )
        elif variant == ONLINE_MULTISIG_WATCH_ONLY:
            result = self._handle_online_multisig_watch_only_variant(
                application, multi_instance,
            )
        elif application == SECOND_APPLICATION:
            result = self._handle_second_application_variant(
                variant, is_load_wallet,
            )

        return result

    def _handle_online_watch_only_variant(self, application: str, multi_instance: bool) -> str | None:
        """Handle ONLINE_WATCH_ONLY variant resolution."""
        if multi_instance:
            return OFFLINE_CREATE_ON_DEVICE if application == FIRST_APPLICATION else ONLINE_WATCH_ONLY
        self.setup_watch_only_single_instance()
        return None

    def _handle_online_multisig_watch_only_variant(self, application: str, multi_instance: bool) -> str | None:
        """Handle ONLINE_MULTISIG_WATCH_ONLY variant resolution."""
        if multi_instance:
            return OFFLINE_MULTISIG_ON_DEVICE if application == FIRST_APPLICATION else ONLINE_MULTISIG_WATCH_ONLY
        self.setup_multisig_watch_only_single_instance()
        return None

    def _handle_second_application_variant(self, variant: str, is_load_wallet: bool) -> str:
        """Handle variant resolution for second application."""
        if is_load_wallet or variant in MULTISIG_VARIANTS:
            return variant
        return ONLINE_WATCH_ONLY if variant in REQUIRE_USB_VARIANTS else ONLINE_CREATE_ON_DEVICE

    def _accept_terms_and_conditions(self):
        """Accept terms and conditions if displayed."""
        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()
        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()

    def _handle_password_setup(self):
        """Handle password setup flow."""
        if self.do_is_displayed(self.set_password_page_objects.password_input()):
            self.set_password_page_objects.enter_password('walletpassword')
        if self.do_is_displayed(self.set_password_page_objects.confirm_password_input()):
            self.set_password_page_objects.enter_confirm_password(
                'walletpassword',
            )
        if self.do_is_displayed(self.set_password_page_objects.proceed_button()):
            self.set_password_page_objects.click_proceed_button()

    def create_wallet(self, application, variant: str, is_load_wallet: bool = False):
        """
        Creates a wallet.
        """
        self.do_focus_on_application(application)
        effective_variant = self._resolve_effective_variant(
            application, variant, is_load_wallet,
        )
        if effective_variant is None:
            return

        self._accept_terms_and_conditions()
        self.drive_selection_flow(application, effective_variant)

        if effective_variant in LOAD_WALLET_VARIANT:
            if self.do_is_displayed(self.welcome_page_objects.restore_button()):
                self.welcome_page_objects.click_restore_button()
            return

        if effective_variant in HARDWARE_WALLET_VARIANTS and effective_variant not in MULTISIG_HARDWARE_VARIANTS:
            self.set_up_hardware_wallet(application)

        if effective_variant not in MULTISIG_VARIANTS:
            if self.do_is_displayed(self.welcome_page_objects.create_button()):
                self.welcome_page_objects.click_create_button()

        if effective_variant == ONLINE_WATCH_ONLY:
            xpub_vanilla, xpub_colored, fingerprint, _ = self.collect_keyring_values_from_app()
            self.do_focus_on_application(application)
            self.set_up_watch_only_wallet(
                xpub_vanilla, xpub_colored, fingerprint,
            )

        self._handle_password_setup()

        # For watch-only multisig, the UI shows cosigner import cards, not export buttons
        # Register the application but skip key export (watch-only doesn't have its own keys)
        if effective_variant == ONLINE_MULTISIG_WATCH_ONLY:
            coordinator = get_multisig_coordinator()
            coordinator.register_application(application)
        elif effective_variant in MULTISIG_VARIANTS:
            self.initiate_multisig_setup(application, effective_variant)

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

    def setup_watch_only_single_instance(self):
        """Single-instance watch-only flow: spawn a temp second app, create offline wallet,
        collect xpubs/fingerprint, and configure the first app as watch-only.
        """
        env = self.get_current_environment()
        if not env:
            return
        # Prepare FIRST app to the watch-only dialog
        self.do_focus_on_application(FIRST_APPLICATION)
        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()
        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()
        self.drive_selection_flow(FIRST_APPLICATION, ONLINE_WATCH_ONLY)
        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()
        proc = None
        try:
            actual_path = os.path.dirname(local_store.get_path())
            app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
            delete_app_data(app2_data)
            # Launch temp second instance with default environment (not TestEnvironment)
            proc = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{
                    APP2_NAME
                }-{__version__}-x86_64.AppImage"],
                env=None,
            )
            # Wait for the second application window
            if hasattr(env, 'wait_for_application'):
                env.wait_for_application(SECOND_APPLICATION)
            # Maximize the second window for stability
            subprocess.run(
                [
                    'wmctrl', '-r', SECOND_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            second_app = root.child(roleName='frame', name=SECOND_APPLICATION)
            second_wallet = Wallet(second_app)
            second_wallet.create_wallet(
                SECOND_APPLICATION, OFFLINE_CREATE_ON_DEVICE, is_load_wallet=True,
            )

            xpub_vanilla, xpub_colored, fingerprint, _ = second_wallet.collect_keyring_values_from_app(
                SECOND_APPLICATION,
            )

            self.do_focus_on_application(FIRST_APPLICATION)
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
        except Exception as e:
            print(f"Error in setup_watch_only_single_instance: {e}")
        finally:
            # Safely terminate the temp second process
            try:
                if proc and hasattr(env, 'terminate_process'):
                    env.terminate_process(proc)
                elif proc:
                    proc.terminate()
            except Exception:
                pass

    def initiate_multisig_setup(self, application: str, wallet_variant: str | None = None):
        """
        Phase 1 of multisig setup: reach the exchange screen and store local data.
        """
        coordinator = get_multisig_coordinator()
        coordinator.register_application(application)

        self.do_focus_on_application(application)

        required_signers = 2
        try:
            if self.do_is_displayed(self.multisig_setup_page_objects.total_signer_input()):
                val = self.multisig_setup_page_objects.get_total_signer_value()
                if val and val.isdigit():
                    _total_signers = int(val)  # noqa: F841
            if self.do_is_displayed(self.multisig_setup_page_objects.required_signer_input()):
                val = self.multisig_setup_page_objects.get_required_signer_value()
                if val and val.isdigit():
                    required_signers = int(val)
        except (ValueError, TypeError):
            pass

        coordinator.set_threshold(required_signers)

        if self.do_is_displayed(self.multisig_setup_page_objects.continue_button()):
            self.multisig_setup_page_objects.click_continue_button()

        # Handle hardware wallet flow for multisig
        if wallet_variant and wallet_variant in MULTISIG_HARDWARE_VARIANTS:
            self.hw_emulator = self.set_up_hardware_wallet(
                application,
                reset_regtest_flag=False,
            )

        colored_xpub = None
        cosigner_string = None
        if self.do_is_displayed(self.multisig_setup_page_objects.colored_xpub_copy_button()):
            self.multisig_setup_page_objects.click_colored_xpub_copy_button()
            colored_xpub = self.multisig_setup_page_objects.do_get_copied_address()
        if self.do_is_displayed(self.multisig_setup_page_objects.cosigner_string_copy_button()):
            self.multisig_setup_page_objects.click_cosigner_string_copy_button()
            cosigner_string = self.multisig_setup_page_objects.do_get_copied_address()

        if colored_xpub:
            coordinator.store_colored_xpub(application, colored_xpub)
        if cosigner_string:
            coordinator.store_cosigner_string(application, cosigner_string)

    def import_multisig_data(self, application: str, import_all: bool = False):
        """
        Phase 2: Import the other cosigner's data.

        For watch-only multisig wallets (import_all=True):
        - Step 2 (Review frame): Enter first cosigner string (from App 1), click next
        - Step 3 (Cosigner frame): Enter remaining cosigner strings (index 2+), click continue

        For signer wallets (import_all=False):
        - Import only one other cosigner at index 2

        Args:
            application: Application name.
            import_all: If True, import all other cosigner strings (for watch-only wallets).
                       If False, import only one other cosigner (for signer wallets).
        """
        coordinator = get_multisig_coordinator()
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.multisig_setup_page_objects.continue_button()):
            self.multisig_setup_page_objects.click_continue_button()

        if import_all:
            # For watch-only wallets: import all other cosigners
            all_cosigners = coordinator.get_all_other_cosigner_strings(application)
            
            # Step 2 (Review frame): Enter first cosigner string (from App 1 - offline signer)
            if all_cosigners and len(all_cosigners) >= 1:
                _, first_cosigner_string = all_cosigners[0]
                if first_cosigner_string:
                    # Enter in the review frame input field
                    self.multisig_setup_page_objects.enter_review_cosigner_string(first_cosigner_string)
                    # Click next to proceed to cosigner frame
                    if self.do_is_displayed(self.multisig_setup_page_objects.continue_button()):
                        self.multisig_setup_page_objects.click_continue_button()
            
            # Step 3 (Cosigner frame): Enter remaining cosigner strings (from App 3, etc.)
            if len(all_cosigners) >= 2:
                for index, (_, cosigner_string) in enumerate(all_cosigners[1:], start=2):
                    if cosigner_string:
                        self.multisig_setup_page_objects.import_cosigner_data(
                            index, cosigner_string,
                        )
        else:
            # For signer wallets: import only one other cosigner
            other_cosigner_string = coordinator.get_other_cosigner_string(
                application,
            )
            if other_cosigner_string:
                self.multisig_setup_page_objects.import_cosigner_data(
                    2, other_cosigner_string,
                )

    def finalize_multisig_setup(self, application: str):
        """
        Phase 3: Finalize multisig setup and start services if needed.
        """
        coordinator = get_multisig_coordinator()
        self.do_focus_on_application(application)

        # Update bridge config once both wallets have their xpubs ready
        if len(coordinator.get_colored_xpubs()) >= 2 and not coordinator.is_bridge_updated():
            coordinator.update_bridge_config(coordinator.get_threshold())

        if self.do_is_displayed(self.multisig_setup_page_objects.continue_button()):
            self.multisig_setup_page_objects.click_continue_button()

        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()

    def save_multisig_load_credentials(self, application: str, is_hardware: bool = False, is_online: bool = False):
        """
        Save credentials from a multisig wallet for load flow.
        Call this after finalize_multisig_setup for load variants.

        Args:
            application: Application name.
            is_hardware: Whether this is a hardware wallet variant.
            is_online: Whether this is an online variant (needs online backup).
        """
        coordinator = get_multisig_coordinator()
        self.do_focus_on_application(application)

        if is_hardware:
            # Collect xpubs and fingerprint for hardware wallet
            xpub_vanilla, xpub_colored, fingerprint, password = self.collect_keyring_values_from_app(
                application, is_load_wallet=True,
            )
            coordinator.store_load_credentials(
                application,
                xpub_vanilla=xpub_vanilla,
                xpub_colored=xpub_colored,
                fingerprint=fingerprint,
                password=password,
            )
        else:
            # Collect mnemonic for software wallet
            mnemonic, password = self.collect_mnemonic_password(self)
            coordinator.store_load_credentials(
                application,
                mnemonic=mnemonic,
                password=password,
            )

        # Take backup after saving credentials
        if is_online:
            self.perform_online_backup(self)
        else:
            self.trigger_usb_sync(self)

    def load_multisig_wallet(self, application: str, is_hardware: bool = False, is_online: bool = False, wallet_variant_name: str | None = None):
        """
        Load a multisig wallet using saved credentials.
        Resets the app and loads wallet with stored credentials.

        Args:
            application: Application name.
            is_hardware: Whether this is a hardware wallet variant.
            is_online: Whether this is an online variant (uses Google auth).
        """
        coordinator = get_multisig_coordinator()
        credentials = coordinator.get_load_credentials(application)

        if not credentials:
            print(f"[ERROR] No load credentials found for {application}")
            return

        subprocess.run(['wmctrl', '-a', application], check=False)

        # Give window manager time to switch
        time.sleep(0.5)

        # Focus on the reset application
        # Note: env.reset_first_instance() already created fresh page objects
        self.do_focus_on_application(application)

        # Step 1: TNC scroll and accept
        self._accept_terms_and_conditions()

        if wallet_variant_name is not None:
            wallet_variant_name = map_to_load_variant(wallet_variant_name)
            self.drive_selection_flow(application, wallet_variant_name)

        # Step 3: Click restore button
        if self.do_is_displayed(self.welcome_page_objects.restore_button()):
            self.welcome_page_objects.click_restore_button()

        # Step 4: Restore with saved credentials via Google auth
        if is_online:
            # Online variant - use Google auth flow
            self.google_auth(
                mnemonic=credentials.get('mnemonic'),
                password=credentials.get('password'),
                xpub_vanilla=credentials.get('xpub_vanilla'),
                xpub_colored=credentials.get('xpub_colored'),
                fingerprint=credentials.get('fingerprint'),
            )
        elif is_hardware:
            self.restore_with_xpubs(
                credentials.get('xpub_vanilla'),
                credentials.get('xpub_colored'),
                credentials.get('fingerprint'),
                credentials.get('password'),
            )
        else:
            self.restore_with_mnemonic(
                credentials.get('mnemonic'),
                credentials.get('password'),
            )

        # Enter password and login
        password = credentials.get('password')
        if password and self.do_is_displayed(self.enter_wallet_password_page_objects.password_input()):
            self.enter_wallet_password_page_objects.enter_password(password)
        if self.do_is_displayed(self.enter_wallet_password_page_objects.login_button()):
            self.enter_wallet_password_page_objects.click_login_button()

    def setup_multisig_watch_only_single_instance(self):
        """
        Single-instance multisig watch-only flow: spawn a temp second app,
        create offline multisig wallet, collect xpubs/fingerprint,
        and configure the first app as multisig watch-only.
        """
        env = self.get_current_environment()
        if not env:
            return
        # Prepare FIRST app to the multisig watch-only dialog
        self.do_focus_on_application(FIRST_APPLICATION)
        if self.do_is_displayed(self.term_and_condition_page_objects.tnc_scrollbar()):
            self.term_and_condition_page_objects.scroll_to_end()
        if self.do_is_displayed(self.term_and_condition_page_objects.accept_button()):
            self.term_and_condition_page_objects.click_accept_button()
        self.drive_selection_flow(
            FIRST_APPLICATION, ONLINE_MULTISIG_WATCH_ONLY,
        )
        if self.do_is_displayed(self.welcome_page_objects.create_button()):
            self.welcome_page_objects.click_create_button()
        proc = None
        try:
            actual_path = os.path.dirname(local_store.get_path())
            app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
            delete_app_data(app2_data)
            # Launch temp second instance with default environment (not TestEnvironment)
            proc = subprocess.Popen(
                [f"e2e_tests/applications/iris-wallet-vault_{
                    APP2_NAME
                }-{__version__}-x86_64.AppImage"],
                env=None,
            )
            # Wait for the second application window
            if hasattr(env, 'wait_for_application'):
                env.wait_for_application(SECOND_APPLICATION)
            # Maximize the second window for stability
            subprocess.run(
                [
                    'wmctrl', '-r', SECOND_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            second_app = root.child(roleName='frame', name=SECOND_APPLICATION)
            second_wallet = Wallet(second_app)
            second_wallet.create_wallet(
                SECOND_APPLICATION, OFFLINE_MULTISIG_ON_DEVICE, is_load_wallet=True,
            )

            xpub_vanilla, xpub_colored, fingerprint, _ = second_wallet.collect_keyring_values_from_app(
                SECOND_APPLICATION,
            )

            self.do_focus_on_application(FIRST_APPLICATION)
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
        except Exception as e:
            print(f"Error in setup_multisig_watch_only_single_instance: {e}")
        finally:
            # Safely terminate the temp second process
            try:
                if proc and hasattr(env, 'terminate_process'):
                    env.terminate_process(proc)
                elif proc:
                    proc.terminate()
            except Exception:
                pass

    def create_and_fund_wallet(self, application, variant: str, fund=True, is_restore_wallet: bool = False):
        """
        Create a new wallet and fund it.
        """
        if is_restore_wallet:
            self.create_wallet(application, variant)

        elif application == FIRST_APPLICATION and variant in LOAD_WALLET_VARIANT and variant not in MULTISIG_VARIANTS:
            self.load_wallet(application, variant, fund)
            return
        else:
            self.create_wallet(application, variant)
            if fund:
                self.fund_wallet(application)

    def load_wallet(self, application, variant: str, fund: bool):
        """
        Load a wallet.

        For single-sig: Uses second app's credentials to load first app.
        """
        # Single-sig: Create wallet on second app and load first app with second's credentials
        self.do_focus_on_application(application)
        self.create_wallet(application, variant)

        mnemonic, password, xpub_vanilla, xpub_colored, fingerprint = self.setup_second_wallet(
            variant,
        )

        self.do_focus_on_application(application)

        if variant in REQUIRE_USB_VARIANTS:
            if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                self.usb_sync_dialog_page_objects.click_continue_button()
            if variant in HARDWARE_WALLET_VARIANTS:
                self.restore_with_xpubs(
                    xpub_vanilla, xpub_colored, fingerprint, password,
                )
            else:
                self.restore_with_mnemonic(mnemonic, password)
        else:
            self.google_auth(
                mnemonic=mnemonic, password=password, xpub_vanilla=xpub_vanilla,
                xpub_colored=xpub_colored, fingerprint=fingerprint,
            )

        if self.do_is_displayed(self.enter_wallet_password_page_objects.password_input()):
            self.enter_wallet_password_page_objects.enter_password(password)
        if self.do_is_displayed(self.enter_wallet_password_page_objects.login_button()):
            self.enter_wallet_password_page_objects.click_login_button()

        if variant not in REQUIRE_USB_VARIANTS and fund:
            self.fund_wallet(application)

        clear_fake_usb_mount_all()
        self.handle_second_instance_reset()

    def setup_second_wallet(self, variant: str) -> tuple:
        """Handles key retrieval and wallet setup for the second application.

        Only used for single-sig load: Creates wallet on second app, collects credentials.
        Multisig load is handled directly in load_wallet().
        """
        # Get the second app frame from the TestEnvironment to ensure correct app context
        env = self.get_current_environment()
        second_app = None
        if env and hasattr(env, 'second_application'):
            second_app = env.second_application
            print(f"[SETUP_SECOND] Using second_application from env: {
                  second_app
                  }")

        # Fallback to finding frame directly if not available from env
        if not second_app:
            second_app = root.child(roleName='frame', name=SECOND_APPLICATION)
            print(f"[SETUP_SECOND] Fallback: found frame from root: {
                  second_app
                  }")

        if not second_app:
            # mnemonic, password, xpub_vanilla, xpub_colored, fingerprint
            return None, None, None, None, None

        second_wallet = Wallet(second_app)
        create_variant = map_load_to_create(variant)

        mnemonic = password = xpub_vanilla = xpub_colored = fingerprint = None

        # Single-sig: Create wallet on second app and collect credentials from it
        second_wallet.create_wallet(
            SECOND_APPLICATION, create_variant, is_load_wallet=True,
        )
        second_wallet.do_focus_on_application(SECOND_APPLICATION)

        if variant in HARDWARE_WALLET_VARIANTS:
            xpub_vanilla, xpub_colored, fingerprint, password = second_wallet.collect_keyring_values_from_app(
                SECOND_APPLICATION, is_load_wallet=True,
            )
        else:
            mnemonic, password = self.collect_mnemonic_password(
                second_wallet,
            )

        if variant in REQUIRE_USB_VARIANTS:
            self.trigger_usb_sync(second_wallet)
        else:
            self.perform_online_backup(second_wallet)

        return mnemonic, password, xpub_vanilla, xpub_colored, fingerprint

    def collect_mnemonic_password(self, wallet: Wallet) -> tuple:
        """Collects mnemonic and password from the wallet."""
        mnemonic = password = None
        if wallet.do_is_displayed(wallet.sidebar_page_objects.settings_button()):
            wallet.sidebar_page_objects.click_settings_button()
        if wallet.do_is_displayed(wallet.settings_page_objects.keyring_toggle_button()):
            wallet.settings_page_objects.click_keyring_toggle_button()
        if wallet.do_is_displayed(wallet.keyring_dialog_page_objects.keyring_mnemonic_copy_button()):
            wallet.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
            mnemonic = wallet.keyring_dialog_page_objects.do_get_copied_address()
        if wallet.do_is_displayed(wallet.keyring_dialog_page_objects.keyring_password_copy_button()):
            wallet.keyring_dialog_page_objects.click_keyring_password_copy_button()
            password = wallet.keyring_dialog_page_objects.do_get_copied_address()
        if wallet.do_is_displayed(wallet.keyring_dialog_page_objects.cancel_button()):
            wallet.keyring_dialog_page_objects.click_cancel_button()
        return mnemonic, password

    def trigger_usb_sync(self, wallet: Wallet):
        """Triggers USB sync on the wallet.

        Uses wallet.application to ensure correct app is focused in multi-instance scenarios.
        """
        wallet.do_focus_on_application(wallet.application)
        if wallet.do_is_displayed(wallet.fungible_page_objects.usb_sync_frame()):
            wallet.fungible_page_objects.click_usb_sync_frame()
        if wallet.do_is_displayed(wallet.usb_sync_dialog_page_objects.continue_button()):
            wallet.usb_sync_dialog_page_objects.click_continue_button()

    def perform_online_backup(self, wallet: Wallet):
        """Performs online backup on the wallet."""
        if wallet.do_is_displayed(wallet.sidebar_page_objects.backup_button()):
            wallet.sidebar_page_objects.click_backup_button()
        if wallet.do_is_displayed(wallet.backup_page_objects.configure_button()):
            wallet.backup_page_objects.click_configurable_button()
        wallet.google_auth()
        if wallet.do_is_displayed(wallet.toaster_page_objects.toaster_close_button()):
            wallet.toaster_page_objects.click_toaster_close_button()
        if wallet.do_is_displayed(wallet.backup_page_objects.backup_wallet_data_button()):
            wallet.backup_page_objects.click_backup_wallet_data_button()
        if wallet.do_is_displayed(wallet.toaster_page_objects.toaster_frame()):
            wallet.toaster_page_objects.click_toaster_close_button()

    def handle_second_instance_reset(self):
        """Handle cleanup or reset of the second application instance after wallet load."""
        env = self.get_current_environment()
        if not env:
            return

        requested_instances = getattr(
            env, '_requested_instances', getattr(env, 'num_instances', 1),
        )
        originally_single = requested_instances < 2

        if originally_single:
            try:
                proc = getattr(env, 'second_process', None)
                if proc:
                    env.terminate_process(proc)
                    env.second_process = None
            except Exception:
                pass
        else:
            # Multi-instance mode: reset second instance
            env.reset_second_instance()

    def drive_selection_flow(self, application, variant: str):
        """
        Drive the 4-step selection flow using option indices (1 or 2).
        A step value of 0 means skip that selection step entirely.
        """
        step1, step2, step3, step4, step5 = resolve_wallet_steps(variant)
        self.do_focus_on_application(application)

        # Step 1: Wallet type (Standard/Multisig)
        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step1)
            self.selection_page_objects.click_continue_button()

        # Step 2: Network type (Online/Offline)
        if self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step2)
            self.selection_page_objects.click_continue_button()

        # Step 3: Connection mode (0 = skip for offline variants)
        if step3 != 0 and self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step3)
            self.selection_page_objects.click_continue_button()

        # Step 4: Entry type (Create/Load)
        if step4 != 0 and self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step4)
            self.selection_page_objects.click_continue_button()

        # Step 5: Device type (On-device/Hardware)
        if step5 != 0 and self.do_is_displayed(self.selection_page_objects.option_1_button()):
            self.selection_page_objects.select_option(step5)
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

        # Get the first app frame from the TestEnvironment to ensure correct app context
        # This is the same approach used in setup_second_wallet for the second app
        env = self.get_current_environment()
        first_app = None
        if env and hasattr(env, 'first_application'):
            first_app = env.first_application
        if env and hasattr(env, 'second_application'):
            first_app = env.second_application

        # Fallback to finding frame directly if not available from env
        if not first_app:
            first_app = root.child(roleName='frame', name=app_name)

        if not first_app:
            return None, None, None, None

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

    def sign_psbt(self, application, variant_name, is_rgb: bool = False, is_issue_ifa: bool = False):
        """
        Sign psbt.
        """
        try:
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.sidebar_page_objects.fungibles_button()):
                self.sidebar_page_objects.click_fungibles_button()

            if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
                self.fungible_page_objects.click_refresh_button()

            if variant_name == ONLINE_WATCH_ONLY:
                if self.do_is_displayed(self.fungible_page_objects.usb_sync_frame()):
                    self.fungible_page_objects.click_usb_sync_frame()

                if self.do_is_displayed(self.usb_sync_dialog_page_objects.continue_button()):
                    self.usb_sync_dialog_page_objects.click_continue_button()

            if self.do_is_displayed(self.fungible_page_objects.psbt_info_frame()):
                self.fungible_page_objects.click_psbt_info_frame()

            if variant_name in HARDWARE_WALLET_VARIANTS:
                # RGB Ledger app can sign both BTC and RGB transactions
                self.hw_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )

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
                        LEDGER_EMULATOR_APP_NAME, is_rgb, is_issue_ifa,
                    )

                self.do_focus_on_application(application)

            if variant_name == ONLINE_WATCH_ONLY:
                self.usb_sync(is_receive=True)

        except Exception as e:
            raise e
        finally:
            if self.hw_emulator:
                self.hw_emulator.terminate()

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

        _, description = self.toaster_page_objects.click_toaster_frame()

        if self.do_is_displayed(self.fungible_page_objects.refresh_button()):
            self.fungible_page_objects.click_refresh_button()

        return description

    def confirm_transaction_on_hardware_wallet(self, application, is_rgb: bool = False, is_issue_ifa: bool = False):
        """
        Confirm transaction on hardware wallet for single-sig.
        - For RGB/inflate: 4 right + both, then 5 right + both
        - For NIA/CFA/IFA/send BTC: 4 right + both
        """
        self.do_focus_on_application(application)
        time.sleep(3)
        if is_rgb or is_issue_ifa:
            # RGB or inflate: 4 right + both, then 5 right + both
            self.hw_emulator_page_objects.click_right_arrow_key(4)
            self.hw_emulator_page_objects.press_left_and_right()
            time.sleep(1)
            self.hw_emulator_page_objects.click_right_arrow_key(5)
            self.hw_emulator_page_objects.press_left_and_right()
        else:
            # NIA or send BTC: 4 right + both
            self.hw_emulator_page_objects.click_right_arrow_key(4)
            self.hw_emulator_page_objects.press_left_and_right()
        
        time.sleep(2)

    def sign_multisig_on_hardware_wallet(self, application):
        """
        Sign multisig transaction on hardware wallet.
        Called after app sends SIGN_PSBT request.
        Sequence: 13 right + left+right (register policy), then 4 right + left+right (sign)
        """
        self.do_focus_on_application(application)
        # First sequence: 13 right arrows then left+right (register wallet policy)
        self.hw_emulator_page_objects.click_right_arrow_key(13, delay=0.8)
        self.hw_emulator_page_objects.press_left_and_right(duration=0.2)
        # Wait for sign transaction screen to appear
        time.sleep(2)
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
