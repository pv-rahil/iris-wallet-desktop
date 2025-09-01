"""Unit test for Welcome ui."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QDialog

from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_welcome import WelcomeWidget


@pytest.fixture
def welcome_widget(qtbot):
    """Fixture to create and return an instance of WelcomeWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = WelcomeWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_update_create_status(welcome_widget: WelcomeWidget):
    """Test the update_create_status method of WelcomeWidget."""
    # Test when is_created is True
    welcome_widget.update_create_status(True)
    assert welcome_widget.create_btn.text() == 'Creating...'
    assert not welcome_widget.create_btn.isEnabled()

    # Test when is_created is False
    welcome_widget.update_create_status(False)
    assert welcome_widget.create_btn.text() == 'create_button'
    assert welcome_widget.create_btn.isEnabled()


def test_restore_wallet(welcome_widget: WelcomeWidget):
    """Test the restore_wallet method of WelcomeWidget."""
    with patch('PySide6.QtWidgets.QGraphicsBlurEffect') as mock_blur_effect, \
            patch('src.views.ui_welcome.RestoreMnemonicWidget') as mock_restore_widget, \
            patch('src.views.ui_welcome.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET):
        mock_blur_effect.return_value = MagicMock()
        mock_restore_widget.return_value = MagicMock()

        welcome_widget.restore_wallet()

        assert mock_restore_widget.called


def test_restore_wallet_offline_flow(qtbot):
    """Covers the offline wallet branch with USB sync dialog and restore.
    Ensures we reach welcome_view_model.restore_offline_wallet.
    """
    view_model = MagicMock(MainViewModel=MagicMock())
    view_model.welcome_view_model = MagicMock()
    widget = WelcomeWidget(view_model)
    qtbot.addWidget(widget)
    with patch('src.views.ui_welcome.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET), \
            patch.object(widget.usb_detector, 'detect_usb_drives', return_value=[MagicMock()]), \
            patch('src.views.ui_welcome.USBSyncDialog') as mock_sync_dialog, \
            patch('src.views.ui_welcome.RestoreMnemonicWidget') as mock_restore:
        # Mock the USB dialog to return accepted and provide selections
        sync_instance = MagicMock()
        sync_instance.exec.return_value = QDialog.Accepted
        sync_instance.get_selected_drive.return_value = MagicMock()
        sync_instance.list_usb_zip_files.return_value = ['wallet.zip']
        mock_sync_dialog.return_value = sync_instance

        restore_instance = MagicMock()
        restore_instance.exec.return_value = QDialog.Accepted
        restore_instance.mnemonic_input.text.return_value = 'm'
        restore_instance.xpub_vanilla_input.text.return_value = 'xv'
        restore_instance.xpub_colored_input.text.return_value = 'xc'
        restore_instance.fingerprint_input.text.return_value = 'ff'
        restore_instance.password_input.text.return_value = 'pw'
        mock_restore.return_value = restore_instance

        widget.restore_wallet()
        assert view_model.welcome_view_model.restore_offline_wallet.called


def test_on_create_click_watch_only_accept(qtbot):
    """Test on_create_click with watch-only wallet access type."""
    # Prepare SettingRepository to return WATCH_ONLY at init
    with patch('src.views.ui_welcome.SettingRepository.get_wallet_access_type') as get_access:
        get_access.return_value = WalletAccessType.WATCH_ONLY
        vm = MagicMock()
        vm.welcome_view_model = MagicMock()
        w = WelcomeWidget(vm)
        qtbot.addWidget(w)
        with patch('src.views.ui_welcome.WatchOnlyDialog') as mock_dlg:
            inst = MagicMock()
            inst.exec.return_value = QDialog.Accepted
            mock_dlg.return_value = inst
            w.on_create_click()
            assert vm.welcome_view_model.on_create_click.called


def test_on_create_click_watch_only_reject(qtbot):
    """Test on_create_click with watch-only wallet access type."""
    with patch('src.views.ui_welcome.SettingRepository.get_wallet_access_type') as get_access:
        get_access.return_value = WalletAccessType.WATCH_ONLY
        vm = MagicMock()
        vm.welcome_view_model = MagicMock()
        w = WelcomeWidget(vm)
        qtbot.addWidget(w)
        with patch('src.views.ui_welcome.WatchOnlyDialog') as mock_dlg:
            inst = MagicMock()
            inst.exec.return_value = QDialog.Rejected
            mock_dlg.return_value = inst
            w.on_create_click()
            assert not vm.welcome_view_model.on_create_click.called


def test_loading_screen_show_hide(qtbot):
    """Test show_loading_screen and hide_loading_screen methods."""
    vm = MagicMock()
    vm.welcome_view_model = MagicMock()
    w = WelcomeWidget(vm)
    qtbot.addWidget(w)
    # Patch LoadingTranslucentScreen used in show_loading_screen
    with patch('src.views.ui_welcome.LoadingTranslucentScreen') as mock_loading:
        inst = MagicMock()
        mock_loading.return_value = inst
        w.show_loading_screen()
        assert inst.start.called
        w.hide_loading_screen()
        assert inst.stop.called


def test_update_loading_state(welcome_widget: WelcomeWidget):
    """Test the update_loading_state method of WelcomeWidget."""
    # Test when is_loading is True
    welcome_widget.update_loading_state(True)
    assert not welcome_widget.create_btn.isEnabled()

    # Test when is_loading is False
    welcome_widget.update_loading_state(False)
    assert welcome_widget.create_btn.isEnabled()


def test_handle_message(welcome_widget: WelcomeWidget):
    """Test the handle_message method of WelcomeWidget."""
    with patch('src.views.ui_welcome.ToastManager') as mock_toast_manager:
        welcome_widget.handle_message(ToastPreset.ERROR, 'Test Error Message')
        mock_toast_manager.error.assert_called_once_with('Test Error Message')
        mock_toast_manager.success.assert_not_called()

        welcome_widget.handle_message(
            ToastPreset.SUCCESS, 'Test Success Message',
        )
        mock_toast_manager.error.assert_called_once()
        mock_toast_manager.success.assert_called_once_with(
            'Test Success Message',
        )
