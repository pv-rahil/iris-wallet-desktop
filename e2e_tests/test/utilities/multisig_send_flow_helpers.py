# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements, too-many-instance-attributes
"""
Multisig send flow and verification helper functions for e2e tests.
"""
from __future__ import annotations

import allure

from accessible_constant import CONFIRMATION_DIALOG
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_with_hardware_wallet
from e2e_tests.test.utilities.psbt_helpers import sign_and_broadcast_psbt_offline_multisig
from e2e_tests.test.utilities.psbt_helpers import sign_and_broadcast_psbt_offline_single_sig
from e2e_tests.test.utilities.send_flow_helpers import focus_first_wallet
from e2e_tests.test.utilities.send_flow_helpers import focus_second_wallet
from e2e_tests.test.utilities.send_flow_helpers import focus_third_wallet
from e2e_tests.test.utilities.send_flow_helpers import initiate_third_wallet_and_get_invoice
from e2e_tests.test.utilities.send_flow_helpers import navigate_to_asset_and_click_send
from e2e_tests.test.utilities.wallet_setup_helpers import _refresh_third_wallet_by_asset_type
from e2e_tests.test.utilities.wallet_setup_helpers import get_fresh_page_objects
from src.model.enums.enums_model import TransactionStatusEnumModel


def multisig_send_asset_flow_with_verification(
    wallets_and_operations,
    invoice: str, asset_name: str,
    asset_ticker: str, send_amount: str,
    wallet_variant_name: str,
    asset_type: str = 'ifa',
    verify_assertions: bool = True,
) -> None:
    """
    Execute multisig send asset flow with PSBT creation, cosigning, and verification.
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


def generate_multisig_invoice_and_send(
    wallets_and_operations,
    asset_name: str, asset_ticker: str,
    send_amount: str, wallet_variant_name: str,
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


def handle_confirmation_dialog_and_usb_sync(self, wallet_feature) -> None:
    """
    Handle confirmation dialog and USB sync for offline wallet operations.
    """
    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_dialog()):
        self.confirmation_dialog_page_objects.click_confirmation_dialog()

    if self.do_is_displayed(self.confirmation_dialog_page_objects.confirmation_continue_button()):
        self.confirmation_dialog_page_objects.click_confirmation_continue_button()

    wallet_feature.usb_sync(is_receive=True)


def handle_native_auth_and_focus(self, application: str, is_native_auth_enabled: bool = False) -> None:
    """
    Handle native auth password entry and focus application.
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
    self, application: str,
    wallet_feature, is_native_auth_enabled: bool = False,
    utxo_required: bool = False, is_hardware: bool = False,
    ledger_app_name: str = LEDGER_EMULATOR_APP_NAME,
) -> None:
    """
    Handle native auth, UTXO confirmation with hardware wallet, and success flow.
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
    self, application: str,
    wallet_feature, is_native_auth_enabled: bool = False,
) -> None:
    """
    Handle UTXO confirmation dialog and USB sync for offline multisig wallet.
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
) -> None:
    """
    Execute offline multisig issue asset test flow with 3 apps.
    Handles funding, issuing, and signing for offline multisig wallet tests.
    """
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
            wallet_variant_name,
        )

    with allure.step(''):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.usb_sync()

    # Refresh third wallet and sign
    with allure.step('Refresh third wallet and sign PSBT'):
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    with allure.step('Sign PSBT from first wallet (offline hardware signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
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
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()


def focus_first_wallet_and_click_inflatable(wallets_and_operations) -> None:
    """
    Focus on first wallet and click inflatable button.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()


def focus_first_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on first wallet and refresh fungible assets.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()


def focus_second_wallet_and_click_inflatable(wallets_and_operations) -> None:
    """
    Focus on second wallet and click inflatable button.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()


def focus_second_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on second wallet and refresh fungible assets.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()


def focus_third_wallet_and_click_bitcoin_frame(wallets_and_operations) -> None:
    """
    Focus on third wallet and click bitcoin frame.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.fungible_page_objects.click_bitcoin_frame()


def focus_third_wallet_and_refresh_fungible(wallets_and_operations) -> None:
    """
    Focus on third wallet and refresh fungible assets.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()


def focus_first_wallet_and_click_bitcoin_frame(wallets_and_operations) -> None:
    """
    Focus on first wallet and click bitcoin frame.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()


def focus_third_wallet_and_refresh_bitcoin(wallets_and_operations) -> None:
    """
    Focus on third wallet and refresh bitcoin.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()


def focus_second_wallet_and_click_fungibles(wallets_and_operations) -> None:
    """
    Focus on second wallet and click fungibles button.
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

    if asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    elif asset_type == 'ifa':
        page_objects.sidebar_page_objects.click_inflatable_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)
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
    """
    if asset_type == 'cfa':
        page_objects.sidebar_page_objects.click_collectibles_button()
        page_objects.collectible_page_objects.click_cfa_frame(asset_name)
    elif asset_type == 'nia':
        page_objects.sidebar_page_objects.click_fungibles_button()
        page_objects.fungible_page_objects.click_nia_frame(asset_name)
    else:
        page_objects.sidebar_page_objects.click_inflatable_button()
        page_objects.inflatable_page_objects.click_ifa_frame(asset_name)

    status = page_objects.asset_detail_page_objects.get_transfer_status()
    return status


def issue_nia_multisig_flow(
    wallets_and_operations, asset_ticker: str,
    asset_name: str, asset_amount: str,
    wallet_variant_name: str, is_native_auth_enabled: bool = False,
) -> None:
    """
    Issue NIA asset for multisig wallet flow.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
        FIRST_APPLICATION, asset_ticker, asset_name, asset_amount,
        wallet_variant_name=wallet_variant_name, is_native_auth_enabled=is_native_auth_enabled,
    )


def issue_cfa_multisig_flow(
    wallets_and_operations, asset_name: str,
    asset_description: str, asset_amount: str,
    wallet_variant_name: str, is_native_auth_enabled: bool = False,
) -> None:
    """
    Issue CFA asset for multisig wallet flow.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
        FIRST_APPLICATION, asset_name, asset_description, asset_amount,
        wallet_variant_name=wallet_variant_name, is_native_auth_enabled=is_native_auth_enabled,
    )


def offline_single_sig_create_utxo_for_send_test_flow(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, send_amount: str,
    asset_type: str = 'nia', test_environment=None,
) -> str:
    """
    Create UTXO for send test flow for offline single sig wallet.
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
    wallets_and_operations.second_page_features.send_features.create_psbt(
        application=SECOND_APPLICATION, receiver_invoice=invoice, amount=send_amount,
        wallet_variant_name=wallet_variant_name, utxo_required=True,
    )

    # Sign and broadcast UTXO PSBT
    sign_and_broadcast_psbt_offline_single_sig(
        wallets_and_operations, wallet_variant_name,
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_features,
        is_rgb=False,
    )

    return invoice


def offline_send_transfer_multisig(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, asset_type: str = 'nia',
    send_amount: str | None = None,
) -> None:
    """
    Complete send transfer flow for multisig offline wallet.
    Creates UTXO, signs and broadcasts it, then creates transfer PSBT and broadcasts.
    """
    # Step 1: Get invoice from fourth wallet (receiver)
    with allure.step('Get invoice from fourth wallet (receiver)'):
        wallets_and_operations.fourth_page_operations.do_focus_on_application(
            FOURTH_APPLICATION,
        )
        invoice = wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(
            FOURTH_APPLICATION,
        )

    # Step 2: Create UTXO PSBT from second wallet (coordinator)
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

    # Step 3: Sign and broadcast UTXO PSBT
    sign_and_broadcast_psbt_offline_multisig(
        wallets_and_operations, wallet_variant_name,
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_features,
    )

    # Step 4: Resume and broadcast transfer PSBT
    _resume_and_broadcast_transfer_offline(
        wallets_and_operations, wallet_variant_name, asset_name, asset_type,
    )


def _resume_and_broadcast_transfer_offline(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, asset_type: str,
) -> None:
    """
    Resume draft transfer and broadcast it for offline multisig.
    """
    # Navigate to asset and resume draft transfer
    with allure.step('Navigate to asset and resume draft transfer'):
        navigate_to_asset_and_click_send(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            asset_name, asset_type=asset_type, click_send=False,
        )

    # Resume and send transfer
    with allure.step('Resume draft and send transfer'):
        wallets_and_operations.second_page_features.send_features.send_asset_for_multisig(
            SECOND_APPLICATION, wallet_variant_name,
        )

    # Sign from third wallet (cosigner)
    with allure.step('Sign PSBT from third wallet (cosigner)'):
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE, is_rgb=True,
        )

    with allure.step('Sign PSBT from first wallet (offline hardware signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_rgb=True,
        )

    # Broadcast from second wallet
    with allure.step('Broadcast PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )


def offline_issue_sign_refresh_multisig(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, asset_type: str = 'ifa',
) -> None:
    """
    Sign and broadcast issue PSBT for offline multisig wallet.
    """
    # Step 1: Sign PSBT from first wallet (offline signer with hardware wallet)
    with allure.step('Sign issue PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        # Refresh to see the PSBT from USB sync
        if asset_type == 'ifa':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        else:  # cfa
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()

        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    # Step 2: Sign PSBT from third wallet (cosigner)
    with allure.step('Sign issue PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        else:  # cfa
            wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()

        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    # Step 3: Broadcast from second wallet (coordinator)
    with allure.step('Broadcast issue PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        else:  # cfa
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )


def offline_send_transfer_single_sig(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, asset_type: str = 'nia',
    refresh_count: int = 0,
) -> None:
    """
    Send transfer for single sig offline wallet.
    Resumes the draft transfer created after UTXO creation.
    """
    # Navigate to the asset (don't click send - we're resuming a draft)
    navigate_to_asset_and_click_send(
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_objects,
        asset_name, asset_type=asset_type, click_send=False,
    )

    # Resume the draft transfer (created after UTXO creation)
    if wallets_and_operations.second_page_operations.do_is_displayed(
        wallets_and_operations.second_page_objects.asset_detail_page_objects.resume_draft_frame(),
    ):
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_resume_draft_frame()

    # Click send button to proceed with the draft
    if wallets_and_operations.second_page_operations.do_is_displayed(
        wallets_and_operations.second_page_objects.send_asset_page_objects.send_button(),
    ):
        wallets_and_operations.second_page_objects.send_asset_page_objects.click_send_button()

    wallets_and_operations.second_page_objects.receive_asset_page_objects.click_receive_asset_close_button()

    # USB sync to pass PSBT to offline signer
    wallets_and_operations.second_page_features.wallet_features.usb_sync()

    # Sign and broadcast transfer PSBT
    sign_and_broadcast_psbt_offline_single_sig(
        wallets_and_operations, wallet_variant_name,
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_features,
    )

    # Refresh to see the transfer
    for _ in range(refresh_count):
        focus_second_wallet(wallets_and_operations)
        if asset_type == 'ifa':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
            wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        elif asset_type == 'nia':
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
            wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        else:
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
            wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


def offline_resume_transfer_multisig(
    wallets_and_operations, wallet_variant_name: str,
    asset_name: str, asset_type: str = 'nia',
) -> None:
    """
    Resume draft transfer for multisig offline wallet.
    Used after UTXO has already been created and b
    """
    # Resume transfer from second wallet
    with allure.step('Resume transfer from second wallet'):
        navigate_to_asset_and_click_send(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            asset_name, asset_type=asset_type, click_send=False,
        )
        wallets_and_operations.second_page_features.send_features.send_asset_for_multisig(
            SECOND_APPLICATION, wallet_variant_name,
        )

    # Sign from third wallet
    with allure.step('Sign PSBT from third wallet'):
        _refresh_third_wallet_by_asset_type(wallets_and_operations, asset_type)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE, is_rgb=True,
        )

    with allure.step('Sign PSBT from first wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_rgb=True,
        )

    # Broadcast from second wallet
    with allure.step('Broadcast PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )


def click_issue_button_get_toaster_and_close(page_objects) -> str:
    """
    Click issue button, get toaster description, and close.
    """
    page_objects.issue_ifa_page_objects.click_issue_ifa_button()
    _, toaster_description = page_objects.toaster_page_objects.click_toaster_frame()
    return toaster_description


def focus_first_wallet_and_refresh_inflatable(wallets_and_operations) -> None:
    """
    Focus on first wallet and refresh inflatable assets.
    """
    focus_first_wallet(wallets_and_operations)
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
    wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()


def focus_second_wallet_and_refresh_inflatable(wallets_and_operations) -> None:
    """
    Focus on second wallet and refresh inflatable assets.
    """
    focus_second_wallet(wallets_and_operations)
    wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
    wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()


def focus_second_wallet_refresh_inflatable_and_sign(
    wallets_and_operations, wallet_variant_name: str,
) -> None:
    """
    Focus on second wallet, refresh inflatable assets, and sign PSBT.
    """
    wallets_and_operations.second_page_operations.do_focus_on_application(
        SECOND_APPLICATION,
    )
    wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
    wallets_and_operations.second_page_features.wallet_features.sign_psbt(
        SECOND_APPLICATION, wallet_variant_name,
    )


def focus_third_wallet_and_sign_online_multisig(
    wallets_and_operations, wallet_variant_name: str,
) -> None:
    """
    Focus on third wallet and sign PSBT for online multisig.
    """
    focus_third_wallet(wallets_and_operations)
    wallets_and_operations.third_page_features.wallet_features.sign_psbt(
        THIRD_APPLICATION, wallet_variant_name, is_rgb=True,
    )


def handle_success_home_button_and_success(page_objects) -> None:
    """
    Handle success home button click.
    """
    if page_objects.success_page_objects.home_button():
        page_objects.success_page_objects.click_home_button()


def verify_offline_multisig_transfer(
    wallets_and_operations, asset_name: str,
    send_amount: str, asset_type: str = 'nia',
) -> None:
    """
    Verify transfer status and received amount for offline multisig wallet tests.
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
