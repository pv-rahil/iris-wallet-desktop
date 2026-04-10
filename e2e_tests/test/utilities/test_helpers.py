# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements
"""
Common test helpers for e2e tests to reduce code duplication.
"""
from __future__ import annotations

import threading
import allure

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import MULTISIG_LOAD_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.executable_shell_script import mine
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import map_load_to_create
from src.model.enums.enums_model import TransactionStatusEnumModel


class BaseIssueAsset:
    """
    Base class for issue asset feature classes providing common hardware wallet handling.
    """

    hardware_wallet_emulator = None

    def _init_hardware_wallet(self, variant_name: str | None, app_name: str) -> bool:
        """
        Initialize hardware wallet emulator if variant requires it.

        Args:
            variant_name: Wallet variant name.
            app_name: Ledger app name.

        Returns:
            True if hardware wallet was initialized.
        """
        if variant_name in HARDWARE_WALLET_VARIANTS:
            self.hardware_wallet_emulator = handle_hardware_wallet(
                app_name=app_name,
            )
            return True
        return False

    def _cleanup_hardware_wallet(self) -> None:
        """Clean up hardware wallet emulator if it exists."""
        if self.hardware_wallet_emulator:
            self.hardware_wallet_emulator.terminate()
            self.hardware_wallet_emulator = None


def verify_invalid_invoice_validation(
    page_objects,
    invoice: str,
    expected_message: str,
) -> str:
    """
    Verify invalid invoice validation.

    Args:
        page_objects: Page objects instance.
        invoice: Invoice to validate.
        expected_message: Expected validation message.

    Returns:
        Validation label text.
    """
    with allure.step('Enter invalid invoice'):
        page_objects.send_asset_page_objects.enter_asset_invoice(
            invoice,
        )
    with allure.step('get the asset invoice validation label'):
        validation_label = page_objects.send_asset_page_objects.get_asset_address_validation_label()
        page_objects.send_asset_page_objects.click_send_asset_close_button()

    with allure.step('Verify error message'):
        assert validation_label == expected_message

    return validation_label


def verify_expired_invoice_validation(
    wallets_and_operations,
    asset_name: str,
    invoice: str,
    expected_message: str,
    asset_type: str = 'ifa',
) -> str:
    """
    Navigate to asset, click send, and verify expired/invalid invoice validation.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name.
        invoice: Invoice to validate.
        expected_message: Expected validation message.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Validation label text.
    """
    with allure.step(f'Navigate to {asset_type} asset and click send'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_objects.send_asset_page_objects.enter_asset_invoice(
            invoice,
        )

    with allure.step('get the asset invoice validation label (offline wallet)'):
        validation_label = wallets_and_operations.second_page_objects.send_asset_page_objects.get_asset_address_validation_label()
        wallets_and_operations.second_page_objects.send_asset_page_objects.click_send_asset_close_button()

    with allure.step(f'Verify error message for {asset_type} asset (offline wallet)'):
        assert validation_label == expected_message

    return validation_label


def send_asset_with_invoice(
    send_features,
    application,
    invoice: str,
    amount: str,
    wallet_variant_name: str | None = None,
    purpose: str = 'send_asset',
) -> None:
    """
    Send asset with invoice, handling hardware wallet variant.

    Args:
        send_features: Send features instance.
        application: Application instance.
        invoice: Receiver invoice.
        amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        purpose: Purpose string.
    """
    if wallet_variant_name and wallet_variant_name in HARDWARE_WALLET_VARIANTS:
        send_features.send(
            application=application,
            receiver_invoice=invoice,
            amount=amount,
            is_hardware_wallet=True,
            purpose=purpose,
        )
    else:
        send_features.send(
            application=application,
            receiver_invoice=invoice,
            amount=amount,
        )


def send_asset_flow_with_verification(
    wallets_and_operations,
    invoice: str,
    asset_name: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'ifa',
    expected_status: str | None = None,
) -> None:
    """
    Combined helper for navigating to asset, sending, and verifying transfer status.

    Args:
        wallets_and_operations: Wallet test setup instance.
        invoice: Invoice for sending.
        asset_name: Asset name.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        expected_status: Expected transfer status (default: WAITING_COUNTERPARTY).
    """
    if expected_status is None:
        expected_status = TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    with allure.step(f'Navigate to {asset_type} asset and send'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            asset_name,
            asset_type=asset_type,
        )
        send_asset_with_invoice(
            wallets_and_operations.first_page_features.send_features,
            FIRST_APPLICATION,
            invoice,
            send_amount,
            wallet_variant_name,
        )

    with allure.step('Verify transfer status and received amount'):
        verify_transfer_status_and_received_amount(
            wallets_and_operations.first_page_objects,
            wallets_and_operations.second_page_objects,
            wallets_and_operations.second_page_operations,
            asset_name,
            send_amount,
            expected_status,
            asset_type=asset_type,
        )


def verify_transfer_status_and_received_amount(
    first_page_objects,
    second_page_objects,
    second_page_operations,
    asset_name: str,
    expected_amount: str,
    expected_status: str,
    asset_type: str = 'ifa',
) -> tuple[str, str]:
    """
    Verify transfer status and received amount.

    Args:
        first_page_objects: First app page objects.
        second_page_objects: Second app page objects.
        second_page_operations: Second app operations.
        asset_name: Asset name to verify.
        expected_amount: Expected received amount.
        expected_status: Expected transfer status.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Tuple of (actual_transfer_status, received_amount).
    """
    with allure.step('Verify transaction status'):
        if asset_type == 'ifa':
            first_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            first_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            first_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )

        actual_transfer_status = first_page_objects.asset_detail_page_objects.get_transfer_status()
        first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Verify received amount'):
        second_page_operations.do_focus_on_application(
            second_page_operations.application,
        )
        if asset_type == 'ifa':
            second_page_objects.sidebar_page_objects.click_inflatable_button()
            second_page_objects.inflatable_page_objects.click_refresh_button()
            second_page_objects.inflatable_page_objects.click_refresh_button()
            second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            second_page_objects.fungible_page_objects.click_refresh_button()
            second_page_objects.fungible_page_objects.click_refresh_button()
            second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            second_page_objects.sidebar_page_objects.click_collectibles_button()
            second_page_objects.collectible_page_objects.click_refresh_button()
            second_page_objects.collectible_page_objects.click_refresh_button()
            second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )

        received_amount = second_page_objects.asset_detail_page_objects.get_total_balance()
        second_page_objects.asset_detail_page_objects.click_close_button()

        mine(1)

    with allure.step('Verify assertions'):
        assert received_amount == expected_amount
        assert actual_transfer_status == expected_status

    return actual_transfer_status, received_amount


def focus_and_navigate_to_asset(
    page_operations,
    page_objects,
    asset_name: str,
    asset_type: str = 'ifa',
) -> None:
    """
    Focus on application and navigate to asset detail.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        asset_name: Asset name to navigate to.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    page_operations.do_focus_on_application(page_operations.application)

    if asset_type == 'ifa':
        page_objects.sidebar_page_objects.click_inflatable_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)
    elif asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    elif asset_type == 'cfa':
        page_objects.sidebar_page_objects.click_collectibles_button()
        page_objects.collectible_page_objects.click_cfa_frame(asset_name)

    page_objects.asset_detail_page_objects.click_send_button()


def initiate_third_wallet_and_get_invoice(
    third_page_features,
    application,
    variant: str,
) -> str:
    """
    Initiate third single-sig wallet and get invoice.

    Args:
        third_page_features: Third page features instance.
        application: Application instance.
        variant: Wallet variant.

    Returns:
        Generated invoice.
    """
    third_page_features.wallet_features.create_and_fund_wallet(
        application=application,
        variant=variant,
    )
    invoice = third_page_features.receive_features.receive_asset_from_sidebar(
        application,
    )
    return invoice


def verify_transfer_status_on_app3(
    first_page_objects,
    third_page_operations,
    third_page_objects,
    asset_name: str,
    expected_status: str,
    asset_type: str = 'ifa',
) -> str:
    """
    Verify transfer status and received amount on App 3.

    Args:
        first_page_objects: First app page objects.
        third_page_operations: Third app operations.
        third_page_objects: Third app page objects.
        asset_name: Asset name to verify.
        expected_status: Expected transfer status.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Actual transfer status.
    """
    actual_transfer_status = first_page_objects.asset_detail_page_objects.get_transfer_status()
    assert actual_transfer_status == expected_status

    with allure.step('Verify received amount on App 3'):
        third_page_operations.do_focus_on_application(
            third_page_operations.application,
        )
        if asset_type == 'ifa':
            third_page_objects.sidebar_page_objects.click_inflatable_button()
            third_page_objects.inflatable_page_objects.click_refresh_button()
            third_page_objects.inflatable_page_objects.click_refresh_button()
            third_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            third_page_objects.fungible_page_objects.click_refresh_button()
            third_page_objects.fungible_page_objects.click_refresh_button()
            third_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            third_page_objects.sidebar_page_objects.click_collectibles_button()
            third_page_objects.collectible_page_objects.click_refresh_button()
            third_page_objects.collectible_page_objects.click_refresh_button()
            third_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )

    return actual_transfer_status


def sign_psbt_and_verify_transfer(
    wallets_and_operations,
    wallet_variant_name: str,
    asset_name: str,
    asset_type: str = 'ifa',
) -> None:
    """
    Sign PSBT and verify transfer status.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        asset_name: Asset name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """

    wallets_and_operations.second_page_features.wallet_features.sign_psbt(
        SECOND_APPLICATION, wallet_variant_name,
    )

    with allure.step('Verify transfer status'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )


def refresh_collectibles_on_app2(wallets_and_operations) -> None:
    """
    Refresh collectibles on App 2.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    wallets_and_operations.second_page_operations.do_focus_on_application(
        SECOND_APPLICATION,
    )
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
    wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
    wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


def handle_hardware_wallet_init(self, variant_name, app_name):
    """
    Initialize hardware wallet emulator if variant is hardware wallet.

    Args:
        self: Feature class instance with hardware_wallet_emulator attribute.
        variant_name: Wallet variant name.
        app_name: Ledger app name.

    Returns:
        True if hardware wallet was initialized.
    """
    if variant_name in HARDWARE_WALLET_VARIANTS:
        self.hardware_wallet_emulator = handle_hardware_wallet(
            app_name=app_name,
        )
        return True
    return False


def handle_hardware_wallet_cleanup(self) -> None:
    """
    Clean up hardware wallet emulator.

    Args:
        self: Feature class instance with hardware_wallet_emulator attribute.
    """
    if self.hardware_wallet_emulator:
        self.hardware_wallet_emulator.terminate()


def get_invoice_from_third_app(
    third_page_features,
    application,
) -> str:
    """
    Get invoice from third application (for offline wallet tests).

    Args:
        third_page_features: Third page features instance.
        application: Application instance.

    Returns:
        Generated invoice.
    """
    return third_page_features.receive_features.receive_asset_from_sidebar(
        application,
    )


def setup_multisig_wallets(
    wallets_and_operations,
    wallet_variant_name,
) -> None:
    """
    Setup two multisig wallets with cosigner data import and finalization.
    For load variants, also saves credentials, resets app, and reloads wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    is_load_variant = wallet_variant_name in MULTISIG_LOAD_VARIANTS
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    is_online = wallet_variant_name not in REQUIRE_USB_VARIANTS
    if is_load_variant:
        wallet_variant_name = map_load_to_create(wallet_variant_name)

    with allure.step('Initiate first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Initiate second multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=ONLINE_MULTISIG_ON_DEVICE, fund=False,
        )

    with allure.step('Import cosigner data into first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.import_multisig_data(
            application=FIRST_APPLICATION,
        )

    with allure.step('Import cosigner data into second multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.import_multisig_data(
            application=SECOND_APPLICATION,
        )

    with allure.step('Finalize first multisig wallet setup'):
        wallets_and_operations.first_page_features.wallet_features.finalize_multisig_setup(
            application=FIRST_APPLICATION,
        )

    with allure.step('Finalize second multisig wallet setup'):
        wallets_and_operations.second_page_features.wallet_features.finalize_multisig_setup(
            application=SECOND_APPLICATION,
        )    

    # Handle load wallet flow - only for FIRST application
    if is_load_variant:
        with allure.step('Save credentials from first multisig wallet for load'):
            wallets_and_operations.first_page_features.wallet_features.save_multisig_load_credentials(
                application=FIRST_APPLICATION,
                is_hardware=is_hardware,
                is_online=is_online,
            )

        with allure.step('Load first multisig wallet with saved credentials'):
            # Reset and get updated wallet_features from environment
            env = wallets_and_operations.first_page_features.wallet_features.get_current_environment()
            if env:
                env.reset_first_instance()
                # Use the updated wallet_features from environment after reset
                updated_wallet_features = env.first_page_features.wallet_features
                updated_wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=wallet_variant_name,
                )
            else:
                wallets_and_operations.first_page_features.wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=wallet_variant_name,
                )


def setup_offline_multisig_two_app_wallets(
    wallets_and_operations,
    wallet_variant_name,
) -> None:
    """
    Setup offline multisig wallet with 2 applications for UI tests (about, help, login auth, keyring, settings).
    Both wallets are proper multisig wallets - NOT watch-only.
    
    App 1: Offline multisig wallet (signer) - hardware or on-device
    App 2: Online multisig wallet (paired coordinator) - on-device

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    is_load_variant = wallet_variant_name in MULTISIG_LOAD_VARIANTS
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    
    # Map load variant to create variant for first wallet
    first_wallet_variant = wallet_variant_name
    if is_load_variant:
        first_wallet_variant = map_load_to_create(wallet_variant_name)

    # App 1: Offline multisig wallet (signer)
    with allure.step('Initiate first offline multisig wallet (signer)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=first_wallet_variant, fund=False,
        )

    # App 2: Online multisig wallet (paired coordinator) - always online on-device
    with allure.step('Initiate second online multisig wallet (paired coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=ONLINE_MULTISIG_ON_DEVICE, fund=False,
        )

    # Import cosigner data
    with allure.step('Import cosigner data into first offline multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.import_multisig_data(
            application=FIRST_APPLICATION,
        )

    with allure.step('Import cosigner data into second online multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.import_multisig_data(
            application=SECOND_APPLICATION,
        )

    # Finalize setup
    with allure.step('Finalize first offline multisig wallet setup'):
        wallets_and_operations.first_page_features.wallet_features.finalize_multisig_setup(
            application=FIRST_APPLICATION,
        )

    with allure.step('Finalize second online multisig wallet setup'):
        wallets_and_operations.second_page_features.wallet_features.finalize_multisig_setup(
            application=SECOND_APPLICATION,
        )

    # Handle load wallet flow for first application
    if is_load_variant:
        is_online = wallet_variant_name not in REQUIRE_USB_VARIANTS
        with allure.step('Save credentials from first multisig wallet for load'):
            wallets_and_operations.first_page_features.wallet_features.save_multisig_load_credentials(
                application=FIRST_APPLICATION,
                is_hardware=is_hardware,
                is_online=is_online,
            )

        with allure.step('Load first multisig wallet with saved credentials'):
            env = wallets_and_operations.first_page_features.wallet_features.get_current_environment()
            if env:
                env.reset_first_instance()
                updated_wallet_features = env.first_page_features.wallet_features
                updated_wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )
            else:
                wallets_and_operations.first_page_features.wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )


def setup_offline_multisig_hardware_wallets(
    wallets_and_operations,
    wallet_variant_name,
) -> None:
    """
    Setup offline multisig wallet with 4 applications for transaction flow tests.
    
    - App 1: Offline multisig wallet (signer) - hardware or on-device
    - App 2: Online multisig wallet (watch-only coordinator) - imports both signers' data
    - App 3: Online multisig wallet (cosigner) - on-device
    - App 4: Receiver wallet (single-sig)

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    is_load_variant = wallet_variant_name in MULTISIG_LOAD_VARIANTS
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    
    # Map load variant to create variant for first wallet
    first_wallet_variant = wallet_variant_name
    if is_load_variant:
        first_wallet_variant = map_load_to_create(wallet_variant_name)

    # App 1: Offline multisig wallet (signer)
    with allure.step('Initiate first offline multisig wallet (signer)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=first_wallet_variant, fund=False,
        )

    # App 2: Online multisig wallet (watch-only coordinator)
    with allure.step('Initiate second online multisig wallet (watch-only coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=ONLINE_MULTISIG_WATCH_ONLY, fund=False,
        )

    # App 3: Online multisig wallet (cosigner) - on-device variant
    with allure.step('Initiate third online multisig wallet (cosigner)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_MULTISIG_ON_DEVICE, fund=False,
        )

    # Import cosigner data
    with allure.step('Import cosigner data into first offline multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.import_multisig_data(
            application=FIRST_APPLICATION,
        )

    with allure.step('Import all cosigner data into second watch-only multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.import_multisig_data(
            application=SECOND_APPLICATION, import_all=True,
        )

    with allure.step('Import cosigner data into third online multisig wallet'):
        wallets_and_operations.third_page_features.wallet_features.import_multisig_data(
            application=THIRD_APPLICATION,
        )

    # Finalize setup
    with allure.step('Finalize first offline multisig wallet setup'):
        wallets_and_operations.first_page_features.wallet_features.finalize_multisig_setup(
            application=FIRST_APPLICATION,
        )

    with allure.step('Finalize second online multisig wallet setup'):
        wallets_and_operations.second_page_features.wallet_features.finalize_multisig_setup(
            application=SECOND_APPLICATION,
        )

    with allure.step('Finalize third online multisig wallet setup'):
        wallets_and_operations.third_page_features.wallet_features.finalize_multisig_setup(
            application=THIRD_APPLICATION,
        )

    # App 4: Create receiver wallet (single-sig)
    with allure.step('Initiate fourth receiver wallet'):
        wallets_and_operations.fourth_page_features.wallet_features.create_and_fund_wallet(
            application=FOURTH_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE, fund=False,
        )

    # Handle load wallet flow for first application
    if is_load_variant:
        is_online = wallet_variant_name not in REQUIRE_USB_VARIANTS
        with allure.step('Save credentials from first multisig wallet for load'):
            wallets_and_operations.first_page_features.wallet_features.save_multisig_load_credentials(
                application=FIRST_APPLICATION,
                is_hardware=is_hardware,
                is_online=is_online,
            )

        with allure.step('Load first multisig wallet with saved credentials'):
            env = wallets_and_operations.first_page_features.wallet_features.get_current_environment()
            if env:
                env.reset_first_instance()
                updated_wallet_features = env.first_page_features.wallet_features
                updated_wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )
            else:
                wallets_and_operations.first_page_features.wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )


def setup_offline_multisig_three_app_wallets(
    wallets_and_operations,
    wallet_variant_name,
) -> None:
    """
    Setup offline multisig wallet with 3 applications for issue tests (NIA/IFA/CFA).
    All wallets are proper multisig wallets - NOT watch-only.
    
    - App 1: Offline multisig wallet (signer) - hardware or on-device
    - App 2: Online multisig wallet (coordinator) - on-device
    - App 3: Online multisig wallet (cosigner) - on-device

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    is_load_variant = wallet_variant_name in MULTISIG_LOAD_VARIANTS
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    
    # Map load variant to create variant for first wallet
    first_wallet_variant = wallet_variant_name
    if is_load_variant:
        first_wallet_variant = map_load_to_create(wallet_variant_name)

    # App 1: Offline multisig wallet (signer)
    with allure.step('Initiate first offline multisig wallet (signer)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=first_wallet_variant, fund=False,
        )

    # App 2: Online multisig wallet (coordinator) - on-device variant
    with allure.step('Initiate second online multisig wallet (coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=ONLINE_MULTISIG_ON_DEVICE, fund=False,
        )

    # App 3: Online multisig wallet (cosigner) - on-device variant
    with allure.step('Initiate third online multisig wallet (cosigner)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_MULTISIG_ON_DEVICE, fund=False,
        )

    # Import cosigner data
    with allure.step('Import cosigner data into first offline multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.import_multisig_data(
            application=FIRST_APPLICATION,
        )

    with allure.step('Import cosigner data into second online multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.import_multisig_data(
            application=SECOND_APPLICATION,
        )

    with allure.step('Import cosigner data into third online multisig wallet'):
        wallets_and_operations.third_page_features.wallet_features.import_multisig_data(
            application=THIRD_APPLICATION,
        )

    # Finalize setup
    with allure.step('Finalize first offline multisig wallet setup'):
        wallets_and_operations.first_page_features.wallet_features.finalize_multisig_setup(
            application=FIRST_APPLICATION,
        )

    with allure.step('Finalize second online multisig wallet setup'):
        wallets_and_operations.second_page_features.wallet_features.finalize_multisig_setup(
            application=SECOND_APPLICATION,
        )

    with allure.step('Finalize third online multisig wallet setup'):
        wallets_and_operations.third_page_features.wallet_features.finalize_multisig_setup(
            application=THIRD_APPLICATION,
        )

    # Handle load wallet flow for first application
    if is_load_variant:
        is_online = wallet_variant_name not in REQUIRE_USB_VARIANTS
        with allure.step('Save credentials from first multisig wallet for load'):
            wallets_and_operations.first_page_features.wallet_features.save_multisig_load_credentials(
                application=FIRST_APPLICATION,
                is_hardware=is_hardware,
                is_online=is_online,
            )

        with allure.step('Load first multisig wallet with saved credentials'):
            env = wallets_and_operations.first_page_features.wallet_features.get_current_environment()
            if env:
                env.reset_first_instance()
                updated_wallet_features = env.first_page_features.wallet_features
                updated_wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )
            else:
                wallets_and_operations.first_page_features.wallet_features.load_multisig_wallet(
                    application=FIRST_APPLICATION,
                    is_hardware=is_hardware,
                    is_online=is_online,
                    wallet_variant_name=first_wallet_variant,
                )


def fund_and_refresh_multisig_wallets(
    wallets_and_operations,
    asset_type: str = 'ifa',
) -> None:
    """
    Fund first multisig wallet and refresh second multisig wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_type: Asset type ('ifa', 'nia', 'cfa') for refresh button.
    """
    with allure.step('Fund first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            application=FIRST_APPLICATION,
        )

    with allure.step('Refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


def fund_and_refresh_offline_multisig_wallets(
    wallets_and_operations,
    asset_type: str = 'ifa',
) -> None:
    """
    Fund second wallet (online coordinator) and refresh third wallet for offline multisig.
    For offline multisig hardware wallet setup with 4 apps.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_type: Asset type ('ifa', 'nia', 'cfa') for refresh button.
    """
    with allure.step('Fund second online multisig wallet (coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            application=SECOND_APPLICATION,
        )

    with allure.step('Refresh third multisig wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()


def refresh_second_wallet_and_verify_asset(
    wallets_and_operations,
    asset_name: str,
    asset_type: str = 'nia',
) -> str:
    """
    Refresh second multisig wallet and verify asset name on first wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Expected asset name.
        asset_type: Asset type ('nia', 'cfa').

    Returns:
        Actual asset name.
    """
    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Verify asset name'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        if asset_type == 'nia':
            actual_name = wallets_and_operations.first_page_objects.fungible_page_objects.get_nia_asset_name(
                asset_name,
            )
        else:  # cfa
            actual_name = wallets_and_operations.first_page_objects.collectible_page_objects.get_cfa_asset_name(
                asset_name,
            )
        assert actual_name == asset_name
        return actual_name


def offline_wallet_send_asset_flow(
    wallets_and_operations,
    invoice: str,
    asset_name: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'ifa',
) -> str:
    """
    Execute offline wallet send asset flow with PSBT creation, signing, and broadcast.

    Args:
        wallets_and_operations: Wallet test setup instance.
        invoice: Invoice for sending.
        asset_name: Asset name.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Transfer status.
    """
    with allure.step(f'Send {asset_type} asset for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()

    with allure.step(f'Create {asset_type} psbt for offline wallet'):
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount, wallet_variant_name=wallet_variant_name,
        )

    with allure.step(f'Sign {asset_type} psbt for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name, is_rgb=True,
        )

    with allure.step(f'Broadcast {asset_type} psbt for offline wallet'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify transfer status for offline wallet'):
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        actual_transfer_status = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Verify received amount for offline wallet'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        if asset_type == 'ifa':
            wallets_and_operations.third_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        received_amount = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Verify assertions for offline wallet'):
        assert received_amount == send_amount

    return actual_transfer_status


def multisig_send_asset_flow_with_verification(
    wallets_and_operations,
    invoice: str,
    asset_name: str,
    asset_ticker: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'ifa',
    verify_assertions: bool = True,
) -> None:
    """
    Execute multisig send asset flow with PSBT creation, cosigning, and verification.

    Args:
        wallets_and_operations: Wallet test setup instance.
        invoice: Invoice for sending.
        asset_name: Asset name.
        asset_ticker: Asset ticker for UTXO creation.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_ticker,
            )
        elif asset_type == 'nia':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            application=FIRST_APPLICATION, receiver_invoice=invoice, amount=send_amount, wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    with allure.step('Cosign transfer from second multisig wallet (App 2)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step(f'Send {asset_type} asset from multisig (App 1) to App 3'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    if verify_assertions:
        with allure.step('Verify transfer status'):
            wallets_and_operations.first_page_operations.do_focus_on_application(
                FIRST_APPLICATION,
            )
            if asset_type == 'ifa':
                wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
                wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
                wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
                    asset_name,
                )
            elif asset_type == 'nia':
                wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
                wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
                wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
                    asset_name,
                )
            elif asset_type == 'cfa':
                wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
                wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
                wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
                    asset_name,
                )
            actual_transfer_status = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_transfer_status()
            assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

        with allure.step('Verify received amount on App 3'):
            wallets_and_operations.third_page_operations.do_focus_on_application(
                THIRD_APPLICATION,
            )
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
            if asset_type == 'ifa':
                wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
                wallets_and_operations.third_page_objects.inflatable_page_objects.click_ifa_frame(
                    asset_name,
                )
            elif asset_type == 'nia':
                wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
                    asset_name,
                )
            elif asset_type == 'cfa':
                wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
                wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
                    asset_name,
                )
            received_amount = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_total_balance()
            assert received_amount == send_amount


def offline_multisig_send_asset_flow_with_verification(
    wallets_and_operations,
    invoice: str,
    asset_name: str,
    asset_ticker: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'ifa',
    verify_assertions: bool = True,
) -> None:
    """
    Execute offline multisig send asset flow with 4 apps:
    - App 1: Offline hardware wallet (signer)
    - App 2: Online watch-only wallet (coordinator)
    - App 3: Online on-device wallet (cosigner)
    - App 4: Receiver wallet

    Args:
        wallets_and_operations: Wallet test setup instance.
        invoice: Invoice for sending.
        asset_name: Asset name.
        asset_ticker: Asset ticker for UTXO creation.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        verify_assertions: Whether to verify assertions.
    """
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS

    with allure.step('Issue asset from second wallet (online coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            SECOND_APPLICATION, asset_ticker, asset_name, '2000', wallet_variant_name,
        )
        # Refresh third wallet
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        if asset_type == 'nia':
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'ifa':
            wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        # Sign from third wallet (cosigner)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )
        # Sign from first wallet (offline signer) - required for 2-of-2 multisig
        # App 2 is watch-only coordinator, so both App 1 and App 3 must sign
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        if asset_type == 'nia':
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'ifa':
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )
        # Refresh second wallet
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'nia':
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'ifa':
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Create UTXO PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_ticker,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount, wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    # Sign from first wallet (offline signer) - required for 2-of-2 multisig
    # App 2 is watch-only coordinator, so both App 1 and App 3 must sign
    with allure.step('Sign PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        elif asset_type == 'cfa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step(f'Send {asset_type} asset from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        wallets_and_operations.second_page_features.send_features.send_asset_for_multisig(
            SECOND_APPLICATION, wallet_variant_name,
        )

    if verify_assertions:
        with allure.step('Verify transfer status on second wallet'):
            wallets_and_operations.second_page_operations.do_focus_on_application(
                SECOND_APPLICATION,
            )
            if asset_type == 'ifa':
                wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
                wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
                wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                    asset_name,
                )
            elif asset_type == 'nia':
                wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
                wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
                wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                    asset_name,
                )
            elif asset_type == 'cfa':
                wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
                wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
                wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
                    asset_name,
                )
            actual_transfer_status = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
            assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

        with allure.step('Verify received amount on fourth wallet (receiver)'):
            wallets_and_operations.fourth_page_operations.do_focus_on_application(
                FOURTH_APPLICATION,
            )
            if asset_type == 'ifa':
                wallets_and_operations.fourth_page_objects.sidebar_page_objects.click_inflatable_button()
                wallets_and_operations.fourth_page_objects.inflatable_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.inflatable_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.inflatable_page_objects.click_ifa_frame(
                    asset_name,
                )
            elif asset_type == 'nia':
                wallets_and_operations.fourth_page_objects.sidebar_page_objects.click_fungibles_button()
                wallets_and_operations.fourth_page_objects.fungible_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.fungible_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.fungible_page_objects.click_nia_frame(
                    asset_name,
                )
            elif asset_type == 'cfa':
                wallets_and_operations.fourth_page_objects.sidebar_page_objects.click_collectibles_button()
                wallets_and_operations.fourth_page_objects.collectible_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.collectible_page_objects.click_refresh_button()
                wallets_and_operations.fourth_page_objects.collectible_page_objects.click_cfa_frame(
                    asset_name,
                )
            received_amount = wallets_and_operations.fourth_page_objects.asset_detail_page_objects.get_total_balance()
            assert received_amount == send_amount


def multisig_issue_asset_flow(
    wallets_and_operations,
    wallet_variant_name,
    issue_func,
    asset_identifier,
    utxo_required: bool = True,
) -> None:
    """
    Execute multisig issue asset flow with UTXO creation and signing.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        issue_func: Function to call for issuing asset.
        asset_identifier: Asset ticker or name.
        utxo_required: Whether UTXO creation is required.
    """
    with allure.step('Create Utxo for issue asset'):
        issue_func(
            FIRST_APPLICATION, asset_identifier,
            utxo_required=utxo_required,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Sign and broadcast from second wallet'):
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('refresh first multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Issue asset with sufficient sats and utxo from draft'):
        issue_func(FIRST_APPLICATION, asset_identifier)


def handle_utxo_confirmation_dialog(
    page_objects,
    page_operations,
    utxo_required: bool = False,
) -> None:
    """
    Handle UTXO confirmation dialog if required.

    Args:
        page_objects: Page objects instance.
        page_operations: Page operations instance.
        utxo_required: Whether UTXO creation is required.
    """

    if utxo_required:
        page_operations.do_focus_on_application(CONFIRMATION_DIALOG)
        if page_operations.do_is_displayed(page_objects.confirmation_dialog_page_objects.confirmation_dialog()):
            page_objects.confirmation_dialog_page_objects.click_confirmation_dialog()

        if page_operations.do_is_displayed(page_objects.confirmation_dialog_page_objects.confirmation_continue_button()):
            page_objects.confirmation_dialog_page_objects.click_confirmation_continue_button()
    else:
        if page_operations.do_is_displayed(page_objects.success_page_objects.home_button()):
            page_objects.success_page_objects.click_home_button()


def handle_utxo_confirmation_with_hardware_wallet(
    page_objects,
    page_operations,
    wallet_feature,
    application: str,
    utxo_required: bool = False,
    is_hardware: bool = False,
) -> None:
    """
    Handle UTXO confirmation dialog with hardware wallet signing.

    Args:
        page_objects: Page objects instance.
        page_operations: Page operations instance.
        wallet_feature: Wallet feature instance.
        application: Application name.
        utxo_required: Whether UTXO creation is required.
        is_hardware: Whether this is a hardware wallet.
    """
    if utxo_required:
        page_operations.do_focus_on_application(CONFIRMATION_DIALOG)
        if page_operations.do_is_displayed(page_objects.confirmation_dialog_page_objects.confirmation_dialog()):
            page_objects.confirmation_dialog_page_objects.click_confirmation_dialog()

        if page_operations.do_is_displayed(page_objects.confirmation_dialog_page_objects.confirmation_continue_button()):
            page_objects.confirmation_dialog_page_objects.click_confirmation_continue_button()

        # After clicking continue, app sends request to hardware wallet
        # Then we do the button presses to register policy and sign
        if is_hardware:
            wallet_feature.sign_multisig_on_hardware_wallet(application)
    else:
        if is_hardware:
            wallet_feature.sign_multisig_on_hardware_wallet(application)
        if page_operations.do_is_displayed(page_objects.success_page_objects.home_button()):
            page_objects.success_page_objects.click_home_button()
