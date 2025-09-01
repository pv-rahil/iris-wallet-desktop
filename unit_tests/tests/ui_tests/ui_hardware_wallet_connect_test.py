# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `HardwareWalletConnectWidget`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QDialog

from src.views.ui_hardware_wallet_connect import HardwareWalletConnectWidget


@pytest.fixture
def vm():
    """Provide a mocked view model with navigation stubs."""
    m = MagicMock()
    m.page_navigation = MagicMock()
    m.restore_view_model = MagicMock()
    return m


@pytest.fixture
def widget(qt_app, vm):
    """Provide the `HardwareWalletConnectWidget` under test and ensure cleanup."""
    w = HardwareWalletConnectWidget(vm)
    yield w
    w.close()


def test_initial_state(widget: HardwareWalletConnectWidget):
    """Continue button is disabled initially before device option selection."""
    assert widget.continue_btn.isEnabled() is False


def test_click_ledger_enables_continue(widget: HardwareWalletConnectWidget):
    """Selecting a device option should enable Continue."""
    # simulate clicking ledger option
    handler = widget.make_option_click_handler(widget.ledger_btn, 'Ledger')
    handler()
    assert widget.continue_btn.isEnabled() is True


@patch('src.views.ui_hardware_wallet_connect.RestoreMnemonicWidget.exec', return_value=QDialog.Accepted)
@patch('src.views.ui_hardware_wallet_connect.HWDeviceSelectionDialog.exec', return_value=QDialog.Accepted)
@patch('src.views.ui_hardware_wallet_connect.SettingRepository.get_wallet_entry_type', return_value=None)
def test_show_device_dialog_navigate_welcome_for_create(_entry, _hw, _restore, widget: HardwareWalletConnectWidget, vm):
    """Create flow: after dialogs accepted, navigate to welcome page."""
    handler = widget.make_option_click_handler(widget.ledger_btn, 'Ledger')
    handler()
    widget.show_device_dialog()
    assert vm.page_navigation.welcome_page.called


@patch('src.views.ui_hardware_wallet_connect.HWDeviceSelectionDialog.exec', return_value=QDialog.Accepted)
@patch('src.views.ui_hardware_wallet_connect.SettingRepository.get_wallet_entry_type')
def test_show_device_dialog_load_flow_calls_welcome(_get_entry, _hw, widget: HardwareWalletConnectWidget, vm):
    """Load flow: navigates to welcome page after restore dialog."""
    _get_entry.return_value = MagicMock()  # treat as WalletEntryType.LOAD
    handler = widget.make_option_click_handler(widget.ledger_btn, 'Ledger')
    handler()
    with patch('src.views.ui_hardware_wallet_connect.RestoreMnemonicWidget.exec', return_value=QDialog.Accepted):
        widget.show_device_dialog()
    assert vm.page_navigation.welcome_page.called


def test_handle_close_calls_selection_page(widget: HardwareWalletConnectWidget, vm):
    """Close should route back to selection page."""
    widget.handle_close()
    assert vm.page_navigation.selection_page.called
