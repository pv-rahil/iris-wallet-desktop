# pylint: disable=redefined-outer-name, unused-import
"""
    E2E test for login app authentication
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
from e2e_tests.test.utilities.test_helpers import setup_offline_multisig_two_app_wallets


@pytest.mark.skip_for_multisig
@allure.feature('Login app')
@allure.story('Test login app toggle button')
@pytest.mark.parametrize('test_environment', [False], indirect=True)
def test_login_app_toggle_button_on(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the login app toggle button functionality.

    This test case creates first wallet,
    toggles the login app auth button to on, and restarts the application.

    Args:
        test_environment: The test environment setup.
        wallets_and_operations: The wallets and operations setup.

    Returns:
        None
    """
    with allure.step('Create and fund first wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )

    with allure.step('Toggle the login app auth button to on and restart the application'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_login_app_toggle_button()

        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_multisig
@allure.feature('Login app')
@allure.story('Test login app with authentication')
@pytest.mark.parametrize('test_environment', [False], indirect=True)
def test_login_app_with_authentication(wallets_and_operations: WalletTestSetup):
    """
    Test the login app with authentication functionality.

    This test case types the login password, asserts the state of the toggle button,
    toggles it to off, and types the login password again.

    Args:
        test_environment: The test environment setup.
        wallets_and_operations: The wallets and operations setup.

    Returns:
        None
    """
    with allure.step('assert the state of toggle button and toggle it to off'):
        wallets_and_operations.first_page_operations.enter_native_password()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        assert True is wallets_and_operations.first_page_objects.settings_page_objects.login_auth_toggle_button().checked
        wallets_and_operations.first_page_objects.settings_page_objects.click_login_app_toggle_button()

        wallets_and_operations.first_page_operations.enter_native_password()

        assert False is wallets_and_operations.first_page_objects.settings_page_objects.login_auth_toggle_button().checked


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Login app for multisig')
@allure.story('Test login app toggle button for multisig')
def test_login_app_toggle_button_on_for_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the login app toggle button functionality for multisig wallets.

    This test case sets up multisig wallets, toggles the login app auth button to on,
    and restarts the application.

    Args:
        test_environment: The test environment setup.
        wallets_and_operations: The wallets and operations setup.
        wallet_variant_name: The wallet variant name.

    Returns:
        None
    """
    with allure.step('Setup multisig wallets'):
        setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Toggle the login app auth button to on and restart the application'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.first_page_objects.settings_page_objects.click_login_app_toggle_button()

        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Login app for multisig')
@allure.story('Test login app with authentication for multisig')
def test_login_app_with_authentication_for_multisig(wallets_and_operations: WalletTestSetup):
    """
    Test the login app with authentication functionality for multisig.

    This test case types the login password, asserts the state of the toggle button,
    toggles it to off, and types the login password again.

    Args:
        wallets_and_operations: The wallets and operations setup.

    Returns:
        None
    """
    with allure.step('Assert the state of toggle button and toggle it to off'):
        wallets_and_operations.first_page_operations.enter_native_password()
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_settings_button()
        assert True is wallets_and_operations.first_page_objects.settings_page_objects.login_auth_toggle_button().checked
        wallets_and_operations.first_page_objects.settings_page_objects.click_login_app_toggle_button()

        wallets_and_operations.first_page_operations.enter_native_password()

        assert False is wallets_and_operations.first_page_objects.settings_page_objects.login_auth_toggle_button().checked


# ==============================================================================
# Offline Multisig Tests (2 apps - offline wallet + paired wallet)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Login app for offline multisig')
@allure.story('Test login app toggle button for offline multisig')
def test_login_app_toggle_button_on_for_offline_multisig(test_environment, wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """
    Test the login app toggle button functionality for offline multisig wallets (2 apps).

    This test case sets up offline multisig wallets, toggles the login app auth button to on,
    and restarts the application.

    Args:
        test_environment: The test environment setup.
        wallets_and_operations: The wallets and operations setup.
        wallet_variant_name: The wallet variant name.

    Returns:
        None
    """
    with allure.step('Setup offline multisig wallets'):
        setup_offline_multisig_two_app_wallets(
            wallets_and_operations, wallet_variant_name,
        )

    with allure.step('Toggle the login app auth button to on and restart the application'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        wallets_and_operations.second_page_objects.settings_page_objects.click_login_app_toggle_button()

        test_environment.restart_single_instance(reset_data=False)


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('Login app for offline multisig')
@allure.story('Test login app with authentication for offline multisig')
def test_login_app_with_authentication_for_offline_multisig(wallets_and_operations: WalletTestSetup):
    """
    Test the login app with authentication functionality for offline multisig (2 apps).

    This test case types the login password, asserts the state of the toggle button,
    toggles it to off, and types the login password again.

    Args:
        wallets_and_operations: The wallets and operations setup.
        wallet_variant_name: The wallet variant name.

    Returns:
        None
    """
    with allure.step('Assert the state of toggle button and toggle it to off'):
        wallets_and_operations.second_page_operations.enter_native_password()
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_settings_button()
        assert True is wallets_and_operations.second_page_objects.settings_page_objects.login_auth_toggle_button().checked
        wallets_and_operations.second_page_objects.settings_page_objects.click_login_app_toggle_button()

        wallets_and_operations.second_page_operations.enter_native_password()

        assert False is wallets_and_operations.second_page_objects.settings_page_objects.login_auth_toggle_button().checked
