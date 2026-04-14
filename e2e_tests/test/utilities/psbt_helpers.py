# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements
"""
PSBT signing and broadcasting helper functions for e2e tests.
"""
from __future__ import annotations

import allure

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.atspi_helpers import aggressive_cleanup
from e2e_tests.test.utilities.atspi_helpers import refresh_atspi_tree
from src.model.enums.enums_model import TransactionStatusEnumModel


def sign_and_broadcast_psbt_offline_single_sig(
    wallets_and_operations,
    wallet_variant_name: str,
    second_page_operations,
    second_page_features,
) -> None:
    """
    Sign PSBT from offline signer and broadcast for offline single-sig wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        second_page_operations: Second page operations instance.
        second_page_features: Second page features instance.
    """
    with allure.step('Sign PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_rgb=True,
        )

    with allure.step('Broadcast PSBT from second wallet (coordinator)'):
        second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        second_page_features.wallet_features.broadcast_psbt(SECOND_APPLICATION)


def sign_and_broadcast_psbt_offline_multisig(
    wallets_and_operations,
    wallet_variant_name: str,
    second_page_operations,
    second_page_features,
    cosigner_variant: str = 'ONLINE_MULTISIG_ON_DEVICE',
) -> None:
    """
    Sign PSBT from offline signer, cosigner, and broadcast for offline multisig wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        second_page_operations: Second page operations instance.
        second_page_features: Second page features instance.
        cosigner_variant: Cosigner wallet variant name.
    """
    cosigner = cosigner_variant if cosigner_variant != 'ONLINE_MULTISIG_ON_DEVICE' else ONLINE_MULTISIG_ON_DEVICE

    with allure.step('Sign PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    # USB sync from first wallet back to coordinator so cosigner can access signed PSBT
    with allure.step('USB sync from first wallet back to coordinator'):
        wallets_and_operations.first_page_features.wallet_features.usb_sync()

    with allure.step('Sign PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, cosigner,
        )

    with allure.step('Broadcast PSBT from second wallet (coordinator)'):
        second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )


def focus_refresh_and_sign_psbt(
    page_operations,
    page_objects,
    page_features,
    application: str,
    wallet_variant_name: str,
    asset_type: str = 'nia',
) -> None:
    """
    Focus on application, refresh asset list, and sign PSBT.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        page_features: Page features instance.
        application: Application name.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    page_operations.do_focus_on_application(application)
    if asset_type == 'ifa':
        page_objects.inflatable_page_objects.click_refresh_button()
    elif asset_type == 'nia':
        page_objects.fungible_page_objects.click_refresh_button()
    elif asset_type == 'cfa':
        page_objects.collectible_page_objects.click_refresh_button()
    page_features.wallet_features.sign_psbt(application, wallet_variant_name)


def focus_and_refresh_asset_list(
    page_operations,
    page_objects,
    application: str,
    asset_type: str = 'nia',
) -> None:
    """
    Focus on application and refresh asset list.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        application: Application name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    page_operations.do_focus_on_application(application)
    if asset_type == 'ifa':
        page_objects.inflatable_page_objects.click_refresh_button()
    elif asset_type == 'nia':
        page_objects.fungible_page_objects.click_refresh_button()
    elif asset_type == 'cfa':
        page_objects.collectible_page_objects.click_refresh_button()


def sign_psbt_from_two_wallets_and_broadcast(
    wallets_and_operations,
    wallet_variant_name: str,
    first_wallet_app: str,
    second_wallet_app: str,
    third_wallet_app: str,
    asset_type: str = 'nia',
) -> None:
    """
    Sign PSBT from two wallets (cosigner and offline signer) and broadcast from coordinator.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name for offline signer.
        first_wallet_app: First wallet application (offline signer).
        second_wallet_app: Second wallet application (coordinator/broadcaster).
        third_wallet_app: Third wallet application (cosigner).
        asset_type: Asset type for refresh ('ifa', 'nia', 'cfa').
    """
    # Sign from third wallet (cosigner)
    focus_refresh_and_sign_psbt(
        wallets_and_operations.third_page_operations,
        wallets_and_operations.third_page_objects,
        wallets_and_operations.third_page_features,
        third_wallet_app, ONLINE_MULTISIG_ON_DEVICE, asset_type,
    )
    # Sign from first wallet (offline signer)
    focus_refresh_and_sign_psbt(
        wallets_and_operations.first_page_operations,
        wallets_and_operations.first_page_objects,
        wallets_and_operations.first_page_features,
        first_wallet_app, wallet_variant_name, asset_type,
    )
    # Broadcast PSBT from second wallet (coordinator)
    wallets_and_operations.second_page_operations.do_focus_on_application(
        SECOND_APPLICATION,
    )
    wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
        second_wallet_app, is_multisig=True,
    )


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

    # Helper to get sidebar/refresh/page objects based on asset type
    def get_asset_nav_objects(page_objects):
        if asset_type == 'ifa':
            return (
                page_objects.sidebar_page_objects.click_inflatable_button,
                page_objects.inflatable_page_objects,
            )
        if asset_type == 'nia':
            return (
                page_objects.sidebar_page_objects.click_fungibles_button,
                page_objects.fungible_page_objects,
            )
        # cfa
        return (
            page_objects.sidebar_page_objects.click_collectibles_button,
            page_objects.collectible_page_objects,
        )

    def get_asset_frame(sidebar_click, page_obj, name):
        sidebar_click()
        page_obj.click_refresh_button()
        if asset_type == 'ifa':
            page_obj.click_ifa_frame(name)
        elif asset_type == 'nia':
            page_obj.click_nia_frame(name)
        else:
            page_obj.click_cfa_frame(name)

    # Step 1: Create UTXO PSBT from second wallet (coordinator)
    with allure.step('Create UTXO PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.second_page_objects,
        )
        get_asset_frame(sidebar_click, page_obj, asset_ticker)
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount,
            wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    # Refresh AT-SPI after UTXO creation
    aggressive_cleanup()

    # Step 2: Sign UTXO PSBT from third wallet (cosigner)
    with allure.step('Sign UTXO PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.third_page_objects,
        )
        sidebar_click()
        page_obj.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    # Step 3: Sign UTXO PSBT from first wallet (offline signer)
    with allure.step('Sign UTXO PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.first_page_objects,
        )
        sidebar_click()
        page_obj.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    # Refresh AT-SPI after signing round
    aggressive_cleanup()

    # Step 4: Broadcast UTXO PSBT from second wallet (coordinator)
    with allure.step('Broadcast UTXO PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION, verify_ready=False,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

    # Refresh AT-SPI after broadcast
    aggressive_cleanup()

    # Step 5: Send asset from second wallet (coordinator)
    with allure.step(f'Send {asset_type} asset from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.second_page_objects,
        )
        sidebar_click()
        page_obj.click_refresh_button()
        page_obj.click_refresh_button()
        if asset_type == 'ifa':
            page_obj.click_ifa_frame(asset_name)
        elif asset_type == 'nia':
            page_obj.click_nia_frame(asset_name)
        else:
            page_obj.click_cfa_frame(asset_name)
        wallets_and_operations.second_page_features.send_features.send_asset_for_multisig(
            SECOND_APPLICATION, wallet_variant_name,
        )

    # Step 6: Sign transfer PSBT from first wallet (offline signer) - MUST be first for USB sync
    with allure.step('Sign transfer PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.first_page_objects,
        )
        sidebar_click()
        page_obj.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    # Refresh AT-SPI after signing round
    aggressive_cleanup()

    # Step 7: Sign transfer PSBT from third wallet (cosigner) - after offline signer has signed
    with allure.step('Sign transfer PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION, verify_ready=False,
        )
        sidebar_click, page_obj = get_asset_nav_objects(
            wallets_and_operations.third_page_objects,
        )
        sidebar_click()
        page_obj.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    # Full AT-SPI reset before broadcast - this is where tests often get stuck
    refresh_atspi_tree()

    # Refresh AT-SPI after signing round
    aggressive_cleanup()

    # Step 8: Broadcast transfer PSBT from second wallet (coordinator)
    with allure.step('Broadcast transfer PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION, verify_ready=False,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

    # Final AT-SPI refresh before assertions
    aggressive_cleanup()

    if verify_assertions:
        with allure.step('Verify transfer status on second wallet'):
            wallets_and_operations.second_page_operations.do_focus_on_application(
                SECOND_APPLICATION, verify_ready=True,
            )
            sidebar_click, page_obj = get_asset_nav_objects(
                wallets_and_operations.second_page_objects,
            )
            sidebar_click()
            page_obj.click_refresh_button()
            if asset_type == 'ifa':
                page_obj.click_ifa_frame(asset_name)
            elif asset_type == 'nia':
                page_obj.click_nia_frame(asset_name)
            else:
                page_obj.click_cfa_frame(asset_name)
            actual_transfer_status = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
            assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

        with allure.step('Verify received amount on fourth wallet (receiver)'):
            wallets_and_operations.fourth_page_operations.do_focus_on_application(
                FOURTH_APPLICATION, verify_ready=True,
            )
            sidebar_click, page_obj = get_asset_nav_objects(
                wallets_and_operations.fourth_page_objects,
            )
            sidebar_click()
            page_obj.click_refresh_button()
            page_obj.click_refresh_button()
            if asset_type == 'ifa':
                page_obj.click_ifa_frame(asset_name)
            elif asset_type == 'nia':
                page_obj.click_nia_frame(asset_name)
            else:
                page_obj.click_cfa_frame(asset_name)
            received_amount = wallets_and_operations.fourth_page_objects.asset_detail_page_objects.get_total_balance()
            assert received_amount == send_amount
