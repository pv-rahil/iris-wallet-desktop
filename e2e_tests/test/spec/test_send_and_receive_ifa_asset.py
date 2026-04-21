# pylint: disable=redefined-outer-name, unused-import, unused-argument, too-many-statements
"""Iris wallet send and receive operation automation test suite for IFA asset"""
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
from e2e_tests.test.utilities.multisig_send_flow_helpers import generate_multisig_invoice_and_send
from e2e_tests.test.utilities.multisig_send_flow_helpers import navigate_to_asset_and_get_balance
from e2e_tests.test.utilities.multisig_send_flow_helpers import navigate_to_asset_and_get_transfer_status
from e2e_tests.test.utilities.multisig_send_flow_helpers import offline_issue_sign_refresh_multisig
from e2e_tests.test.utilities.multisig_send_flow_helpers import offline_multisig_create_utxo_for_send_test_flow
from e2e_tests.test.utilities.multisig_send_flow_helpers import offline_resume_transfer_multisig
from e2e_tests.test.utilities.multisig_send_flow_helpers import offline_send_transfer_single_sig
from e2e_tests.test.utilities.multisig_send_flow_helpers import offline_single_sig_create_utxo_for_send_test_flow
from e2e_tests.test.utilities.multisig_send_flow_helpers import verify_offline_multisig_transfer
from e2e_tests.test.utilities.psbt_helpers import focus_and_refresh_asset_list
from e2e_tests.test.utilities.psbt_helpers import focus_refresh_and_sign_psbt
from e2e_tests.test.utilities.send_flow_helpers import focus_and_navigate_to_asset
from e2e_tests.test.utilities.send_flow_helpers import generate_invoice_and_send_asset
from e2e_tests.test.utilities.send_flow_helpers import verify_expired_invoice_validation
from e2e_tests.test.utilities.send_flow_helpers import verify_invalid_invoice_validation
from e2e_tests.test.utilities.send_flow_helpers import verify_invalid_invoice_validation_step
from e2e_tests.test.utilities.translation_utils import TranslationManager
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_offline_multisig_hardware_wallets
from src.model.enums.enums_model import TransactionStatusEnumModel

ASSET_TICKER = 'IFK'
IFA_ASSET_NAME = 'Inflatable'
ASSET_AMOUNT = '2000'
TOTAL_SUPPLY = '10000'
SEND_AMOUNT = '50'
INVOICE = 'rgb:~/~/utxob:2msKeFq-uPjwpYxVY-jKS2ymYBq-SqmyP3ovg-AGvth8491-J7seMBm?expiry=1709616110&endpoints=rpc://10.0.2.2:3000/json-rpc'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of send operation for IFA asset in iris wallet')
@allure.story('Testing send IFA asset with expired invoice')
def test_send_ifa_with_expired_invoice(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """Test send IFA asset with expired invoice"""

    with allure.step('Create and fund first wallet for send and receive IFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )
    with allure.step('Create and fund second wallet for send and receive IFA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue IFA asset'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=ASSET_TICKER,
            asset_name=IFA_ASSET_NAME, issue_amount=ASSET_AMOUNT,
            total_supply=TOTAL_SUPPLY, variant_name=wallet_variant_name,
        )

    with allure.step('Send IFA asset with expired invoice'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            IFA_ASSET_NAME,
            asset_type='ifa',
        )
    with allure.step('Verify invalid invoice validation'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of receive, send, and transaction status for IFA asset in iris wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for IFA asset')
def test_send_and_receive_ifa_asset_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for IFA asset"""

    with allure.step('Issue IFA asset'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=ASSET_TICKER,
            asset_name=IFA_ASSET_NAME, issue_amount=ASSET_AMOUNT,
            total_supply=TOTAL_SUPPLY, variant_name=wallet_variant_name,
        )

    generate_invoice_and_send_asset(
        wallets_and_operations,
        IFA_ASSET_NAME,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='ifa',
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for IFA asset in iris wallet for offline wallet')
@allure.story('Testing send IFA asset with expired invoice for offline wallet')
def test_send_ifa_with_expired_invoice_for_offline_wallet(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset with expired invoice for offline wallet"""

    with allure.step('Create and fund first wallet for send and receive IFA (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet for send and receive IFA (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet for send and receive IFA (offline wallet)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Create psbt for IFA asset (offline wallet)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()

        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_ticker=ASSET_TICKER,
            asset_name=IFA_ASSET_NAME, asset_amount=ASSET_AMOUNT,
            total_supply=TOTAL_SUPPLY,
        )

    with allure.step('Sign PSBT for IFA asset (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for IFA asset (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Issue IFA asset (offline wallet)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f"{IFA_ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    verify_expired_invoice_validation(
        wallets_and_operations,
        IFA_ASSET_NAME,
        INVOICE,
        TranslationManager.translate('invalid_invoice'),
        asset_type='ifa',
    )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send IFA asset')
@allure.story('Create utxo PSBT, sign with offline signer, then broadcast')
def test_offline_single_sig_create_utxo_for_send_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset in offline single-sig setup (3 apps) - Create UTXO for send."""
    offline_single_sig_create_utxo_for_send_test_flow(
        wallets_and_operations, wallet_variant_name, IFA_ASSET_NAME, SEND_AMOUNT,
        asset_type='ifa', test_environment=test_environment,
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send IFA asset')
@allure.story('Create transfer PSBT, sign with offline signer, then broadcast')
def test_offline_single_sig_send_transfer_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset in offline single-sig setup (3 apps) - Send transfer."""
    offline_send_transfer_single_sig(
        wallets_and_operations, wallet_variant_name, IFA_ASSET_NAME, asset_type='ifa', refresh_count=2,
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Offline single-sig send IFA asset')
@allure.story('Verify transaction status and amount')
def test_offline_single_sig_verify_for_ifa(wallets_and_operations: WalletTestSetup):
    """Test send IFA asset in offline single-sig setup (3 apps) - Verify transfer."""
    # Verify transfer status on sender (second wallet)
    actual_transfer_status = navigate_to_asset_and_get_transfer_status(
        wallets_and_operations.second_page_operations,
        wallets_and_operations.second_page_objects,
        IFA_ASSET_NAME, asset_type='ifa',
    )
    assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    # Verify received amount on receiver (third wallet)
    received_amount = navigate_to_asset_and_get_balance(
        wallets_and_operations.third_page_operations,
        wallets_and_operations.third_page_objects,
        IFA_ASSET_NAME, asset_type='ifa',
        application=THIRD_APPLICATION, refresh_count=1,
    )
    assert received_amount == SEND_AMOUNT


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for IFA asset in iris wallet for multisig')
@allure.story('Testing send IFA asset with invalid invoice for multisig')
def test_send_ifa_with_invalid_invoice_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset with invalid invoice for multisig"""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='ifa')

    with allure.step('Issue IFA asset for multisig wallet'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, TOTAL_SUPPLY, ASSET_AMOUNT, wallet_variant_name,
        )
        focus_refresh_and_sign_psbt(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            wallets_and_operations.second_page_features,
            SECOND_APPLICATION, wallet_variant_name, asset_type='ifa',
        )
        focus_and_refresh_asset_list(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            FIRST_APPLICATION, asset_type='ifa',
        )
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, wallet_variant_name,
        )
        focus_and_refresh_asset_list(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            SECOND_APPLICATION, asset_type='ifa',
        )

    with allure.step('Navigate to IFA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.first_page_operations,
            wallets_and_operations.first_page_objects,
            IFA_ASSET_NAME,
            asset_type='ifa',
        )

    with allure.step('Verify invalid invoice validation for IFA asset (multisig)'):
        verify_invalid_invoice_validation(
            wallets_and_operations.first_page_objects,
            INVOICE,
            TranslationManager.translate('invalid_invoice'),
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for IFA asset in iris wallet for multisig')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for IFA asset for multisig')
def test_send_and_receive_ifa_asset_multisig_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for IFA asset for multisig"""

    generate_multisig_invoice_and_send(
        wallets_and_operations,
        IFA_ASSET_NAME,
        ASSET_TICKER,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='ifa',
        verify_assertions=True,
    )


# ==============================================================================
# Offline Multisig Tests (4 apps - split into separate tests)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Automation of send operation for IFA asset in iris wallet for offline multisig')
@allure.story('Testing send IFA asset with invalid invoice for offline multisig')
def test_send_ifa_with_invalid_invoice_for_offline_multisig(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset with invalid invoice for offline multisig (hardware and on-device, create and load)"""

    setup_offline_multisig_hardware_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    fund_and_refresh_offline_multisig_wallets(
        wallets_and_operations, asset_type='ifa',
    )

    with allure.step('Issue IFA asset for offline multisig wallet'):
        # Issue from second wallet (online coordinator) - creates PSBT and syncs to offline
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_for_offline_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, TOTAL_SUPPLY, ASSET_AMOUNT, wallet_variant_name,
        )

        # Sign, broadcast, and refresh for offline multisig
        offline_issue_sign_refresh_multisig(
            wallets_and_operations, wallet_variant_name, IFA_ASSET_NAME, asset_type='ifa',
        )

    with allure.step('Issue IFA asset (offline multisig)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f"{IFA_ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Navigate to IFA asset for sending'):
        focus_and_navigate_to_asset(
            wallets_and_operations.second_page_operations,
            wallets_and_operations.second_page_objects,
            IFA_ASSET_NAME,
            asset_type='ifa',
        )

    with allure.step('Verify invalid invoice validation for IFA asset (offline multisig)'):
        verify_invalid_invoice_validation_step(wallets_and_operations, INVOICE)

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send IFA asset')
@allure.story('Create utxo PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_create_utxo_for_send_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset in offline multisig setup (4 apps) - Send after UTXO created."""
    offline_multisig_create_utxo_for_send_test_flow(
        wallets_and_operations,
        wallet_variant_name,
        IFA_ASSET_NAME,
        SEND_AMOUNT,
        asset_type='ifa',
    )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send IFA asset')
@allure.story('Create transfer PSBT, sign with offline signer and cosigner, then broadcast')
def test_offline_multisig_send_transfer_ifa(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send IFA asset in offline multisig setup (4 apps) - Send transfer."""
    offline_resume_transfer_multisig(
        wallets_and_operations, wallet_variant_name, IFA_ASSET_NAME, asset_type='ifa',
    )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Offline multisig send IFA asset')
@allure.story('Verify transaction status and amount')
def test_offline_multisig_verify_for_ifa(wallets_and_operations: WalletTestSetup):
    """Test send IFA asset in offline multisig setup (4 apps) - Verify transfer."""
    verify_offline_multisig_transfer(
        wallets_and_operations,
        asset_name=IFA_ASSET_NAME,
        send_amount=SEND_AMOUNT,
        asset_type='ifa',
    )
