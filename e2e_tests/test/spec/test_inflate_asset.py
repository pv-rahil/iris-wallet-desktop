# pylint: disable=redefined-outer-name, unused-import, unused-argument, too-many-lines
"""Test module for secondary issuance (inflate) of IFA assets across all wallet variants"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets

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
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
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


# ============== SINGLE SIG OFFLINE WALLET TESTS ==============

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@allure.feature('Secondary Issuance - Single Sig Offline')
@allure.story('Issue and inflate IFA asset via PSBT for offline wallet')
def test_issue_and_inflate_ifa_single_sig_offline(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test issuing and inflating IFA asset via PSBT flow for offline/watch-only wallet."""

    with allure.step('Create offline wallet (watch-only) and online signing wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue IFA asset via PSBT flow'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_watch_only_wallet(
            SECOND_APPLICATION, IFA_ASSET_NAME_1,
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
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f'{IFA_ASSET_NAME_1} (Draft)',
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Create PSBT for inflation'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_secondary_issuance_button()
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.enter_asset_amount(
            INFLATE_AMOUNT,
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast inflation PSBT'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Finalize inflation from draft'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f'{IFA_ASSET_NAME_1} (Draft)',
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

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


# ============== HARDWARE WALLET TESTS ==============

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Secondary Issuance - Hardware Wallet')
@allure.story('Issue and inflate IFA asset with hardware wallet')
def test_issue_and_inflate_ifa_hardware_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test issuing and inflating IFA asset with hardware wallet."""

    with allure.step('Create and fund hardware wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue IFA asset'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, INITIAL_SUPPLY, IFA_ASSET_TOTAL_SUPPLY, wallet_variant_name,
        )

    with allure.step('Inflate IFA asset with hardware wallet'):
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset(
            FIRST_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name,
        )

    with allure.step('Verify inflate amount in transaction frame'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
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
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME_1, IFA_ASSET_TOTAL_SUPPLY, INITIAL_SUPPLY,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
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
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset_for_multisig(
            FIRST_APPLICATION, IFA_ASSET_NAME_1, INFLATE_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign UTXO PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create inflate PSBT from draft'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.inflate_features.inflate_ifa_asset_from_draft(
            FIRST_APPLICATION, IFA_ASSET_NAME_1,
        )

    with allure.step('Sign inflation PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Verify inflate amount in transaction frame'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
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
