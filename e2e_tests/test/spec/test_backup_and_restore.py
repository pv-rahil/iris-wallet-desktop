# pylint: disable=redefined-outer-name, unused-import,unused-argument, too-many-statements, too-many-lines
"""Test module for the backup page functionality"""
from __future__ import annotations

import allure
import pytest
from dotenv import load_dotenv

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import SECOND_APPLICATION
from accessible_constant import THIRD_APPLICATION
from e2e_tests.test.utilities.app_setup import load_qm_translation
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import fund_and_refresh_multisig_wallets
from e2e_tests.test.utilities.test_helpers import refresh_collectibles_on_app2
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.translation_utils import TranslationManager
from e2e_tests.test.utilities.wallet_variants import map_to_load_variant
from src.utils.info_message import INFO_BACKUP_COMPLETED
from src.utils.info_message import INFO_RESTORE_COMPLETED
load_dotenv()
MNEMONIC = None
XPUB_VANILLA = None
PASSWORD = None
MASTER_FINGERPRINT = None
XPUB_COLORED = None
NIA_TICKER = 'TTK'
NIA_NAME = 'Tether'
CFA_NAME = 'CFA'
CFA_DESC = 'This is CFA asset'
IFA_TICKER = 'IFK'
IFA_NAME = 'Inflatable'
IFA_TOTAL_SUPPLY = '10000'
BTC_SEND_AMOUNT = '0.001'
ISSUE_AMOUNT = '2000'
SEND_AMOUNT = '50'
NIA_RECEIVE_AMOUNT_BEFORE = None
CFA_RECEIVE_AMOUNT_BEFORE = None
IFA_RECEIVE_AMOUNT_BEFORE = None
BTC_BALANCE_BEFORE = None
pytestmark = pytest.mark.order(1)


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Mnemonic and backup configuration')
@allure.story('Mnemonic and backup configuration functionality')
def test_mnemonic_and_backup_configure(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """
    Test the mnemonic and backup configuration functionality.
    This test case covers the following scenarios:
    - Create a wallet
    - Copy mnemonic from setting page
    - Assert copied mnemonic with backup page mnemonic
    - Verify the backup configuration functionality
    :param wallets_and_operations: WalletTestSetup instance
    :return: None
    """
    global MNEMONIC, PASSWORD, XPUB_VANILLA, XPUB_COLORED, MASTER_FINGERPRINT
    with allure.step('Create a wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )
    with allure.step('Check the backup configuration'):
        if wallet_variant_name not in LOAD_WALLET_VARIANT:
            wallets_and_operations.first_page_operations.do_focus_on_application(
                FIRST_APPLICATION,
            )
            backup_tooltip = wallets_and_operations.first_page_objects.fungible_page_objects.get_backup_tooltip()
            assert backup_tooltip == TranslationManager.translate(
                'backup_tooltip_text',
            )
    with allure.step('Copy mnemonic from setting page'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_xpub_vanilla_copy_button()
            XPUB_VANILLA = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_xpub_colored_copy_button()
            XPUB_COLORED = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_fingerprint_copy_button()
            MASTER_FINGERPRINT = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
            PASSWORD = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        else:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
            MNEMONIC = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_cancel_button()
    if wallet_variant_name not in HARDWARE_WALLET_VARIANTS:
        with allure.step('assert copied mnemonic with backup page mnemonic'):
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_backup_button()
            wallets_and_operations.first_page_objects.backup_page_objects.click_show_mnemonic_button()
            mnemonic = wallets_and_operations.first_page_objects.backup_page_objects.get_mnemonic()
            assert mnemonic == MNEMONIC
            wallets_and_operations.first_page_objects.backup_page_objects.click_backup_close_button()
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Backup and Restore with asset transfers')
@allure.story('RGB20 from A->B, RGB25 from B->A, backup A, reset and restore A, then assert state')
def test_nia_and_cfa_transfer(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    E2E: Create two apps, fund both, create NIA (RGB20) in Wallet A and send to B.
    Create CFA (RGB25) in Wallet B and send to A. Backup Wallet A, reset first app,
    restore it and verify send/receive state is intact in Wallet A across variants.
    """
    global NIA_RECEIVE_AMOUNT_BEFORE, CFA_RECEIVE_AMOUNT_BEFORE

    with allure.step('Issue NIA (RGB20) in Wallet A'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_utxo(
            application=FIRST_APPLICATION, asset_ticker=NIA_TICKER, asset_name=NIA_NAME, asset_amount=ISSUE_AMOUNT, variant_name=wallet_variant_name,
        )

    with allure.step('Issue CFA (RGB25) in Wallet B'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            application=SECOND_APPLICATION, asset_name=CFA_NAME, asset_description=CFA_DESC, asset_amount=ISSUE_AMOUNT,
        )

    with allure.step('Generate invoice in Wallet A for CFA receive and send from B'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        cfa_invoice_a = wallets_and_operations.first_page_features.receive_features.receive_asset_from_sidebar(
            FIRST_APPLICATION, variant_name=wallet_variant_name,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.send(
            application=SECOND_APPLICATION, receiver_invoice=cfa_invoice_a, amount=SEND_AMOUNT,
        )

    with allure.step('Capture CFA received amount in Wallet A'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        CFA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Generate invoice in Wallet B for NIA receive'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        nia_invoice_b = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION,
        )

    with allure.step('Send NIA from Wallet A to Wallet B'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=nia_invoice_b, amount=SEND_AMOUNT, is_hardware_wallet=True, purpose='send_asset',
            )
        else:
            wallets_and_operations.first_page_features.send_features.send(
                application=FIRST_APPLICATION, receiver_invoice=nia_invoice_b, amount=SEND_AMOUNT,
            )

    with allure.step('Capture NIA transfer status in Wallet A and received amount in Wallet B'):

        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()

        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        NIA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Backup page')
@allure.story('Backup page functionality')
def test_backup(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the backup page functionality.
    This test case covers the following scenarios:
    - Create a wallet
    - Configure backup
    - Take a backup of wallet
    """
    description = None
    with allure.step('Configure backup'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_backup_button()
        if wallet_variant_name not in LOAD_WALLET_VARIANT:
            wallets_and_operations.first_page_objects.backup_page_objects.click_configurable_button()
            wallets_and_operations.first_page_features.wallet_features.google_auth()
            wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_close_button()
    with allure.step('Take a backup of wallet'):
        wallets_and_operations.first_page_objects.backup_page_objects.click_backup_wallet_data_button()
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_BACKUP_COMPLETED
        test_environment.restart_single_instance()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_offline_wallet
@allure.feature('Restore page')
@allure.story('Restore page functionality')
def test_restore(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    This test case is used to restore the wallet from the backup.
    """
    description = None
    with allure.step('Restore the wallet'):
        wallets_and_operations.first_page_objects.term_and_condition_page_objects.scroll_to_end()
        wallets_and_operations.first_page_objects.term_and_condition_page_objects.click_accept_button()
        load_variant = map_to_load_variant(wallet_variant_name)
        wallets_and_operations.first_page_features.wallet_features.drive_selection_flow(
            application=FIRST_APPLICATION, variant=load_variant,
        )
        wallets_and_operations.first_page_objects.welcome_page_objects.click_restore_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.wallet_features.google_auth(
                xpub_vanilla=XPUB_VANILLA,
                xpub_colored=XPUB_COLORED,
                fingerprint=MASTER_FINGERPRINT,
                password=PASSWORD,
            )
        else:
            wallets_and_operations.first_page_features.wallet_features.google_auth(
                mnemonic=MNEMONIC,
                password=PASSWORD,
            )
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_RESTORE_COMPLETED
        with allure.step('Off keyring for restore wallet with keyring off'):
            wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.enter_password(
                password=PASSWORD,
            )
            wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.click_login_button()

    with allure.step('Capture CFA received amount in Wallet A'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        cfa_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture NIA received amount in Wallet B'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        nia_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    assert CFA_RECEIVE_AMOUNT_BEFORE == cfa_received_amount_after
    assert NIA_RECEIVE_AMOUNT_BEFORE == nia_received_amount_after


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.skip_for_watch_only
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('load wallet for offline wallet')
@allure.story('load wallet functionality for offline wallet')
def test_load_wallet_for_offline_wallet(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    This test case is used to load the wallet from the backup.
    """
    global MNEMONIC, PASSWORD, XPUB_VANILLA, XPUB_COLORED, MASTER_FINGERPRINT
    with allure.step('Create and fund first wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Create and fund second wallet'):
        wallets_and_operations.second_page_features.wallet_features.create_and_fund_wallet(
            application=SECOND_APPLICATION, variant=wallet_variant_name,
        )

    with allure.step('Create and fund third wallet'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            XPUB_VANILLA, XPUB_COLORED, MASTER_FINGERPRINT, PASSWORD = wallets_and_operations.first_page_features.wallet_features.collect_keyring_values_from_app(
                is_load_wallet=True,
            )
        else:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
            MNEMONIC = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_cancel_button()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for offline wallet')
@allure.story('CFA from B->A via PSBT')
def test_cfa_transfer_for_offline_wallet(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Offline E2E using PSBT:
    - Issue CFA in Wallet B and send to A via PSBT (SECOND -> FIRST)
    - Verify received amounts in target wallets
    """
    global CFA_RECEIVE_AMOUNT_BEFORE

    # CFA: B -> A via PSBT
    with allure.step('Issue CFA (RGB25) in Wallet B'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_utxo(
            application=THIRD_APPLICATION, asset_name=CFA_NAME, asset_description=CFA_DESC, asset_amount=ISSUE_AMOUNT,
        )

    with allure.step('Generate invoice in Wallet A for CFA receive (PSBT)'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            SECOND_APPLICATION, variant_name=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.usb_sync()
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
        cfa_invoice_a = wallets_and_operations.second_page_features.receive_features.receive_asset_from_sidebar(
            application=SECOND_APPLICATION, variant_name=wallet_variant_name,
        )

    with allure.step('Create PSBT for CFA transfer in Wallet B'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.third_page_features.send_features.send(
            application=THIRD_APPLICATION, receiver_invoice=cfa_invoice_a, amount=SEND_AMOUNT,
        )
    refresh_collectibles_on_app2(wallets_and_operations)
    wallets_and_operations.second_page_features.wallet_features.usb_sync()

    with allure.step('Capture CFA received amount in Wallet A'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.usb_sync()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        CFA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.skip_for_hardware_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for offline wallet')
@allure.story('NIA from A->B via PSBT')
def test_nia_transfer_for_offline_wallet(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Offline E2E using PSBT:
    - Issue NIA in Wallet A and send to B via PSBT (FIRST -> SECOND)
    - Verify received amounts in target wallets
    """
    global NIA_RECEIVE_AMOUNT_BEFORE
    # NIA: A -> B via PSBT
    with allure.step('Issue NIA in Wallet A'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_offline_wallet(
            application=SECOND_APPLICATION, asset_ticker=NIA_TICKER, asset_name=NIA_NAME, asset_amount=ISSUE_AMOUNT,
        )
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
    with allure.step('Issuing NIA asset for backup and restore'):
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            NIA_TICKER,
        )
        wallets_and_operations.second_page_objects.issue_nia_page_objects.click_issue_nia_button()
        wallets_and_operations.second_page_objects.success_page_objects.click_home_button()

    with allure.step('Generate invoice in Wallet B for NIA receive (PSBT)'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        nia_invoice_b = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            application=THIRD_APPLICATION,
        )

    with allure.step('Create PSBT for NIA transfer in Wallet A'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.second_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        wallets_and_operations.second_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.second_page_features.send_features.create_psbt(
            application=SECOND_APPLICATION, receiver_invoice=nia_invoice_b, amount=SEND_AMOUNT, wallet_variant_name=wallet_variant_name,
        )

    with allure.step('Sign NIA PSBT in Wallet A and broadcast from Wallet B'):
        wallets_and_operations.first_page_features.wallet_features.sign_psbt(
            application=FIRST_APPLICATION, variant_name=wallet_variant_name, is_rgb=True,
        )
        wallets_and_operations.second_page_features.wallet_features.broadcast_psbt(
            application=SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.usb_sync()
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.third_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        wallets_and_operations.third_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture NIA amount in Wallet A'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.usb_sync()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        NIA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
    wallets_and_operations.first_page_objects.fungible_page_objects.click_usb_sync_frame()
    wallets_and_operations.first_page_objects.usb_sync_dialog_page_objects.click_continue_button()
    test_environment.restart_single_instance()


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Restore page (offline wallet)')
@allure.story('Restore page functionality for offline wallet')
def test_restore_for_offline_wallet(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Restore the wallet and assert the previously captured CFA/NIA received amounts.
    Mirrors the online restore test pattern.
    """
    description = None
    with allure.step('Restore the wallet'):
        load_variant = map_to_load_variant(wallet_variant_name)
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=load_variant, fund=False, is_restore_wallet=True,
        )
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.usb_sync_dialog_page_objects.click_continue_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_features.wallet_features.restore_with_xpubs(
                xpub_vanilla=XPUB_VANILLA,
                xpub_colored=XPUB_COLORED,
                fingerprint=MASTER_FINGERPRINT,
                password=PASSWORD,
            )
        else:
            wallets_and_operations.first_page_features.wallet_features.restore_with_mnemonic(
                mnemonic=MNEMONIC,
                password=PASSWORD,
            )
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_RESTORE_COMPLETED
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.enter_password(
            password=PASSWORD,
        )
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.click_login_button()
    with allure.step('Capture CFA received amount in Wallet A (post-restore)'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        cfa_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture NIA received amount in Wallet A (post-restore)'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        nia_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    assert CFA_RECEIVE_AMOUNT_BEFORE == cfa_received_amount_after
    assert NIA_RECEIVE_AMOUNT_BEFORE == nia_received_amount_after


@pytest.mark.skip_for_multisig
@pytest.mark.skip_for_create_wallet_variants
@pytest.mark.skip_for_load_wallet_variants
@allure.feature('Watch-only wallet')
@allure.story('Watch-only backup and restore flow')
@pytest.mark.parametrize('test_environment', [False], indirect=True)
def test_watch_only_backup_and_restore(test_environment, wallets_and_operations: WalletTestSetup):
    """
    Configure watch-only, backup, restart clean, restore watch-only via xpubs, assert success.
    """
    # Configure watch-only in single-instance mode
    with allure.step('Configure watch-only wallet'):
        wallets_and_operations.first_page_features.wallet_features.setup_watch_only_single_instance()

    # Optionally configure backup provider (Google) before taking backup
    with allure.step('Configure backup provider (Google)'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_backup_button()
        wallets_and_operations.first_page_objects.backup_page_objects.click_configurable_button()
        wallets_and_operations.first_page_features.wallet_features.google_auth()
        wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_close_button()

    # Take backup and assert
    with allure.step('Backup watch-only wallet'):
        wallets_and_operations.first_page_objects.backup_page_objects.click_backup_wallet_data_button()
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_BACKUP_COMPLETED
        wallets_and_operations.first_page_objects.backup_page_objects.click_backup_close_button()

    # Collect xpubs/fingerprint prior to restart
    with allure.step('Collect xpubs/fingerprint for watch-only before restart'):
        xpub_vanilla, xpub_colored, fingerprint, password = (
            wallets_and_operations.first_page_features.wallet_features.collect_keyring_values_from_app(
                is_load_wallet=True,
            )
        )

    # Restart with clean data and restore via xpubs (Google backup path)
    with allure.step('Restart app with clean data and restore watch-only via xpubs'):
        test_environment.restart_single_instance(reset_data=True)
        wallets_and_operations.first_page_features.wallet_features.navigate_to_watch_only_restore(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.wallet_features.google_auth(
            password=password, xpub_vanilla=xpub_vanilla, xpub_colored=xpub_colored, fingerprint=fingerprint,
        )
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_RESTORE_COMPLETED


# ============== MULTISIG BACKUP AND RESTORE TESTS ==============

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Mnemonic and backup configuration for multisig')
@allure.story('Mnemonic and backup configuration functionality for multisig')
def test_mnemonic_and_backup_configure_for_multisig(wallets_and_operations: WalletTestSetup, load_qm_translation, wallet_variant_name):
    """
    Test the mnemonic and backup configuration functionality for multisig.
    """
    global MNEMONIC, PASSWORD
    with allure.step('Setup multisig wallets'):
        setup_multisig_wallets(wallets_and_operations, wallet_variant_name)
        fund_and_refresh_multisig_wallets(wallets_and_operations, 'nia')

    with allure.step('Create third wallet for receiving'):
        wallets_and_operations.third_page_features.wallet_features.create_and_fund_wallet(
            application=THIRD_APPLICATION, variant=ONLINE_CREATE_ON_DEVICE,
        )

    with allure.step('Copy mnemonic from setting page for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
        MNEMONIC = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.first_page_objects.keyring_dialog_page_objects.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_cancel_button()

    with allure.step('assert copied mnemonic with backup page mnemonic for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_backup_button()
        wallets_and_operations.first_page_objects.backup_page_objects.click_show_mnemonic_button()
        mnemonic = wallets_and_operations.first_page_objects.backup_page_objects.get_mnemonic()
        assert mnemonic == MNEMONIC
        wallets_and_operations.first_page_objects.backup_page_objects.click_backup_close_button()
    wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Issue NIA for multisig')
def test_issue_nia_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Issue NIA asset for multisig via PSBT flow.
    """
    with allure.step('Create UTXO PSBT for NIA issuance'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, NIA_TICKER, NIA_NAME, ISSUE_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Issue NIA from draft'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_nia_features.issue_nia_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, NIA_TICKER,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Issue CFA for multisig')
def test_issue_cfa_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Issue CFA asset for multisig via PSBT flow.
    """
    with allure.step('Create UTXO PSBT for CFA issuance'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_for_multisig_wallet(
            FIRST_APPLICATION, CFA_NAME, CFA_DESC, ISSUE_AMOUNT,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Issue CFA from draft'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_cfa_features.issue_cfa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, CFA_NAME,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()


@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Send CFA for multisig')
def test_send_cfa_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Send CFA asset from multisig to third wallet via PSBT flow.
    """
    global CFA_RECEIVE_AMOUNT_BEFORE

    with allure.step('Generate invoice in third wallet for CFA receive'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        cfa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Create UTXO PSBT for CFA send from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, cfa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign CFA send PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.second_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send CFA from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
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

    with allure.step('Capture CFA amount in multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        CFA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Send NIA for multisig')
def test_send_nia_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Send NIA asset from multisig to third wallet via PSBT flow.
    """
    global NIA_RECEIVE_AMOUNT_BEFORE

    with allure.step('Generate invoice in third wallet for NIA receive'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        nia_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Create UTXO PSBT for NIA send from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, nia_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign NIA send PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send NIA from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
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

    with allure.step('Capture NIA amount in multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        NIA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Send BTC for multisig')
def test_send_btc_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Send BTC from multisig to third wallet via PSBT flow.
    """
    global BTC_BALANCE_BEFORE

    with allure.step('Get bitcoin address from third wallet'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_receive_bitcoin_button()
        address, _ = wallets_and_operations.third_page_features.receive_features.receive(
            THIRD_APPLICATION,
        )

    with allure.step('Create PSBT for BTC send from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_send_bitcoin_button()
        wallets_and_operations.first_page_features.send_features.create_psbt(
            FIRST_APPLICATION, address, BTC_SEND_AMOUNT,
        )

    with allure.step('Sign BTC PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )
        _, description = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()

    with allure.step('Refresh and verify BTC transaction'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.fungible_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        BTC_BALANCE_BEFORE = wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.get_bitcoin_balance()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    with allure.step('Verify transaction in third wallet'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_refresh_button()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_transaction_frame()
        tx_id = wallets_and_operations.third_page_objects.bitcoin_transaction_detail_page_objects.get_bitcoin_tx_id()
        wallets_and_operations.third_page_objects.bitcoin_transaction_detail_page_objects.click_close_button()
        wallets_and_operations.third_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    assert description is not None
    assert tx_id is not None

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Issue IFA for multisig')
def test_issue_ifa_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Issue IFA asset for multisig via PSBT flow.
    """
    with allure.step('Create UTXO PSBT for IFA issuance'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, IFA_TICKER, utxo_required=True,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name, is_issue_ifa=True,
        )

    with allure.step('Issue IFA from draft'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_features.issue_ifa_features.issue_ifa_with_sufficient_sats_and_no_utxo_multisig_wallet(
            FIRST_APPLICATION, IFA_TICKER,
        )
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()

    with allure.step('Verify IFA asset name'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        asset_name = wallets_and_operations.first_page_objects.inflatable_page_objects.get_ifa_asset_name(
            IFA_NAME,
        )
        assert asset_name == IFA_NAME

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup and Restore with asset transfers for multisig')
@allure.story('Send IFA for multisig')
def test_send_ifa_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Send IFA asset from multisig to third wallet via PSBT flow.
    """
    global IFA_RECEIVE_AMOUNT_BEFORE

    with allure.step('Generate invoice in third wallet for IFA receive'):
        wallets_and_operations.third_page_operations.do_focus_on_application(
            THIRD_APPLICATION,
        )
        ifa_invoice = wallets_and_operations.third_page_features.receive_features.receive_asset_from_sidebar(
            THIRD_APPLICATION,
        )

    with allure.step('Create UTXO PSBT for IFA send from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_NAME,
        )
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_send_button()
        wallets_and_operations.first_page_features.send_features.create_psbt_for_multisig(
            FIRST_APPLICATION, ifa_invoice, SEND_AMOUNT, wallet_variant_name, utxo_required=True,
        )

    with allure.step('Sign IFA send PSBT from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.second_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.second_page_features.wallet_features.sign_psbt(
            SECOND_APPLICATION, wallet_variant_name,
        )

    with allure.step('Send IFA from multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_NAME,
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

    with allure.step('Capture IFA amount in multisig wallet'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_refresh_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_NAME,
        )
        IFA_RECEIVE_AMOUNT_BEFORE = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [3], indirect=True)
@allure.feature('Backup page for multisig')
@allure.story('Backup page functionality for multisig')
def test_backup_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the backup page functionality for multisig.
    """
    description = None

    with allure.step('Configure backup for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_backup_button()
        wallets_and_operations.first_page_objects.backup_page_objects.click_configurable_button()
        wallets_and_operations.first_page_features.wallet_features.google_auth()
        wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_close_button()

    with allure.step('Take a backup of wallet for multisig'):
        wallets_and_operations.first_page_objects.backup_page_objects.click_backup_wallet_data_button()
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_BACKUP_COMPLETED
        test_environment.restart_single_instance()

@pytest.mark.skip_for_single_sig
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Restore page for multisig')
@allure.story('Restore page functionality for multisig')
def test_restore_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Restore the wallet for multisig and assert the previously captured CFA/NIA/IFA received amounts and BTC balance.
    """
    description = None
    with allure.step('Restore the wallet for multisig'):
        wallets_and_operations.first_page_objects.term_and_condition_page_objects.scroll_to_end()
        wallets_and_operations.first_page_objects.term_and_condition_page_objects.click_accept_button()
        load_variant = map_to_load_variant(wallet_variant_name)
        wallets_and_operations.first_page_features.wallet_features.drive_selection_flow(
            application=FIRST_APPLICATION, variant=load_variant,
        )
        wallets_and_operations.first_page_objects.welcome_page_objects.click_restore_button()
        wallets_and_operations.first_page_features.wallet_features.google_auth(
            mnemonic=MNEMONIC,
            password=PASSWORD,
        )
        wallets_and_operations.first_page_operations.wait_for_toaster_message()
        _, description = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert description == INFO_RESTORE_COMPLETED
        with allure.step('Off keyring for restore wallet with keyring off for multisig'):
            wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.enter_password(
                password=PASSWORD,
            )
            wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.click_login_button()

    with allure.step('Capture CFA received amount in Wallet A for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_collectibles_button()
        wallets_and_operations.first_page_objects.collectible_page_objects.click_cfa_frame(
            CFA_NAME,
        )
        cfa_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture NIA received amount in Wallet A for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_nia_frame(
            NIA_NAME,
        )
        nia_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture IFA received amount in Wallet A for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_inflatable_button()
        wallets_and_operations.first_page_objects.inflatable_page_objects.click_ifa_frame(
            IFA_NAME,
        )
        ifa_received_amount_after = wallets_and_operations.first_page_objects.asset_detail_page_objects.get_total_balance()
        wallets_and_operations.first_page_objects.asset_detail_page_objects.click_close_button()

    with allure.step('Capture BTC balance in Wallet A for multisig'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_fungibles_button()
        wallets_and_operations.first_page_objects.fungible_page_objects.click_bitcoin_frame()
        btc_balance_after = wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.get_bitcoin_balance()
        wallets_and_operations.first_page_objects.bitcoin_detail_page_objects.click_bitcoin_close_button()

    assert CFA_RECEIVE_AMOUNT_BEFORE == cfa_received_amount_after
    assert NIA_RECEIVE_AMOUNT_BEFORE == nia_received_amount_after
    assert IFA_RECEIVE_AMOUNT_BEFORE == ifa_received_amount_after
    assert BTC_BALANCE_BEFORE == btc_balance_after
