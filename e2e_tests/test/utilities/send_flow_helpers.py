# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements, too-many-instance-attributes
"""
Send flow and verification helper functions for e2e tests.
"""
from __future__ import annotations

import re

import allure

from accessible_constant import FIRST_APPLICATION
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.translation_utils import TranslationManager
from src.model.enums.enums_model import TransactionStatusEnumModel


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


def verify_invalid_invoice_validation_step(wallets_and_operations, invoice: str) -> None:
    """
    Verify invalid invoice validation with default translated message.

    Args:
        wallets_and_operations: Wallet test setup instance.
        invoice: Invalid invoice string.
    """
    with allure.step('Verify invalid invoice validation'):
        verify_invalid_invoice_validation(
            wallets_and_operations.second_page_objects,
            invoice,
            TranslationManager.translate('invalid_invoice'),
        )


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
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
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


def focus_first_wallet_and_sign(wallets_and_operations, wallet_variant_name: str) -> None:
    """
    Focus on first wallet and sign PSBT.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    wallets_and_operations.first_page_operations.do_focus_on_application(
        FIRST_APPLICATION,
    )
    wallets_and_operations.first_page_features.wallet_features.sign_psbt(
        FIRST_APPLICATION, wallet_variant_name, is_rgb=True,
    )


def focus_first_wallet(wallets_and_operations) -> None:
    """
    Focus on first wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    wallets_and_operations.first_page_operations.do_focus_on_application(
        FIRST_APPLICATION,
    )


def focus_second_wallet(wallets_and_operations) -> None:
    """
    Focus on second wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    wallets_and_operations.second_page_operations.do_focus_on_application(
        SECOND_APPLICATION,
    )


def focus_third_wallet(wallets_and_operations) -> None:
    """
    Focus on third wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    wallets_and_operations.third_page_operations.do_focus_on_application(
        THIRD_APPLICATION,
    )


def generate_invoice_and_send_asset(
    wallets_and_operations,
    asset_name: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'nia',
) -> None:
    """
    Generate invoice from second wallet and execute send asset flow with verification.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name to send.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    with allure.step(f'Generate invoice for receiving {asset_type.upper()} asset'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    send_asset_flow_with_verification(
        wallets_and_operations,
        invoice,
        asset_name,
        send_amount,
        wallet_variant_name,
        asset_type=asset_type,
    )


def focus_second_wallet_and_navigate_to_ifa_tx(wallets_and_operations, ifa_asset_name: str) -> None:
    """
    Focus on second wallet, navigate to IFA asset and click RGB transaction on chain frame.

    Args:
        wallets_and_operations: Wallet test setup instance.
        ifa_asset_name: IFA asset name to navigate to.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
    wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
    wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
        ifa_asset_name,
    )
    wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()


def verify_tx_on_third_wallet(wallets_and_operations, asset_name: str, asset_type: str = 'nia') -> str:
    """
    Focus on third wallet, navigate to asset and get transaction ID.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name to navigate to.
        asset_type: Asset type ('nia', 'cfa', 'ifa').

    Returns:
        Transaction ID string.
    """
    wallets_and_operations.third_page_operations.do_focus_on_application(
        THIRD_APPLICATION,
    )
    if asset_type == 'nia':
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            asset_name,
        )
    elif asset_type == 'cfa':
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            asset_name,
        )
    elif asset_type == 'ifa':
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_ifa_frame(
            asset_name,
        )
    wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
    tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
    wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
    wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
    tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
    return tx_id


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


def send_asset_with_invoice(
    send_features,
    application: str,
    invoice: str,
    amount: str,
    wallet_variant_name: str,
) -> None:
    """
    Send asset using invoice.

    Args:
        send_features: Send features instance.
        application: Application identifier.
        invoice: Recipient invoice.
        amount: Amount to send.
        wallet_variant_name: Wallet variant name.
    """
    send_features.send(
        application=application,
        receiver_invoice=invoice,
        amount=amount,
    )


def verify_transfer_status_and_received_amount(
    first_page_objects,
    second_page_objects,
    second_page_operations,
    asset_name: str,
    send_amount: str,
    expected_status: str,
    asset_type: str = 'ifa',
) -> None:
    """
    Verify transfer status on sender wallet and received amount on receiver wallet.

    Args:
        first_page_objects: First wallet page objects (sender).
        second_page_objects: Second wallet page objects (receiver).
        second_page_operations: Second wallet page operations.
        asset_name: Asset name.
        send_amount: Expected received amount.
        expected_status: Expected transfer status.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    with allure.step('Verify transfer status on sender'):
        if asset_type == 'ifa':
            first_page_objects.sidebar_page_objects.click_inflatable_button()
            first_page_objects.inflatable_page_objects.click_refresh_button()
            first_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            first_page_objects.sidebar_page_objects.click_fungibles_button()
            first_page_objects.fungible_page_objects.click_refresh_button()
            first_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            first_page_objects.sidebar_page_objects.click_collectibles_button()
            first_page_objects.collectible_page_objects.click_refresh_button()
            first_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        actual_transfer_status = first_page_objects.asset_detail_page_objects.get_transfer_status()
        assert actual_transfer_status == expected_status

    with allure.step('Verify received amount on receiver'):
        second_page_operations.do_focus_on_application(
            second_page_operations.application,
        )
        if asset_type == 'ifa':
            second_page_objects.sidebar_page_objects.click_inflatable_button()
            second_page_objects.inflatable_page_objects.click_refresh_button()
            second_page_objects.inflatable_page_objects.click_ifa_frame(
                asset_name,
            )
        elif asset_type == 'nia':
            second_page_objects.sidebar_page_objects.click_fungibles_button()
            second_page_objects.fungible_page_objects.click_refresh_button()
            second_page_objects.fungible_page_objects.click_nia_frame(
                asset_name,
            )
        elif asset_type == 'cfa':
            second_page_objects.sidebar_page_objects.click_collectibles_button()
            second_page_objects.collectible_page_objects.click_refresh_button()
            second_page_objects.collectible_page_objects.click_cfa_frame(
                asset_name,
            )
        received_amount = second_page_objects.asset_detail_page_objects.get_total_balance()
        assert received_amount == send_amount


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


def navigate_to_asset_and_click_send(
    page_operations,
    page_objects,
    asset_name: str,
    asset_type: str = 'ifa',
    refresh: bool = True,
    click_send: bool = True,
) -> None:
    """
    Navigate to asset detail page and optionally click send button.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        asset_name: Asset name to navigate to.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        refresh: Whether to refresh before clicking asset.
        click_send: Whether to click send button. Set to False for draft transfers.
    """
    page_operations.do_focus_on_application(SECOND_APPLICATION)

    if asset_type == 'ifa':
        page_objects.sidebar_page_objects.click_inflatable_button()
        if refresh:
            page_objects.inflatable_page_objects.click_refresh_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)
    elif asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        if refresh:
            page_objects.fungible_page_objects.click_refresh_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    elif asset_type == 'cfa':
        page_objects.sidebar_page_objects.click_collectibles_button()
        if refresh:
            page_objects.collectible_page_objects.click_refresh_button()
        page_objects.collectible_page_objects.click_cfa_frame(asset_name)

    if click_send:
        page_objects.asset_detail_page_objects.click_send_button()
