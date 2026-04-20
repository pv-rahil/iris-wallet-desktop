# pylint: disable=redefined-outer-name, unused-import, unused-argument, too-many-lines
"""Test module for secondary issuance (inflate) of IFA assets across all wallet variants"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import TestEnvironment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_first_wallet_and_click_inflatable
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_first_wallet_and_refresh_inflatable
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_second_wallet_and_refresh_inflatable
from e2e_tests.test.utilities.send_flow_helpers import focus_first_wallet
from e2e_tests.test.utilities.send_flow_helpers import focus_second_wallet
from e2e_tests.test.utilities.send_flow_helpers import focus_second_wallet_and_navigate_to_ifa_tx
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import get_fresh_page_objects
from e2e_tests.test.utilities.wallet_setup_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_offline_multisig_hardware_wallets

ASSET_TICKER = 'IFK'
IFA_ASSET_NAME_1 = 'Inflatable'
INITIAL_SUPPLY = '1000'
IFA_ASSET_TOTAL_SUPPLY = '10000'
INFLATE_AMOUNT = '500'

pytestmark = pytest.mark.order(1)


# ============== SINGLE SIG ONLINE WALLET TESTS ==============

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Secondary Issuance - Single Sig Online')
@allure.story('Issue and inflate IFA asset')
def test_issue_and_inflate_ifa_single_sig_online(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test issuing and inflating IFA asset for single sig online wallet."""

    with allure.step('Create and fund wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue IFA asset'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, INITIAL_SUPPLY, IFA_ASSET_TOTAL_SUPPLY, wallet_variant_name,
        )

    with allure.step('Inflate IFA asset'):
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset(
            FIRST_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name,
        )

    with allure.step('Verify inflate amount in transaction frame'):
        focus_first_wallet_and_click_inflatable(wallets_and_operations)
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_amount = wallets_and_operations.first_page_objects.asset_transaction_detail_page_objects.get_transferred_amount()
        wallets_and_operations.first_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()
        tx_amount = tx_amount.replace('+', '')

        assert tx_amount == INFLATE_AMOUNT


# ============== SINGLE SIG OFFLINE WALLET TESTS ==============

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Secondary Issuance - Single Sig Offline')
@allure.story('Issue IFA asset via PSBT for offline wallet')
def test_offline_single_sig_issue_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test issuing IFA asset via PSBT flow for offline/watch-only wallet."""

    with allure.step('Create offline wallet (watch-only) and online signing wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue IFA asset via PSBT flow'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_offline_wallet(
            SECOND_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, INITIAL_SUPPLY, IFA_ASSET_TOTAL_SUPPLY,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast PSBT'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Finalize issuance from draft'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_watch_only_wallet(
            SECOND_APPLICATION, IFA_ASSET_NAME_1,
        )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Secondary Issuance - Single Sig Offline')
@allure.story('Inflate IFA asset via PSBT for offline wallet')
def test_offline_single_sig_inflate_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test inflating IFA asset via PSBT flow for offline/watch-only wallet."""
    # Get fresh page objects from environment after reset
    second_page_objects, second_page_features, second_page_operations = get_fresh_page_objects(
        wallets_and_operations, app_index=2,
    )

    # First cycle: Create UTXO for inflation
    with allure.step('Create UTXO PSBT for inflation'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_features.inflate_features.inflate_ifa_asset_begin(
            SECOND_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign UTXO PSBT for inflation'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast UTXO PSBT for inflation'):
        second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    # Second cycle: Create inflation PSBT from draft
    with allure.step('Create inflation PSBT from draft'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_objects.sidebar_page_objects.click_inflatable_button()
        second_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        second_page_objects.asset_detail_page_objects.click_resume_secondary_issuance_draft_frame()
        second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        second_page_objects.receive_asset_page_objects.click_receive_asset_close_button()
        second_page_features.wallet_features.usb_sync()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_inflate=True,
        )

    with allure.step('Broadcast inflation PSBT'):
        second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Secondary Issuance - Single Sig Offline')
@allure.story('Verify inflate amount for offline wallet')
def test_offline_single_sig_verify_inflate_ifa(wallets_and_operations: WalletTestSetup):
    """Test verifying inflate amount for offline/watch-only wallet."""

    with allure.step('Verify inflate amount in transaction frame'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_amount = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_transferred_amount()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_amount = tx_amount.replace('+', '')

        assert tx_amount == INFLATE_AMOUNT


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Secondary Issuance - Multisig On-Device Online')
@allure.story('Inflate IFA asset for multisig')
def test_inflate_ifa_multisig_on_device_online(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test secondary issuance (inflate) for multisig on-device online wallet."""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Fund multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Create UTXO PSBT for IFA issuance'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, IFA_ASSET_TOTAL_SUPPLY, INITIAL_SUPPLY, wallet_variant_name,
        )
        focus_second_wallet(wallets_and_operations)
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Issue IFA asset from draft'):
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

    with allure.step('Create UTXO PSBT for secondary issuance'):
        focus_first_wallet(wallets_and_operations)
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset_for_multisig(
            FIRST_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign UTXO PSBT from second wallet'):
        focus_second_wallet_and_refresh_inflatable(wallets_and_operations)
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create inflate PSBT from draft'):
        focus_first_wallet(wallets_and_operations)
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset_from_draft(
            FIRST_APPLICATION, IFA_ASSET_NAME_1,
        )

    with allure.step('Sign inflation PSBT from second wallet'):
        focus_second_wallet_and_refresh_inflatable(wallets_and_operations)
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Verify inflate amount in transaction frame'):
        focus_first_wallet(wallets_and_operations)
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_amount = wallets_and_operations.first_page_objects.asset_transaction_detail_page_objects.get_transferred_amount()
        wallets_and_operations.first_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()
        tx_amount = tx_amount.replace('+', '')

        assert tx_amount == INFLATE_AMOUNT


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Secondary Issuance - Offline Multisig')
@allure.story('Create UTXO PSBT for inflation')
def test_offline_multisig_create_utxo_for_inflate_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test secondary issuance (inflate) for offline multisig wallet - Create UTXO PSBT."""

    setup_offline_multisig_hardware_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    fund_and_refresh_offline_multisig_wallets(
        wallets_and_operations, asset_type='ifa',
    )

    with allure.step('Create UTXO PSBT for IFA issuance from watch-only coordinator'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_for_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, IFA_ASSET_TOTAL_SUPPLY, INITIAL_SUPPLY, wallet_variant_name,
        )

    with allure.step('Sign PSBT from cosigner (App 3)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    with allure.step('Sign PSBT from offline signer (App 1) - required for 2-of-2 multisig'):
        focus_first_wallet_and_refresh_inflatable(wallets_and_operations)
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for IFA issuance from second wallet (coordinator)'):
        focus_second_wallet(wallets_and_operations)
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

    with allure.step('Issue IFA asset from draft'):
        focus_second_wallet_and_refresh_inflatable(wallets_and_operations)
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for secondary issuance'):
        focus_second_wallet(wallets_and_operations)
        wallets_and_operations.second_page_features.inflate_features.inflate_ifa_asset_for_multisig(
            SECOND_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign UTXO PSBT from cosigner (App 3)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    with allure.step('Sign UTXO PSBT from offline signer (App 1) - required for 2-of-2 multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast UTXO PSBT for inflation from second wallet (coordinator)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Secondary Issuance - Offline Multisig')
@allure.story('Create inflate PSBT and broadcast')
def test_offline_multisig_inflate_transfer_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test secondary issuance (inflate) for offline multisig wallet - Inflate PSBT."""
    # Get fresh page objects from environment after reset
    _, second_page_features, second_page_operations = get_fresh_page_objects(
        wallets_and_operations, app_index=2,
    )

    with allure.step('Create inflate PSBT from draft'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_features.inflate_features.inflate_ifa_asset_from_draft(
            SECOND_APPLICATION, IFA_ASSET_NAME_1,
        )

    with allure.step('Sign inflation PSBT from cosigner (App 3)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    with allure.step('Sign inflation PSBT from offline signer (App 1) - required for 2-of-2 multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast inflation PSBT from second wallet (coordinator)'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION, is_multisig=True,
        )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Secondary Issuance - Offline Multisig')
@allure.story('Verify inflate amount')
def test_offline_multisig_verify_inflate_ifa(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test secondary issuance (inflate) for offline multisig wallet - Verify."""
    # Get fresh page objects from environment after reset
    second_page_objects, _, _ = get_fresh_page_objects(
        wallets_and_operations, app_index=2,
    )

    with allure.step('Verify inflate amount in transaction frame'):
        focus_second_wallet_and_navigate_to_ifa_tx(
            wallets_and_operations, IFA_ASSET_NAME_1,
        )
        tx_amount = second_page_objects.asset_transaction_detail_page_objects.get_transferred_amount()
        second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        second_page_objects.asset_detail_page_objects.click_close_button()
        tx_amount = tx_amount.replace('+', '')

        assert tx_amount == INFLATE_AMOUNT
