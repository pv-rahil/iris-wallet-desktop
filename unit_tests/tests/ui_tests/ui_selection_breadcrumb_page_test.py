# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-few-public-methods
"""UI tests for `SelectionBreadcrumbWidget`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QWidget

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


def test_get_flow_step_indices_online(widget: SelectionBreadcrumbWidget):
    """Online flow should include all steps 0,1,2,3."""
    widget.selected_titles = [WalletType.ONLINE_TYPE_WALLET.value]
    assert widget.get_flow_step_indices() == [0, 1, 2, 3]


def test_get_flow_step_indices_offline(widget: SelectionBreadcrumbWidget):
    """Offline flow should skip step 1 (security) -> indices 0,2,3."""
    widget.selected_titles = [WalletType.OFFLINE_TYPE_WALLET.value]
    assert widget.get_flow_step_indices() == [0, 2, 3]


def test_get_breadcrumb_idx_offline_mapping(widget: SelectionBreadcrumbWidget):
    """Breadcrumb index mapping should compress indices for offline flow."""
    widget.selected_titles = [WalletType.OFFLINE_TYPE_WALLET.value]
    assert widget.get_breadcrumb_idx(0) == 0
    assert widget.get_breadcrumb_idx(2) == 1
    assert widget.get_breadcrumb_idx(3) == 2
    # Any other falls back to itself
    assert widget.get_breadcrumb_idx(1) == 1


def test_update_breadcrumbs_builds_pending_and_sets_active(widget: SelectionBreadcrumbWidget, monkeypatch):
    """update_breadcrumbs should create committed crumbs + a pending default for current step and set active index."""
    # Simulate selections at step 0 (online) and step 1 (with private key)
    widget.selected_logos = [
        widget.steps[0]['widget'].params.logo_1_path,
    ]
    widget.selected_titles = [
        widget.steps[0]['widget'].params.logo_1_title,
    ]
    widget.current_index = 1  # we're on the next step

    class DummySignal:
        """Dummy signal class for testing."""

        def __init__(self, name):
            """Initialize the signal with a name."""
            self.name = name
            self.connected = []

        def connect(self, cb):
            """Connect a callback to the signal."""
            self.connected.append(cb)

    class DummyBar(QWidget):
        """Dummy breadcrumb bar class for testing."""

        def __init__(self, *_args, **_kwargs):
            """Initialize the DummyBar widget."""
            super().__init__()
            self.crumb_clicked = DummySignal('crumb_clicked')
            self.cls_button = MagicMock()
            self.cls_button.clicked = DummySignal('clicked')
            self.set_calls = []

        def set_breadcrumbs(self, crumbs, active_index):
            """Set the breadcrumbs and active index."""
            self.set_calls.append((crumbs, active_index))

    monkeypatch.setattr(
        'src.views.ui_selection_breadcrumb_page.BreadcrumbBar', DummyBar,
    )

    widget.update_breadcrumbs()

    # _crumbs should have committed first + pending for current
    assert len(widget._crumbs) == 2
    assert widget._crumbs[0]['pending'] is False
    assert widget._crumbs[1]['pending'] is True

    # Breadcrumb widget attached to current page and set_breadcrumbs called with active index matching current_index
    current_page = widget.steps[widget.current_index]['widget']
    assert hasattr(current_page, 'breadcrumb_widget')
    assert isinstance(current_page.breadcrumb_widget, DummyBar)
    assert current_page.breadcrumb_widget.set_calls
    crumbs, active_index = current_page.breadcrumb_widget.set_calls[-1]
    assert crumbs == widget._crumbs
    # active index should correspond to crumb whose step_index == current_index -> pending crumb
    assert active_index == 1


def test_on_breadcrumb_clicked_ignores_pending(widget: SelectionBreadcrumbWidget, monkeypatch):
    """Clicking a pending crumb should do nothing (no navigation)."""
    # Prepare crumbs with a pending at index 1
    widget._crumbs = [
        {'step_index': 0, 'pending': False},
        {'step_index': 1, 'pending': True},
    ]
    widget.current_index = 1
    with patch.object(widget, 'update_breadcrumbs', new=MagicMock()) as mock_update:
        widget.on_breadcrumb_clicked(1)

    # Should not navigate or update
    mock_update.assert_not_called()
    assert widget.current_index == 1


def test_on_breadcrumb_clicked_committed_navigates(widget: SelectionBreadcrumbWidget, monkeypatch):
    """Clicking a committed crumb should update current_index and refresh breadcrumbs."""
    widget._crumbs = [
        {'step_index': 0, 'pending': False},
        {'step_index': 1, 'pending': False},
    ]
    widget.current_index = 1
    with patch.object(widget, 'update_breadcrumbs', new=MagicMock()) as mock_update:
        widget.on_breadcrumb_clicked(0)

    assert widget.current_index == 0
    mock_update.assert_called_once()
