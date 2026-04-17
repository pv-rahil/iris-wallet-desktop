# pylint: disable=redefined-outer-name, unused-import, too-many-statements
"""Tests for refresh transfer"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import TestEnvironment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_first_wallet_and_refresh_fungible
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_second_wallet_and_click_fungibles
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_second_wallet_and_refresh_fungible
from e2e_tests.test.utilities.multisig_send_flow_helpers import focus_third_wallet_and_refresh_fungible
from e2e_tests.test.utilities.multisig_send_flow_helpers import generate_multisig_invoice_and_send
from e2e_tests.test.utilities.multisig_send_flow_helpers import issue_nia_multisig_flow
from e2e_tests.test.utilities.psbt_helpers import offline_multisig_send_asset_flow_with_verification
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import fund_and_refresh_offline_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import get_fresh_page_objects
from e2e_tests.test.utilities.wallet_setup_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.wallet_setup_helpers import setup_offline_multisig_hardware_wallets
from src.model.enums.enums_model import TransactionStatusEnumModel

ASSET_TICKER = 'TTK'
ASSET_NAME = 'Tether'
ASSET_AMOUNT = '2000'
SEND_AMOUNT = '50'


@pytest.mark.skip_for_offline_wallet
@pytest.mark.skip_for_multisig
@allure.feature('Test for refresh transfer')
@allure.story('Test for refresh transfer from home refresh and then check the status to success after mine the transaction')
def test_refresh_transfer(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for refresh transfer"""

    with allure.step('Create and fund first wallet for refresh transfer'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund second wallet for refresh transfer'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue NIA asset for refresh transfer'):
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=ASSET_TICKER, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Generate invoice'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Send NIA asset to correct invoice'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )

        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )

    with allure.step('Click on send button'):
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
    with allure.step('Send NIA asset to correct invoice'):
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT, is_hardware_wallet=True, purpose='send_asset',
            )
        else:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT,
            )

    with allure.step('Refresh transfer'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Validate transfer status'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_first_app = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_second_app = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()

        assert actual_transfer_status_first_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
        assert actual_transfer_status_second_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value


@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Test for refresh transfer for offline wallet')
@allure.story('Test for refresh transfer from home refresh and then check the status to success after mine the transaction for offline wallet')
def test_refresh_transfer_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for refresh transfer for offline wallet"""

    with allure.step('Create and fund first wallet for refresh transfer for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet for refresh transfer for offline wallet'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet for refresh transfer for offline wallet'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Issue NIA asset for refresh transfer for offline wallet'):
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_ticker=ASSET_TICKER, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Generate invoice for offline wallet'):
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Send NIA asset to correct invoice for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )

        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )

        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
    with allure.step('Create psbt for offline wallet'):
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT, wallet_variant_name=wallet_variant_name,
        )
    with allure.step('Sign UTXO psbt for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name, is_rgb=True,
        )
    with allure.step('Broadcast UTXO psbt for offline wallet'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
    with allure.step('Send transfer for offline wallet'):
        focus_second_wallet_and_click_fungibles(wallets_and_operations)
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        wallets_and_operations.second_page_features.send_features.send_asset_for_single_sig_offline(
            application=SECOND_APPLICATION,
        )
    with allure.step('Sign transfer psbt for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name, is_rgb=True,
        )
    with allure.step('Broadcast transfer psbt for offline wallet'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Refresh transfer for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Validate transfer status for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_first_app = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_second_app = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()

        assert actual_transfer_status_first_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
        assert actual_transfer_status_second_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Test for refresh transfer for multisig')
@allure.story('Setup and issue NIA asset for multisig')
def test_refresh_transfer_setup_and_issue_nia_for_multisig(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Setup wallets and issue NIA asset for refresh transfer tests"""

    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    fund_and_refresh_multisig_wallets(wallets_and_operations, asset_type='nia')

    with allure.step('Issue NIA asset for multisig wallet'):
        issue_nia_multisig_flow(
            wallets_and_operations, wallet_variant_name, ASSET_TICKER, ASSET_NAME, ASSET_AMOUNT,
        )
        focus_first_wallet_and_refresh_fungible(wallets_and_operations)

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Test for refresh transfer for multisig')
@allure.story('Send NIA asset and validate transfer status for multisig')
def test_refresh_transfer_send_and_validate_for_multisig(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Send NIA asset and validate transfer status for multisig"""

    generate_multisig_invoice_and_send(
        wallets_and_operations,
        ASSET_NAME,
        ASSET_TICKER,
        SEND_AMOUNT,
        wallet_variant_name,
        asset_type='nia',
        verify_assertions=False,
    )

    with allure.step('Refresh transfer for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Validate transfer status for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_first_app = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_third_app = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()

        assert actual_transfer_status_first_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
        assert actual_transfer_status_third_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Test for refresh transfer for offline multisig')
@allure.story('Setup and issue NIA asset for offline multisig')
def test_refresh_transfer_setup_and_issue_nia_for_offline_multisig(test_environment: TestEnvironment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Setup wallets and issue NIA asset for offline multisig refresh transfer tests"""

    setup_offline_multisig_hardware_wallets(
        wallets_and_operations, wallet_variant_name,
    )

    fund_and_refresh_offline_multisig_wallets(
        wallets_and_operations, asset_type='nia',
    )

    with allure.step('Issue NIA asset from watch-only coordinator (App 2)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, ASSET_NAME, ASSET_AMOUNT, wallet_variant_name,
        )

    with allure.step('Sign PSBT from cosigner (App 3)'):
        focus_third_wallet_and_refresh_fungible(wallets_and_operations)
        wallets_and_operations.third_page_features.wallet_features.sign_psbt(
            THIRD_APPLICATION, ONLINE_MULTISIG_ON_DEVICE,
        )

    with allure.step('Sign PSBT from offline signer (App 1) - required for 2-of-2 multisig'):
        focus_first_wallet_and_refresh_fungible(wallets_and_operations)
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            FIRST_APPLICATION, wallet_variant_name,
        )

    with allure.step('Issue NIA asset from draft'):
        focus_second_wallet_and_refresh_fungible(wallets_and_operations)
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(
            SECOND_APPLICATION, ASSET_TICKER, wallet_variant_name,
        )

    test_environment.reset_second_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [4], indirect=True)
@allure.feature('Test for refresh transfer for offline multisig')
@allure.story('Send NIA asset and validate transfer status for offline multisig')
def test_refresh_transfer_send_and_validate_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Send NIA asset and validate transfer status for offline multisig"""
    # Get fresh page objects from environment after reset
    second_page_objects, _, second_page_operations = get_fresh_page_objects(
        wallets_and_operations, app_index=2,
    )

    with allure.step('Generate invoice from receiver (App 4)'):
        invoice = wallets_and_operations.fourth_page_features.receive_features.receive_asset_from_sidebar(
            FOURTH_APPLICATION,
        )

    offline_multisig_send_asset_flow_with_verification(
        invoice=invoice,
        wallets_and_operations=wallets_and_operations,
        asset_ticker=ASSET_TICKER,
        asset_name=ASSET_NAME,
        wallet_variant_name=wallet_variant_name,
        send_amount=SEND_AMOUNT,
        asset_type='nia',
        verify_assertions=False,
    )

    with allure.step('Refresh transfer for offline multisig'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.fourth_page_operations.do_focus_on_application(
            FOURTH_APPLICATION,
        )
        wallets_and_operations.fourth_page_objects.fungible_page_objects.click_refresh_button()
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.fourth_page_operations.do_focus_on_application(
            FOURTH_APPLICATION,
        )
        wallets_and_operations.fourth_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Validate transfer status for offline multisig'):
        second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_second_app = second_page_objects.asset_detail_page_objects.get_transfer_status()
        second_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.fourth_page_operations.do_focus_on_application(
            FOURTH_APPLICATION,
        )
        wallets_and_operations.fourth_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME,
        )
        actual_transfer_status_fourth_app = wallets_and_operations.fourth_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.fourth_page_objects.asset_detail_page_objects.click_close_button()

        assert actual_transfer_status_second_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
        assert actual_transfer_status_fourth_app == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value
