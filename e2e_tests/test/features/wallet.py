# pylint: disable=consider-using-with, too-many-branches, too-many-statements, too-many-nested-blocks, too-many-public-methods
"""
Wallet class for creating and funding a wallet.
"""
from __future__ import annotations

import os
import subprocess
import time

from dogtail.tree import root

from accessible_constant import APP2_NAME
from accessible_constant import APP3_NAME
from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import MULTISIG_VARIANTS
from accessible_constant import OFFLINE_CREATE_ON_DEVICE
from accessible_constant import OFFLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_WATCH_ONLY
from accessible_constant import ONLINE_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import SECOND_APPLICATION
from accessible_constant import SECOND_APPLICATION_PATH
from accessible_constant import THIRD_APPLICATION
from accessible_constant import THIRD_APPLICATION_PATH
from e2e_tests.test.features.wallet_operations import WalletOperationsMixin
from e2e_tests.test.utilities.atspi_helpers import refresh_atspi_tree
from e2e_tests.test.utilities.dogtail_config import is_ci_environment
from e2e_tests.test.utilities.executable_shell_script import mine
from e2e_tests.test.utilities.executable_shell_script import send_to_address
from e2e_tests.test.utilities.fake_usb import clear_fake_usb_mount_all
from e2e_tests.test.utilities.multisig_coordinator import get_multisig_coordinator
from e2e_tests.test.utilities.reset_app import delete_app_data
from e2e_tests.test.utilities.wallet_variants import map_load_to_create
from e2e_tests.test.utilities.wallet_variants import map_to_load_variant
from e2e_tests.test.utilities.wallet_variants import resolve_steps as resolve_wallet_steps
from src.utils.constant import APP_NAME
from src.utils.local_store import local_store
from src.version import __version__


class Wallet(WalletOperationsMixin):
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

    def _handle_password_setup(self, wallet_and_operation=None):
        """Handle password setup flow."""
        if wallet_and_operation:
            wallet = wallet_and_operation
        else:
            wallet = self
        if wallet.do_is_displayed(wallet.set_password_page_objects.password_input()):
            wallet.set_password_page_objects.enter_password(
                'walletpassword',
            )
        if wallet.do_is_displayed(wallet.set_password_page_objects.confirm_password_input()):
            wallet.set_password_page_objects.enter_confirm_password(
                'walletpassword',
            )
        if wallet.do_is_displayed(wallet.set_password_page_objects.proceed_button()):
            wallet.set_password_page_objects.click_proceed_button()

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

        # Refresh AT-SPI tree after wallet creation to get fresh element references
        refresh_atspi_tree()
        time.sleep(0.5)

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
            # Launch temp second instance with proper environment for AT-SPI
            app_env = os.environ.copy()
            app_env['QT_ACCESSIBILITY'] = '1'
            proc = subprocess.Popen(
                [f"""e2e_tests/applications/iris-wallet-vault_{
                    APP2_NAME
                }-{__version__}-x86_64.AppImage"""],
                env=app_env,
            )
            # Wait for the second application window using TestEnvironment method
            env.wait_for_application(SECOND_APPLICATION)
            # Maximize the second window for stability
            subprocess.run(
                [
                    'wmctrl', '-r', SECOND_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            # Use TestEnvironment's method to find the application frame
            app_node = env.find_application_node(SECOND_APPLICATION)
            if app_node:
                second_app = app_node.child(
                    roleName='frame', name=SECOND_APPLICATION,
                )
            else:
                # Fallback to direct search
                second_app = root.child(
                    roleName='frame', name=SECOND_APPLICATION,
                )
            second_wallet = Wallet(second_app)
            second_wallet.create_wallet(
                SECOND_APPLICATION, OFFLINE_CREATE_ON_DEVICE, is_load_wallet=True,
            )

            # Refresh AT-SPI tree after wallet creation to get fresh element references
            refresh_atspi_tree()
            time.sleep(1)

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
                if proc:
                    env.terminate_process(proc)
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
            all_cosigners = coordinator.get_all_other_cosigner_strings(
                application,
            )

            # Step 2 (Review frame): Enter first cosigner string (from App 1 - offline signer)
            if all_cosigners and len(all_cosigners) >= 1:
                _, first_cosigner_string = all_cosigners[0]
                if first_cosigner_string:
                    # Enter in the review frame input field
                    self.multisig_setup_page_objects.enter_review_cosigner_string(
                        first_cosigner_string,
                    )
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

        # Refresh AT-SPI tree after wallet load to get fresh element references
        refresh_atspi_tree()
        time.sleep(1)

    def setup_multisig_watch_only_with_temp_signer(self, wallets_and_operations):
        """
        Setup watch-only wallet for 2-app multisig tests.
        App 1 = watch-only (main wallet for tests)
        App 2 = signer 1 (already running)
        Spawn temp App 3 = signer 2

        Flow:
        1. Setup App 2 as signer (OFFLINE_MULTISIG_ON_DEVICE)
        2. Spawn temp App 3 as second signer
        3. Setup multisig on both signers
        4. Setup watch-only on App 1 with cosigner data from both signers

        Args:
            wallets_and_operations: Wallet test setup instance.
        """
        env = self.get_current_environment()
        if not env:
            return

        coordinator = get_multisig_coordinator()
        coordinator.reset()

        # Get correct wallet instances for each app
        second_wallet = wallets_and_operations.second_page_features.wallet_features

        proc = None
        try:
            # Step 1: Setup App 2 as first signer
            second_wallet.do_focus_on_application(SECOND_APPLICATION)
            if second_wallet.do_is_displayed(second_wallet.term_and_condition_page_objects.tnc_scrollbar()):
                second_wallet.term_and_condition_page_objects.scroll_to_end()
            if second_wallet.do_is_displayed(second_wallet.term_and_condition_page_objects.accept_button()):
                second_wallet.term_and_condition_page_objects.click_accept_button()
            second_wallet.drive_selection_flow(
                SECOND_APPLICATION, OFFLINE_MULTISIG_ON_DEVICE,
            )
            if second_wallet.do_is_displayed(second_wallet.welcome_page_objects.create_button()):
                second_wallet.welcome_page_objects.click_create_button()
            self._handle_password_setup(second_wallet)
            second_wallet.initiate_multisig_setup(
                SECOND_APPLICATION, OFFLINE_MULTISIG_ON_DEVICE,
            )

            # Step 2: Spawn temp App 3 as second signer
            actual_path = os.path.dirname(local_store.get_path())
            app3_data = actual_path.replace(APP_NAME, THIRD_APPLICATION_PATH)
            delete_app_data(app3_data)

            app_env = os.environ.copy()
            app_env['QT_ACCESSIBILITY'] = '1'

            proc = subprocess.Popen(
                [f"""e2e_tests/applications/iris-wallet-vault_{
                    APP3_NAME
                }-{__version__}-x86_64.AppImage"""],
                env=app_env,
            )
            env.wait_for_application(THIRD_APPLICATION)
            subprocess.run(
                [
                    'wmctrl', '-r', THIRD_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )

            # Get reference to temp third app
            app3_node = env.find_application_node(THIRD_APPLICATION)
            if app3_node:
                third_app = app3_node.child(
                    roleName='frame', name=THIRD_APPLICATION,
                )
            else:
                third_app = root.child(
                    roleName='frame', name=THIRD_APPLICATION,
                )

            third_wallet = Wallet(third_app)

            # Step 3: Setup App 3 as second signer
            third_wallet.do_focus_on_application(THIRD_APPLICATION)
            if third_wallet.do_is_displayed(third_wallet.term_and_condition_page_objects.tnc_scrollbar()):
                third_wallet.term_and_condition_page_objects.scroll_to_end()
            if third_wallet.do_is_displayed(third_wallet.term_and_condition_page_objects.accept_button()):
                third_wallet.term_and_condition_page_objects.click_accept_button()
            third_wallet.drive_selection_flow(
                THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
            )
            if third_wallet.do_is_displayed(third_wallet.welcome_page_objects.create_button()):
                third_wallet.welcome_page_objects.click_create_button()
            self._handle_password_setup(third_wallet)
            third_wallet.initiate_multisig_setup(
                THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
            )

            refresh_atspi_tree()
            time.sleep(1)

            # Step 4: Import cosigner data on both signers
            second_wallet.do_focus_on_application(SECOND_APPLICATION)
            second_wallet.import_multisig_data(
                SECOND_APPLICATION, import_all=False,
            )
            third_wallet.import_multisig_data(
                THIRD_APPLICATION, import_all=False,
            )

            # Step 5: Finalize both signers
            second_wallet.finalize_multisig_setup(SECOND_APPLICATION)
            third_wallet.finalize_multisig_setup(THIRD_APPLICATION)

            refresh_atspi_tree()
            time.sleep(1)

            # Step 6: Setup watch-only on App 1 (self = first_page_features.wallet_features)
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

            if self.do_is_displayed(self.set_password_page_objects.password_input()):
                self.set_password_page_objects.enter_password('walletpassword')
            if self.do_is_displayed(self.set_password_page_objects.confirm_password_input()):
                self.set_password_page_objects.enter_confirm_password(
                    'walletpassword',
                )
            if self.do_is_displayed(self.set_password_page_objects.proceed_button()):
                self.set_password_page_objects.click_proceed_button()

            # Import all cosigner data for watch-only (from both signers)
            self.import_multisig_data(FIRST_APPLICATION, import_all=True)

            # Finalize watch-only setup
            self.finalize_multisig_setup(FIRST_APPLICATION)

        except Exception as e:
            print(f"Error in setup_multisig_watch_only_with_temp_signer: {e}")
        finally:
            # Safely terminate the temp third process
            try:
                if proc:
                    env.terminate_process(proc)
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
        if is_ci_environment():
            for _ in range(3):
                refresh_atspi_tree()
                time.sleep(0.5)
            # Longer delay to let UI settle after wallet load in CI
            time.sleep(1.5)

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
            print(f"""[SETUP_SECOND] Using second_application from env:
                  {second_app}""")

        # Fallback to finding frame directly if not available from env
        if not second_app:
            second_app = root.child(roleName='frame', name=SECOND_APPLICATION)
            print(f"""[SETUP_SECOND] Fallback: found frame from root:
                  {second_app}""")

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

        # Handle wallet mode summary dialog if it appears, otherwise click continue on selection page
        for _ in range(3):
            if self.do_is_displayed(self.wallet_mode_summary_dialog_page_objects.continue_button()):
                self.wallet_mode_summary_dialog_page_objects.click_continue_button()
                break
            if self.do_is_displayed(self.selection_page_objects.continue_button()):
                self.selection_page_objects.continue_button().click()
            else:
                break
