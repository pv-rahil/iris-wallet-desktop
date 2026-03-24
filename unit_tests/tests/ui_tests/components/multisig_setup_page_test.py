# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for MultisigSetupPage."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.views.components.multisig_setup_page import MultisigSetupPage


@pytest.fixture
def vm():
    """Provide a view model stub with page_navigation."""
    m = MagicMock()
    m.page_navigation = MagicMock()
    return m


@pytest.fixture
def widget_watch_only(qt_app, vm):
    """Instantiate the page in watch-only mode."""
    with patch('src.views.components.multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.components.multisig_setup_page.get_value', return_value='test_password'):
        w = MultisigSetupPage(vm)
        qt_app.processEvents()
        yield w


@pytest.fixture
def widget_with_privkey(qt_app, vm):
    """Instantiate the page in with-private-key (non watch-only) mode."""
    with patch('src.views.components.multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WITH_PRIVATE_KEY), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.components.multisig_setup_page.get_value', return_value='test_password'):
        w = MultisigSetupPage(vm)
        qt_app.processEvents()
        yield w


def test_close_button_calls_selection_page(widget_watch_only: MultisigSetupPage, vm):
    """Close button should navigate back to selection page."""
    widget_watch_only.close_btn.click()
    assert vm.page_navigation.selection_page.called


def test_watch_only_flow_threshold_confirm_and_finish(widget_watch_only: MultisigSetupPage, vm, mocker):
    """Watch-only: Step1 -> Step2 (cosigners) -> finish navigates to welcome page."""
    # Set M and N
    widget_watch_only.total_signer_input.setText('3')
    widget_watch_only.required_signer_input.setText('2')

    # Spy on config set
    set_cfg = mocker.patch(
        'src.views.components.multisig_setup_page.SettingRepository.set_multisig_config',
    )
    
    # Mock data validation properties
    mocker.patch.object(widget_watch_only, '_save_watch_only_review_fields', return_value=True)
    mocker.patch.object(widget_watch_only, '_save_cosigners_data', return_value=True)

    # Step 1 -> confirm threshold -> Step 2 Review
    widget_watch_only.continue_button.click()
    widget_watch_only.parent().update() if widget_watch_only.parent() else None

    # After confirming threshold, inputs locked
    assert widget_watch_only.required_signer_input.isEnabled() is False
    assert widget_watch_only.total_signer_input.isEnabled() is False
    assert len(widget_watch_only.cosigner_rows) == 2  # for 2 and 3
    set_cfg.assert_called_once_with(2, 3)
    
    assert not widget_watch_only.review_frame.isHidden()
    assert widget_watch_only.cos_frame.isHidden()
    
    # Step 2 -> Step 3 Cosigners
    widget_watch_only.continue_button.click()
    widget_watch_only.parent().update() if widget_watch_only.parent() else None
    
    assert not widget_watch_only.cos_frame.isHidden()
    assert widget_watch_only.review_frame.isHidden()

    # Step 3 -> finish -> welcome page
    # Since inputs are empty, it might be disabled by UI logic. Force enable.
    widget_watch_only.continue_button.setEnabled(True)
    widget_watch_only.continue_button.click()
    assert vm.page_navigation.welcome_page.called


def test_with_privkey_flow_steps_and_back(widget_with_privkey: MultisigSetupPage, vm, mocker):
    """With private key: Step1 -> Step2(review) -> Step3(cosigners) -> finish, and Back behavior resets config on returning to step1."""
    widget_with_privkey.total_signer_input.setText('2')
    widget_with_privkey.required_signer_input.setText('2')
    set_cfg = mocker.patch(
        'src.views.components.multisig_setup_page.SettingRepository.set_multisig_config',
    )
    
    # Mock cosigners validation
    mocker.patch.object(widget_with_privkey, '_save_cosigners_data', return_value=True)

    # Step 1 -> Step 2 (review visible, cos hidden)
    widget_with_privkey.continue_button.click()
    # Process events to update visibility
    widget_with_privkey.parent().update() if widget_with_privkey.parent() else None
    assert not widget_with_privkey.review_frame.isHidden()
    assert widget_with_privkey.cos_frame.isHidden()
    assert not widget_with_privkey.back_button.isHidden()
    assert widget_with_privkey.close_btn.isHidden()

    # Step 2 -> Step 3 (cosigners)
    widget_with_privkey.continue_button.click()
    widget_with_privkey.parent().update() if widget_with_privkey.parent() else None
    assert not widget_with_privkey.cos_frame.isHidden()
    assert widget_with_privkey.review_frame.isHidden()

    # Step 3 -> finish navigates to welcome
    widget_with_privkey.continue_button.setEnabled(True)
    widget_with_privkey.continue_button.click()
    assert vm.page_navigation.welcome_page.called

    # Go back path from Step 2 to Step 1 should reset config to None, None
    # Recreate to reach Step 2 again
    widget_with_privkey = None
    with patch('src.views.components.multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WITH_PRIVATE_KEY), \
            patch('src.views.components.multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.components.multisig_setup_page.get_value', return_value='test_password'):
        w = MultisigSetupPage(vm)
    w.total_signer_input.setText('2')
    w.required_signer_input.setText('2')
    set_cfg = mocker.patch(
        'src.views.components.multisig_setup_page.SettingRepository.set_multisig_config',
    )
    w.continue_button.click()
    # Back from Step 2 -> Step 1
    w._go_back()
    # It may have been called first with (2,2) during confirm, then (None,None) on back
    assert any(
        args == ((None, None),) or args == (None, None)
        for args, _ in set_cfg.call_args_list
    )
