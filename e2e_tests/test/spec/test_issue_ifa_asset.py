# pylint: disable=redefined-outer-name, unused-import
"""
Tests for IFA asset issuance.
"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.multisig_coordinator import get_multisig_coordinator
from e2e_tests.test.utilities.psbt_helpers import focus_and_refresh_asset_list
from e2e_tests.test.utilities.psbt_helpers import focus_refresh_and_sign_psbt
from e2e_tests.test.utilities.send_flow_helpers import multisig_issue_asset_flow
from e2e_tests.test.utilities.send_flow_helpers import offline_multisig_issue_asset_test_flow
from e2e_tests.test.utilities.send_flow_helpers import refresh_second_wallet_and_verify_asset
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_offline_multisig_three_app_wallets
from src.utils.error_message import ERROR_INSUFFICIENT_FUNDS

ASSET_TICKER = 'IFK'
IFA_ASSET_NAME = 'Inflatable'
ASSET_AMOUNT = '2000'
IFA_ASSET_TOTAL_SUPPLY = '10000'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue IFA asset without sufficient sats')
@allure.story('Issue IFA asset without sufficient sats which will produce error toaster')
def test_issue_ifa_without_sufficient_sats(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance without sufficient sats.
    """

    with allure.step('Create and fund first wallet for issue IFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Issue IFA asset without sufficient sats'):
        description = wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_asset_without_sat(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY,
        )

    assert description == ERROR_INSUFFICIENT_FUNDS


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue IFA asset with sufficient sats and no utxo')
@allure.story('Issue IFA asset with sufficient sats and no utxo which will create utxos and then create asset')
def test_issue_ifa_with_sufficient_sats_and_no_utxo(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance with sufficient sats and no utxo.
    """

    with allure.step('Fund wallet for issue IFA asset'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Verifies there is no utxo for issue IFA asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 1

    with allure.step('Issue IFA asset with sufficient sats and no utxo'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY, wallet_variant_name,
        )

    with allure.step('Verify asset name on inflatables page'):
        asset_name = wallets_and_operations.first_page_objects.inflatable_page_objects.get_ifa_asset_name(
            IFA_ASSET_NAME,
        )
        assert asset_name == IFA_ASSET_NAME


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue IFA asset without sufficient sats for offline wallet')
@allure.story('Issue IFA asset without sufficient sats which will produce error toaster for offline wallet')
def test_issue_ifa_without_sufficient_sats_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance without sufficient sats for offline/watch-only.
    """

    with allure.step('Create first wallet (offline/watch-only) for IFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create second wallet (offline/watch-only) for IFA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Attempt to issue IFA asset without sufficient sats'):
        description = wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_asset_without_sat(
            SECOND_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY,
        )

    assert description == ERROR_INSUFFICIENT_FUNDS


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue IFA asset with sufficient sats and no utxo for offline wallet')
@allure.story('Create PSBT for IFA issuance, sign and broadcast, then finalize issuance (offline/watch-only)')
def test_issue_ifa_with_sufficient_sats_and_no_utxo_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA issuance via PSBT flow in offline/watch-only mode.
    """

    with allure.step('Fund wallet for IFA issuance (offline/watch-only)'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    with allure.step('Verify there is no UTXO for IFA issuance'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.second_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 1

    with allure.step('Create an unsigned PSBT for IFA issuance from draft'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_watch_only_wallet(
            SECOND_APPLICATION, IFA_ASSET_NAME,
        )

    with allure.step('Sign the IFA PSBT'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name, is_issue_ifa=True,
        )

    with allure.step('Broadcast the IFA PSBT'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Finalize IFA issuance from draft after broadcast'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f'{IFA_ASSET_NAME} (Draft)',
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Verify asset name on inflatables page (offline/watch-only)'):
        asset_name = wallets_and_operations.second_page_objects.inflatable_page_objects.get_ifa_asset_name(
            IFA_ASSET_NAME,
        )

    assert asset_name == IFA_ASSET_NAME


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue IFA asset for multisig wallet')
@allure.story('Issue IFA asset with multisig wallet requiring two applications')
def test_issue_ifa_multisig_without_sufficient_sats_for_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance without sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    coordinator = get_multisig_coordinator()
    coordinator.reset()

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Issue IFA asset without sufficient sats'):
        description = wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_asset_without_sat(
            FIRST_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY,
        )

    assert description == ERROR_INSUFFICIENT_FUNDS


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue IFA asset for multisig wallet')
@allure.story('Issue IFA asset with sufficient sats for multisig wallet')
def test_issue_ifa_multisig_with_sufficient_sats_for_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance with sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    with allure.step('fund first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            application=FIRST_APPLICATION,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Create Utxo for issue IFA asset'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, wallet_variant_name, utxo_required=True,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Sign and broadcast from second wallet'):
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name, is_issue_ifa=True,
        )

    with allure.step('refresh first multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Issue IFA asset with sufficient sats and utxo from draft'):
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, wallet_variant_name,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Verify asset name'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        asset_name = wallets_and_operations.first_page_objects.inflatable_page_objects.get_ifa_asset_name(
            IFA_ASSET_NAME,
        )
        assert asset_name == IFA_ASSET_NAME


# ==============================================================================
# Offline Multisig Tests (3 apps - issue flow without send)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Issue IFA asset for offline multisig')
@allure.story('Issue IFA asset without sufficient sats for offline multisig wallet')
def test_issue_ifa_without_sufficient_sats_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance without sufficient sats for offline multisig wallet (3 apps).
    """
    setup_offline_multisig_three_app_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    with allure.step('Issue IFA asset without sufficient sats'):
        description = wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_asset_without_sat(
            SECOND_APPLICATION, ASSET_TICKER, IFA_ASSET_NAME, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY,
        )

    assert description == ERROR_INSUFFICIENT_FUNDS


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Issue IFA asset for offline multisig')
@allure.story('Issue IFA asset with sufficient sats for offline multisig wallet')
def test_issue_ifa_with_sufficient_sats_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test IFA asset issuance with sufficient sats for offline multisig wallet (3 apps).
    """
    offline_multisig_issue_asset_test_flow(
        wallets_and_operations,
        wallet_variant_name,
        wallets_and_operations.second_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet,
        ASSET_TICKER,
        asset_type='ifa',
        is_issue_ifa=True,
    )

    # Refresh second wallet and issue from draft
    with allure.step('Refresh second wallet and issue IFA from draft'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            f'{IFA_ASSET_NAME} (Draft)',
        )
        wallets_and_operations.second_page_objects.issue_ifa_page_objects.click_issue_ifa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    # Verify asset
    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.second_page_objects.inflatable_page_objects.get_ifa_asset_name(
            IFA_ASSET_NAME,
        )
        assert asset_name == IFA_ASSET_NAME
