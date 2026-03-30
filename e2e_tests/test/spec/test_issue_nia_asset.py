# pylint: disable=redefined-outer-name, unused-import
"""
Tests for NIA asset issuance.
"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import MULTISIG_VARIANTS
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.multisig_coordinator import get_multisig_coordinator

ASSET_TICKER = 'TTK'
NIA_ASSET_NAME = 'Tether'
ASSET_AMOUNT = '2000'
ISSUE_NIA_TOASTER_MESSAGE = 'You have insufficient funds'

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue NIA asset without sufficient sats')
@allure.story('Issue NIA asset without sufficient sats which will produce error toaster')
def test_issue_nia_without_sufficient_sats(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance without sufficient sats.
    """

    with allure.step('Create and fund first wallet for issue NIA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Issue NIA asset without sufficient sats'):
        description = wallets_and_operations.first_page_features.issue_nia_features.issue_nia_asset_without_sat(
            FIRST_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT,
        )

    assert description == ISSUE_NIA_TOASTER_MESSAGE

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue NIA asset with sufficient sats and no utxo')
@allure.story('Issue NIA asset with sufficient sats which will create utxo and create asset')
def test_issue_nia_with_sufficient_sats_and_no_utxo(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance with sufficient sats and no utxo.
    """

    with allure.step('Fund wallet for issue NIA asset'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Verifies there is no utxo for issue NIA asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 1

    with allure.step('Issue NIA asset with sufficient sats and no utxo'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo(
            FIRST_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT, wallet_variant_name,
        )

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.first_page_objects.fungible_page_objects.get_nia_asset_name(
            NIA_ASSET_NAME,
        )
        assert asset_name == NIA_ASSET_NAME

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Issue NIA asset with sufficient sats')
@allure.story('Issue NIA asset with sufficient sats which will create asset')
def test_issue_nia_with_sufficient_sats_and_utxo(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance with sufficient sats and utxo.
    """

    with allure.step('Verified that one utxo exists for issue NIA asset'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        nia_asset_id = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_utxo_asset_id(
            'NA',
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 3
        assert nia_asset_id == 'NA'

    with allure.step('Issue NIA asset with sufficient sats and utxo'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.first_page_objects.fungible_page_objects.get_nia_asset_name(
            NIA_ASSET_NAME,
        )
        assert asset_name == NIA_ASSET_NAME


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue NIA asset without sufficient sats for offline wallet')
@allure.story('Issue NIA asset without sufficient sats which will produce error toaster for offline wallet')
def test_issue_nia_without_sufficient_sats_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance without sufficient sats for offline wallet.
    """
    with allure.step('Create first wallet for issue NIA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create second wallet for issue NIA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Issue NIA asset without sufficient sats'):
        description = wallets_and_operations.second_page_features.issue_nia_features.issue_nia_asset_without_sat(
            SECOND_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT,
        )

    assert description == ISSUE_NIA_TOASTER_MESSAGE

@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Issue NIA asset with sufficient sats and no utxo for offline wallet')
@allure.story('Issue NIA asset with sufficient sats which will create utxo and create asset for offline wallet')
def test_issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance with sufficient sats and no utxo for offline wallet.
    """

    with allure.step('Fund wallet for issue NIA asset'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    with allure.step('Verifies there is no utxo for issue NIA asset'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_view_unspents_button()
        count = wallets_and_operations.second_page_objects.view_unspent_list_page_objects.get_unspent_widget()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        assert count == 1

    with allure.step('Create a psbt for issue asset'):
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_watch_only_wallet(
            SECOND_APPLICATION, ASSET_TICKER,
        )

    with allure.step('Sign the nia psbt'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Broadcast the nia psbt'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            SECOND_APPLICATION,
        )

    with allure.step('Issuing NIA asset'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Verify asset name'):
        asset_name = wallets_and_operations.second_page_objects.fungible_page_objects.get_nia_asset_name(
            NIA_ASSET_NAME,
        )
        assert asset_name == NIA_ASSET_NAME


@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue NIA asset for multisig wallet')
@allure.story('Issue NIA asset with multisig wallet requiring two applications')
def test_issue_nia_multisig_without_sufficient_sats(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance without sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    coordinator = get_multisig_coordinator()
    coordinator.reset()

    with allure.step('Initiate first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Initiate second multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Import cosigner data into first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.import_multisig_data(
            application=FIRST_APPLICATION,
        )

    with allure.step('Import cosigner data into second multisig wallet'):
        wallets_and_operations.second_page_features.wallet_features.import_multisig_data(
            application=SECOND_APPLICATION,
        )

    with allure.step('Finalize first multisig wallet setup'):
        wallets_and_operations.first_page_features.wallet_features.finalize_multisig_setup(
            application=FIRST_APPLICATION,
        )

    with allure.step('Finalize second multisig wallet setup'):
        wallets_and_operations.second_page_features.wallet_features.finalize_multisig_setup(
            application=SECOND_APPLICATION,
        )

    with allure.step('Issue NIA asset without sufficient sats'):
        description = wallets_and_operations.first_page_features.issue_nia_features.issue_nia_asset_without_sat(
            FIRST_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT,
        )

    assert description == ISSUE_NIA_TOASTER_MESSAGE


@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('Issue NIA asset for multisig wallet')
@allure.story('Issue NIA asset with sufficient sats for multisig wallet')
def test_issue_nia_multisig_with_sufficient_sats(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test NIA asset issuance with sufficient sats for multisig wallet.
    Multisig requires two applications running in parallel.
    """
    with allure.step('fund first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            application=FIRST_APPLICATION,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Create Utxo for issue NIA asset'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, utxo_required=True,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Sign and broadcast from second wallet'):
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('refresh first multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(FIRST_APPLICATION)
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Issue NIA asset with sufficient sats and utxo from draft'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER,
        )

    with allure.step('refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Verify asset name'):
        wallets_and_operations.first_page_operations.do_focus_on_application(FIRST_APPLICATION)
        asset_name = wallets_and_operations.first_page_objects.fungible_page_objects.get_nia_asset_name(
            NIA_ASSET_NAME,
        )
        assert asset_name == NIA_ASSET_NAME
