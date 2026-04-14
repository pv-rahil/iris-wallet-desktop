# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements, too-many-lines
"""
Send flow and verification helper functions for e2e tests.
"""
from __future__ import annotations

import re

import allure

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_with_hardware_wallet
from e2e_tests.test.utilities.psbt_helpers import sign_and_broadcast_psbt_offline_multisig
from e2e_tests.test.utilities.psbt_helpers import sign_and_broadcast_psbt_offline_single_sig
from e2e_tests.test.utilities.translation_utils import TranslationManager
from e2e_tests.test.utilities.wallet_setup_helpers import _refresh_third_wallet_by_asset_type
from e2e_tests.test.utilities.wallet_setup_helpers import get_fresh_page_objects
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


def generate_multisig_invoice_and_send(
    wallets_and_operations,
    asset_name: str,
    asset_ticker: str,
    send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'nia',
    verify_assertions: bool = True,
) -> None:
    """
    Generate invoice from third wallet and execute multisig send asset flow with verification.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name to send.
        asset_ticker: Asset ticker.
        send_amount: Amount to send.
        wallet_variant_name: Wallet variant name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        verify_assertions: Whether to verify assertions.
    """
    with allure.step(f'Initiate third wallet for receiving {asset_type.upper()} asset'):
        invoice = initiate_third_wallet_and_get_invoice(
            wallets_and_operations.third_page_features,
            THIRD_APPLICATION,
            ONLINE_CREATE_ON_DEVICE,
        )

    multisig_send_asset_flow_with_verification(
        wallets_and_operations=wallets_and_operations,
        invoice=invoice,
        asset_name=asset_name,
        asset_ticker=asset_ticker,
        send_amount=send_amount,
        wallet_variant_name=wallet_variant_name,
        asset_type=asset_type,
        verify_assertions=verify_assertions,
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
    page_operations.do_focus_on_application(page_operations.application)

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


def handle_confirmation_dialog_and_usb_sync(self, wallet_feature) -> None:
    """
    Handle confirmation dialog and USB sync for offline wallet operations.

    Args:
        self: Feature class instance with page objects.
        wallet_feature: Wallet feature instance for USB sync.
    """
    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
        self.confirmation_dialog_page_objects.click_confirmation_dialog()

    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
        self.confirmation_dialog_page_objects.click_confirmation_continue_button()

    wallet_feature.usb_sync(is_receive=True)


def handle_native_auth_and_focus(self, application: str, is_native_auth_enabled: bool = False) -> None:
    """
    Handle native auth password entry and focus application.

    Args:
        self: Feature class instance.
        application: Application name.
        is_native_auth_enabled: Whether native auth is enabled.
    """
    if is_native_auth_enabled is True:
        self.enter_native_password()

    self.do_focus_on_application(application)


def handle_success_home_button(self) -> None:
    """
    Handle success page home button click.

    Args:
        self: Feature class instance with page objects.
    """
    if self.do_is_displayed(self.success_page_objects.home_button()):
        self.success_page_objects.click_home_button()


def handle_native_auth_utxo_and_success(
    self,
    application: str,
    wallet_feature,
    is_native_auth_enabled: bool = False,
    utxo_required: bool = False,
    is_hardware: bool = False,
    ledger_app_name: str = LEDGER_EMULATOR_APP_NAME,
) -> None:
    """
    Handle native auth, UTXO confirmation with hardware wallet, and success flow.

    Args:
        self: Feature class instance with page objects.
        application: Application name.
        wallet_feature: Wallet feature instance.
        is_native_auth_enabled: Whether native auth is enabled.
        utxo_required: Whether UTXO creation is required.
        is_hardware: Whether this is a hardware wallet.
        ledger_app_name: Ledger app name for hardware wallet.
    """
    if is_native_auth_enabled:
        self.enter_native_password()
    if utxo_required:
        handle_utxo_confirmation_with_hardware_wallet(
            self, self, wallet_feature, ledger_app_name,
            utxo_required=True, is_hardware=is_hardware,
        )
    else:
        if self.do_is_displayed(self.success_page_objects.home_button()):
            self.success_page_objects.click_home_button()


def handle_offline_multisig_utxo_confirmation_and_usb_sync(
    self,
    application: str,
    wallet_feature,
    is_native_auth_enabled: bool = False,
) -> None:
    """
    Handle UTXO confirmation dialog and USB sync for offline multisig wallet.

    Args:
        self: Feature class instance with page objects.
        application: Application name.
        wallet_feature: Wallet feature instance.
        is_native_auth_enabled: Whether native auth is enabled.
    """
    if is_native_auth_enabled:
        self.enter_native_password()

    # Handle UTXO confirmation dialog (no hardware signing)
    self.do_focus_on_application(CONFIRMATION_DIALOG)
    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
        self.confirmation_dialog_page_objects.click_confirmation_dialog()

    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
        self.confirmation_dialog_page_objects.click_confirmation_continue_button()

    self.do_focus_on_application(application)

    # USB sync to pass PSBT to offline wallet
    wallet_feature.usb_sync()


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


def offline_multisig_issue_asset_test_flow(
    wallets_and_operations,
    wallet_variant_name,
    issue_func,
    asset_identifier,
    asset_type: str = 'ifa',
    is_issue_ifa: bool = False,
) -> None:
    """
    Execute offline multisig issue asset test flow with 3 apps.
    Handles funding, issuing, and signing for offline multisig wallet tests.

    Note: This function assumes wallets are already set up via setup_offline_multisig_three_app_wallets
    in the preceding "without sufficient sats" test.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        issue_func: Function to call for issuing asset.
        asset_identifier: Asset name or ticker.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        is_issue_ifa: Whether this is an IFA issue (for hardware wallet signing).
    """
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS

    # Fund the second wallet (online coordinator)
    with allure.step('Fund second online multisig wallet (coordinator)'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    # Refresh third wallet
    with allure.step('Refresh third multisig wallet (cosigner)'):
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)

    # Issue asset from second wallet
    with allure.step(f'Issue {asset_type.upper()} asset from second wallet (online coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        elif asset_type == 'cfa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        issue_func(
            SECOND_APPLICATION, asset_identifier,
            wallet_variant_name, utxo_required=True,
        )

    # Refresh third wallet and sign
    with allure.step('Refresh third wallet and sign PSBT'):
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE, is_issue_ifa=is_issue_ifa,
        )

    # Sign from first wallet if hardware
    if is_hardware:
        with allure.step('Sign PSBT from first wallet (offline hardware signer)'):
            wallets_and_operations.first_page_operations.do_focus_on_application(
                FIRST_APPLICATION,
            )
            wallets_and_operations.first_page_features.wallet_features.sign_psbt(
                FIRST_APPLICATION, wallet_variant_name, is_issue_ifa=is_issue_ifa,
            )

    # Broadcast from second wallet
    with allure.step('Broadcast PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )


def offline_multisig_create_utxo_for_send_test_flow(
    wallets_and_operations,
    wallet_variant_name,
    asset_name: str,
    send_amount: str,
    asset_type: str = 'ifa',
) -> str:
    """
    Execute offline multisig create UTXO for send test flow.
    Handles invoice generation, UTXO PSBT creation, signing, and broadcasting.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        asset_name: Asset name to send.
        send_amount: Amount to send.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Invoice string for the receiver wallet.
    """
    with allure.step('Get invoice from fourth receiver wallet'):
        invoice = wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(
            FOURTH_APPLICATION,
        )

    # Create UTXO PSBT
    with allure.step('Create UTXO PSBT from second wallet (coordinator)'):
        navigate_to_asset_and_click_send(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            asset_name, asset_type=asset_type,
        )
        wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount,
            wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    # Sign and broadcast UTXO PSBT
    sign_and_broadcast_psbt_offline_multisig(
        wallets_and_operations, wallet_variant_name,
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_features,
    )

    return invoice


def focus_first_wallet_and_click_collectibles(wallets_and_operations) -> None:
    """
    Focus on first wallet and click collectibles button.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()


def focus_first_wallet_and_click_inflatable(wallets_and_operations) -> None:
    """
    Focus on first wallet and click inflatable button.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()


def focus_first_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on first wallet and refresh fungible assets.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()


def focus_second_wallet_and_click_inflatable(wallets_and_operations) -> None:
    """
    Focus on second wallet and click inflatable button.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()


def focus_second_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on second wallet and refresh fungible assets.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()


def focus_third_wallet_and_click_bitcoin_frame(wallets_and_operations) -> None:
    """
    Focus on third wallet and click bitcoin frame.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.fungible_page_objects.click_bitcoin_frame()


def focus_third_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on third wallet and refresh fungible assets.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()


def focus_first_wallet_and_click_bitcoin_frame(wallets_and_operations) -> None:
    """
    Focus on first wallet and click bitcoin frame.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()


def focus_third_wallet_and_refresh_bitcoin(wallets_and_operations) -> None:
    """
    Focus on third wallet and refresh bitcoin.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()


def focus_second_wallet_and_click_fungibles(wallets_and_operations) -> None:
    """
    Focus on second wallet and click fungibles button.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()


def navigate_to_asset_and_get_balance(
    page_operations,
    page_objects,
    asset_name: str,
    asset_type: str = 'ifa',
    application: str | None = None,
    refresh_count: int = 0,
) -> str:
    """
    Navigate to asset and get its balance.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        asset_name: Asset name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        application: Application to focus (optional).
        refresh_count: Number of times to refresh (optional).

    Returns:
        Asset balance string.
    """
    if application:
        page_operations.do_focus_on_application(application)

    for _ in range(refresh_count):
        if asset_type == 'ifa':
            page_objects.sidebar_page_objects.click_inflatable_button()
            page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            page_objects.sidebar_page_objects.click_fungibles_button()
            page_objects.fungible_page_objects.click_refresh_button()
        else:
            page_objects.sidebar_page_objects.click_collectibles_button()
            page_objects.collectible_page_objects.click_refresh_button()

    if asset_type == 'ifa':
        page_objects.sidebar_page_objects.click_inflatable_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)
    elif asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    else:
        page_objects.sidebar_page_objects.click_collectibles_button()
        page_objects.collectible_page_objects.click_cfa_frame(asset_name)

    balance = page_objects.asset_detail_page_objects.get_total_balance()
    page_objects.asset_detail_page_objects.click_close_button()
    return balance


def navigate_to_asset_and_get_transfer_status(
    page_operations,
    page_objects,
    asset_name: str,
    asset_type: str = 'ifa',
) -> str:
    """
    Navigate to asset and get its transfer status.

    Args:
        page_operations: Page operations instance.
        page_objects: Page objects instance.
        asset_name: Asset name.
        asset_type: Asset type ('ifa', 'nia', 'cfa').

    Returns:
        Transfer status string.
    """
    if asset_type == 'ifa':
        page_objects.sidebar_page_objects.click_inflatable_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)
    elif asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    else:
        page_objects.sidebar_page_objects.click_collectibles_button()
        page_objects.collectible_page_objects.click_cfa_frame(asset_name)

    status = page_objects.asset_detail_page_objects.get_transfer_status()
    return status


def issue_nia_multisig_flow(
    wallets_and_operations,
    asset_ticker: str,
    asset_name: str,
    asset_amount: str,
    wallet_variant_name: str,
    is_native_auth_enabled: bool = False,
) -> None:
    """
    Issue NIA asset for multisig wallet flow.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_ticker: Asset ticker.
        asset_name: Asset name.
        asset_amount: Asset amount.
        wallet_variant_name: Wallet variant name.
        is_native_auth_enabled: Whether native auth is enabled.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
        FIRST_APPLICATION, asset_ticker, asset_name, asset_amount,
        wallet_variant_name=wallet_variant_name, is_native_auth_enabled=is_native_auth_enabled,
    )


def issue_cfa_multisig_flow(
    wallets_and_operations,
    asset_name: str,
    asset_description: str,
    asset_amount: str,
    wallet_variant_name: str,
    is_native_auth_enabled: bool = False,
) -> None:
    """
    Issue CFA asset for multisig wallet flow.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name.
        asset_description: Asset description.
        asset_amount: Asset amount.
        wallet_variant_name: Wallet variant name.
        is_native_auth_enabled: Whether native auth is enabled.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
        FIRST_APPLICATION, asset_name, asset_description, asset_amount,
        wallet_variant_name=wallet_variant_name, is_native_auth_enabled=is_native_auth_enabled,
    )


def offline_single_sig_create_utxo_for_send_test_flow(
    wallets_and_operations,
    wallet_variant_name: str,
    asset_name: str,
    send_amount: str,
    asset_type: str = 'nia',
    test_environment=None,
) -> str:
    """
    Create UTXO for send test flow for offline single sig wallet.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
        asset_name: Asset name.
        send_amount: Send amount.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
        test_environment: Test environment instance (optional).

    Returns:
        Invoice string.
    """
    # Get invoice from third wallet (receiver)
    focus_third_wallet(wallets_and_operations)
    invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
        THIRD_APPLICATION,
    )

    # Create UTXO PSBT from second wallet (coordinator)
    navigate_to_asset_and_click_send(
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_objects,
        asset_name, asset_type=asset_type,
    )
    wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
        application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount,
        wallet_variant_name=wallet_variant_name, utxo_required=True,
    )

    # Sign and broadcast UTXO PSBT
    sign_and_broadcast_psbt_offline_single_sig(
        wallets_and_operations, wallet_variant_name,
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_features,
    )

    return invoice


class OfflineSendFlow:
    """
    Helper class for offline send flow operations.
    """

    def __init__(self, wallets_and_operations):
        """
        Initialize OfflineSendFlow.

        Args:
            wallets_and_operations: Wallet test setup instance.
        """
        self.wallets_and_operations = wallets_and_operations

    def create_utxo(self, asset_name: str, send_amount: str, wallet_variant_name: str, asset_type: str = 'nia') -> str:
        """
        Create UTXO for send flow.

        Args:
            asset_name: Asset name.
            send_amount: Send amount.
            wallet_variant_name: Wallet variant name.
            asset_type: Asset type.

        Returns:
            Invoice string.
        """
        return offline_multisig_create_utxo_for_send_test_flow(
            self.wallets_and_operations, wallet_variant_name, asset_name, send_amount, asset_type,
        )

    def send_transfer_single_sig(
        self,
        wallet_variant_name: str,
        asset_name: str,
        asset_type: str = 'nia',
        refresh_count: int = 0,
    ) -> None:
        """
        Send transfer for single sig offline wallet.
        Resumes the draft transfer created after UTXO creation.

        Args:
            wallet_variant_name: Wallet variant name.
            asset_name: Asset name.
            asset_type: Asset type ('ifa', 'nia', 'cfa').
            refresh_count: Number of times to refresh.
        """
        # Navigate to the asset (don't click send - we're resuming a draft)
        navigate_to_asset_and_click_send(
            self.wallets_and_operations.second_page_operations,
            self.wallets_and_operations.second_page_objects,
            asset_name, asset_type=asset_type, click_send=False,
        )

        # Resume the draft transfer (created after UTXO creation)
        if self.wallets_and_operations.second_page_operations.do_is_displayed(
            self.wallets_and_operations.second_page_objects.asset_detail_page_objects.resume_draft_frame(),
        ):
            self.wallets_and_operations.second_page_objects.asset_detail_page_objects.click_resume_draft_frame()

        # Click send button to proceed with the draft
        if self.wallets_and_operations.second_page_operations.do_is_displayed(
            self.wallets_and_operations.second_page_objects.send_asset_page_objects.send_button(),
        ):
            self.wallets_and_operations.second_page_objects.send_asset_page_objects.click_send_button()

        # USB sync to pass PSBT to offline signer
        self.wallets_and_operations.second_page_features.wallet_features.usb_sync()

        # Sign and broadcast transfer PSBT
        sign_and_broadcast_psbt_offline_single_sig(
            self.wallets_and_operations, wallet_variant_name,
            self.wallets_and_operations.second_page_operations,
            self.wallets_and_operations.second_page_features,
        )

        # Refresh to see the transfer
        for _ in range(refresh_count):
            focus_second_wallet(self.wallets_and_operations)
            if asset_type == 'ifa':
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
                self.wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
            elif asset_type == 'nia':
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
                self.wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
            else:
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
                self.wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    def send_transfer_multisig(
        self,
        wallet_variant_name: str,
        asset_name: str,
        asset_type: str = 'nia',
        send_amount: str | None = None,
    ) -> None:
        """
        Complete send transfer flow for multisig offline wallet.
        Creates UTXO, signs and broadcasts it, then creates transfer PSBT and broadcasts.

        Args:
            wallet_variant_name: Wallet variant name.
            asset_name: Asset name.
            asset_type: Asset type ('ifa', 'nia', 'cfa').
            send_amount: Amount to send (optional, uses default if not provided).
        """
        # Step 1: Get invoice from fourth wallet (receiver)
        with allure.step('Get invoice from fourth wallet (receiver)'):
            self.wallets_and_operations.fourth_page_operations.do_focus_on_application(
                FOURTH_APPLICATION,
            )
            invoice = self.wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(
                FOURTH_APPLICATION,
            )

        # Step 2: Create UTXO PSBT from second wallet (coordinator)
        with allure.step('Create UTXO PSBT from second wallet (coordinator)'):
            navigate_to_asset_and_click_send(
                self.wallets_and_operations.second_page_operations,
                self.wallets_and_operations.second_page_objects,
                asset_name, asset_type=asset_type,
            )
            self.wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
                application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount,
                wallet_variant_name=wallet_variant_name, utxo_required=True,
            )

        # Step 3: Sign and broadcast UTXO PSBT
        sign_and_broadcast_psbt_offline_multisig(
            self.wallets_and_operations, wallet_variant_name,
            self.wallets_and_operations.second_page_operations,
            self.wallets_and_operations.second_page_features,
        )

        # Step 4: Resume and broadcast transfer PSBT
        self._resume_and_broadcast_transfer(
            wallet_variant_name, asset_name, asset_type,
        )

    def resume_transfer_multisig(
        self,
        wallet_variant_name: str,
        asset_name: str,
        asset_type: str = 'nia',
    ) -> None:
        """
        Resume draft transfer for multisig offline wallet.
        Used after UTXO has already been created and broadcast in a previous test.

        Args:
            wallet_variant_name: Wallet variant name.
            asset_name: Asset name.
            asset_type: Asset type ('ifa', 'nia', 'cfa').
        """
        self._resume_and_broadcast_transfer(
            wallet_variant_name, asset_name, asset_type,
        )

    def _resume_and_broadcast_transfer(
        self,
        wallet_variant_name: str,
        asset_name: str,
        asset_type: str,
    ) -> None:
        """
        Internal method to resume draft transfer and broadcast it.

        Args:
            wallet_variant_name: Wallet variant name.
            asset_name: Asset name.
            asset_type: Asset type ('ifa', 'nia', 'cfa').
        """
        # Navigate to asset and resume draft transfer
        with allure.step('Navigate to asset and resume draft transfer'):
            navigate_to_asset_and_click_send(
                self.wallets_and_operations.second_page_operations,
                self.wallets_and_operations.second_page_objects,
                asset_name, asset_type=asset_type, click_send=False,
            )

            # Resume the draft transfer (created after UTXO creation)
            if self.wallets_and_operations.second_page_operations.do_is_displayed(
                self.wallets_and_operations.second_page_objects.asset_detail_page_objects.resume_draft_frame(),
            ):
                self.wallets_and_operations.second_page_objects.asset_detail_page_objects.click_resume_draft_frame()

            # Click send button to proceed with the draft
            if self.wallets_and_operations.second_page_operations.do_is_displayed(
                self.wallets_and_operations.second_page_objects.send_asset_page_objects.send_button(),
            ):
                self.wallets_and_operations.second_page_objects.send_asset_page_objects.click_send_button()

        # USB sync to pass PSBT to offline signer
        self.wallets_and_operations.second_page_features.wallet_features.usb_sync()

        # Sign and broadcast transfer PSBT
        sign_and_broadcast_psbt_offline_multisig(
            self.wallets_and_operations, wallet_variant_name,
            self.wallets_and_operations.second_page_operations,
            self.wallets_and_operations.second_page_features,
        )

    def issue_sign_refresh_multisig(
        self,
        wallet_variant_name: str,
        asset_name: str,
        asset_type: str = 'ifa',
    ) -> None:
        """
        Sign and broadcast issue PSBT for offline multisig wallet.
        After issue_ifa_for_offline_multisig_wallet creates PSBT and syncs to offline signer,
        this method signs with offline signer, syncs back, signs with cosigner, and broadcasts.

        Args:
            wallet_variant_name: Wallet variant name.
            asset_name: Asset name.
            asset_type: Asset type ('ifa', 'nia', 'cfa').
        """
        # Step 1: Sign PSBT from first wallet (offline signer with hardware wallet)
        with allure.step('Sign issue PSBT from first wallet (offline signer)'):
            self.wallets_and_operations.first_page_operations.do_focus_on_application(
                FIRST_APPLICATION,
            )
            # Refresh to see the PSBT from USB sync
            if asset_type == 'ifa':
                self.wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
                self.wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
            elif asset_type == 'nia':
                self.wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
                self.wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
            else:  # cfa
                self.wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
                self.wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()

            self.wallets_and_operations.first_page_features.wallet_features.sign_psbt(
                FIRST_APPLICATION, wallet_variant_name,
            )

        # Step 3: Sign PSBT from third wallet (cosigner)
        with allure.step('Sign issue PSBT from third wallet (cosigner)'):
            self.wallets_and_operations.third_page_operations.do_focus_on_application(
                THIRD_APPLICATION,
            )
            if asset_type == 'ifa':
                self.wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
                self.wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
            elif asset_type == 'nia':
                self.wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
                self.wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
            else:  # cfa
                self.wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
                self.wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()

            self.wallets_and_operations.third_page_features.wallet_features.sign_psbt(
                THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
            )

        # Step 4: Broadcast from second wallet (coordinator)
        with allure.step('Broadcast issue PSBT from second wallet (coordinator)'):
            self.wallets_and_operations.second_page_operations.do_focus_on_application(
                SECOND_APPLICATION,
            )
            if asset_type == 'ifa':
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
                self.wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
            elif asset_type == 'nia':
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
                self.wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
            else:  # cfa
                self.wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
                self.wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

            self.wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
                SECOND_APPLICATION, is_multisig=True,
            )


def click_issue_button_get_toaster_and_close(page_objects) -> str:
    """
    Click issue button, get toaster message, and close.

    Args:
        page_objects: Page objects instance.

    Returns:
        Toaster description string.
    """
    page_objects.issue_ifa_page_objects.click_issue_ifa_button()
    _, toaster_description = page_objects.toaster_page_objects.click_toaster_frame()
    return toaster_description


def focus_first_wallet_and_refresh_inflatable(wallets_and_operations) -> None:
    """
    Focus on first wallet and refresh inflatable assets.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
    wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()


def focus_second_wallet_and_refresh_inflatable(wallets_and_operations) -> None:
    """
    Focus on second wallet and refresh inflatable assets.

    Args:
        wallets_and_operations: Wallet test setup instance.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
    wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()


def focus_third_wallet_and_sign_online_multisig(
    wallets_and_operations,
    wallet_variant_name: str,
) -> None:
    """
    Focus on third wallet and sign PSBT for online multisig.

    Args:
        wallets_and_operations: Wallet test setup instance.
        wallet_variant_name: Wallet variant name.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_features.wallet_features.sign_psbt(
        THIRD_APPLICATION, wallet_variant_name, is_rgb=True,
    )


def handle_success_home_button_and_success(page_objects) -> None:
    """
    Handle success home button click.

    Args:
        page_objects: Page objects instance.
    """
    if page_objects.success_page_objects.home_button():
        page_objects.success_page_objects.click_home_button()


def verify_offline_multisig_transfer(
    wallets_and_operations,
    asset_name: str,
    send_amount: str,
    asset_type: str = 'nia',
) -> None:
    """
    Verify transfer status and received amount for offline multisig wallet tests.

    Args:
        wallets_and_operations: Wallet test setup instance.
        asset_name: Asset name to verify.
        send_amount: Expected received amount.
        asset_type: Asset type ('ifa', 'nia', 'cfa').
    """
    # Get fresh page objects from environment after reset
    second_page_objects, _, second_page_operations = get_fresh_page_objects(
        wallets_and_operations, app_index=2,
    )

    # Verify transfer status on sender (second wallet)
    actual_transfer_status = navigate_to_asset_and_get_transfer_status(
        second_page_operations,
        second_page_objects,
        asset_name,
        asset_type=asset_type,
    )
    assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    # Verify received amount on receiver (fourth wallet)
    received_amount = navigate_to_asset_and_get_balance(
        wallets_and_operations.fourth_page_operations,
        wallets_and_operations.fourth_page_objects,
        asset_name,
        asset_type=asset_type,
        application=FOURTH_APPLICATION,
        refresh_count=2,
    )
    assert received_amount == send_amount
