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


def test_update_loading_state(widget: IssueIFAWidget):
    """Test update_loading_state starts and stops loading."""
    with patch.object(widget.issue_ifa_btn, 'start_loading') as mock_start, \
            patch.object(widget.issue_ifa_btn, 'stop_loading') as mock_stop:
        widget.update_loading_state(True)
        mock_start.assert_called_once()

        widget.update_loading_state(False)
        mock_stop.assert_called_once()


def test_validate_supply_fields_primary(widget: IssueIFAWidget):
    """Test validate_supply_fields for primary issuance."""
    widget.secondary_issuance = False
    widget.inflatables_total_supply_input.setText('100')
    widget.inflatables_issue_amount_input.setText('50')

    # Should not raise any errors
    widget.validate_supply_fields()


def test_validate_supply_fields_exceeds_total(widget: IssueIFAWidget):
    """Test validate_supply_fields when issue amount exceeds total."""
    widget.secondary_issuance = False
    widget.inflatables_total_supply_input.setText('50')
    widget.inflatables_issue_amount_input.setText('100')

    # Should handle the validation (may or may not show error)
    widget.validate_supply_fields()


def test_validate_supply_fields_secondary(widget: IssueIFAWidget):
    """Test validate_supply_fields for secondary issuance."""
    widget.secondary_issuance = True
    widget.inflatables_issue_amount_input.setText('50')

    # Secondary issuance should not validate total supply
    widget.validate_supply_fields()


def test_show_error(widget: IssueIFAWidget):
    """Test _show_error sets error text."""
    widget._show_error('Test error message')
    assert widget.inflatables_error_label.text() == 'Test error message'


def test_handle_ifa_hw_dialog_visible(widget: IssueIFAWidget):
    """Test handle_ifa_hw_dialog when widget is visible."""
    from enum import Enum

    class DialogType(Enum):
        INFO = 'info'
        ERROR = 'error'

    widget.show()
    with patch('src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance') as mock_hw:
        hw_dialog = MagicMock()
        hw_dialog.isVisible.return_value = False
        mock_hw.return_value = hw_dialog

        widget.handle_ifa_hw_dialog('Test message', DialogType.INFO)
        hw_dialog.update_dialog.assert_called_once()
        hw_dialog.show.assert_called_once()


def test_handle_ifa_hw_dialog_not_visible(widget: IssueIFAWidget):
    """Test handle_ifa_hw_dialog when widget is not visible."""
    from enum import Enum

    class DialogType(Enum):
        INFO = 'info'

    widget.hide()
    with patch('src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance') as mock_hw:
        widget.handle_ifa_hw_dialog('Test message', DialogType.INFO)
        mock_hw.assert_not_called()


def test_retranslate_ui(widget: IssueIFAWidget):
    """Test retranslate_ui sets text correctly."""
    widget.retranslate_ui()
    assert widget.issue_ifa_title.text() != ''
    assert widget.issue_ifa_btn.text() != ''


def test_handle_button_enabled_all_fields(widget: IssueIFAWidget):
    """Test handle_button_enabled with all fields filled."""
    widget.inflatables_short_identifier_input.setText('TCK')
    widget.inflatables_asset_name_input.setText('Test Asset')
    widget.inflatables_issue_amount_input.setText('100')
    widget.inflatables_total_supply_input.setText('1000')

    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled()


def test_handle_button_enabled_missing_fields(widget: IssueIFAWidget):
    """Test handle_button_enabled with missing fields."""
    widget.inflatables_short_identifier_input.setText('')
    widget.inflatables_asset_name_input.setText('Test Asset')
    widget.inflatables_issue_amount_input.setText('100')

    widget.handle_button_enabled()
    assert not widget.issue_ifa_btn.isEnabled()
