# pylint: disable=redefined-outer-name, unused-import
"""
Tests for issuing CFA assets with different scenarios.
"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.multisig_coordinator import get_multisig_coordinator
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.test_helpers import multisig_issue_asset_flow
from e2e_tests.test.utilities.test_helpers import refresh_second_wallet_and_verify_asset
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets

CFA_ASSET_NAME = 'CFA'
ASSET_DESCRIPTION = 'This is CFA asset'
ASSET_AMOUNT = '2000'
ISSUE_CFA_TOASTER_MESSAGE = 'You have insufficient funds'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue CFA asset without sufficient sats')
@allure.story('Issue CFA asset without sufficient sats which will produce error toaster')
def test_issue_cfa_without_sufficient_sats(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test issuing CFA asset without sufficient sats.
    """

    with allure.step('Create and fund first wallet for issue CFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Issue CFA asset without sat'):
        description = wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_asset_without_sat(
            FIRST_APPLICATION, CFA_ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT,
        )

    with allure.step('Verify toaster title and message'):
        assert description == ISSUE_CFA_TOASTER_MESSAGE


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue CFA asset with sufficient sats but no utxo')
@allure.story('Issue CFA asset with sufficient sats and no utxo which will first create utxo and then create asset')
def test_issue_cfa_with_sufficient_sats_and_no_utxo(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test issuing CFA asset with sufficient sats but no utxo.
    """

    with allure.step('Fund wallet for issue CFA asset'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Verifies there is no utxo for issue CFA asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 1

    with allure.step('Issue CFA with sufficient sats and no utxo'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo(
            FIRST_APPLICATION, CFA_ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT, wallet_variant_name,
        )

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.first_page_objects.collectible_page_objects.get_cfa_asset_name(
            CFA_ASSET_NAME,
        )
        assert asset_name == CFA_ASSET_NAME


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue CFA asset with sufficient sats and utxo')
@allure.story('Issue CFA asset with sufficient sats and utxo which will create asset')
def test_issue_cfa_with_sufficient_sats_and_utxo(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test issuing CFA asset with sufficient sats and utxo.
    """

    with allure.step('Verified that one utxo exists for issue CFA asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()

        count = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_widget()

        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()

        assert count == 2

    with allure.step('Issue CFA with sufficient sats and utxo'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, CFA_ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.first_page_objects.collectible_page_objects.get_cfa_asset_name(
            CFA_ASSET_NAME,
        )
        assert asset_name == CFA_ASSET_NAME


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue CFA asset without sufficient sats for offline wallet')
@allure.story('Issue CFA asset without sufficient sats which will produce error toaster for offline wallet')
def test_issue_cfa_without_sufficient_sats_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test CFA asset issuance without sufficient sats for offline wallet.
    """
    with allure.step('Create first wallet for issue CFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create second wallet for issue CFA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Issue CFA asset without sufficient sats'):
        description = wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_asset_without_sat(
            SECOND_APPLICATION, CFA_ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT,
        )

    assert description == ISSUE_CFA_TOASTER_MESSAGE


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue CFA asset with sufficient sats and no utxo for offline wallet')
@allure.story('Issue CFA asset with sufficient sats which will create utxo and create asset for offline wallet')
def test_issue_cfa_with_sufficient_sats_and_no_utxo_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test CFA asset issuance with sufficient sats and no utxo for offline wallet.
    """

    with allure.step('Fund wallet for issue CFA asset'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    with allure.step('Verifies there is no utxo for issue CFA asset'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.second_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Create a psbt for issue asset'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_watch_only_wallet(
            SECOND_APPLICATION, CFA_ASSET_NAME,
        )

    with allure.step('Sign the cfa psbt'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast the cfa psbt'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Issuing CFA asset'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            f'{CFA_ASSET_NAME} (Draft)',
        )
        wallets_and_operations.second_page_objects.issue_cfa_page_objects.click_issue_cfa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.second_page_objects.collectible_page_objects.get_cfa_asset_name(
            CFA_ASSET_NAME,
        )
    assert count == 1
    assert asset_name == CFA_ASSET_NAME


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue CFA asset for multisig wallet')
@allure.story('Issue CFA asset with multisig wallet requiring two applications')
def test_issue_cfa_multisig_without_sufficient_sats_for_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test CFA asset issuance without sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    coordinator = get_multisig_coordinator()
    coordinator.reset()

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Issue CFA asset without sufficient sats'):
        description = wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_asset_without_sat(
            FIRST_APPLICATION, CFA_ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT,
        )

    assert description == ISSUE_CFA_TOASTER_MESSAGE


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue CFA asset for multisig wallet')
@allure.story('Issue CFA asset with sufficient sats for multisig wallet')
def test_issue_cfa_multisig_with_sufficient_sats_for_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test CFA asset issuance with sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='nia')

    multisig_issue_asset_flow(
        wallets_and_operations,
        wallet_variant_name,
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet,
        CFA_ASSET_NAME,
        utxo_required=True,
    )

    refresh_second_wallet_and_verify_asset(
        wallets_and_operations, CFA_ASSET_NAME, asset_type='cfa',
    )
