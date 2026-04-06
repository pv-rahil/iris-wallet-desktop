# pylint: disable=redefined-outer-name, unused-import
"""
Tests for view unspent list.
"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets


@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('View unspent list')
@allure.story('Verify outpoint in unspent list')
def test_view_unspent_list(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test view unspent list.
    """

    with allure.step('Create and fund first wallet for view unspent'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('verifies the outpoint'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        wallets_and_operations.first_page_objects.view_unspent_list_page_objects.click_unspent_frame()
        actual_outpoint = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_utxo_outpoint()
        outpoint = wallets_and_operations.first_page_operations.do_get_copied_address()

        assert actual_outpoint == outpoint


@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_multisig
@allure.feature('View unspent list for offline wallet')
@allure.story('Verify outpoint in unspent list for offline wallet')
def test_view_unspent_list_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test view unspent list.
    """

    with allure.step('Create and fund first wallet for view unspent'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=True,
        )

    with allure.step('verifies the outpoint'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_view_unspents_button()
        wallets_and_operations.second_page_objects.view_unspent_list_page_objects.click_unspent_frame()
        actual_outpoint = wallets_and_operations.second_page_objects.view_unspent_list_page_objects.get_unspent_utxo_outpoint()
        outpoint = wallets_and_operations.second_page_operations.do_get_copied_address()

        assert actual_outpoint == outpoint


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('View unspent list for multisig')
@allure.story('Verify outpoint in unspent list for multisig')
def test_view_unspent_list_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test view unspent list for multisig."""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Fund first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Verifies the outpoint for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_view_unspents_button()
        wallets_and_operations.first_page_objects.view_unspent_list_page_objects.click_unspent_frame()
        actual_outpoint = wallets_and_operations.first_page_objects.view_unspent_list_page_objects.get_unspent_utxo_outpoint()
        outpoint = wallets_and_operations.first_page_operations.do_get_copied_address()

        assert actual_outpoint == outpoint
