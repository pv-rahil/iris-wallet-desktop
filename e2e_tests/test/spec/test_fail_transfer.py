# pylint: disable=redefined-outer-name, unused-import
"""E2E test for fail transfer"""
from __future__ import annotations

import time

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import RGB_LEDGER_APP_NAME
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet
from src.utils.info_message import INFO_FAIL_TRANSFER_SUCCESSFULLY


ASSET_TICKER = 'TTK'
NIA_ASSET_NAME = 'Tether'
ASSET_AMOUNT = '2000'

pytestmark = pytest.mark.skip_for_multisig


@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('Fail transfer feature')
@allure.story('Test for fail transfer')
def test_fail_transfer(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for fail transfer"""
    hardware_wallet = None

    with allure.step('Creating and funding the wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issuing an RGB asset'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Generating an invoice'):
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            asset_name=NIA_ASSET_NAME,
        )
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            hardware_wallet = handle_hardware_wallet(
                app_name=RGB_LEDGER_APP_NAME,
            )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_receive_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            time.sleep(2)
            wallets_and_operations.first_page_operations.do_focus_on_application(
                LEDGER_EMULATOR_APP_NAME,
            )
            for _ in range(2):
                wallets_and_operations.first_page_objects.hw_emulator_page_objects.click_right_arrow_key(
                    4,
                )
                wallets_and_operations.first_page_objects.hw_emulator_page_objects.press_left_and_right()
            wallets_and_operations.first_page_objects.hw_emulator_page_objects.click_right_arrow_key(
                1,
            )
            wallets_and_operations.first_page_objects.hw_emulator_page_objects.press_left_and_right()
            time.sleep(2)
        wallets_and_operations.first_page_objects.receive_asset_page_objects.click_receive_asset_close_button()

    with allure.step('Failing the transfer'):
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            asset_name=NIA_ASSET_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_fail_transfer_button()
        wallets_and_operations.first_page_objects.confirmation_dialog_page_objects.click_confirmation_continue_button()

    _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    assert toaster_description == INFO_FAIL_TRANSFER_SUCCESSFULLY
    if hardware_wallet:
        hardware_wallet.terminate()


@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@allure.feature('Fail transfer feature for offline wallet')
@allure.story('Test for fail transfer for offline wallet')
def test_fail_transfer_for_offline(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for fail transfer for offline wallet"""

    with allure.step('Creating and funding the wallet for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )
    with allure.step('Issuing an RGB asset for offline wallet'):
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(
            SECOND_APPLICATION, ASSET_TICKER, NIA_ASSET_NAME, ASSET_AMOUNT,
        )
    with allure.step('Sign and broadcast the PSBT'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
    with allure.step('Click on fungibles button'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
    with allure.step('Click on issue nia button'):
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Generating an invoice for offline wallet'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            asset_name=NIA_ASSET_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_receive_button()
        wallets_and_operations.second_page_objects.receive_asset_page_objects.click_receive_asset_close_button()

    with allure.step('Failing the transfer for offline wallet'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            asset_name=NIA_ASSET_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_fail_transfer_button()
        wallets_and_operations.second_page_objects.confirmation_dialog_page_objects.click_confirmation_continue_button()

    _, toaster_description = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()

    assert toaster_description == INFO_FAIL_TRANSFER_SUCCESSFULLY
