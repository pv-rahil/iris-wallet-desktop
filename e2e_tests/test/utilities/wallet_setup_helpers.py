# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements
"""
Wallet setup helper functions for e2e tests.
"""
from __future__ import annotations

import allure

from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import MULTISIG_LOAD_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.wallet_variants import map_load_to_create


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
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)


def setup_and_fund_offline_multisig_wallets(
    wallets_and_operations,
    wallet_variant_name,
    asset_type: str = 'nia',
) -> None:
    """
    Setup offline multisig wallets and fund the coordinator in one call.
    Combines setup_offline_multisig_hardware_wallets and funding.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type for refresh (default: 'nia').
    """
    setup_offline_multisig_hardware_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    with allure.step('Fund second online multisig wallet (coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            application=SECOND_APPLICATION,
        )


def _focus_third_wallet(wallets_and_operations) -> None:
    """
    Focus on third wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    wallets_and_operations.third_page_operations.do_focus_on_application(
        THIRD_APPLICATION,
    )


def _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type: str = 'ifa') -> None:
    """
    Focus on third wallet and click refresh button based on asset type.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    _focus_third_wallet(wallets_and_operations)
    if asset_type == 'ifa':
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
    elif asset_type == 'nia':
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
    elif asset_type == 'cfa':
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()


# pylint: disable=too-many-return-statements
def get_fresh_page_objects(wallets_and_operations, app_index: int = 2):
    """
    Get fresh page objects from environment after reset.

    This is critical after reset_second_instance or reset_first_instance to ensure
    we have the updated application nodes and avoid stale element references.

    Args:
        wallets_and_operations: Wallet test setup instance (proxy).
        app_index: Application index (1=first, 2=second, 3=third, 4=fourth).

    Returns:
        Tuple of (page_objects, page_features, page_operations) for the specified app.
    """
    # Get environment from wallet_features
    if app_index == 1:
        env = wallets_and_operations.first_page_features.wallet_features.get_current_environment()
    elif app_index == 2:
        env = wallets_and_operations.second_page_features.wallet_features.get_current_environment()
    elif app_index == 3:
        env = wallets_and_operations.third_page_features.wallet_features.get_current_environment()
    else:
        env = wallets_and_operations.fourth_page_features.wallet_features.get_current_environment()

    if not env:
        # Fallback to proxy properties
        if app_index == 1:
            return (
                wallets_and_operations.first_page_objects,
                wallets_and_operations.first_page_features,
                wallets_and_operations.first_page_operations,
            )
        if app_index == 2:
            return (
                wallets_and_operations.second_page_objects,
                wallets_and_operations.second_page_features,
                wallets_and_operations.second_page_operations,
            )
        if app_index == 3:
            return (
                wallets_and_operations.third_page_objects,
                wallets_and_operations.third_page_features,
                wallets_and_operations.third_page_operations,
            )
        return (
            wallets_and_operations.fourth_page_objects,
            wallets_and_operations.fourth_page_features,
            wallets_and_operations.fourth_page_operations,
        )

    # Get fresh page objects from environment
    if app_index == 1:
        return (
            env.first_page_objects,
            env.first_page_features,
            env.first_page_operations,
        )
    if app_index == 2:
        return (
            env.second_page_objects,
            env.second_page_features,
            env.second_page_operations,
        )
    if app_index == 3:
        return (
            env.third_page_objects,
            env.third_page_features,
            env.third_page_operations,
        )
    return (
        env.fourth_page_objects,
        env.fourth_page_features,
        env.fourth_page_operations,
    )
