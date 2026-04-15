# pylint: disable=redefined-outer-name, unused-import, unused-argument, too-many-statements
"""Iris wallet send and receive operation automation test suite for NIA asset"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import TestEnvironment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.send_flow_helpers import focus_and_navigate_to_asset
from e2e_tests.test.utilities.send_flow_helpers import generate_invoice_and_send_asset
from e2e_tests.test.utilities.send_flow_helpers import initiate_third_wallet_and_get_invoice
from e2e_tests.test.utilities.send_flow_helpers import issue_nia_multisig_flow
from e2e_tests.test.utilities.send_flow_helpers import multisig_send_asset_flow_with_verification
from e2e_tests.test.utilities.send_flow_helpers import navigate_to_asset_and_get_balance
from e2e_tests.test.utilities.send_flow_helpers import navigate_to_asset_and_get_transfer_status
from e2e_tests.test.utilities.send_flow_helpers import offline_multisig_create_utxo_for_send_test_flow
from e2e_tests.test.utilities.send_flow_helpers import offline_single_sig_create_utxo_for_send_test_flow
from e2e_tests.test.utilities.send_flow_helpers import OfflineSendFlow
from e2e_tests.test.utilities.send_flow_helpers import verify_expired_invoice_validation
from e2e_tests.test.utilities.send_flow_helpers import verify_invalid_invoice_validation
from e2e_tests.test.utilities.send_flow_helpers import verify_invalid_invoice_validation_step
from e2e_tests.test.utilities.send_flow_helpers import verify_offline_multisig_transfer
from e2e_tests.test.utilities.translation_utils import TranslationManager
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_offline_multisig_hardware_wallets
from src.model.enums.enums_model import TransactionStatusEnumModel

ASSET_TICKER = 'TTK'
NIA_ASSET_NAME = 'Tether'
ASSET_AMOUNT = '2000'
SEND_AMOUNT = '50'
INVOICE = 'rgb:~/~/utxob:2msKeFq-uPjwpYxVY-jKS2ymYBq-SqmyP3ovg-AGvth8491-J7seMBm?expiry=1709616110&endpoints=rpc://10.0.2.2:3000/json-rpc'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of send operation for NIA asset in iris wallet')
@allure.story('Testing send NIA asset with expired invoice')
def test_send_nia_with_expired_invoice(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """Test send NIA asset with expired invoice"""

    with allure.step('Create and fund first wallet for send and receive NIA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )
    with allure.step('Create and fund second wallet for send and receive NIA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue NIA asset'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=ASSET_TICKER, asset_name=NIA_ASSET_NAME, asset_amount=ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Send NIA asset with expired invoice'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            NIA_ASSET_NAME,
            asset_type='nia',
        )
    with allure.step('Verify invalid invoice validation for NIA asset'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of receive, send, and transaction status for NIA asset in iris wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for NIA asset')
def test_send_and_receive_nia_asset_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for NIA asset"""

    with allure.step('Issue NIA asset'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=ASSET_TICKER, asset_name=NIA_ASSET_NAME, asset_amount=ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    generate_invoice_and_send_asset(
        wallets_and_operations,
        NIA_ASSET_NAME,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='nia',
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for NIA asset in iris wallet for offline wallet')
@allure.story('Testing send NIA asset with expired invoice for offline wallet')
def test_send_nia_with_expired_invoice_for_offline_wallet(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset with expired invoice for offline wallet"""

    with allure.step('Create and fund first wallet for send and receive NIA (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet for send and receive NIA (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet for send and receive NIA (offline wallet)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Create psbt for NIA asset (offline wallet)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()

        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_ticker=ASSET_TICKER, asset_name=NIA_ASSET_NAME, asset_amount=ASSET_AMOUNT,
        )

    with allure.step('Sign PSBT for NIA asset (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for NIA asset (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Issue NIA asset (offline wallet)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            f"{NIA_ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    verify_expired_invoice_validation(
        wallets_and_operations,
        NIA_ASSET_NAME,
        INVOICE,
        TranslationManager.translate('invalid_invoice'),
        asset_type='nia',
    )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send NIA asset')
@allure.story('Create utxo PSBT, sign with offline signer, then broadcast')
def test_offline_single_sig_create_utxo_for_send_nia(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset in offline single-sig setup (3 apps) - Create UTXO for send."""
    offline_single_sig_create_utxo_for_send_test_flow(
        wallets_and_operations, wallet_variant_name, NIA_ASSET_NAME, SEND_AMOUNT,
        asset_type='nia', test_environment=test_environment,
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send NIA asset')
@allure.story('Create transfer PSBT, sign with offline signer, then broadcast')
def test_offline_single_sig_send_transfer_nia(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset in offline single-sig setup (3 apps) - Send transfer."""
    send_flow = OfflineSendFlow(wallets_and_operations)
    send_flow.send_transfer_single_sig(
        wallet_variant_name, NIA_ASSET_NAME, asset_type='nia', refresh_count=2,
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send NIA asset')
@allure.story('Verify transaction status and amount')
def test_offline_single_sig_verify_for_nia(wallets_and_operations: WalletTestSetup):
    """Test send NIA asset in offline single-sig setup (3 apps) - Verify transfer."""
    # Verify transfer status on sender (second wallet)
    actual_transfer_status = navigate_to_asset_and_get_transfer_status(
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_objects,
        NIA_ASSET_NAME, asset_type='nia',
    )
    assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    # Verify received amount on receiver (third wallet)
    received_amount = navigate_to_asset_and_get_balance(
        wallets_and_operations.third_page_operations,
        wallets_and_operations.third_page_objects,
        NIA_ASSET_NAME, asset_type='nia',
        application=THIRD_APPLICATION,
        refresh_count=2,
    )
    assert received_amount == SEND_AMOUNT


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for NIA asset in iris wallet for multisig')
@allure.story('Testing send NIA asset with invalid invoice for multisig')
def test_send_nia_with_invalid_invoice_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset with invalid invoice for multisig"""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='nia')

    with allure.step('Issue NIA asset for multisig wallet'):
        issue_nia_multisig_flow(
            wallets_and_operations, wallet_variant_name, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT,
        )

    with allure.step('Navigate to NIA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            NIA_ASSET_NAME,
            asset_type='nia',
        )

    with allure.step('Verify invalid invoice validation for NIA asset (multisig)'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for NIA asset in iris wallet for multisig')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for NIA asset for multisig')
def test_send_and_receive_nia_asset_multisig_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for NIA asset for multisig"""

    with allure.step('Initiate third single-sig wallet for receiving NIA asset'):
        invoice = initiate_third_wallet_and_get_invoice(
            third_page_features=wallets_and_operations.third_page_features,
            application=THIRD_APPLICATION,
            variant=ONLINE_CREATE_ON_DEVICE,
        )

    multisig_send_asset_flow_with_verification(
        wallets_and_operations=wallets_and_operations,
        invoice=invoice,
        asset_name=NIA_ASSET_NAME,
        asset_ticker=NIA_ASSET_NAME,
        send_amount=SEND_AMOUNT,
        wallet_variant_name=wallet_variant_name,
        asset_type='nia',
        verify_assertions=True,
    )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Automation of send operation for NIA asset in iris wallet for offline multisig')
@allure.story('Testing send NIA asset with invalid invoice for offline multisig')
def test_send_nia_with_invalid_invoice_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset with invalid invoice for offline multisig (hardware and on-device, create and load)"""

    setup_offline_multisig_hardware_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    fund_and_refresh_offline_multisig_wallets(
        wallets_and_operations, asset_type='nia',
    )

    with allure.step('Issue NIA asset for offline multisig wallet'):
        # Issue from second wallet (online coordinator) - creates PSBT and syncs to offline
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_for_offline_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT, wallet_variant_name,
        )

        # Sign, broadcast, and refresh for offline multisig
        send_flow = OfflineSendFlow(wallets_and_operations)
        send_flow.issue_sign_refresh_multisig(
            wallet_variant_name, NIA_ASSET_NAME, asset_type='nia',
        )

    with allure.step('Issue NIA asset (offline multisig)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            f"{NIA_ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Navigate to NIA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            NIA_ASSET_NAME,
            asset_type='nia',
        )

    with allure.step('Verify invalid invoice validation for NIA asset (offline multisig)'):
        verify_invalid_invoice_validation_step(wallets_and_operations, INVOICE)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send NIA asset')
@allure.story('Create utxo PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_create_utxo_for_send_nia(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset in offline multisig setup (4 apps) - Create UTXO for send."""
    offline_multisig_create_utxo_for_send_test_flow(
        wallets_and_operations, wallet_variant_name, NIA_ASSET_NAME, SEND_AMOUNT, asset_type='nia',
    )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send NIA asset')
@allure.story('Create transfer PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_send_transfer_nia(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send NIA asset in offline multisig setup (4 apps) - Send transfer."""
    send_flow = OfflineSendFlow(wallets_and_operations)
    send_flow.resume_transfer_multisig(
        wallet_variant_name, NIA_ASSET_NAME, asset_type='nia',
    )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send NIA asset')
@allure.story('Verify transaction status and amount')
def test_offline_multisig_verify_for_nia(wallets_and_operations: WalletTestSetup):
    """Test send NIA asset in offline multisig setup (4 apps) - Verify transfer."""
    verify_offline_multisig_transfer(
        wallets_and_operations,
        asset_name=NIA_ASSET_NAME,
        send_amount=SEND_AMOUNT,
        asset_type='nia',
    )
