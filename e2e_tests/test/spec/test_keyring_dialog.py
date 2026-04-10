# pylint: disable=redefined-outer-name, unused-import
"""
This file contains test cases for the keyring functionality in the application.
"""
from __future__ import annotations

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.test_helpers import setup_offline_multisig_two_app_wallets

MNEMONIC = None
PASSWORD = None
XPUB_VANILLA = None
XPUB_COLORED = None
MASTER_FINGERPRINT = None


@pytest.mark.skip_for_multisig
@allure.feature('Keyring')
@allure.story('Keyring Dialog')
@pytest.mark.parametrize('test_environment', [False], indirect=True)
def test_keyring_dialog(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the keyring dialog functionality by restarting the application within the same test.

    :param test_environment: The test environment fixture.
    :param wallets_and_operations: The wallets and operations fixture.
    """
    with allure.step('Create and fund first wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('toggle the keyring button and save wallet secrets (mnemonic/password or xpubs/fingerprint)'):
        global MNEMONIC, PASSWORD, XPUB_VANILLA, XPUB_COLORED, MASTER_FINGERPRINT
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        # If hardware watch-only wallet, the dialog shows xpubs and fingerprint instead of mnemonic
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_xpub_vanilla_copy_button()
            XPUB_VANILLA = wallets_and_operations.first_page_operations.do_get_copied_address()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_xpub_colored_copy_button()
            XPUB_COLORED = wallets_and_operations.first_page_operations.do_get_copied_address()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_fingerprint_copy_button()
            MASTER_FINGERPRINT = wallets_and_operations.first_page_operations.do_get_copied_address()
        else:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
            MNEMONIC = wallets_and_operations.first_page_operations.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.first_page_operations.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
        if getattr(wallets_and_operations.first_page_objects.keyring_dialog_page_objects.keyring_check_box(), 'checked', None) is False:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_continue_button()
        if not wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        ):
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_continue_button()

        wallets_and_operations.first_page_objects.settings_page_objects.set_keyring_enable_ci()
        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_multisig
@allure.feature('Keyring')
@allure.story('Keyring option')
@pytest.mark.parametrize('test_environment', [False], indirect=True)
def test_keyring_option(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the keyring option by restarting the app and verifying the keyring toggle button state.

    :param wallets_and_operations: The wallets and operations fixture.
    """
    with allure.step('Restart the app for testing keyring option'):

        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.password_input().click()
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.enter_password(
            password=PASSWORD,
        )
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.click_login_button()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        if not wallets_and_operations.first_page_operations.do_is_displayed(wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button):
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        assert wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        )
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_xpub_vanilla_value(
                XPUB_VANILLA,
            )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_xpub_colored_value(
                XPUB_COLORED,
            )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_fingerprint_value(
                MASTER_FINGERPRINT,
            )
        else:
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_mnemonic_value(
                MNEMONIC,
            )
        wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_password_value(
            PASSWORD,
        )
        wallets_and_operations.first_page_objects.restore_wallet_page_objects.click_continue_button()
        if not wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        ):
            wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
            if wallet_variant_name in HARDWARE_WALLET_VARIANTS:
                wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_xpub_vanilla_value(
                    XPUB_VANILLA,
                )
                wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_xpub_colored_value(
                    XPUB_COLORED,
                )
                wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_fingerprint_value(
                    MASTER_FINGERPRINT,
                )
            else:
                wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_mnemonic_value(
                    MNEMONIC,
                )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_password_value(
                PASSWORD,
            )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.click_continue_button()
        # Wait for toggle state to update (AT-SPI needs time to sync)
        assert wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Keyring for multisig')
@allure.story('Keyring dialog for multisig')
def test_keyring_dialog_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the keyring dialog functionality for multisig wallets.

    :param wallets_and_operations: The wallets and operations fixture.
    :param wallet_variant_name: The wallet variant name.
    """
    global MNEMONIC, PASSWORD
    with allure.step('Setup multisig wallets'):
        setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Copy mnemonic from setting page for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_mnemonic_copy_button()
        MNEMONIC = wallets_and_operations.first_page_operations.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.first_page_operations.do_get_copied_address()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
        if getattr(wallets_and_operations.first_page_objects.keyring_dialog_page_objects.keyring_check_box(), 'checked', None) is False:
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
        wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_continue_button()
        if not wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        ):
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_check_box()
            wallets_and_operations.first_page_objects.keyring_dialog_page_objects.click_continue_button()

        wallets_and_operations.first_page_objects.settings_page_objects.set_keyring_enable_ci()
        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Keyring for multisig')
@allure.story('Keyring option for multisig')
def test_keyring_option_for_multisig(wallets_and_operations: WalletTestSetup):
    """
    Test the keyring option for multisig by restarting the app and verifying the keyring toggle button state.

    :param wallets_and_operations: The wallets and operations fixture.
    """
    with allure.step('Restart the app for testing keyring option for multisig'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.password_input().click()
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.enter_password(
            password=PASSWORD,
        )
        wallets_and_operations.first_page_objects.enter_wallet_password_page_objects.click_login_button()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        if not wallets_and_operations.first_page_operations.do_is_displayed(wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button):
            wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        assert wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        )
        wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
        wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_mnemonic_value(
            MNEMONIC,
        )
        wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_password_value(
            PASSWORD,
        )
        wallets_and_operations.first_page_objects.restore_wallet_page_objects.click_continue_button()
        if not wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        ):
            wallets_and_operations.first_page_objects.settings_page_objects.click_keyring_toggle_button()
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_mnemonic_value(
                MNEMONIC,
            )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.enter_password_value(
                PASSWORD,
            )
            wallets_and_operations.first_page_objects.restore_wallet_page_objects.click_continue_button()
        # Wait for toggle state to update (AT-SPI needs time to sync)
        assert wallets_and_operations.first_page_operations.wait_for_toggle_state(
            wallets_and_operations.first_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        )


# ==============================================================================
# Offline Multisig Tests (2 apps - offline wallet + paired wallet)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Keyring for offline multisig')
@allure.story('Keyring dialog for offline multisig')
def test_keyring_dialog_for_offline_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the keyring dialog functionality for offline multisig wallets (2 apps).

    :param wallets_and_operations: The wallets and operations fixture.
    :param wallet_variant_name: The wallet variant name.
    """
    global XPUB_VANILLA, XPUB_COLORED, MASTER_FINGERPRINT, PASSWORD
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    
    with allure.step('Setup offline multisig wallets'):
        setup_offline_multisig_two_app_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Copy xpubs/fingerprint from settings page for offline multisig'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.second_page_objects.settings_page_objects.click_keyring_toggle_button()
        
        if is_hardware:
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_keyring_xpub_vanilla_copy_button()
            XPUB_VANILLA = wallets_and_operations.second_page_operations.do_get_copied_address()
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_keyring_xpub_colored_copy_button()
            XPUB_COLORED = wallets_and_operations.second_page_operations.do_get_copied_address()
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_keyring_fingerprint_copy_button()
            MASTER_FINGERPRINT = wallets_and_operations.second_page_operations.do_get_copied_address()
        
        wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_keyring_password_copy_button()
        PASSWORD = wallets_and_operations.second_page_operations.do_get_copied_address()
        wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_check_box()
        if getattr(wallets_and_operations.second_page_objects.keyring_dialog_page_objects.keyring_check_box(), 'checked', None) is False:
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_check_box()
        wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_continue_button()
        if not wallets_and_operations.second_page_operations.wait_for_toggle_state(
            wallets_and_operations.second_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        ):
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_check_box()
            wallets_and_operations.second_page_objects.keyring_dialog_page_objects.click_continue_button()

        wallets_and_operations.second_page_objects.settings_page_objects.set_keyring_enable_ci()
        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Keyring for offline multisig')
@allure.story('Keyring option for offline multisig')
def test_keyring_option_for_offline_multisig(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the keyring option for offline multisig by restarting the app and verifying the keyring toggle button state (2 apps).

    :param wallets_and_operations: The wallets and operations fixture.
    :param wallet_variant_name: The wallet variant name.
    """
    is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
    
    with allure.step('Restart the app for testing keyring option for offline multisig'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.enter_wallet_password_page_objects.password_input().click()
        wallets_and_operations.second_page_objects.enter_wallet_password_page_objects.enter_password(
            password=PASSWORD,
        )
        wallets_and_operations.second_page_objects.enter_wallet_password_page_objects.click_login_button()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        if not wallets_and_operations.second_page_operations.do_is_displayed(wallets_and_operations.second_page_objects.settings_page_objects.keyring_toggle_button):
            wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        assert wallets_and_operations.second_page_operations.wait_for_toggle_state(
            wallets_and_operations.second_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=False,
            timeout=5,
        )
        wallets_and_operations.second_page_objects.settings_page_objects.click_keyring_toggle_button()
        
        if is_hardware:
            wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_xpub_vanilla_value(
                XPUB_VANILLA,
            )
            wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_xpub_colored_value(
                XPUB_COLORED,
            )
            wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_fingerprint_value(
                MASTER_FINGERPRINT,
            )
        
        wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_password_value(
            PASSWORD,
        )
        wallets_and_operations.second_page_objects.restore_wallet_page_objects.click_continue_button()
        if not wallets_and_operations.second_page_operations.wait_for_toggle_state(
            wallets_and_operations.second_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        ):
            wallets_and_operations.second_page_objects.settings_page_objects.click_keyring_toggle_button()
            if is_hardware:
                wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_xpub_vanilla_value(
                    XPUB_VANILLA,
                )
                wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_xpub_colored_value(
                    XPUB_COLORED,
                )
                wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_fingerprint_value(
                    MASTER_FINGERPRINT,
                )
            wallets_and_operations.second_page_objects.restore_wallet_page_objects.enter_password_value(
                PASSWORD,
            )
            wallets_and_operations.second_page_objects.restore_wallet_page_objects.click_continue_button()
        # Wait for toggle state to update (AT-SPI needs time to sync)
        assert wallets_and_operations.second_page_operations.wait_for_toggle_state(
            wallets_and_operations.second_page_objects.settings_page_objects.keyring_toggle_button,
            expected_checked=True,
            timeout=5,
        )
