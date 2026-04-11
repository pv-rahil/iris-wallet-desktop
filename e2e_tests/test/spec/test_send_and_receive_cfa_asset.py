# pylint: disable=redefined-outer-name, unused-import, too-many-statements
"""Iris wallet send and receive operation automation test suite for CFA asset"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import OFFLINE_MULTISIG_HARDWARE
from accessible_constant import OFFLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import TestEnvironment
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import focus_and_navigate_to_asset
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.test_helpers import multisig_send_asset_flow_with_verification
from e2e_tests.test.utilities.test_helpers import offline_multisig_send_asset_flow_with_verification
from e2e_tests.test.utilities.test_helpers import offline_wallet_send_asset_flow
from e2e_tests.test.utilities.test_helpers import send_asset_flow_with_verification
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.test_helpers import setup_offline_multisig_hardware_wallets
from e2e_tests.test.utilities.test_helpers import verify_expired_invoice_validation
from e2e_tests.test.utilities.test_helpers import verify_invalid_invoice_validation
from e2e_tests.test.utilities.translation_utils import TranslationManager
from src.model.enums.enums_model import TransactionStatusEnumModel

ASSET_NAME = 'CFA'
ASSET_DESCRIPTION = 'This is CFA asset'
ASSET_AMOUNT = '2000'
SEND_AMOUNT = '50'
INVOICE = 'rgb:~/~/utxob:2msKeFq-uPjwpYxVY-jKS2ymYBq-SqmyP3ovg-AGvth8491-J7seMBm?expiry=1709616110&endpoints=rpc://10.0.2.2:3000/json-rpc'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of send operation for CFA asset in iris wallet')
@allure.story('Testing send CFA asset with expired invoice')
def test_send_cfa_with_expired_invoice(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with expired invoice"""

    with allure.step('Create and fund first wallet for send and receive CFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund second wallet for send and receive CFA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue CFA asset'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_description=ASSET_DESCRIPTION, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Navigate to CFA asset'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            ASSET_NAME,
            asset_type='cfa',
        )

    with allure.step('Verify invalid invoice validation for CFA asset'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset')
def test_send_and_receive_cfa_asset_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset"""

    with allure.step('Generate invoice for CFA asset'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            application=SECOND_APPLICATION,
        )

    send_asset_flow_with_verification(
        wallets_and_operations,
        invoice,
        ASSET_NAME,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='cfa',
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for CFA asset in iris wallet for offline wallet')
@allure.story('Testing send CFA asset with expired invoice for offline wallet')
def test_send_cfa_with_expired_invoice_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with expired invoice for offline wallet"""

    with allure.step('Create and fund first wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Create psbt for CFA asset (offline wallet)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()

        wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_description=ASSET_DESCRIPTION, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT,
        )

    with allure.step('Sign PSBT for CFA asset (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for CFA asset (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Issue CFA asset (offline wallet)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            f"{ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_cfa_page_objects.click_issue_cfa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    verify_expired_invoice_validation(
        wallets_and_operations,
        ASSET_NAME,
        INVOICE,
        TranslationManager.translate('invalid_invoice'),
        asset_type='cfa',
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet for offline wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset for offline wallet')
def test_send_and_receive_cfa_asset_operation_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset for offline wallet"""

    with allure.step('Generate invoice for offline wallet'):
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    offline_wallet_send_asset_flow(
        wallets_and_operations=wallets_and_operations,
        invoice=invoice,
        asset_name=ASSET_NAME,
        send_amount=SEND_AMOUNT,
        wallet_variant_name=wallet_variant_name,
        asset_type='cfa',
    )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for CFA asset in iris wallet for multisig')
@allure.story('Testing send CFA asset with invalid invoice for multisig')
def test_send_cfa_with_invalid_invoice_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with invalid invoice for multisig"""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='cfa')

    with allure.step('Issue CFA asset for multisig wallet'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Navigate to CFA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            ASSET_NAME,
            asset_type='cfa',
        )

    with allure.step('Verify invalid invoice validation for CFA asset (multisig)'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet for multisig')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset for multisig')
def test_send_and_receive_cfa_asset_multisig_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset for multisig"""

    with allure.step('Generate invoice from a third application'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    multisig_send_asset_flow_with_verification(
        wallets_and_operations=wallets_and_operations,
        invoice=invoice,
        asset_name=ASSET_NAME,
        asset_ticker=ASSET_NAME,
        send_amount=SEND_AMOUNT,
        wallet_variant_name=wallet_variant_name,
        asset_type='cfa',
        verify_assertions=True,
    )


# ==============================================================================
# Offline Multisig Tests (4 apps - full transaction flow)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Automation of send operation for CFA asset in iris wallet for offline multisig')
@allure.story('Testing send CFA asset with invalid invoice for offline multisig')
def test_send_cfa_with_invalid_invoice_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with invalid invoice for offline multisig (hardware and on-device, create and load)"""

    setup_offline_multisig_hardware_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_offline_multisig_wallets(wallets_and_operations, asset_type='cfa')

    with allure.step('Issue CFA asset for offline multisig wallet'):
        # Issue from second wallet (online coordinator) - creates PSBT and syncs to offline
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_for_offline_multisig_wallet(
            SECOND_APPLICATION, ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT, wallet_variant_name,
        )

        # Refresh and sign from first wallet (offline signer)
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

        # Broadcast PSBT from second wallet (coordinator)
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

        # Refresh and sign from third wallet (cosigner)
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

        # Refresh second wallet (coordinator)
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Issue CFA asset (offline multisig)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            f"{ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_cfa_page_objects.click_issue_cfa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Navigate to CFA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            ASSET_NAME,
            asset_type='cfa',
        )

    with allure.step('Verify invalid invoice validation for CFA asset (offline multisig)'):
        verify_invalid_invoice_validation(
            wallets_and_operations.second_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send CFA asset')
@allure.story('Create utxo PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_create_utxo_for_send_cfa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset in offline multisig setup (4 apps) - Create UTXO for send."""
    with allure.step('Get invoice from fourth receiver wallet'):
        invoice = wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(FOURTH_APPLICATION)

    # Create UTXO PSBT
    with allure.step('Create UTXO PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(ASSET_NAME)
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.create_psbt_for_multisig(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT,
            wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    # Sign UTXO PSBT from cosigner first
    with allure.step('Sign UTXO PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(THIRD_APPLICATION)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE)

    # Sign UTXO PSBT from offline signer
    with allure.step('Sign UTXO PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(FIRST_APPLICATION)
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(FIRST_APPLICATION, wallet_variant_name)

    # Broadcast UTXO PSBT
    with allure.step('Broadcast UTXO PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(SECOND_APPLICATION, is_multisig=True)

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send CFA asset')
@allure.story('Create transfer PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_send_transfer_cfa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset in offline multisig setup (4 apps) - Send transfer."""

    # Send asset
    with allure.step('Send CFA asset from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(ASSET_NAME)
        wallets_and_operations.second_page_features.send_features.send_asset_for_multisig(SECOND_APPLICATION, wallet_variant_name)

    # Sign transfer PSBT from offline signer first
    with allure.step('Sign transfer PSBT from first wallet (offline signer)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(FIRST_APPLICATION)
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(FIRST_APPLICATION, wallet_variant_name)

    # Sign transfer PSBT from cosigner
    with allure.step('Sign transfer PSBT from third wallet (cosigner)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(THIRD_APPLICATION)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE)

    # Broadcast transfer PSBT
    with allure.step('Broadcast transfer PSBT from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(SECOND_APPLICATION, is_multisig=True)

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send CFA asset')
@allure.story('Verify transaction status and amount')
def test_offline_multisig_verify_for_cfa(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset in offline multisig setup (4 apps) - Verify transfer."""
    # Verify transfer status on sender (second wallet)
    with allure.step('Verify transfer status on second wallet (sender)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION, verify_ready=True)
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(ASSET_NAME)
        actual_transfer_status = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
        assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    # Verify received amount on receiver (fourth wallet)
    with allure.step('Verify received amount on fourth wallet (receiver)'):
        wallets_and_operations.fourth_page_operations.do_focus_on_application(FOURTH_APPLICATION, verify_ready=True)
        wallets_and_operations.fourth_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.fourth_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.fourth_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.fourth_page_objects.collectible_page_objects.click_cfa_frame(ASSET_NAME)
        received_amount = wallets_and_operations.fourth_page_objects.asset_detail_page_objects.get_total_balance()
        assert received_amount == SEND_AMOUNT
