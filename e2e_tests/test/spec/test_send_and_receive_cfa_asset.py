# pylint: disable=redefined-outer-name, unused-import, too-many-statements
"""Iris wallet send and receive operation automation test suite for CFA asset"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.translation_utils import TranslationManager
from src.model.enums.enums_model import TransactionStatusEnumModel

ASSET_NAME = 'CFA'
ASSET_DESCRIPTION = 'This is CFA asset'
ASSET_AMOUNT = '2000'
SEND_AMOUNT = '50'
INVOICE = 'rgb:~/~/utxob:2msKeFq-uPjwpYxVY-jKS2ymYBq-SqmyP3ovg-AGvth8491-J7seMBm?expiry=1709616110&endpoints=rpc://10.0.2.2:3000/json-rpc'


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of send operation for CFA asset in iris wallet')
@allure.story('Testing send CFA asset with expired invoice')
def test_send_cfa_with_expired_invoice(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with expired invoice"""

    with allure.step('Create and fund first wallet for send and receive CFA'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund second wallet for send and receive CFA'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Issue CFA asset'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_description=ASSET_DESCRIPTION, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Send CFA asset with expired invoice'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
    with allure.step('Send CFA asset with expired invoice'):
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_objects.send_asset_page_objects.enter_asset_invoice(
            INVOICE,
        )
    with allure.step('get the cfa asset invoice validation label'):
        validation_label = wallets_and_operations.first_page_objects.send_asset_page_objects.get_asset_address_validation_label()
        wallets_and_operations.first_page_objects.send_asset_page_objects.click_send_asset_close_button()

    with allure.step('Verify error message for CFA asset'):
        assert validation_label == TranslationManager.translate(
            'invalid_invoice',
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset')
def test_send_and_receive_cfa_asset_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset"""

    with allure.step('Generate invoice'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Send CFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
    with allure.step('Send CFA asset'):
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=invoice,
                amount=SEND_AMOUNT,
                is_hardware_wallet=True, purpose='send_asset',
            )
        else:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT,
            )

    with allure.step('Verify transfer status'):
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        actual_transfer_status = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Verify received amount'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        received_amount = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Verify assertions'):
        assert received_amount == SEND_AMOUNT
        assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of send operation for CFA asset in iris wallet for offline wallet')
@allure.story('Testing send CFA asset with expired invoice for offline wallet')
def test_send_cfa_with_expired_invoice_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send CFA asset with expired invoice for offline wallet"""

    with allure.step('Create and fund first wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet for send and receive CFA (offline wallet)'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Create psbt for CFA asset (offline wallet)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()

        wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_description=ASSET_DESCRIPTION, asset_name=ASSET_NAME, asset_amount=ASSET_AMOUNT,
        )

    with allure.step('Sign PSBT for CFA asset (offline wallet)'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast PSBT for CFA asset (offline wallet)'):
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Issue CFA asset (offline wallet)'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            f"{ASSET_NAME} (Draft)",
        )
        wallets_and_operations.second_page_objects.issue_cfa_page_objects.click_issue_cfa_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Send CFA asset with expired invoice (offline wallet)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_objects.send_asset_page_objects.enter_asset_invoice(
            INVOICE,
        )
    with allure.step('get the asset invoice validation label (offline wallet)'):
        validation_lbl = wallets_and_operations.second_page_objects.send_asset_page_objects.get_asset_address_validation_label()
        wallets_and_operations.second_page_objects.send_asset_page_objects.click_send_asset_close_button()

    with allure.step('Verify error message for CFA asset (offline wallet)'):
        assert validation_lbl == TranslationManager.translate(
            'invalid_invoice',
        )


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet for offline wallet')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset for offline wallet')
def test_send_and_receive_cfa_asset_operation_for_offline_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset for offline wallet"""

    with allure.step('Generate invoice for offline wallet'):
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Send CFA asset for offline wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
    with allure.step('Create cfa psbt for offline wallet'):
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT,
        )
    with allure.step('Sign cfa psbt for offline wallet'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name, is_rgb=True,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify transfer status for offline wallet'):
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        actual_transfer_status = wallets_and_operations.second_page_objects.asset_detail_page_objects.get_transfer_status()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Verify received amount for offline wallet'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME,
        )
        received_amount = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Verify assertions for offline wallet'):
        assert received_amount == SEND_AMOUNT
        assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Automation of receive, send, and transaction status for CFA asset in iris wallet for multisig')
@allure.story('End-to-End testing of receiving, sending, and verifying transaction status for CFA asset for multisig')
def test_send_and_receive_cfa_asset_multisig_operation(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test send and receive operation for CFA asset for multisig"""

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

    with allure.step('Fund first multisig wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            application=FIRST_APPLICATION,
        )

    with allure.step('Refresh second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Issue CFA asset for multisig wallet'):
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME, ASSET_DESCRIPTION, ASSET_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION)
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Generate invoice from a third application'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )
        invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Send CFA asset from multisig (App 1) to App 3'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION)
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME)
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            application=FIRST_APPLICATION, receiver_invoice=invoice, amount=SEND_AMOUNT, wallet_variant_name=wallet_variant_name, utxo_required=True,
        )

    with allure.step('Cosign transfer from second multisig wallet (App 2)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send CFA asset from multisig (App 1) to App 3'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION)
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME)
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name)
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Verify transfer status'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION)
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME)
        actual_transfer_status = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_transfer_status()
        assert actual_transfer_status == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION)
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME)
        received_amount = wallets_and_operations.third_page_objects.asset_detail_page_objects.get_total_balance()
        assert received_amount == SEND_AMOUNT
