# pylint: disable=redefined-outer-name, unused-import, unused-argument, too-many-statements
"""Iris wallet send and receive operation automation test suite for IFA asset"""
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
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import focus_and_navigate_to_asset
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.test_helpers import initiate_third_wallet_and_get_invoice
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

    with allure.step('Generate invoice for receiving IFA asset'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    # IFA: send asset flow with verification
    send_asset_flow_with_verification(
        wallets_and_operations,
        invoice,
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
def test_send_ifa_with_expired_invoice_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
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
            asset_name=IFA_ASSET_NAME, issue_amount=ASSET_AMOUNT,
            total_supply=TOTAL_SUPPLY, variant_name=wallet_variant_name,
        )

    with allure.step('Sign PSBT for IFA asset (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for IFA asset (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    verify_expired_invoice_validation(
        wallets_and_operations,
        IFA_ASSET_NAME,
        INVOICE,
        TranslationManager.translate('invalid_invoice'),
        asset_type='ifa',
    )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for IFA asset in iris wallet for offline wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for IFA asset for offline wallet')
def test_send_and_receive_ifa_asset_operation_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for IFA asset for offline wallet"""

    with allure.step('Generate invoice for offline wallet for receiving IFA asset'):
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    # IFA offline wallet: send asset flow
    offline_wallet_send_asset_flow(
        wallets_and_operations,
        invoice,
        IFA_ASSET_NAME,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='ifa',
    )


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
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

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

    with allure.step('Initiate third single-sig wallet for receiving IFA asset'):
        invoice = initiate_third_wallet_and_get_invoice(
            wallets_and_operations.third_page_features,
            THIRD_APPLICATION,
            ONLINE_CREATE_ON_DEVICE,
        )

    multisig_send_asset_flow_with_verification(
        wallets_and_operations,
        invoice,
        IFA_ASSET_NAME,
        ASSET_TICKER,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='ifa',
        verify_assertions=True,
    )


# ==============================================================================
# Offline Multisig Tests (4 apps - full transaction flow)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for IFA asset in iris wallet for offline multisig')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for IFA asset for offline multisig')
def test_send_and_receive_ifa_asset_offline_multisig_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for IFA asset for offline multisig (hardware and on-device, create and load)"""

    setup_offline_multisig_hardware_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Get invoice from fourth receiver wallet'):
        invoice = wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(
            FOURTH_APPLICATION,
        )

    offline_multisig_send_asset_flow_with_verification(
        wallets_and_operations=wallets_and_operations,
        invoice=invoice,
        asset_name=IFA_ASSET_NAME,
        asset_ticker=ASSET_TICKER,
        send_amount=SEND_AMOUNT,
        wallet_variant_name=wallet_variant_name,
        asset_type='ifa',
        verify_assertions=True,
    )
