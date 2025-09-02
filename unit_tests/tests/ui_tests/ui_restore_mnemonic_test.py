"""Unit test for Restore Mnemonic ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize

from src.model.enums.enums_model import KeyStorageType
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import MNEMONIC_KEY
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


@pytest.fixture
def restore_mnemonic_widget(qtbot):
    """Fixture to create and return an instance of RestoreMnemonicWidget."""
    mock_navigation = MagicMock()
    view_model = MainViewModel(mock_navigation)
    view_model.backup_view_model = MagicMock()
    widget = RestoreMnemonicWidget(None, view_model)
    qtbot.addWidget(widget)
    return widget


def test_setup_ui_connection(restore_mnemonic_widget):
    """Test that UI connections are set up correctly."""
    restore_mnemonic_widget.cancel_button.clicked.emit()
    restore_mnemonic_widget.password_input.textChanged.emit('password')
    restore_mnemonic_widget.mnemonic_input.textChanged.emit('mnemonic')

    restore_mnemonic_widget.cancel_button.clicked.disconnect()
    restore_mnemonic_widget.password_input.textChanged.disconnect()
    restore_mnemonic_widget.mnemonic_input.textChanged.disconnect()


def test_handle_button_enable(restore_mnemonic_widget, qtbot):
    """Test the enable/disable state of the continue button based on input fields."""
    # Test when mnemonic is visible and both fields are empty
    restore_mnemonic_widget.mnemonic_visibility = True
    restore_mnemonic_widget.mnemonic_input.setText('')
    restore_mnemonic_widget.password_input.setText('')
    restore_mnemonic_widget.handle_button_enable()
    assert not restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is visible and both fields are filled
    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_button_enable()
    assert restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is not visible and password is empty
    restore_mnemonic_widget.mnemonic_visibility = False
    restore_mnemonic_widget.password_input.setText('')
    restore_mnemonic_widget.handle_button_enable()
    assert not restore_mnemonic_widget.continue_button.isEnabled()

    # Test when mnemonic is not visible and password is filled
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_button_enable()
    assert restore_mnemonic_widget.continue_button.isEnabled()


def test_retranslate_ui(restore_mnemonic_widget, qtbot):
    """Test that UI texts are set correctly."""
    restore_mnemonic_widget.retranslate_ui()

    assert restore_mnemonic_widget.mnemonic_detail_text_label.text(
    ) == 'enter_mnemonic_phrase_info'
    assert restore_mnemonic_widget.mnemonic_input.placeholderText() == 'input_phrase'
    assert restore_mnemonic_widget.cancel_button.text() == 'cancel'
    assert restore_mnemonic_widget.continue_button.text() == 'continue'
    assert restore_mnemonic_widget.password_input.placeholderText() == 'enter_wallet_password'


def test_handle_on_keyring_toggle_enable(restore_mnemonic_widget, qtbot):
    """Test that enable_keyring is called with correct arguments and dialog closes."""
    restore_mnemonic_widget._view_model.setting_view_model.enable_keyring = MagicMock()

    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.handle_on_keyring_toggle_enable()

    restore_mnemonic_widget._view_model.setting_view_model.enable_keyring.assert_called_once_with(
        password='password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_restore_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on restore_page."""
    restore_mnemonic_widget.origin_page = 'restore_page'
    restore_mnemonic_widget.restore_wallet = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.restore_wallet.assert_called_once()
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_setting_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on setting_page."""
    restore_mnemonic_widget.origin_page = 'setting_page'
    restore_mnemonic_widget.handle_on_keyring_toggle_enable = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.handle_on_keyring_toggle_enable.assert_called_once()
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_backup_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on backup_page."""
    restore_mnemonic_widget.origin_page = 'backup_page'
    restore_mnemonic_widget._view_model.backup_view_model.backup_when_keyring_unaccessible = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget._view_model.backup_view_model.backup_when_keyring_unaccessible.assert_called_once_with(
        mnemonic='mnemonic', password='password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_on_close(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on on_close."""
    restore_mnemonic_widget.origin_page = 'on_close'
    restore_mnemonic_widget.on_continue = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.on_continue.emit.assert_called_once_with(
        'mnemonic', 'password',
    )
    assert not restore_mnemonic_widget.isVisible()


def test_on_continue_button_click_setting_card(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked on setting_card."""
    restore_mnemonic_widget.origin_page = 'setting_card'
    restore_mnemonic_widget.accept = MagicMock()

    restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
    restore_mnemonic_widget.password_input.setText('password')
    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.accept.assert_called_once()


def test_on_continue_button_click_unknown_page(restore_mnemonic_widget, qtbot):
    """Test behavior when 'continue' button is clicked with unknown origin page."""
    restore_mnemonic_widget.origin_page = 'unknown_page'
    mock_toast = MagicMock()

    with patch('src.views.ui_restore_mnemonic.ToastManager', mock_toast):
        restore_mnemonic_widget.mnemonic_input.setText('mnemonic')
        restore_mnemonic_widget.password_input.setText('password')
        restore_mnemonic_widget.on_continue_button_click()

        mock_toast.error.assert_called_once_with('Unknown origin page')


def test_on_click_cancel(restore_mnemonic_widget, qtbot):
    """Test that the dialog closes when cancel button is clicked."""
    restore_mnemonic_widget.close = MagicMock()

    restore_mnemonic_widget.on_click_cancel()

    restore_mnemonic_widget.close.assert_called_once()


def test_handle_mnemonic_input_visibility(restore_mnemonic_widget):
    """Test the handle_mnemonic_input_visibility method according to new logic."""
    # Mock relevant widgets and methods
    restore_mnemonic_widget.mnemonic_input = MagicMock()
    restore_mnemonic_widget.mnemonic_detail_text_label = MagicMock()
    restore_mnemonic_widget.mnemonic_frame = MagicMock()
    restore_mnemonic_widget.setMaximumSize = MagicMock()
    restore_mnemonic_widget.maximumSize = MagicMock(
        return_value=QSize(370, 292),
    )

    # Test when mnemonic_visibility is False
    restore_mnemonic_widget.mnemonic_visibility = False
    restore_mnemonic_widget.handle_mnemonic_input_visibility()

    restore_mnemonic_widget.mnemonic_input.hide.assert_called_once()
    restore_mnemonic_widget.mnemonic_detail_text_label.setMaximumSize.assert_called_once_with(
        QSize(295, 50),
    )
    restore_mnemonic_widget.mnemonic_detail_text_label.setText.assert_called_once()
    restore_mnemonic_widget.mnemonic_frame.setFixedHeight.assert_called_once_with(
        200,
    )
    # Should not be called in False branch
    restore_mnemonic_widget.setMaximumSize.assert_not_called()

    # Reset mocks
    restore_mnemonic_widget.mnemonic_input.reset_mock()
    restore_mnemonic_widget.mnemonic_detail_text_label.setMaximumSize.reset_mock()
    restore_mnemonic_widget.mnemonic_detail_text_label.setText.reset_mock()
    restore_mnemonic_widget.mnemonic_frame.setFixedHeight.reset_mock()
    restore_mnemonic_widget.setMaximumSize.reset_mock()

    # Test when mnemonic_visibility is True
    restore_mnemonic_widget.mnemonic_visibility = True
    restore_mnemonic_widget.handle_mnemonic_input_visibility()

    restore_mnemonic_widget.setMaximumSize.assert_called_once_with(
        QSize(370, 292),
    )
    restore_mnemonic_widget.mnemonic_input.show.assert_called_once()
    restore_mnemonic_widget.mnemonic_detail_text_label.setMaximumSize.assert_not_called()
    restore_mnemonic_widget.mnemonic_detail_text_label.setText.assert_not_called()
    restore_mnemonic_widget.mnemonic_frame.setFixedHeight.assert_not_called()


def test_handle_mnemonic_input_visibility_hardware_or_watch_only(restore_mnemonic_widget):
    """Cover branch when hardware/watch-only: hide mnemonic, show xpub/fingerprint, adjust sizes."""
    restore_mnemonic_widget.is_hardware_wallet = True
    restore_mnemonic_widget.is_watch_only_wallet = False

    restore_mnemonic_widget.mnemonic_input = MagicMock()
    restore_mnemonic_widget.xpub_vanilla_input = MagicMock()
    restore_mnemonic_widget.xpub_colored_input = MagicMock()
    restore_mnemonic_widget.fingerprint_input = MagicMock()
    restore_mnemonic_widget.mnemonic_detail_text_label = MagicMock()
    restore_mnemonic_widget.resize = MagicMock()

    restore_mnemonic_widget.handle_mnemonic_input_visibility()

    restore_mnemonic_widget.mnemonic_input.hide.assert_called_once()
    restore_mnemonic_widget.xpub_vanilla_input.show.assert_called_once()
    restore_mnemonic_widget.xpub_colored_input.show.assert_called_once()
    restore_mnemonic_widget.fingerprint_input.show.assert_called_once()
    restore_mnemonic_widget.mnemonic_detail_text_label.setMaximumSize.assert_called_once_with(
        QSize(295, 60),
    )
    restore_mnemonic_widget.resize.assert_called_once_with(400, 500)


def test_on_continue_button_click_welcome_page_calls_store(restore_mnemonic_widget):
    """Cover welcome_page branch which stores xpub/mnemonic via helper."""
    restore_mnemonic_widget.origin_page = 'welcome_page'
    restore_mnemonic_widget.store_xpub_and_mnemonic = MagicMock()

    restore_mnemonic_widget.on_continue_button_click()

    restore_mnemonic_widget.store_xpub_and_mnemonic.assert_called_once()


def test_restore_wallet_hardware_watch_only_calls_restore_with_xpubs(restore_mnemonic_widget):
    """Cover restore path for hardware/watch-only wallets passing xpubs/fingerprint/password."""
    restore_mnemonic_widget.is_hardware_wallet = True
    restore_mnemonic_widget.is_watch_only_wallet = False
    restore_mnemonic_widget.accept = MagicMock()
    restore_mnemonic_widget._view_model.restore_view_model = MagicMock()

    restore_mnemonic_widget.xpub_vanilla_input = MagicMock()
    restore_mnemonic_widget.xpub_colored_input = MagicMock()
    restore_mnemonic_widget.fingerprint_input = MagicMock()
    restore_mnemonic_widget.password_input = MagicMock()
    restore_mnemonic_widget.xpub_vanilla_input.text.return_value = 'xpubv'
    restore_mnemonic_widget.xpub_colored_input.text.return_value = 'xpubc'
    restore_mnemonic_widget.fingerprint_input.text.return_value = 'fpr'
    restore_mnemonic_widget.password_input.text.return_value = 'pwd'

    restore_mnemonic_widget.restore_wallet()

    restore_mnemonic_widget.accept.assert_called_once()
    restore_mnemonic_widget._view_model.restore_view_model.restore.assert_called_once_with(
        mnemonic=None, password='pwd', xpub_vanilla='xpubv', xpub_colored='xpubc', fingerprint='fpr',
    )


def test_restore_wallet_software_calls_restore_with_mnemonic(restore_mnemonic_widget):
    """Cover restore path for software wallets passing mnemonic/password."""
    restore_mnemonic_widget.is_hardware_wallet = False
    restore_mnemonic_widget.is_watch_only_wallet = False
    restore_mnemonic_widget.accept = MagicMock()
    restore_mnemonic_widget._view_model.restore_view_model = MagicMock()

    restore_mnemonic_widget.mnemonic_input = MagicMock()
    restore_mnemonic_widget.password_input = MagicMock()
    restore_mnemonic_widget.mnemonic_input.text.return_value = 'mn'
    restore_mnemonic_widget.password_input.text.return_value = 'pwd'

    restore_mnemonic_widget.restore_wallet()

    restore_mnemonic_widget.accept.assert_called_once()
    restore_mnemonic_widget._view_model.restore_view_model.restore.assert_called_once_with(
        mnemonic='mn', password='pwd',
    )


def test_store_xpub_and_mnemonic_on_device(restore_mnemonic_widget, mocker):
    """Cover ON_DEVICE storage path: derive keys, set values, encrypt and write mnemonic, accept dialog."""
    # Patch storage type to ON_DEVICE
    mocker.patch(
        'src.views.ui_restore_mnemonic.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.ON_DEVICE,
    )
    mocker.patch(
        'src.views.ui_restore_mnemonic.SettingRepository.get_wallet_network', return_value='regtest',
    )
    mocker.patch(
        'src.views.ui_restore_mnemonic.get_bitcoin_network_from_enum',
        return_value='regtest-net',
    )

    # Prepare restored keys
    restored = SimpleNamespace(
        account_xpub_vanilla='vx', account_xpub_colored='cx', master_fingerprint='ff',
    )
    mocker.patch(
        'src.views.ui_restore_mnemonic.CommonOperationRepository.restore_keys', return_value=restored,
    )

    local_store = mocker.patch('src.views.ui_restore_mnemonic.local_store')
    mnemonic_store = mocker.patch(
        'src.views.ui_restore_mnemonic.mnemonic_store',
    )
    app_paths = mocker.patch('src.views.ui_restore_mnemonic.app_paths')
    app_paths.mnemonic_file_path = '/tmp/mn'

    restore_mnemonic_widget.mnemonic_input = MagicMock()
    restore_mnemonic_widget.password_input = MagicMock()
    restore_mnemonic_widget.mnemonic_input.text.return_value = 'mn'
    restore_mnemonic_widget.password_input.text.return_value = 'pwd'
    restore_mnemonic_widget.accept = MagicMock()

    mnemonic_store.encrypt.return_value = 'encmn'

    restore_mnemonic_widget.store_xpub_and_mnemonic()

    local_store.set_value.assert_any_call(ACCOUNT_XPUB_VANILLA, 'vx')
    local_store.set_value.assert_any_call(ACCOUNT_XPUB_COLORED, 'cx')
    local_store.set_value.assert_any_call(MASTER_FINGERPRINT, 'ff')
    mnemonic_store.encrypt.assert_called_once_with(
        password='pwd', mnemonic='mn',
    )
    local_store.write_to_file.assert_called_once_with(
        file_name=MNEMONIC_KEY, file_path='/tmp/mn', value='encmn',
    )
    restore_mnemonic_widget.accept.assert_called_once()


def test_store_xpub_and_mnemonic_manual_values(restore_mnemonic_widget, mocker):
    """Cover non-ON_DEVICE path: store manual xpubs and fingerprint, accept dialog."""
    mocker.patch(
        'src.views.ui_restore_mnemonic.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )

    local_store = mocker.patch('src.views.ui_restore_mnemonic.local_store')

    restore_mnemonic_widget.xpub_vanilla_input = MagicMock()
    restore_mnemonic_widget.xpub_colored_input = MagicMock()
    restore_mnemonic_widget.fingerprint_input = MagicMock()
    restore_mnemonic_widget.xpub_vanilla_input.text.return_value = 'vx'
    restore_mnemonic_widget.xpub_colored_input.text.return_value = 'cx'
    restore_mnemonic_widget.fingerprint_input.text.return_value = 'ff'
    restore_mnemonic_widget.accept = MagicMock()

    restore_mnemonic_widget.store_xpub_and_mnemonic()

    local_store.set_value.assert_any_call(ACCOUNT_XPUB_VANILLA, 'vx')
    local_store.set_value.assert_any_call(ACCOUNT_XPUB_COLORED, 'cx')
    local_store.set_value.assert_any_call(MASTER_FINGERPRINT, 'ff')
    restore_mnemonic_widget.accept.assert_called_once()
