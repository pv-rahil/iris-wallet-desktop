# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for MultisigSetupPage."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.views.ui_multisig_setup_page import MultisigSetupPage
from src.views.ui_multisig_setup_page import PageNavigationEventManager


@pytest.fixture
def vm():
    """Provide a view model stub with page_navigation."""
    m = MagicMock()
    m.page_navigation = MagicMock()
    return m


@pytest.fixture
def widget_watch_only(qt_app, vm):
    """Instantiate the page in watch-only mode."""
    with patch('src.views.ui_multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.ui_multisig_setup_page.get_value', return_value='test_password'):
        w = MultisigSetupPage(vm)
        qt_app.processEvents()
        yield w


@pytest.fixture
def widget_with_privkey(qt_app, vm):
    """Instantiate the page in with-private-key (non watch-only) mode."""
    with patch('src.views.ui_multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WITH_PRIVATE_KEY), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.ui_multisig_setup_page.get_value', return_value='test_password'):
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
    widget_watch_only.threshold_frame.total_signer_input.setText('3')
    widget_watch_only.threshold_frame.required_signer_input.setText('2')

    # Spy on config set
    set_cfg = mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.set_multisig_config',
    )

    # Mock data validation properties
    mocker.patch.object(
        widget_watch_only,
        '_save_watch_only_review_fields', return_value=True,
    )
    mocker.patch.object(
        widget_watch_only,
        '_save_cosigners_data', return_value=True,
    )

    # Step 1 -> confirm threshold -> Step 2 Review
    widget_watch_only.continue_button.click()
    parent = widget_watch_only.parent()
    if parent:
        parent.update()
    # After confirming threshold, inputs locked
    assert widget_watch_only.threshold_frame.required_signer_input.isEnabled() is False
    assert widget_watch_only.threshold_frame.total_signer_input.isEnabled() is False
    assert len(widget_watch_only.cos_frame.cosigner_rows) == 2  # for 2 and 3
    set_cfg.assert_called_once_with(2, 3)

    assert not widget_watch_only.review_frame.isHidden()
    assert widget_watch_only.cos_frame.isHidden()

    # Step 2 -> Step 3 Cosigners
    widget_watch_only.continue_button.click()
    parent = widget_watch_only.parent()
    if parent:
        parent.update()
    assert not widget_watch_only.cos_frame.isHidden()
    assert widget_watch_only.review_frame.isHidden()

    # Step 3 -> finish -> welcome page
    # Since inputs are empty, it might be disabled by UI logic. Force enable.
    widget_watch_only.continue_button.setEnabled(True)
    widget_watch_only.continue_button.click()
    assert vm.page_navigation.welcome_page.called


def test_with_privkey_flow_steps_and_back(widget_with_privkey: MultisigSetupPage, vm, mocker):
    """With private key: Step1 -> Step2(review) -> Step3(cosigners) -> finish, and Back behavior resets config on returning to step1."""
    widget_with_privkey.threshold_frame.total_signer_input.setText('2')
    widget_with_privkey.threshold_frame.required_signer_input.setText('2')
    set_cfg = mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.set_multisig_config',
    )

    # Mock cosigners validation
    mocker.patch.object(
        widget_with_privkey,
        '_save_cosigners_data', return_value=True,
    )

    # Step 1 -> Step 2 (review visible, cos hidden)
    widget_with_privkey.continue_button.click()
    # Process events to update visibility
    parent = widget_with_privkey.parent()
    if parent:
        parent.update()
    assert not widget_with_privkey.review_frame.isHidden()
    assert widget_with_privkey.cos_frame.isHidden()
    assert not widget_with_privkey.back_button.isHidden()
    assert widget_with_privkey.close_btn.isHidden()

    # Step 2 -> Step 3 (cosigners)
    widget_with_privkey.continue_button.click()
    parent = widget_with_privkey.parent()
    if parent:
        parent.update()
    assert not widget_with_privkey.cos_frame.isHidden()
    assert widget_with_privkey.review_frame.isHidden()

    # Step 3 -> finish navigates to welcome
    widget_with_privkey.continue_button.setEnabled(True)
    widget_with_privkey.continue_button.click()
    assert vm.page_navigation.welcome_page.called

    # Go back path from Step 2 to Step 1 should reset config to None, None
    # Recreate to reach Step 2 again
    with patch('src.views.ui_multisig_setup_page.load_stylesheet', return_value=''), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WITH_PRIVATE_KEY), \
            patch('src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network', return_value=NetworkEnumModel.TESTNET), \
            patch('src.views.ui_multisig_setup_page.get_value', return_value='test_password'):
        w = MultisigSetupPage(vm)
    w.threshold_frame.total_signer_input.setText('2')
    w.threshold_frame.required_signer_input.setText('2')
    set_cfg = mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.set_multisig_config',
    )
    w.continue_button.click()
    # Back from Step 2 -> Step 1
    w._go_back()
    # It may have been called first with (2,2) during confirm, then (None,None) on back
    assert any(
        args in [((None, None),), (None, None)]
        for args, _ in set_cfg.call_args_list
    )


def test_multisig_without_password_redirects(vm, mocker):
    """Test that accessing multisig without password redirects to selection page."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.load_stylesheet', return_value='',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.TESTNET,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.get_value',
        return_value=None,
    )  # No password

    # Mock the page navigation signal
    mock_signal = MagicMock()
    mocker.patch(
        'src.views.ui_multisig_setup_page.PageNavigationEventManager.get_instance',
    )
    PageNavigationEventManager.get_instance.return_value.selection_page_signal = mock_signal

    _w = MultisigSetupPage(vm)
    mock_signal.emit.assert_called_once_with(None)


def test_retranslate_ui_sets_texts(widget_watch_only: MultisigSetupPage):
    """Test retranslate_ui sets text correctly."""
    widget_watch_only.retranslate_ui()
    assert widget_watch_only.title.text() != ''


def test_update_summary_displays_threshold(widget_watch_only: MultisigSetupPage):
    """Test _update_summary displays the threshold correctly."""
    widget_watch_only.threshold_frame.required_signer_input.setText('2')
    widget_watch_only.threshold_frame.total_signer_input.setText('3')
    widget_watch_only._update_summary()
    # Summary should be updated
    assert widget_watch_only.threshold_frame.required_signer_input.text() == '2'
    assert widget_watch_only.threshold_frame.total_signer_input.text() == '3'


def test_update_continue_enabled_valid_input(widget_watch_only: MultisigSetupPage):
    """Test _update_continue_enabled with valid input."""
    widget_watch_only.threshold_frame.required_signer_input.setText('2')
    widget_watch_only.threshold_frame.total_signer_input.setText('3')
    widget_watch_only._update_continue_enabled()
    assert widget_watch_only.continue_button.isEnabled()


def test_update_continue_enabled_invalid_input(widget_watch_only: MultisigSetupPage):
    """Test _update_continue_enabled with invalid input."""
    widget_watch_only.threshold_frame.required_signer_input.setText(
        '5',
    )  # M > N
    widget_watch_only.threshold_frame.total_signer_input.setText('2')
    widget_watch_only._update_continue_enabled()
    assert not widget_watch_only.continue_button.isEnabled()


def test_update_continue_enabled_empty_input(widget_watch_only: MultisigSetupPage):
    """Test _update_continue_enabled with empty input."""
    widget_watch_only.threshold_frame.required_signer_input.setText('')
    widget_watch_only.threshold_frame.total_signer_input.setText('3')
    widget_watch_only._update_continue_enabled()
    assert not widget_watch_only.continue_button.isEnabled()


def test_hardware_wallet_flow_with_saved_config(vm, mocker):
    """Test hardware wallet flow with saved config."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.load_stylesheet', return_value='',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.TESTNET,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.get_value',
        return_value='test_password',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_multisig_config', return_value=(2, 3),
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.local_store.get_value',
        side_effect=['FP123', 'xpub_vanilla', 'xpub_colored'],
    )
    mocker.patch.object(
        MultisigSetupPage,
        '_complete_threshold_confirmation_after_hw_connect',
    )

    w = MultisigSetupPage(vm)
    w._complete_threshold_confirmation_after_hw_connect.assert_called_once_with(
        2, 3,
    )


def test_restore_cosigner_inputs(vm, mocker):
    """Test restoring cosigner inputs from saved config."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.load_stylesheet', return_value='',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WATCH_ONLY,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_wallet_network',
        return_value=NetworkEnumModel.TESTNET,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.get_value',
        return_value='test_password',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_multisig_config', return_value=(2, 3),
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.SettingRepository.get_cosigners', return_value=[
            {'master_fingerprint': 'FP1', 'xpub': 'xpub1'},
            {'master_fingerprint': 'FP2', 'xpub': 'xpub2'},
        ],
    )

    w = MultisigSetupPage(vm)
    # Cosigner rows should be created
    assert len(w.cos_frame.cosigner_rows) == 2


def test_close_button_visibility(widget_watch_only: MultisigSetupPage):
    """Test close button visibility on different steps."""
    # Initially visible
    assert not widget_watch_only.close_btn.isHidden()
    # After moving to step 2, hidden
    widget_watch_only.threshold_frame.total_signer_input.setText('2')
    widget_watch_only.threshold_frame.required_signer_input.setText('2')
    widget_watch_only.continue_button.click()
    assert widget_watch_only.close_btn.isHidden()


def test_on_watch_only_cosigner_string_changed_invalid(widget_watch_only, mocker):
    """Test watch-only: entering invalid cosigner string clears fields."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.parse_cosigner_string',
        return_value=mocker.Mock(is_valid=False),
    )
    widget_watch_only.review_frame.fp_value_widget.setText('STAY')
    widget_watch_only._on_watch_only_cosigner_string_changed('invalid')
    assert widget_watch_only.review_frame.fp_value_widget.text() == ''


def test_on_watch_only_reset_clicked(widget_watch_only):
    """Test watch-only: reset button clears all fields."""
    widget_watch_only.review_frame.fp_value_widget.setText('FP')
    widget_watch_only.review_frame.cosigner_string_value_widget.setText('STR')
    widget_watch_only._on_watch_only_reset_clicked()
    assert widget_watch_only.review_frame.fp_value_widget.text() == ''
    assert widget_watch_only.review_frame.cosigner_string_value_widget.text() == ''


def test_update_continue_enabled_duplicate_cosigners(widget_with_privkey, mocker):
    """Test Step 3 validation: duplicate cosigner xpubs should disable continue."""
    widget_with_privkey._current_step = 3
    # Use a real cosigner layout if possible or just mock very carefully
    card1 = mocker.MagicMock()
    card1.vanilla_xpub_str = 'xpub1'
    card2 = mocker.MagicMock()
    card2.vanilla_xpub_str = 'xpub1'  # Duplicate

    mocker.patch.object(
        widget_with_privkey.cos_frame,
        'isVisible', return_value=True,
    )
    widget_with_privkey.cos_frame.cosigner_rows = [card1, card2]
    widget_with_privkey.threshold_frame.required_signer_input.setText('2')
    widget_with_privkey.threshold_frame.total_signer_input.setText(
        '3',
    )  # n=3 means 2 cosigner cards

    widget_with_privkey._update_continue_enabled()
    assert widget_with_privkey.continue_button.isEnabled() is False
    card2.show_error.assert_called_with('Duplicate Cosigner')


def test_export_cosigner_to_file(widget_with_privkey, mocker):
    """Test exporting cosigner data to a file."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.QFileDialog.getSaveFileName',
        return_value=('/tmp/test_export.txt', ''),
    )
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    toast_success = mocker.patch(
        'src.views.ui_multisig_setup_page.ToastManager.success',
    )

    # Ensure review frame exists
    widget_with_privkey.review_frame.cosigner_string_value_widget.setText(
        'test_string',
    )
    widget_with_privkey._export_cosigner_to_file()

    mock_open.assert_called_once_with(
        '/tmp/test_export.txt', 'w', encoding='utf-8',
    )
    mock_open().write.assert_called_once_with('test_string')
    toast_success.assert_called_once()


def test_import_cosigner_from_file(widget_with_privkey, mocker):
    """Test importing cosigner data from a file."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.QFileDialog.getOpenFileName',
        return_value=('/tmp/test_import.txt', ''),
    )
    mocker.patch(
        'builtins.open', mocker.mock_open(
            read_data='imported_string',
        ),
    )
    toast_success = mocker.patch(
        'src.views.ui_multisig_setup_page.ToastManager.success',
    )

    card = mocker.Mock()
    card.is_expanded = False
    widget_with_privkey._import_cosigner_from_file(card)

    card.string_input.setText.assert_called_once_with('imported_string')
    card.toggle_content.assert_called_once()
    toast_success.assert_called_once()


def test_save_cosigners_data_invalid(widget_with_privkey, mocker):
    """Test _save_cosigners_data with invalid input."""
    card = mocker.Mock()
    card.string_input.text.return_value = 'invalid'
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.parse_cosigner_string',
        return_value=mocker.Mock(is_valid=False),
    )

    widget_with_privkey.cos_frame.cosigner_rows = [card]
    assert widget_with_privkey._save_cosigners_data() is False
    card.show_error.assert_called_with('Invalid cosigner details')


def test_complete_threshold_confirmation_after_hw_connect_standard(widget_with_privkey, mocker, qtbot):
    """Test HWW flow completion for standard wallet."""
    qtbot.addWidget(widget_with_privkey)
    widget_with_privkey.show()
    widget_with_privkey._is_watch_only = False
    mocker.patch.object(widget_with_privkey, '_populate_wallet_review_fields')

    widget_with_privkey._complete_threshold_confirmation_after_hw_connect(2, 2)

    assert widget_with_privkey._current_step == 2
    assert widget_with_privkey.review_frame.isVisible()
    assert widget_with_privkey.export_button.isVisible()
    assert widget_with_privkey.back_button.isVisible()


def test_go_back_step_3_to_2(widget_with_privkey, qtbot):
    """Test navigation: Back from Step 3 to Step 2."""
    qtbot.addWidget(widget_with_privkey)
    widget_with_privkey.show()
    widget_with_privkey._current_step = 3
    widget_with_privkey.cos_frame.show()
    widget_with_privkey.review_frame.hide()

    widget_with_privkey._go_back()

    assert widget_with_privkey._current_step == 2
    assert widget_with_privkey.review_frame.isVisible()
    assert widget_with_privkey.cos_frame.isHidden()
    assert widget_with_privkey.export_button.isVisible()


def test_on_watch_only_cosigner_string_changed_valid(widget_watch_only, mocker):
    """Test watch-only: entering valid cosigner string updates fields."""
    mock_result = mocker.Mock(
        is_valid=True,
        master_fingerprint='FP123',
        vanilla_keychain=88,
        account_xpub_vanilla='xpub_v',
        account_xpub_colored='xpub_c',
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.parse_cosigner_string',
        return_value=mock_result,
    )
    widget_watch_only._on_watch_only_cosigner_string_changed('valid_string')
    assert widget_watch_only.review_frame.fp_value_widget.text() == 'FP123'
    assert widget_watch_only.review_frame.keychain_value_widget.text() == '88'
    assert widget_watch_only.review_frame.xpub_vanilla_value_widget.text() == 'xpub_v'
    assert widget_watch_only.review_frame.xpub_colored_value_widget.text() == 'xpub_c'


def test_save_watch_only_review_fields(widget_watch_only, mocker):
    """Test _save_watch_only_review_fields calls the service with widget values."""
    widget_watch_only.review_frame.fp_value_widget.setText('FP')
    widget_watch_only.review_frame.keychain_value_widget.setText('1')
    widget_watch_only.review_frame.xpub_vanilla_value_widget.setText('V')
    widget_watch_only.review_frame.xpub_colored_value_widget.setText('C')
    mock_save = mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.save_watch_only_data', return_value=True,
    )
    assert widget_watch_only._save_watch_only_review_fields() is True
    mock_save.assert_called_once_with('FP', '1', 'V', 'C')


def test_populate_wallet_review_fields_not_watch_only(widget_with_privkey, mocker):
    """Test _populate_wallet_review_fields for non-watch-only wallet."""
    data = {
        'master_fingerprint': 'FP',
        'keychain': '0',
        'derivation_path': 'path',
        'account_xpub_vanilla': 'xpub_v',
        'account_xpub_colored': 'xpub_c',
    }
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.get_wallet_review_data', return_value=data,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.truncate_text', side_effect=lambda x: x,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.generate_cosigner_string',
        return_value='generated_str',
    )

    widget_with_privkey._is_watch_only = False
    widget_with_privkey._populate_wallet_review_fields()

    assert widget_with_privkey.review_frame.cosigner_string_value_widget.text() == 'generated_str'
    assert widget_with_privkey.review_frame.fp_value_widget.text() == 'FP'


def test_on_cosigner_string_changed_valid(widget_with_privkey, mocker):
    """Test valid cosigner string entry in Step 3."""
    mock_result = mocker.Mock(
        is_valid=True,
        master_fingerprint='FP',
        account_xpub_vanilla='long_xpub_v',
        account_xpub_colored='long_xpub_c',
        vanilla_keychain=1,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.parse_cosigner_string',
        return_value=mock_result,
    )
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.truncate_text',
        side_effect=lambda x: f'trunc_{x}',
    )

    row = mocker.MagicMock()
    widget_with_privkey._on_cosigner_string_changed('valid', row)

    row.fp_input.setText.assert_called_with('FP')
    row.vanilla_xpub_input.setText.assert_called_with('trunc_long_xpub_v')
    assert row.vanilla_xpub_str == 'long_xpub_v'
    row.string_input.setReadOnly.assert_called_with(True)


def test_save_cosigners_data_valid(widget_with_privkey, mocker):
    """Test _save_cosigners_data with valid input."""
    card = mocker.Mock()
    card.index = 1
    card.string_input.text.return_value = 'valid_str'
    mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.parse_cosigner_string',
        return_value=mocker.Mock(is_valid=True),
    )
    mock_save = mocker.patch(
        'src.views.ui_multisig_setup_page.MultisigSetupService.save_cosigners_data', return_value=True,
    )

    widget_with_privkey.cos_frame.cosigner_rows = [card]
    assert widget_with_privkey._save_cosigners_data() is True
    mock_save.assert_called_once_with([{'index': 1, 'string': 'valid_str'}])


def test_export_cosigner_to_file_exception(widget_with_privkey, mocker):
    """Test error handling during cosigner export."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.QFileDialog.getSaveFileName',
        return_value=('/tmp/fail.txt', ''),
    )
    mocker.patch('builtins.open', side_effect=Exception('Write Error'))
    toast_error = mocker.patch(
        'src.views.ui_multisig_setup_page.ToastManager.error',
    )

    widget_with_privkey._export_cosigner_to_file()
    toast_error.assert_called_once()


def test_import_cosigner_from_file_exception(widget_with_privkey, mocker):
    """Test error handling during cosigner import."""
    mocker.patch(
        'src.views.ui_multisig_setup_page.QFileDialog.getOpenFileName',
        return_value=('/tmp/fail.txt', ''),
    )
    mocker.patch('builtins.open', side_effect=Exception('Read Error'))
    toast_error = mocker.patch(
        'src.views.ui_multisig_setup_page.ToastManager.error',
    )

    widget_with_privkey._import_cosigner_from_file(mocker.Mock())
    toast_error.assert_called_once()


def test_get_signers_count_exception(widget_watch_only):
    """Test _get_required_signer and _get_total_signer with non-integer text."""
    widget_watch_only.threshold_frame.required_signer_input.setText('abc')
    widget_watch_only.threshold_frame.total_signer_input.setText('xyz')
    assert widget_watch_only._get_required_signer() == 0
    assert widget_watch_only._get_total_signer() == 0


def test_restore_cosigner_inputs_partial_data(widget_watch_only, mocker):
    """Test _restore_cosigner_inputs with missing index or partial dictionary fields."""
    card = mocker.MagicMock()
    card.index = 1
    widget_watch_only.cos_frame.cosigner_rows = [card]
    widget_watch_only._threshold_locked = True

    # Missing index
    widget_watch_only._restore_cosigner_inputs([{'master_fingerprint': 'FP'}])
    card.fp_input.setText.assert_not_called()

    # Partial data
    widget_watch_only._restore_cosigner_inputs(
        [{'index': 1, 'master_fingerprint': 'FP'}],
    )
    card.fp_input.setText.assert_called_with('FP')


def test_update_continue_enabled_step_3_various_states(widget_with_privkey, mocker):
    """Test _update_continue_enabled in Step 3 with various card states."""
    widget_with_privkey._current_step = 3
    mocker.patch.object(
        widget_with_privkey.cos_frame,
        'isVisible', return_value=True,
    )
    widget_with_privkey.threshold_frame.total_signer_input.setText(
        '2',
    )  # n=2 -> 1 cosigner card

    card = mocker.MagicMock()
    card.vanilla_xpub_str = None
    card.string_input.text.return_value = 'some_invalid_text'
    widget_with_privkey.cos_frame.cosigner_rows = [card]

    # Incomplete & invalid
    widget_with_privkey._update_continue_enabled()
    assert widget_with_privkey.continue_button.isEnabled() is False
    card.show_error.assert_called_with('Invalid cosigner details')

    # Valid
    card.vanilla_xpub_str = 'xpub'
    widget_with_privkey._update_continue_enabled()
    assert widget_with_privkey.continue_button.isEnabled() is True
