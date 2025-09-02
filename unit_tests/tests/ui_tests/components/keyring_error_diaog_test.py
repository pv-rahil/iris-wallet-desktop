"""Unit test for Keyring error dialog."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import call
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt

from src.model.common_operation_model import KeyringDialogModel
from src.utils.custom_exception import CommonException
from src.views.components.keyring_error_dialog import KeyringErrorDialog


@pytest.fixture
def keyring_error_dialog_widget(qtbot):
    """Fixture to create and return an instance of KeyringErrorDialog."""
    model = KeyringDialogModel(
        mnemonic='mnemonic',
        password='password',
        navigate_to=lambda: None,
        originating_page='settings_page',
    )
    widget = KeyringErrorDialog(model)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def keyring_error_dialog(qtbot):
    """Set up the test environment for KeyringErrorDialog."""
    model = KeyringDialogModel(
        mnemonic='test mnemonic',
        password='test password',
        originating_page=None,
    )
    dialog = KeyringErrorDialog(model)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def watch_only_dialog_widget(qtbot):
    """Create a watch-only dialog (mnemonic None, xpubs present)."""
    model = KeyringDialogModel(
        mnemonic=None,
        password='pw',
        xpub_vanilla='x' * 64,
        xpub_colored='y' * 64,
        master_fingerprint='deadbeef',
        originating_page='settings_page',
        navigate_to=lambda: None,
    )
    dlg = KeyringErrorDialog(model)
    qtbot.addWidget(dlg)
    return dlg


def test_dialog_initialization(keyring_error_dialog):
    """Test if dialog initializes with correct values and states."""
    dialog = keyring_error_dialog

    # Check if the dialog initializes correctly
    assert dialog.mnemonic_value_label.text() == 'test mnemonic'
    assert dialog.wallet_password_value.text() == 'test password'
    # The Continue button should be disabled initially
    assert dialog.continue_button.isEnabled() is False
    # The cancel button should be hidden initially
    assert dialog.cancel_button.isHidden()


def test_continue_button_state_on_checkbox_check(keyring_error_dialog, qtbot):
    """Test continue button state changes based on checkbox."""
    dialog = keyring_error_dialog

    # Initially, the Continue button should be disabled
    assert dialog.continue_button.isEnabled() is False

    # Simulate checking the checkbox to enable the Continue button
    qtbot.mouseClick(dialog.check_box, Qt.LeftButton)
    assert dialog.continue_button.isEnabled() is True

    # Simulate unchecking the checkbox to disable the Continue button
    qtbot.mouseClick(dialog.check_box, Qt.LeftButton)
    assert dialog.continue_button.isEnabled() is False


@patch('src.views.components.keyring_error_dialog.copy_text')
def test_on_click_copy_button_mnemonic(mock_copy_text, keyring_error_dialog_widget: KeyringErrorDialog):
    """Test `on_click_copy_button` for copying mnemonic text."""
    keyring_error_dialog_widget.on_click_copy_button('mnemonic_text')

    mock_copy_text.assert_called_once_with(
        keyring_error_dialog_widget.mnemonic_value_label,
    )


@patch('src.views.components.keyring_error_dialog.copy_text')
def test_on_click_copy_button_password(mock_copy_text, keyring_error_dialog_widget: KeyringErrorDialog):
    """Test `on_click_copy_button` for copying password text."""
    keyring_error_dialog_widget.on_click_copy_button('password_text')

    mock_copy_text.assert_called_once_with(
        keyring_error_dialog_widget.wallet_password_value,
    )


def test_on_click_cancel(keyring_error_dialog, qtbot):
    """Test cancel button click functionality."""
    dialog = keyring_error_dialog
    # Make cancel button visible for this test
    dialog.originating_page = 'settings_page'
    dialog.handle_disable_keyring()
    # Simulate clicking the cancel button
    qtbot.mouseClick(dialog.cancel_button, Qt.LeftButton)

    # Ensure the dialog closes
    assert not dialog.isVisible()


def test_handle_disable_keyring(keyring_error_dialog, qtbot):
    """Test keyring disable handling for different pages."""
    dialog = keyring_error_dialog
    dialog.originating_page = 'settings_page'

    # Check if the cancel button is shown when on the settings page
    dialog.handle_disable_keyring()
    assert not dialog.cancel_button.isHidden()

    # Check if the cancel button is hidden on other pages
    dialog.originating_page = 'some_other_page'
    dialog.handle_disable_keyring()
    assert dialog.cancel_button.isHidden()


def test_on_click_continue_when_origin_is_settings_page(keyring_error_dialog, qtbot, mocker):
    """Test continue button click when originating from settings page."""
    dialog = keyring_error_dialog
    # Simulate that the originating page is 'settings_page'
    dialog.originating_page = 'settings_page'
    dialog.continue_button.setEnabled(True)
    # Mock the methods called inside `on_click_continue`
    mock_handle_when_origin_setting_page = mocker.patch.object(
        dialog, 'handle_when_origin_setting_page', autospec=True,
    )
    mock_handle_when_origin_page_set_wallet = mocker.patch.object(
        dialog, 'handle_when_origin_page_set_wallet', autospec=True,
    )

    # Check if the continue button is enabled before clicking it (additional check)
    assert dialog.continue_button.isEnabled()

    # Simulate clicking the continue button
    qtbot.mouseClick(dialog.continue_button, Qt.LeftButton)

    # Ensure the correct method is called
    # Ensure it called handle_when_origin_setting_page
    mock_handle_when_origin_setting_page.assert_called_once()
    # Ensure handle_when_origin_page_set_wallet was not called
    mock_handle_when_origin_page_set_wallet.assert_not_called()


def test_on_click_continue_when_origin_is_set_wallet_page(keyring_error_dialog, qtbot, mocker):
    """Test continue button click when originating from wallet page."""
    dialog = keyring_error_dialog
    # Simulate that the originating page is 'set_wallet_page'
    dialog.originating_page = 'set_wallet_page'

    # Mock the methods called inside `on_click_continue`
    mock_handle_when_origin_setting_page = mocker.patch.object(
        dialog, 'handle_when_origin_setting_page', autospec=True,
    )
    mock_handle_when_origin_page_set_wallet = mocker.patch.object(
        dialog, 'handle_when_origin_page_set_wallet', autospec=True,
    )

    # Simulate clicking the continue button
    qtbot.mouseClick(dialog.continue_button, Qt.LeftButton)

    # Add a print statement or assert to confirm the logic is executed
    dialog.on_click_continue()
    # Ensure the correct method is called
    # Ensure handle_when_origin_setting_page was not called
    mock_handle_when_origin_setting_page.assert_not_called()
    # Ensure it called handle_when_origin_page_set_wallet
    mock_handle_when_origin_page_set_wallet.assert_called_once()


def test_handle_when_origin_page_set_wallet_success(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_page_set_wallet when checkbox is checked."""
    # Mock dependencies
    mock_set_keyring = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mock_navigate = mocker.MagicMock()
    keyring_error_dialog_widget.navigate_to = mock_navigate
    mock_close = mocker.patch.object(keyring_error_dialog_widget, 'close')

    # Set checkbox to checked
    keyring_error_dialog_widget.check_box.setChecked(True)

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_page_set_wallet()

    # Verify the success path
    mock_set_keyring.assert_called_once_with(status=True)
    mock_navigate.assert_called_once()
    mock_close.assert_called_once()


def test_handle_when_origin_page_set_wallet_unchecked(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_page_set_wallet when checkbox is unchecked."""
    # Mock dependencies
    mock_clear_settings = mocker.patch(
        'src.utils.local_store.local_store.clear_settings',
    )
    mock_close = mocker.patch.object(keyring_error_dialog_widget, 'close')
    mock_exit = mocker.patch('PySide6.QtWidgets.QApplication.instance')

    # Set checkbox to unchecked
    keyring_error_dialog_widget.check_box.setChecked(False)

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_page_set_wallet()

    # Verify the unchecked path
    mock_clear_settings.assert_called_once()
    mock_close.assert_called_once()
    mock_exit.return_value.exit.assert_called_once()


def test_handle_when_origin_page_set_wallet_common_exception(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_page_set_wallet when CommonException is raised."""
    # Mock dependencies
    mock_set_keyring = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
        side_effect=CommonException('Test error'),
    )
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )

    # Set checkbox to checked
    keyring_error_dialog_widget.check_box.setChecked(True)

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_page_set_wallet()

    # Verify exception handling
    mock_set_keyring.assert_called_once_with(status=True)
    mock_toast_manager.assert_called_once()


def test_handle_when_origin_page_set_wallet_general_exception(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_page_set_wallet when general Exception is raised."""
    # Mock dependencies
    test_error = Exception('Something went wrong')
    mock_set_keyring = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
        side_effect=test_error,
    )
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )

    # Set checkbox to checked
    keyring_error_dialog_widget.check_box.setChecked(True)

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_page_set_wallet()

    # Verify exception handling
    mock_set_keyring.assert_called_once_with(status=True)
    mock_toast_manager.assert_called_once_with(test_error)


def test_watch_only_initialization_and_layout(watch_only_dialog_widget):
    """Watch-only dialog should hide mnemonic and show xpub/fingerprint frames."""
    dlg = watch_only_dialog_widget
    assert dlg.is_watch_only is True
    assert dlg.mnemonic_frame.isHidden() is True
    assert dlg.xpub_vanilla_frame.isHidden() is False
    assert dlg.xpub_colored_frame.isHidden() is False
    assert dlg.fingerprint_frame.isHidden() is False


@patch('src.views.components.keyring_error_dialog.copy_text')
def test_watch_only_copy_buttons(mock_copy_text, watch_only_dialog_widget):
    """Copy buttons should forward correct targets for watch-only data."""
    dlg = watch_only_dialog_widget
    # xpub vanilla uses raw string value
    dlg.on_click_copy_button('xpub_vanilla')
    # xpub colored uses raw string value
    dlg.on_click_copy_button('xpub_colored')
    # fingerprint uses QLabel widget value label
    dlg.on_click_copy_button('fingerprint')
    calls = [
        call(dlg._xpub_vanilla),
        call(dlg._xpub_colored),
        call(dlg.fingerprint_value),
    ]
    # Order is preserved as above
    mock_copy_text.assert_has_calls(calls, any_order=False)


def test_retranslate_ui_watch_only_sets_values(watch_only_dialog_widget):
    """retranslate_ui populates labels; xpub values are truncated."""
    dlg = watch_only_dialog_widget
    dlg.retranslate_ui()
    assert dlg.xpub_vanilla_value.text() == dlg._truncate_xpub(dlg._xpub_vanilla)
    assert dlg.xpub_colored_value.text() == dlg._truncate_xpub(dlg._xpub_colored)
    assert dlg.fingerprint_value.text() != ''


def test_truncate_xpub_helper():
    """_truncate_xpub returns unchanged for short, truncated for long."""
    # Create a lightweight dialog instance via minimal model
    model = KeyringDialogModel(mnemonic='m', password='p')
    dlg = KeyringErrorDialog(model)
    short = 'abcd'
    long = 'a' * 40
    assert dlg._truncate_xpub(short) == short
    truncated = dlg._truncate_xpub(long)
    assert '...' in truncated
    assert truncated.startswith(long[:12])
    assert truncated.endswith(long[-12:])


def test_handle_disable_keyring_watch_only_sets_info_and_cancel(watch_only_dialog_widget):
    """When on settings page, info text is set and cancel is shown for watch-only."""
    dlg = watch_only_dialog_widget
    dlg.originating_page = 'settings_page'
    dlg.handle_disable_keyring()
    assert not dlg.cancel_button.isHidden()
    assert dlg.info_label.text() != ''


def test_handle_when_origin_setting_page_success(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_setting_page success path."""
    # Mock dependencies
    mock_network = mocker.MagicMock()
    mock_network.value = 'test_network'
    mock_get_network = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        return_value=mock_network,
    )
    mock_delete_value = mocker.patch(
        'src.views.components.keyring_error_dialog.delete_value',
    )
    mock_set_keyring = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.set_keyring_status',
    )
    mock_close = mocker.patch.object(keyring_error_dialog_widget, 'close')
    mock_navigate = mocker.MagicMock()
    keyring_error_dialog_widget.navigate_to = mock_navigate

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_setting_page()

    # Verify all calls
    mock_get_network.assert_called_once()
    # Should be called 4 times for different keys
    assert mock_delete_value.call_count == 3
    mock_set_keyring.assert_called_once_with(status=True)
    mock_close.assert_called_once()
    mock_navigate.assert_called_once()


def test_handle_when_origin_setting_page_common_exception(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_setting_page when CommonException is raised."""
    # Mock dependencies
    test_error = CommonException('Something went wrong')
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=test_error,
    )
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_setting_page()

    # Verify exception handling
    mock_toast_manager.assert_called_once_with('Something went wrong')


def test_handle_when_origin_setting_page_general_exception(keyring_error_dialog_widget, mocker):
    """Test handle_when_origin_setting_page when general Exception is raised."""
    # Mock dependencies
    test_error = Exception('Something went wrong')
    mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
        side_effect=test_error,
    )
    mock_error = mocker.patch.object(keyring_error_dialog_widget, 'error')
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )

    # Call the method
    keyring_error_dialog_widget.handle_when_origin_setting_page()

    # Verify exception handling
    mock_error.emit.assert_called_once_with('Something went wrong')
    mock_toast_manager.assert_called_once_with(test_error)
