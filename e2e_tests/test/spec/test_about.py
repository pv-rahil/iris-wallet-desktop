# pylint: disable=redefined-outer-name, unused-import
"""Test module for about page tests"""
from __future__ import annotations

from pathlib import Path

import allure
import pytest

from accessible_constant import FIRST_APPLICATION
from accessible_constant import SECOND_APPLICATION
from e2e_tests.test.utilities.app_setup import test_environment
from e2e_tests.test.utilities.app_setup import wallets_and_operations
from e2e_tests.test.utilities.model import WalletTestSetup
from e2e_tests.test.utilities.test_helpers import setup_multisig_wallets
from e2e_tests.test.utilities.test_helpers import setup_offline_multisig_two_app_wallets
from src.utils.info_message import INFO_LOG_SAVE_DESCRIPTION


@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.story('Tests for copy buttons for indexer info')
def test_indexer_info(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test asserting indexer info"""
    with allure.step('Create first wallet'):
        wallets_and_operations.first_page_features.wallet_features.create_and_fund_wallet(
            application=FIRST_APPLICATION, variant=wallet_variant_name, fund=False,
        )
    with allure.step('Indexer URL'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_about_button()
        indexer_url = wallets_and_operations.first_page_objects.about_page_objects.get_indexer_url()
        wallets_and_operations.first_page_objects.about_page_objects.click_indexer_url_copy_button()
        copied_indexer_url = wallets_and_operations.first_page_objects.about_page_objects.do_get_copied_address()

        assert copied_indexer_url == indexer_url


@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.story('Tests for copy buttons for RGB proxy info')
def test_rgb_proxy_info(wallets_and_operations: WalletTestSetup):
    """Test asserting RGB proxy info"""
    with allure.step('RGB proxy URL'):
        rgb_proxy_url = wallets_and_operations.first_page_objects.about_page_objects.get_rgb_proxy_url()
        wallets_and_operations.first_page_objects.about_page_objects.click_rgb_proxy_url_copy_button()
        copied_rgb_proxy_url = wallets_and_operations.first_page_objects.about_page_objects.do_get_copied_address()

        assert copied_rgb_proxy_url == rgb_proxy_url


@pytest.mark.skip_for_multisig
@pytest.mark.parametrize('test_environment', [False], indirect=True)
@allure.feature('About page tests')
@allure.story('Tests for download debug log')
def test_download_debug_log(wallets_and_operations: WalletTestSetup):
    """Test for downloading debug logs"""
    with allure.step('Download debug logs'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )

        wallets_and_operations.first_page_objects.about_page_objects.click_download_debug_log()
        file_name = wallets_and_operations.first_page_objects.about_page_objects.copying_logs_filename() + \
            '.zip'
        homepath = str(Path.home())
        complete_file_path = homepath+'/'+file_name
        wallets_and_operations.first_page_objects.about_page_objects.press_enter()

        _, toaster_desc = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert toaster_desc == INFO_LOG_SAVE_DESCRIPTION.format(
            complete_file_path,
        )


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.story('Tests for copy buttons for indexer info for multisig wallet')
def test_indexer_info_for_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test asserting indexer info for multisig wallet"""
    setup_multisig_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Indexer URL'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_about_button()
        indexer_url = wallets_and_operations.first_page_objects.about_page_objects.get_indexer_url()
        wallets_and_operations.first_page_objects.about_page_objects.click_indexer_url_copy_button()
        copied_indexer_url = wallets_and_operations.first_page_objects.about_page_objects.do_get_copied_address()

        assert copied_indexer_url == indexer_url


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.story('Tests for copy buttons for RGB proxy info for multisig wallet')
def test_rgb_proxy_info_for_multisig_wallet(wallets_and_operations: WalletTestSetup):
    """Test asserting RGB proxy info for multisig wallet"""
    with allure.step('RGB proxy URL'):
        wallets_and_operations.first_page_objects.sidebar_page_objects.click_about_button()
        rgb_proxy_url = wallets_and_operations.first_page_objects.about_page_objects.get_rgb_proxy_url()
        wallets_and_operations.first_page_objects.about_page_objects.click_rgb_proxy_url_copy_button()
        copied_rgb_proxy_url = wallets_and_operations.first_page_objects.about_page_objects.do_get_copied_address()

        assert copied_rgb_proxy_url == rgb_proxy_url


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_offline_wallet
@pytest.mark.parametrize('test_environment', [True], indirect=True)
@allure.feature('About page tests for multisig wallet')
@allure.story('Tests for download debug log for multisig wallet')
def test_download_debug_log_for_multisig_wallet(wallets_and_operations: WalletTestSetup):
    """Test for downloading debug logs for multisig wallet"""
    with allure.step('Download debug logs'):
        wallets_and_operations.first_page_operations.do_focus_on_application(
            FIRST_APPLICATION,
        )

        wallets_and_operations.first_page_objects.about_page_objects.click_download_debug_log()
        file_name = wallets_and_operations.first_page_objects.about_page_objects.copying_logs_filename() + \
            '.zip'
        homepath = str(Path.home())
        complete_file_path = homepath+'/'+file_name
        wallets_and_operations.first_page_objects.about_page_objects.press_enter()

        _, toaster_desc = wallets_and_operations.first_page_objects.toaster_page_objects.click_toaster_frame()
        assert toaster_desc == INFO_LOG_SAVE_DESCRIPTION.format(
            complete_file_path,
        )


# ==============================================================================
# Offline Multisig Tests (2 apps - offline wallet + paired wallet)
# ==============================================================================

@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.story('Tests for copy buttons for indexer info for offline multisig wallet')
def test_indexer_info_for_offline_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test asserting indexer info for offline multisig wallet (2 apps)"""
    setup_offline_multisig_two_app_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Indexer URL from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_about_button()
        indexer_url = wallets_and_operations.second_page_objects.about_page_objects.get_indexer_url()
        wallets_and_operations.second_page_objects.about_page_objects.click_indexer_url_copy_button()
        copied_indexer_url = wallets_and_operations.second_page_operations.do_get_copied_address()

        assert copied_indexer_url == indexer_url


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.story('Tests for copy buttons for RGB proxy info for offline multisig wallet')
def test_rgb_proxy_info_for_offline_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test asserting RGB proxy info for offline multisig wallet (2 apps)"""
    setup_offline_multisig_two_app_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('RGB proxy URL from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.sidebar_page_objects.click_about_button()
        rgb_proxy_url = wallets_and_operations.second_page_objects.about_page_objects.get_rgb_proxy_url()
        wallets_and_operations.second_page_objects.about_page_objects.click_rgb_proxy_url_copy_button()
        copied_rgb_proxy_url = wallets_and_operations.second_page_operations.do_get_copied_address()

        assert copied_rgb_proxy_url == rgb_proxy_url


@pytest.mark.skip_for_single_sig
@pytest.mark.skip_for_online_wallet
@pytest.mark.parametrize('test_environment', [2], indirect=True)
@allure.feature('About page tests for offline multisig wallet')
@allure.story('Tests for download debug log for offline multisig wallet')
def test_download_debug_log_for_offline_multisig_wallet(wallets_and_operations: WalletTestSetup, wallet_variant_name):
    """Test for downloading debug logs for offline multisig wallet (2 apps)"""
    setup_offline_multisig_two_app_wallets(wallets_and_operations, wallet_variant_name)

    with allure.step('Download debug logs from second wallet'):
        wallets_and_operations.second_page_operations.do_focus_on_application(
            SECOND_APPLICATION,
        )
        wallets_and_operations.second_page_objects.about_page_objects.click_download_debug_log()
        file_name = wallets_and_operations.second_page_objects.about_page_objects.copying_logs_filename() + \
            '.zip'
        homepath = str(Path.home())
        complete_file_path = homepath+'/'+file_name
        wallets_and_operations.second_page_objects.about_page_objects.press_enter()

        _, toaster_desc = wallets_and_operations.second_page_objects.toaster_page_objects.click_toaster_frame()
        assert toaster_desc == INFO_LOG_SAVE_DESCRIPTION.format(
            complete_file_path,
        )
