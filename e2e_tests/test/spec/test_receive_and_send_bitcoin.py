# pylint: disable=redefined-outer-name, unused-import, unused-argument
"""Iris wallet send and receive operation automation test suite for bitcoin.
Test suite for iris wallet's send and receive operations with bitcoin."""
from __future__ import annotations

import re

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.translation_utils import TranslationManager
from src.utils.info_message import INFO_BITCOIN_SENT

AMOUNT = '50000000'
FEE_RATE = '8'
INVOICE = 'rgb:~/~/utxob:2msKeFq-uPjwpYxVY-jKS2ymYBq-SqmyP3ovg-AGvth8491-J7seMBm?expiry=1709616110&endpoints=rpc://10.0.2.2:3000/json-rpc'


@pytest.mark.skip_for_offline_wallet
@allure.feature('Iris wallet send operation with zero balance')
@allure.story('Wallet send operation with zero balance which will give error label')
def test_send_bitcoin_with_zero_balance(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """Test sending bitcoin with zero balance."""

    with allure.step('Create and fund first wallet for send and receive bitcoin'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Get bitcoin address'):
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.first_page_features.receive_features.receive(
            application=FIRST_APPLICATION,
        )

    with allure.step('Verify address'):
        assert copied_address == address

    with allure.step('Send bitcoin with zero balance'):
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        validation = wallets_and_operations.first_page_features.send_features.send_with_no_fund(
            application=FIRST_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT,
        )

    with allure.step('Verify error message'):
        assert validation == TranslationManager.translate(
            'asset_amount_validation',
        )

    with allure.step('Close bitcoin detail page'):
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()


@pytest.mark.skip_for_offline_wallet
@allure.feature('Iris wallet receive and send operation automation for bitcoin')
@allure.story('Wallet receive and send operation automation for bitcoin')
def test_receive_and_send_bitcoin(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test receiving and sending bitcoin."""

    with allure.step('Fund first wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Create and fund second wallet for send and receive bitcoin'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Get bitcoin address'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.second_page_features.receive_features.receive(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify address'):
        assert copied_address == address

    with allure.step('Send bitcoin'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT, is_hardware_wallet=True, purpose='send_btc',
            )
        else:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT,
            )
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()
    with allure.step('Refresh bitcoin page'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()

    with allure.step('Verify received balance'):
        received_balance = wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.get_total_balance()
        received_balance = received_balance.replace(' SATS', '')
        assert received_balance == AMOUNT

    with allure.step('Close bitcoin detail page'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()


@pytest.mark.skip_for_offline_wallet
@allure.feature('Iris wallet send operation with custom fee rate')
@allure.story('Wallet send operation with custom fee rate')
def test_send_bitcoin_with_custom_fee_rate(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test sending bitcoin with a custom fee rate."""

    with allure.step('Fund first wallet'):
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            FIRST_APPLICATION,
        )

    with allure.step('Get bitcoin address'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.second_page_features.receive_features.receive(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify address'):
        assert copied_address == address

    with allure.step('Send bitcoin with custom fee rate'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            description = wallets_and_operations.first_page_features.send_features.send_with_custom_fee_rate(
                application=FIRST_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT, fee_rate=FEE_RATE, is_hardware_wallet=True,
            )
        else:
            description = wallets_and_operations.first_page_features.send_features.send_with_custom_fee_rate(
                application=FIRST_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT, fee_rate=FEE_RATE,
            )

    with allure.step('Refresh bitcoin page'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        tx_id = wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()

    with allure.step('Verify transaction id'):
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert description == INFO_BITCOIN_SENT.format(tx_id)

    with allure.step('Close transaction detail page'):
        wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()

    with allure.step('Close bitcoin detail page'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('Close bitcoin detail page in first application'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()


@pytest.mark.skip_for_offline_wallet
@allure.feature('Iris wallet send operation with invalid invoice')
@allure.story('Wallet send operation with invalid invoice')
def test_send_bitcoin_with_invalid_invoice(wallets_and_operations: WalletTestSetup, load_qm_translation):
    """Test sending bitcoin with an invalid invoice."""
    validation_label = None
    with allure.step('Get asset from sidebar'):
        invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Send bitcoin with invalid invoice'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_objects.send_asset_page_objects.enter_asset_invoice(
            invoice,
        )
        validation_label = wallets_and_operations.first_page_objects.send_asset_page_objects.get_asset_address_validation_label()

    with allure.step('Verify error message'):
        assert validation_label == TranslationManager.translate(
            'invalid_address',
        )


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Iris wallet send operation with zero balance for offline')
@allure.story('Wallet send operation with zero balance for offline')
def test_send_bitcoin_with_zero_balance_for_offline(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """Test sending bitcoin with zero balance for offline."""

    with allure.step('Create and fund first wallet for send and receive bitcoin'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Get bitcoin address'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.second_page_features.receive_features.receive(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify address'):
        assert copied_address == address

    with allure.step('Send bitcoin with zero balance'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        validation = wallets_and_operations.second_page_features.send_features.send_with_no_fund(
            application=SECOND_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT,
        )

    with allure.step('Verify error message'):
        assert validation == TranslationManager.translate(
            'asset_amount_validation',
        )

    with allure.step('Close bitcoin detail page'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Iris wallet receive and send operation automation for bitcoin offline')
@allure.story('Wallet receive and send operation automation for bitcoin offline')
def test_receive_and_send_bitcoin_for_offline(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test receiving and sending bitcoin for offline."""

    with allure.step('Fund second wallet'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    with allure.step('Get bitcoin address'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.second_page_features.receive_features.receive(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify address'):
        assert copied_address == address

    with allure.step('Send bitcoin'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT,
        )
    with allure.step('sign psbt for send_btc'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )
    with allure.step('Broadcast psbt for send_btc'):
        description = wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
    with allure.step('Refresh bitcoin page'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        tx_id = wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()

    with allure.step('Verify transaction id'):
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert description == INFO_BITCOIN_SENT.format(tx_id)

    with allure.step('Close transaction detail page'):
        wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()

    with allure.step('Close bitcoin detail page'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Iris wallet send operation with custom fee rate for offline')
@allure.story('Wallet send operation with custom fee rate for offline')
def test_send_bitcoin_with_custom_fee_rate_for_offline(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test sending bitcoin with a custom fee rate for offline."""
    with allure.step('Fund second wallet'):
        wallets_and_operations.second_page_features.wallet_features.fund_wallet(
            SECOND_APPLICATION,
        )

    with allure.step('Get bitcoin address for custom fee rate'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, copied_address = wallets_and_operations.second_page_features.receive_features.receive(
            application=SECOND_APPLICATION,
        )

    with allure.step('Verify address for custom fee rate'):
        assert copied_address == address

    with allure.step('Send bitcoin with custom fee rate'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=copied_address, amount=AMOUNT, fee_rate=FEE_RATE,
        )

    with allure.step('Sign psbt for send_btc with custom fee rate'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Broadcast psbt for send_btc with custom fee rate'):
        description = wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )

    with allure.step('Refresh bitcoin page for custom fee rate'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        tx_id = wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()

    with allure.step('Close transaction detail page for custom fee rate'):
        wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()

    with allure.step('Close bitcoin detail page for custom fee rate'):
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('Verify transaction id for custom fee rate'):
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert description == INFO_BITCOIN_SENT.format(tx_id)


@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_online_wallet
@allure.feature('Iris wallet send operation with invalid invoice for offline')
@allure.story('Wallet send operation with invalid invoice for offline')
def test_send_bitcoin_with_invalid_invoice_for_offline(wallets_and_operations: WalletTestSetup, load_qm_translation):
    """Test sending bitcoin with an invalid invoice for offline."""
    validation_label = None
    with allure.step('Send bitcoin with invalid invoice'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.second_page_objects.send_asset_page_objects.enter_asset_invoice(
            INVOICE,
        )
        validation_label = wallets_and_operations.second_page_objects.send_asset_page_objects.get_asset_address_validation_label()

    with allure.step('Verify error message'):
        assert validation_label == TranslationManager.translate(
            'invalid_address',
        )
