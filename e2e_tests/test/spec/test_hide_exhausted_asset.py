# pylint: disable=redefined-outer-name, unused-import
"""Test module for hiding exhausted asset"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.test_helpers import initiate_third_wallet_and_get_invoice
from e2e_tests.test.utilities.test_helpers import multisig_send_asset_flow_with_verification
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets

ASSET_TICKER = 'TTK'
ASSET_NAME = 'Tether'
ASSET_AMOUNT = '2000'
ISSUE_NIA_TOASTER_MESSAGE = 'You have insufficient funds'


@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_multisig
@allure.feature('Hide exhausted asset')
@allure.story('Toggling on hide exhausted asset')
def test_hide_exhausted_asset_on(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for hiding exhausted asset"""
    with allure.step('Initializing the wallets and funding them'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            FIRST_APPLICATION, variant=wallet_variant_name,
        )

        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Navigating to settings page'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Issuing a asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Generating a RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Send asset to the second page'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.send_features.send(
                FIRST_APPLICATION, invoice, ASSET_AMOUNT, is_hardware_wallet=True, purpose='send_asset',
            )
        else:
            wallets_and_operations.first_page_features.send_features.send(
                FIRST_APPLICATION, invoice, ASSET_AMOUNT,
            )

        child_count = wallets_and_operations.first_page_objects.fungible_page_objects.get_child_count()

        assert len(child_count) == 3


@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_multisig
@allure.feature('Hide exhausted asset')
@allure.story('Toggling off hide exhausted asset')
def test_hide_exhausted_asset_off(wallets_and_operations: WalletTestSetup):
    """Test for hiding exhausted asset"""

    with allure.step('Navigating to settings page'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Send asset to the second page'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        child_count = wallets_and_operations.first_page_objects.fungible_page_objects.get_child_count()

        assert len(child_count) == 4


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Hide exhausted asset for offline wallet')
@allure.story('Toggling on hide exhausted asset for offline wallet')
def test_hide_exhausted_asset_on_offline(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for hiding exhausted asset for offline wallet"""
    with allure.step('Initializing the wallets and funding them'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            SECOND_APPLICATION, variant=wallet_variant_name,
        )
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Navigating to settings page for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.second_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Create PSBT for offline wallet'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(
            SECOND_APPLICATION, ASSET_TICKER, ASSET_NAME, ASSET_AMOUNT,
        )

    with allure.step('Sign psbt for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcasting psbt for offline wallet'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Issue asset for offline wallet'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
    with allure.step('Issue NIA asset for offline wallet'):
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Generating a RGB invoice for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Send asset to the second page for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.create_psbt(
            SECOND_APPLICATION, invoice, ASSET_AMOUNT, wallet_variant_name=wallet_variant_name,
        )

        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_rgb=True,
        )

        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

        child_count = wallets_and_operations.second_page_objects.fungible_page_objects.get_child_count()

        assert len(child_count) == 3


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_multisig
@allure.feature('Hide exhausted asset for offline wallet')
@allure.story('Toggling off hide exhausted asset for offline wallet')
@pytest.mark.parametrize('test_environment', [3], indirect=True)
def test_hide_exhausted_asset_off_offline(wallets_and_operations: WalletTestSetup):
    """Test for hiding exhausted asset for offline wallet"""

    with allure.step('Navigating to settings page for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.second_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Send asset to the second page for offline wallet'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        child_count = wallets_and_operations.second_page_objects.fungible_page_objects.get_child_count()

        assert len(child_count) == 4


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Hide exhausted asset for multisig')
@allure.story('Toggling on hide exhausted asset for multisig')
def test_hide_exhausted_asset_on_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for hiding exhausted asset for multisig"""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='nia')

    with allure.step('Navigating to settings page for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Issue NIA asset for multisig wallet'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME, ASSET_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Generate invoice and send asset for multisig'):
        invoice = initiate_third_wallet_and_get_invoice(
            wallets_and_operations.third_page_features,
            THIRD_APPLICATION,
            ONLINE_CREATE_ON_DEVICE,
        )
        multisig_send_asset_flow_with_verification(
            wallets_and_operations=wallets_and_operations,
            invoice=invoice,
            asset_name=ASSET_NAME,
            asset_ticker=ASSET_TICKER,
            send_amount=ASSET_AMOUNT,
            wallet_variant_name=wallet_variant_name,
            asset_type='nia',
            verify_assertions=False,
        )

        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        child_count = wallets_and_operations.first_page_objects.fungible_page_objects.get_child_count()
        assert len(child_count) == 3


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Hide exhausted asset for multisig')
@allure.story('Toggling off hide exhausted asset for multisig')
def test_hide_exhausted_asset_off_multisig(wallets_and_operations: WalletTestSetup):
    """Test for showing exhausted asset for multisig"""

    with allure.step('Navigating to settings page for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_hide_exhausted_asset_toggle_button()

    with allure.step('Verify asset is visible for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        child_count = wallets_and_operations.first_page_objects.fungible_page_objects.get_child_count()

        assert len(child_count) == 4
