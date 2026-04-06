# pylint: disable=redefined-outer-name, unused-import, too-many-lines
"""Test module for hiding exhausted asset"""
from __future__ import annotations

import re

import allure
import keyring as kr
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import FIRST_SERVICE
from accessible_constant import NATIVE_AUTH_ENABLE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import refresh_collectibles_on_app2
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets
from src.data.repository.setting_repository import SettingRepository
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_BITCOIN_SENT

ASSET_TICKER = 'TTK'
ASSET_NAME_1 = 'Tether'
ASSET_AMOUNT = '2000'
ASSET_DESCRIPTION = 'CFA asset'
ASSET_NAME_2 = 'Test asset'
IFA_ASSET_TICKER = 'IFK'
IFA_ASSET_NAME_1 = 'Inflatable1'
IFA_ASSET_NAME_2 = 'Inflatable2'
IFA_ASSET_TOTAL_SUPPLY = '10000'
SEND_AMOUNT = '200'

pytestmark = [
    pytest.mark.skip_for_hardware_wallet,
    pytest.mark.skip_for_offline_wallet,
]


@pytest.mark.skip_for_multisig
@allure.feature('Ask authorization for important operations')
@allure.story('Toggling on ask authorization for import operations')
def test_ask_auth_for_imp_question_send_bitcoin_on(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for hiding exhausted asset"""
    with allure.step('Initializing the wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            FIRST_APPLICATION, variant=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Turning on ask authorization for import operations'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()

        is_on_or_not = kr.get_password(FIRST_SERVICE, NATIVE_AUTH_ENABLE)
        native_status_casted: bool = SettingRepository.str_to_bool(
            is_on_or_not,
        )

        if native_status_casted is not True:
            wallets_and_operations.first_page_objects.settings_page_objects.click_ask_auth_imp_question()
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Getting the receiver\'s address'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, _ = wallets_and_operations.second_page_features.receive_features.receive(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the bitcoin'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, address, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('asserting tx id'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        bitcoin_tx_id = wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()
        wallets_and_operations.second_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()
        bitcoin_tx_id = re.sub(
            r'[\u200B\u200C\u200D\u2060\uFEFF]', '', bitcoin_tx_id,
        )
        assert toaster_description == INFO_BITCOIN_SENT.format(bitcoin_tx_id)


@pytest.mark.skip_for_multisig
@allure.story('Issuing and sending the RGB assets')
def test_ask_auth_for_imp_question_issue_nia_on(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing NIA asset with ask auth for important operations on"""
    with allure.step('Issuing NIA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME_1, ASSET_AMOUNT, is_native_auth_enabled=True, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending NIA asset')
def test_ask_auth_for_imp_question_send_nia_on(wallets_and_operations: WalletTestSetup):
    """Sending NIA asset with ask auth for important operations on"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        nia_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the NIA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_AMOUNT,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, nia_invoice, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
    with allure.step('asserting tx id'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.skip_for_multisig
@allure.story('Issuing CFA asset')
def test_ask_auth_for_imp_question_issue_cfa_on(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing CFA asset with ask auth for important operations on"""
    with allure.step('Issuing CFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_NAME_1, ASSET_DESCRIPTION, ASSET_AMOUNT, is_native_auth=True, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending CFA asset')
def test_ask_auth_for_imp_question_send_cfa_on(wallets_and_operations: WalletTestSetup):
    """Sending CFA asset with ask auth for important operations on"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        cfa_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the CFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, cfa_invoice, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
    with allure.step('asserting tx id'):
        refresh_collectibles_on_app2(wallets_and_operations)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.skip_for_multisig
@allure.story('Issuing IFA asset')
def test_ask_auth_for_imp_question_issue_ifa_on(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing IFA asset with ask auth for important operations on"""
    with allure.step('Issuing IFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, IFA_ASSET_TICKER, IFA_ASSET_NAME_1, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY, is_native_auth_enabled=True, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending IFA asset')
def test_ask_auth_for_imp_question_send_ifa_on(wallets_and_operations: WalletTestSetup):
    """Sending IFA asset with ask auth for important operations on"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        ifa_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the IFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, ifa_invoice, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
    with allure.step('asserting tx id'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.skip_for_multisig
@allure.feature('Ask authorization for important operations')
@allure.story('Toggling off ask authorization for import operations')
def test_ask_auth_for_imp_question_send_bitcoin_off(wallets_and_operations: WalletTestSetup):
    """test native auth for important operations (send btc) off"""
    with allure.step('Toggling off native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()

        is_on_or_not_1 = kr.get_password(FIRST_SERVICE, NATIVE_AUTH_ENABLE)
        native_status_casted: bool = SettingRepository.str_to_bool(
            is_on_or_not_1,
        )

        if native_status_casted is True:
            wallets_and_operations.first_page_objects.settings_page_objects.click_ask_auth_imp_question()
            wallets_and_operations.first_page_operations.enter_native_password()

    with allure.step('getting address'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, _ = wallets_and_operations.second_page_features.receive_features.receive(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('Sending bitcoin'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, address, ASSET_AMOUNT,
        )
        _, toaster_title = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

        assert toaster_title == 'Success'


@pytest.mark.skip_for_multisig
@allure.story('Issuing NIA asset')
def test_ask_auth_for_imp_question_issue_nia_off(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing NIA asset with ask auth for important operations off"""
    with allure.step('Issuing NIA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME_2, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending NIA asset')
def test_ask_auth_for_imp_question_send_nia_off(wallets_and_operations: WalletTestSetup):
    """Sending NIA asset with ask auth for important operations off"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        nia_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the NIA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, nia_invoice, ASSET_AMOUNT,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
    with allure.step('asserting tx id'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.skip_for_multisig
@allure.story('Issuing CFA asset')
def test_ask_auth_for_imp_question_issue_cfa_off(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing NIA asset with ask auth for important operations off"""
    with allure.step('Issuing CFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, ASSET_NAME_2, ASSET_DESCRIPTION, ASSET_AMOUNT, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending CFA asset')
def test_ask_auth_for_imp_question_send_cfa_off(wallets_and_operations: WalletTestSetup):
    """Sending CFA asset with ask auth for important operations off"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        cfa_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the CFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, cfa_invoice, ASSET_AMOUNT,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
    with allure.step('asserting tx id'):
        refresh_collectibles_on_app2(wallets_and_operations)
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.skip_for_multisig
@allure.story('Issuing IFA asset')
def test_ask_auth_for_imp_question_issue_ifa_off(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing IFA asset with ask auth for important operations off"""
    with allure.step('Issuing IFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_utxo(
            FIRST_APPLICATION, IFA_ASSET_TICKER, IFA_ASSET_NAME_2, ASSET_AMOUNT, IFA_ASSET_TOTAL_SUPPLY, variant_name=wallet_variant_name,
        )


@pytest.mark.skip_for_multisig
@allure.story('Sending IFA asset')
def test_ask_auth_for_imp_question_send_ifa_off(wallets_and_operations: WalletTestSetup):
    """Sending IFA asset with ask auth for important operations off"""
    with allure.step('Getting an RGB invoice'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        ifa_invoice = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Sending the IFA asset'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_2,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.send(
            FIRST_APPLICATION, ifa_invoice, ASSET_AMOUNT,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
    with allure.step('asserting tx id'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_2,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.second_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


# ============== MULTISIG ASK AUTH FOR IMPORTANT OPERATIONS TESTS ==============

@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Ask authorization for important operations for multisig')
@allure.story('Toggling on ask authorization for import operations for multisig')
def test_ask_auth_for_imp_question_send_bitcoin_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for ask auth for important operations send bitcoin for multisig"""
    with allure.step('Setup multisig wallets'):
        setup_multisig_wallets(wallets_and_operations, wallet_variant_name)
        wallets_and_operations.first_page_features.wallet_features.fund_wallet(
            application=FIRST_APPLICATION,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

    with allure.step('Create third wallet for receiving'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Turning on ask authorization for import operations for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()

        is_on_or_not = kr.get_password(FIRST_SERVICE, NATIVE_AUTH_ENABLE)
        native_status_casted: bool = SettingRepository.str_to_bool(
            is_on_or_not,
        )

        if native_status_casted is not True:
            wallets_and_operations.first_page_objects.settings_page_objects.click_ask_auth_imp_question()
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()

    with allure.step('Getting the receiver\'s address for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, _ = wallets_and_operations.third_page_features.receive_features.receive(
            THIRD_APPLICATION,
        )

    with allure.step('Create PSBT for multisig bitcoin send with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_features.send_features.create_psbt(
            FIRST_APPLICATION, address, ASSET_AMOUNT, is_native_auth_enabled=True,
        )

    with allure.step('Sign PSBT from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('asserting tx id for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        bitcoin_tx_id = wallets_and_operations.third_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()
        wallets_and_operations.third_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()
        bitcoin_tx_id = re.sub(
            r'[\u200B\u200C\u200D\u2060\uFEFF]', '', bitcoin_tx_id,
        )
        assert toaster_description == INFO_BITCOIN_SENT.format(bitcoin_tx_id)


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing and sending the RGB assets for multisig')
def test_ask_auth_for_imp_question_issue_nia_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing NIA asset with ask auth for important operations on for multisig"""

    with allure.step('Issue NIA asset for multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME_1, ASSET_AMOUNT, is_native_auth_enabled=True,
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
            FIRST_APPLICATION, ASSET_TICKER, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending NIA asset for multisig')
def test_ask_auth_for_imp_question_send_nia_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending NIA asset with ask auth for important operations on for multisig"""

    with allure.step('Create invoice for send nia'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        nia_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, nia_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True, is_native_auth_enabled=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send NIA asset from multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing CFA asset for multisig')
def test_ask_auth_for_imp_question_issue_cfa_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing CFA asset with ask auth for important operations on for multisig"""

    with allure.step('Issue CFA asset for multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME_1, ASSET_DESCRIPTION, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME_1, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending CFA asset for multisig')
def test_ask_auth_for_imp_question_send_cfa_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending CFA asset with ask auth for important operations on for multisig"""
    with allure.step('Getting an RGB invoice for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        cfa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, cfa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True, is_native_auth_enabled=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send CFA asset from multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Refresh from third app and first app'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_1,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing IFA asset for multisig')
def test_ask_auth_for_imp_question_issue_ifa_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing IFA asset with ask auth for important operations on for multisig"""

    with allure.step('Issue IFA asset for multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, IFA_ASSET_TICKER, IFA_ASSET_NAME_1, IFA_ASSET_TOTAL_SUPPLY, ASSET_AMOUNT, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, IFA_ASSET_TICKER, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending IFA asset for multisig')
def test_ask_auth_for_imp_question_send_ifa_on_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending IFA asset with ask auth for important operations on for multisig"""
    with allure.step('Getting an RGB invoice for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        ifa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_TICKER,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, ifa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True, is_native_auth_enabled=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send IFA asset from multisig with native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name, is_native_auth_enabled=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_1,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)
    with allure.step('Refresh from third app and first app'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Ask authorization for important operations for multisig')
@allure.story('Toggling off ask authorization for import operations for multisig')
def test_ask_auth_for_imp_question_send_bitcoin_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """test native auth for important operations (send btc) off for multisig"""
    with allure.step('Toggling off native auth for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()

        is_on_or_not_1 = kr.get_password(FIRST_SERVICE, NATIVE_AUTH_ENABLE)
        native_status_casted: bool = SettingRepository.str_to_bool(
            is_on_or_not_1,
        )

        if native_status_casted is True:
            wallets_and_operations.first_page_objects.settings_page_objects.click_ask_auth_imp_question()
            wallets_and_operations.first_page_operations.enter_native_password()

    with allure.step('getting address for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, _ = wallets_and_operations.third_page_features.receive_features.receive(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('Create PSBT for multisig bitcoin send'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_features.send_features.create_psbt(
            FIRST_APPLICATION, address, ASSET_AMOUNT,
        )

    with allure.step('Sign PSBT from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_title = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()

        assert toaster_title == 'Success'


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing NIA asset for multisig')
def test_ask_auth_for_imp_question_issue_nia_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing NIA asset with ask auth for important operations off for multisig"""

    with allure.step('Issue NIA asset for multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_TICKER, ASSET_NAME_2, ASSET_AMOUNT,
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


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending NIA asset for multisig')
def test_ask_auth_for_imp_question_send_nia_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending NIA asset with ask auth for important operations off for multisig"""
    with allure.step('Send NIA asset for multisig without native auth'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        nia_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_TICKER,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, nia_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send NIA asset from multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)

    with allure.step('Refresh from third app and first app'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing CFA asset for multisig')
def test_ask_auth_for_imp_question_issue_cfa_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing CFA asset with ask auth for important operations off for multisig"""

    with allure.step('Issue CFA asset for multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME_2, ASSET_DESCRIPTION, ASSET_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, ASSET_NAME_2,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending CFA asset for multisig')
def test_ask_auth_for_imp_question_send_cfa_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending CFA asset with ask auth for important operations off for multisig"""
    with allure.step('Send CFA without native auth'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        cfa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, cfa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send CFA asset from multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            ASSET_NAME_2,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)

    with allure.step('Refresh from third app and first app'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.third_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Issuing IFA asset for multisig')
def test_ask_auth_for_imp_question_issue_ifa_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Issuing IFA asset with ask auth for important operations off for multisig"""

    with allure.step('Issue IFA asset for multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, IFA_ASSET_TICKER, IFA_ASSET_NAME_2, IFA_ASSET_TOTAL_SUPPLY, ASSET_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, IFA_ASSET_TICKER,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()


@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.story('Sending IFA asset for multisig')
def test_ask_auth_for_imp_question_send_ifa_off_for_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Sending IFA asset with ask auth for important operations off for multisig"""
    with allure.step('Getting an RGB invoice for multisig'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        ifa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION, wallet_variant_name,
        )

    with allure.step('Create UTXO PSBT for multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_TICKER,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, ifa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Cosign transfer from second multisig wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send IFA asset from multisig without native auth'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_2,
        )
        wallets_and_operations.first_page_features.send_features.send_asset_for_multisig(
            FIRST_APPLICATION, wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, toaster_description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Verify received amount on App 3'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.third_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_ASSET_NAME_2,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_rgb_transaction_on_chain_frame()
        tx_id = wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.get_tx_id()
        wallets_and_operations.third_page_objects.asset_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()
        tx_id = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', tx_id)
        assert toaster_description == INFO_ASSET_SENT.format(tx_id)
