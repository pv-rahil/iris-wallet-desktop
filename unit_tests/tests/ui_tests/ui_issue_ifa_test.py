# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for IssueIFAWidget."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.rgb_model import RgbAssetPageLoadModel
from src.views.ui_issue_ifa import IssueIFAWidget


@pytest.fixture
def vm_mock():
    """Mock for IssueIFAViewModel."""
    vm = MagicMock()
    # Nested VMs & signals used
    issue_vm = MagicMock()
    issue_vm.issue_button_clicked = MagicMock()
    issue_vm.issue_button_clicked.connect = lambda *_a, **_k: None
    issue_vm.is_issued = MagicMock()
    issue_vm.is_issued.connect = lambda *_a, **_k: None
    vm.issue_ifa_asset_view_model = issue_vm

    utxo_vm = MagicMock()
    utxo_vm.hw_dialog_update = MagicMock()
    utxo_vm.hw_dialog_update.connect = lambda *_a, **_k: None
    utxo_vm.utxo_created = MagicMock()
    utxo_vm.utxo_created.connect = lambda *_a, **_k: None
    utxo_vm.unsigned_psbt = MagicMock()
    utxo_vm.unsigned_psbt.connect = lambda *_a, **_k: None
    vm.utxo_creation_view_model = utxo_vm

    vm.page_navigation = MagicMock()
    return vm


@pytest.fixture
def widget(qt_app, vm_mock):
    """Test fixture for IssueIFAWidget."""
    with patch('src.views.ui_issue_ifa.load_stylesheet', return_value=''), \
            patch('src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance'):
        w = IssueIFAWidget(vm_mock)
        yield w
        w.close()


def test_handle_button_enabled_enables_only_when_all_present(widget: IssueIFAWidget):
    """Test that the issue button is enabled only when all required fields are present."""
    widget.inflatables_short_identifier_input.setText('TCK')
    widget.inflatables_asset_name_input.setText('Name')
    widget.inflatables_issue_amount_input.setText('0')
    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled() is False

    widget.inflatables_issue_amount_input.setText('10')
    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled() is True


def test_on_issue_ifa_click_calls_vm_and_draft(widget: IssueIFAWidget, vm_mock):
    """Test that on_issue_ifa_click calls create_issue_asset_draft."""
    widget.inflatables_short_identifier_input.setText('abc')
    widget.inflatables_asset_name_input.setText('MyAsset')
    widget.inflatables_issue_amount_input.setText('25')
    widget.inflatables_total_supply_input.setText('50')

    with patch.object(widget, 'create_issue_inflatables_asset_draft') as draft:
        widget.on_issue_ifa_click()
        draft.assert_called_once()
        vm_mock.issue_ifa_asset_view_model.issue_ifa_asset.assert_called_once()


def test_secondary_issuance_prefill_and_locks(qt_app, vm_mock):
    """Test that secondary issuance prefill and locks work correctly."""
    params = RgbAssetPageLoadModel(
        asset_id='TCK', asset_name='AssetX',
        image_path=None, asset_type='NIA', is_secondary_issuance=True,
    )
    with patch('src.views.ui_issue_ifa.load_stylesheet', return_value=''):
        w = IssueIFAWidget(vm_mock, params=params)
        try:
            w.show()
            assert w.secondary_issuance is True
            # Name locked, total supply hidden
            assert w.inflatables_asset_name_input.isReadOnly()
            assert w.inflatables_total_supply_title_widget.isHidden()
            assert w.inflatables_total_supply_input.isHidden()
        finally:
            w.close()


def test_handle_ifa_issue_uses_existing_psbt_or_creates(vm_mock):
    """Test that handle_ifa_issue uses existing PSBT or creates a new one."""
    with patch('src.views.ui_issue_ifa.load_stylesheet', return_value=''), \
            patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        w = IssueIFAWidget(vm_mock)
        try:
            # Make widget visible so handle_ifa_issue doesn't return early
            w.show()
            # Use correct purpose 'issue_asset_ifa' (not 'issue_asset')
            vm_mock.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'
            get_sess.return_value = MagicMock(
                list_psbt=lambda signed: [
                    {'purpose': 'issue_asset_ifa', 'psbt': 'P1'},
                ],
            )
            with patch.object(w, 'show_ifa_psbt_page') as show:
                w.handle_ifa_issue()
                show.assert_called_once_with('P1')
            # Case 2: not present -> create_utxos_begin called
            get_sess.return_value = MagicMock(list_psbt=lambda signed: [])
            vm_mock.utxo_creation_view_model.create_utxos_begin.reset_mock()
            w.handle_ifa_issue()
            assert vm_mock.utxo_creation_view_model.create_utxos_begin.called
            args, kwargs = vm_mock.utxo_creation_view_model.create_utxos_begin.call_args
            if args:
                assert args[0] == 'issue_asset_ifa'
            else:
                assert kwargs.get('purpose') == 'issue_asset_ifa'
        finally:
            w.close()
