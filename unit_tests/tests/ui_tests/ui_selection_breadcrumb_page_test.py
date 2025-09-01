# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `SelectionBreadcrumbWidget`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletType
from src.views.ui_selection_breadcrumb_page import SelectionBreadcrumbWidget


@pytest.fixture
def vm():
    """Provide a mocked view model with page navigation stubs."""
    m = MagicMock()
    m.page_navigation = MagicMock()
    return m


@pytest.fixture
def widget(qt_app, vm):
    """Provide the `SelectionBreadcrumbWidget` under test and ensure cleanup."""
    w = SelectionBreadcrumbWidget(vm)
    yield w
    w.close()


def test_offline_flow_skips_security_step(widget: SelectionBreadcrumbWidget):
    """Offline wallet type should skip security step and jump to entry type."""
    # choose offline at step 0
    page0 = widget.steps[0]['widget']
    page0.selected_frame = WalletType.OFFLINE_TYPE_WALLET.value
    widget.handle_continue(0)
    assert widget.current_index == 2  # jumped to entry type


@patch('src.views.ui_selection_breadcrumb_page.WalletModeSummaryDialog.exec', return_value=1)
@patch('src.views.ui_selection_breadcrumb_page.SettingRepository.get_wallet_entry_type', return_value=WalletEntryType.CREATE)
@patch('src.views.ui_selection_breadcrumb_page.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
def test_online_flow_final_navigates_hw_connect(_gk, _ge, _dlg, widget: SelectionBreadcrumbWidget, vm):
    """Online + with private key + create + hardware wallet should navigate to HW connect."""
    # online (default), with_private_key, create, hardware wallet
    widget.steps[0]['widget'].selected_frame = WalletType.ONLINE_TYPE_WALLET.value
    widget.handle_continue(0)
    widget.steps[1]['widget'].selected_frame = WalletAccessType.WITH_PRIVATE_KEY.value
    widget.handle_continue(1)
    widget.steps[2]['widget'].selected_frame = WalletEntryType.CREATE.value
    widget.handle_continue(2)
    widget.steps[3]['widget'].selected_frame = KeyStorageType.HARDWARE_WALLET.value
    widget.handle_continue(3)
    assert vm.page_navigation.hardware_wallet_connect_page.called


@patch('src.views.ui_selection_breadcrumb_page.WalletModeSummaryDialog.exec', return_value=1)
def test_watch_only_flow_routes_to_welcome(_dlg, widget: SelectionBreadcrumbWidget, vm):
    """Watch-only selection should route to welcome page after dialog."""
    # Step 0: online default
    widget.steps[0]['widget'].selected_frame = WalletType.ONLINE_TYPE_WALLET.value
    widget.handle_continue(0)
    # Step 1: choose watch only triggers dialog and welcome
    widget.steps[1]['widget'].selected_frame = WalletAccessType.WATCH_ONLY.value
    widget.handle_continue(1)
    assert vm.page_navigation.welcome_page.called
