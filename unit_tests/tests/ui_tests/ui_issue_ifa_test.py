# pylint: disable=redefined-outer-name,unused-argument,protected-access, too-many-lines
"""UI tests for IssueIFAWidget."""
from __future__ import annotations

from enum import Enum
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import PsbtStatus
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
    widget.ifa_form.ticker_input.setText('TCK')
    widget.ifa_form.name_input.setText('Name')
    widget.ifa_form.issue_amount_input.setText('0')
    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled() is False

    widget.ifa_form.issue_amount_input.setText('10')
    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled() is True


def test_on_issue_ifa_click_calls_vm_and_draft(widget: IssueIFAWidget, vm_mock):
    """Test that on_issue_ifa_click calls create_issue_asset_draft."""
    widget.ifa_form.ticker_input.setText('abc')
    widget.ifa_form.name_input.setText('MyAsset')
    widget.ifa_form.issue_amount_input.setText('25')
    widget.ifa_form.total_supply_input.setText('50')

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
            assert w.ifa_form.name_input.isReadOnly()
            assert w.ifa_form.total_supply_title_widget.isHidden()
            assert w.ifa_form.total_supply_input.isHidden()
        finally:
            w.close()


def test_handle_ifa_issue_uses_existing_psbt_or_creates(vm_mock):
    """Test that handle_ifa_issue uses existing PSBT or creates a new one."""
    with patch('src.views.ui_issue_ifa.load_stylesheet', return_value=''), \
            patch('src.views.ui_issue_ifa.show_utxo_confirmation_dialog', return_value=(True, False)), \
            patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        w = IssueIFAWidget(vm_mock)
        try:
            # Make widget visible so handle_ifa_issue doesn't return early
            w.show()
            # Use correct purpose 'issue_asset_ifa' (not 'issue_asset')
            vm_mock.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'
            get_sess.return_value = MagicMock(
                list_psbt=lambda signed=False: [
                    {'purpose': 'issue_asset_ifa', 'psbt': 'P1'},
                ],
            )
            with patch.object(w, 'show_ifa_psbt_page') as show:
                w.handle_ifa_issue()
                show.assert_called_once_with('P1')
            # Case 2: not present -> create_utxos_begin called
            get_sess.return_value = MagicMock(
                list_psbt=lambda signed=False: [],
            )
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
    widget.ifa_form.total_supply_input.setText('100')
    widget.ifa_form.issue_amount_input.setText('50')

    # Should not raise any errors
    widget.validate_supply_fields()


def test_validate_supply_fields_exceeds_total(widget: IssueIFAWidget):
    """Test validate_supply_fields when issue amount exceeds total."""
    widget.secondary_issuance = False
    widget.ifa_form.total_supply_input.setText('50')
    widget.ifa_form.issue_amount_input.setText('100')

    # Should handle the validation (may or may not show error)
    widget.validate_supply_fields()


def test_validate_supply_fields_secondary(widget: IssueIFAWidget):
    """Test validate_supply_fields for secondary issuance."""
    widget.secondary_issuance = True
    widget.ifa_form.issue_amount_input.setText('50')

    # Secondary issuance should not validate total supply
    widget.validate_supply_fields()


def test_show_error(widget: IssueIFAWidget):
    """Test _show_error sets error text."""
    widget._show_error('Test error message')
    assert widget.ifa_form.error_label.text() == 'Test error message'


def test_handle_ifa_hw_dialog_visible(widget: IssueIFAWidget):
    """Test handle_ifa_hw_dialog when widget is visible."""
    class DialogType(Enum):
        """Dialog type enum."""
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
    class DialogType(Enum):
        """Dialog type enum."""
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
    widget.ifa_form.ticker_input.setText('TCK')
    widget.ifa_form.name_input.setText('Test Asset')
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.total_supply_input.setText('1000')

    widget.handle_button_enabled()
    assert widget.issue_ifa_btn.isEnabled()


def test_handle_button_enabled_missing_fields(widget: IssueIFAWidget):
    """Test handle_button_enabled with missing fields."""
    widget.ifa_form.ticker_input.setText('')
    widget.ifa_form.name_input.setText('Test')
    widget.ifa_form.issue_amount_input.setText('100')

    widget.handle_button_enabled()
    assert not widget.issue_ifa_btn.isEnabled()


def test_on_secondary_issuance_click_with_hardware_wallet(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click with hardware wallet."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.is_hardware_wallet = True
    widget.is_offline_wallet = False
    widget.is_watch_only = False
    widget.is_multisig = False
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.fee_rate_input.setText('10')

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    widget.on_secondary_issuance_click()
    widget._view_model.issue_ifa_asset_view_model.secondary_issuance_begin.assert_called_once()


def test_on_secondary_issuance_click_with_existing_psbt(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click when existing PSBT is found."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.fee_rate_input.setText('10')

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = [
        {'purpose': 'inflation', 'psbt': 'existing_psbt'},
    ]
    mock_svc.get_active_secondary_draft_for_asset.return_value = {
        'id': 1, 'amount': 100,
    }
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    with patch.object(widget, 'show_inflate_psbt_page') as mock_show:
        widget.on_secondary_issuance_click()
        mock_show.assert_called_once_with('existing_psbt')


def test_on_secondary_issuance_click_params_none(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click when params is None."""
    widget.secondary_issuance = True
    widget.params = None

    mock_svc = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    # Should return early without calling viewmodel
    widget.on_secondary_issuance_click()
    widget._view_model.issue_ifa_asset_view_model.secondary_issuance_begin.assert_not_called()


def test_inflatables_asset_issued_with_draft(widget: IssueIFAWidget, mocker):
    """Test inflatables_asset_issued cleans up draft."""
    widget.from_draft = True
    widget.draft_id = '123'

    mock_svc = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    mock_nav = MagicMock()
    widget._view_model.page_navigation.show_success_page = mock_nav

    widget.inflatables_asset_issued('TestAsset')
    mock_svc.delete_draft_issue_asset.assert_called_once_with('123')
    mock_nav.assert_called_once()


def test_inflatables_asset_issued_no_draft(widget: IssueIFAWidget, mocker):
    """Test inflatables_asset_issued without draft."""
    widget.from_draft = False
    widget.draft_id = None

    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=None,
    )

    mock_nav = MagicMock()
    widget._view_model.page_navigation.show_success_page = mock_nav

    widget.inflatables_asset_issued('TestAsset')
    mock_nav.assert_called_once()


def test_validate_supply_fields_value_error(widget: IssueIFAWidget):
    """Test validate_supply_fields with invalid number."""
    widget.secondary_issuance = False
    widget.ifa_form.total_supply_input.setText('not_a_number')
    widget.ifa_form.issue_amount_input.setText('50')

    widget.validate_supply_fields()
    # Should handle ValueError gracefully


def test_validate_supply_fields_negative_values(widget: IssueIFAWidget):
    """Test validate_supply_fields with negative values."""
    widget.secondary_issuance = False
    widget.ifa_form.total_supply_input.setText('-10')
    widget.ifa_form.issue_amount_input.setText('-5')

    widget.validate_supply_fields()
    # Should show error for negative values


def test_on_issue_ifa_click_value_error(widget: IssueIFAWidget, mocker):
    """Test on_issue_ifa_click with invalid number."""
    widget.ifa_form.ticker_input.setText('TCK')
    widget.ifa_form.name_input.setText('Test')
    widget.ifa_form.issue_amount_input.setText('not_a_number')
    widget.ifa_form.total_supply_input.setText('100')

    widget.on_issue_ifa_click()
    # Should handle ValueError and show error


def test_on_issue_ifa_click_negative_values(widget: IssueIFAWidget, mocker):
    """Test on_issue_ifa_click with negative values."""
    widget.ifa_form.ticker_input.setText('TCK')
    widget.ifa_form.name_input.setText('Test')
    widget.ifa_form.issue_amount_input.setText('-10')
    widget.ifa_form.total_supply_input.setText('-100')

    widget.on_issue_ifa_click()
    # Should show error for negative values


def test_on_issue_ifa_click_exceeds_total(widget: IssueIFAWidget, mocker):
    """Test on_issue_ifa_click when issue amount exceeds total."""
    widget.ifa_form.ticker_input.setText('TCK')
    widget.ifa_form.name_input.setText('Test')
    widget.ifa_form.issue_amount_input.setText('200')
    widget.ifa_form.total_supply_input.setText('100')

    widget.on_issue_ifa_click()
    # Should show error when initial supply exceeds total


def test_create_issue_inflatables_asset_draft(widget: IssueIFAWidget, mocker):
    """Test create_issue_inflatables_asset_draft method."""
    mock_svc = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget.create_issue_inflatables_asset_draft('TCK', 'Test', 100, 50)
    mock_svc.upsert_draft_issue_asset.assert_called_once()


def test_show_inflate_psbt_page(widget: IssueIFAWidget, mocker):
    """Test show_inflate_psbt_page navigates correctly."""
    widget.show()
    widget.is_multisig = False
    widget.params = MagicMock(asset_id='asset123')

    mock_svc = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget.show_inflate_psbt_page('psbt_base64')
    mock_svc.add_psbt.assert_called_once()


def test_show_inflate_psbt_page_multisig(widget: IssueIFAWidget, mocker):
    """Test show_inflate_psbt_page with multisig wallet."""
    widget.show()
    widget.is_multisig = True
    widget.params = MagicMock(asset_id='asset123')

    mock_svc = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mock_toast = mocker.patch('src.views.ui_issue_ifa.ToastManager.success')

    widget.show_inflate_psbt_page('psbt_base64')
    mock_toast.assert_called_once()


def test_show_inflate_psbt_page_empty_psbt(widget: IssueIFAWidget, mocker):
    """Test show_inflate_psbt_page with empty PSBT."""
    widget.show()
    widget.is_multisig = False

    widget.show_inflate_psbt_page('')
    # Should return early without calling service


def test_show_ifa_psbt_page_multisig(widget: IssueIFAWidget, mocker):
    """Test show_ifa_psbt_page with multisig wallet."""
    widget.show()
    widget.is_multisig = True
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    mock_toast = mocker.patch('src.views.ui_issue_ifa.ToastManager.success')
    mock_nav = MagicMock()
    widget._view_model.page_navigation.inflatable_asset_page = mock_nav

    widget.show_ifa_psbt_page('psbt_base64')
    mock_toast.assert_called_once()
    mock_nav.assert_called_once()


def test_show_ifa_psbt_page_non_multisig(widget: IssueIFAWidget, mocker):
    """Test show_ifa_psbt_page with non-multisig wallet."""
    widget.show()
    widget.is_multisig = False
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    mock_nav = MagicMock()
    widget._view_model.page_navigation.receive_asset_page = mock_nav

    widget.show_ifa_psbt_page('psbt_base64')
    mock_nav.assert_called_once()


def test_handle_ifa_hw_dialog_success(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_hw_dialog with SUCCESS status."""
    widget.show()

    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = False
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )
    mock_handle = mocker.patch.object(
        widget, '_handle_success_dialog', return_value=True,
    )

    widget.handle_ifa_hw_dialog('message', PsbtStatus.SUCCESS)
    mock_handle.assert_called_once()


def test_handle_ifa_hw_dialog_error_utxo(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_hw_dialog with ERROR status and UTXO error."""
    widget.show()

    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = False
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )
    mock_handle = mocker.patch.object(
        widget, '_handle_utxo_error', return_value=True,
    )

    widget.handle_ifa_hw_dialog('NoAvailableUtxos', PsbtStatus.ERROR)
    mock_handle.assert_called_once()


def test_handle_psbt_posted_to_bridge(widget: IssueIFAWidget, mocker):
    """Test handle_psbt_posted_to_bridge."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = True
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )
    mock_toast = mocker.patch('src.views.ui_issue_ifa.ToastManager.success')
    mock_nav = MagicMock()
    widget._view_model.page_navigation.inflatable_asset_page = mock_nav

    widget.handle_psbt_posted_to_bridge()
    mock_hw.accept.assert_called_once()
    mock_toast.assert_called_once()


def test_handle_ifa_utxo_created_primary(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_utxo_created for primary issuance."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = True
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )

    with patch.object(widget, 'on_issue_ifa_click') as mock_click:
        widget.handle_ifa_utxo_created(True)
        mock_hw.accept.assert_called_once()
        mock_click.assert_called_once()


def test_handle_ifa_utxo_created_secondary(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_utxo_created for secondary issuance."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'inflation'

    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = True
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )

    with patch.object(widget, 'on_secondary_issuance_click') as mock_click:
        widget.handle_ifa_utxo_created(True)
        mock_hw.accept.assert_called_once()
        mock_click.assert_called_once()


def test_handle_ifa_issue_with_existing_psbt(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue when existing PSBT is found."""
    widget.show()
    widget.secondary_issuance = False

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = [
        {'purpose': 'issue_asset_ifa', 'psbt': 'existing_psbt'},
    ]
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )

    with patch.object(widget, 'show_ifa_psbt_page') as mock_show:
        widget.handle_ifa_issue()
        mock_show.assert_called_once_with('existing_psbt')


def test_handle_ifa_issue_secondary_with_existing_psbt(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue for secondary issuance with existing PSBT."""
    widget.show()
    widget.secondary_issuance = True

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = [
        {'purpose': 'inflation', 'psbt': 'existing_psbt'},
    ]
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )

    with patch.object(widget, 'show_ifa_psbt_page') as mock_show:
        widget.handle_ifa_issue()
        mock_show.assert_called_once_with('existing_psbt')


def test_handle_ifa_issue_creates_utxos(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue creates UTXOs when needed."""
    widget.show()
    widget.secondary_issuance = False
    widget.is_hardware_wallet = False

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )
    mocker.patch(
        'src.views.ui_issue_ifa.get_unspent_utxo_count',
        return_value=0,
    )

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_called_once()


def test_handle_ifa_issue_user_cancels(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue when user cancels UTXO dialog."""
    widget.show()
    widget.secondary_issuance = False

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(False, False),
    )

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_not_called()


def test_load_inflatables_draft_data_secondary(widget: IssueIFAWidget, mocker):
    """Test _load_inflatables_draft_data for secondary issuance."""
    widget.secondary_issuance = True
    widget.from_draft = True
    widget.draft_id = '123'

    mock_svc = MagicMock()
    mock_svc.get_ifa_secondary_draft_by_id.return_value = {'amount': 100}
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget._load_inflatables_draft_data()
    mock_svc.get_ifa_secondary_draft_by_id.assert_called_once_with(123)


def test_load_inflatables_draft_data_primary(widget: IssueIFAWidget, mocker):
    """Test _load_inflatables_draft_data for primary issuance."""
    widget.secondary_issuance = False
    widget.from_draft = True
    widget.draft_id = '456'

    mock_svc = MagicMock()
    mock_svc.list_draft_issue_assets.return_value = [
        {
            'id': '456', 'name': 'TestAsset', 'ticker': 'TST',
            'issued_amount': 100, 'inflation_amounts': 50,
        },
    ]
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget._load_inflatables_draft_data()
    assert widget.ifa_form.name_input.text() == 'TestAsset'
    assert widget.ifa_form.ticker_input.text() == 'TST'


def test_load_inflatables_draft_data_no_draft(widget: IssueIFAWidget, mocker):
    """Test _load_inflatables_draft_data when draft not found."""
    widget.secondary_issuance = False
    widget.from_draft = True
    widget.draft_id = '999'

    mock_svc = MagicMock()
    mock_svc.list_draft_issue_assets.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget._load_inflatables_draft_data()


def test_handle_psbt_posted_to_bridge_wrong_purpose(widget: IssueIFAWidget, mocker):
    """Test handle_psbt_posted_to_bridge with wrong purpose."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'other_purpose'

    mock_hw = MagicMock()
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )

    widget.handle_psbt_posted_to_bridge()
    mock_hw.accept.assert_not_called()


def test_handle_ifa_utxo_created_wrong_purpose(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_utxo_created with wrong purpose."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'other_purpose'

    widget.handle_ifa_utxo_created(True)


def test_handle_ifa_utxo_created_status_false(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_utxo_created with status False."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    widget.handle_ifa_utxo_created(False)


def test_show_ifa_psbt_page_wrong_purpose(widget: IssueIFAWidget, mocker):
    """Test show_ifa_psbt_page with wrong purpose."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'other_purpose'

    widget.show_ifa_psbt_page('psbt_base64')


def test_show_ifa_psbt_page_empty_psbt(widget: IssueIFAWidget, mocker):
    """Test show_ifa_psbt_page with empty PSBT."""
    widget.show()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    widget.show_ifa_psbt_page('')


def test_handle_ifa_issue_no_service(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue when wallet service is None."""
    widget.show()
    widget.secondary_issuance = False

    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=None,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_called_once()


def test_on_secondary_issuance_click_standard_wallet(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click with standard wallet."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.is_hardware_wallet = False
    widget.is_offline_wallet = False
    widget.is_watch_only = False
    widget.is_multisig = False
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.fee_rate_input.setText('10')

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mock_svc.get_active_secondary_draft_for_asset.return_value = None
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    widget.on_secondary_issuance_click()
    widget._view_model.issue_ifa_asset_view_model.secondary_issuance.assert_called_once()


def test_on_secondary_issuance_click_watch_only(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click with watch-only wallet."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.is_hardware_wallet = False
    widget.is_offline_wallet = False
    widget.is_watch_only = True
    widget.is_multisig = False
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.fee_rate_input.setText('10')

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mock_svc.get_active_secondary_draft_for_asset.return_value = None
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    widget.on_secondary_issuance_click()
    widget._view_model.issue_ifa_asset_view_model.secondary_issuance_begin.assert_called_once()


def test_on_secondary_issuance_click_multisig(widget: IssueIFAWidget, mocker):
    """Test on_secondary_issuance_click with multisig wallet."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.is_hardware_wallet = False
    widget.is_offline_wallet = False
    widget.is_watch_only = False
    widget.is_multisig = True
    widget.ifa_form.issue_amount_input.setText('100')
    widget.ifa_form.fee_rate_input.setText('10')

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mock_svc.get_active_secondary_draft_for_asset.return_value = None
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.SettingCardRepository.get_default_min_confirmation',
        return_value=MagicMock(min_confirmation=6),
    )

    widget.on_secondary_issuance_click()
    widget._view_model.issue_ifa_asset_view_model.secondary_issuance_begin.assert_called_once()


def test_get_or_create_secondary_draft_new_draft(widget: IssueIFAWidget, mocker):
    """Test _get_or_create_secondary_draft creates new draft."""
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.from_draft = False
    widget.draft_id = None

    mock_svc = MagicMock()
    mock_svc.get_active_secondary_draft_for_asset.return_value = None
    mock_svc.add_ifa_secondary_draft_meta.return_value = 123  # Return integer ID
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    result = widget._get_or_create_secondary_draft(mock_svc, '100')
    assert result is False
    mock_svc.add_ifa_secondary_draft_meta.assert_called_once()


def test_get_or_create_secondary_draft_existing_match(widget: IssueIFAWidget, mocker):
    """Test _get_or_create_secondary_draft with existing matching draft."""
    widget.params = MagicMock(asset_id='asset123', asset_name='TestAsset')
    widget.from_draft = False
    widget.draft_id = None

    mock_svc = MagicMock()
    mock_svc.get_active_secondary_draft_for_asset.return_value = {
        'id': 1, 'amount': 100,
    }
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    result = widget._get_or_create_secondary_draft(mock_svc, '100')
    assert result is False


def test_get_or_create_secondary_draft_no_params(widget: IssueIFAWidget, mocker):
    """Test _get_or_create_secondary_draft when params is None."""
    widget.params = None

    mock_svc = MagicMock()
    result = widget._get_or_create_secondary_draft(mock_svc, '100')
    assert result is False


def test_delete_active_secondary_draft_on_success(widget: IssueIFAWidget, mocker):
    """Test _delete_active_secondary_draft_on_success."""
    widget.secondary_issuance = True
    widget.params = MagicMock(asset_id='asset123')

    mock_delete = mocker.patch(
        'src.views.ui_issue_ifa.delete_active_secondary_draft_on_success',
    )
    widget._delete_active_secondary_draft_on_success()
    mock_delete.assert_called_once()


def test_close_hw_dialog_if_open(widget: IssueIFAWidget, mocker):
    """Test _close_hw_dialog_if_open."""
    mock_hw = MagicMock()
    mock_hw.isVisible.return_value = True
    mocker.patch(
        'src.views.ui_issue_ifa.HardwareWalletOperationDialog.get_instance', return_value=mock_hw,
    )

    widget._close_hw_dialog_if_open()
    mock_hw.accept.assert_called_once()


def test_handle_ifa_issue_hardware_wallet(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue with hardware wallet."""
    widget.show()
    widget.secondary_issuance = False
    widget.is_hardware_wallet = True
    widget.is_offline_wallet = False

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )
    mocker.patch(
        'src.views.ui_issue_ifa.get_unspent_utxo_count',
        return_value=5,
    )

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_called_once()


def test_show_inflate_psbt_page_exception(widget: IssueIFAWidget, mocker):
    """Test show_inflate_psbt_page handles exception."""
    widget.show()
    widget.is_multisig = False
    widget.params = MagicMock(asset_id='asset123')

    mock_svc = MagicMock()
    mock_svc.add_psbt.side_effect = Exception('Test error')
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget.show_inflate_psbt_page('psbt_base64')


def test_load_inflatables_draft_data_exception(widget: IssueIFAWidget, mocker):
    """Test _load_inflatables_draft_data handles exception."""
    widget.secondary_issuance = True
    widget.from_draft = True
    widget.draft_id = '123'

    mock_svc = MagicMock()
    mock_svc.get_ifa_secondary_draft_by_id.side_effect = Exception(
        'Test error',
    )
    mock_svc.list_draft_issue_assets.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    widget._load_inflatables_draft_data()


def test_handle_ifa_issue_inflation_utxo_purpose(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue with inflation_utxo purpose."""
    widget.show()
    widget.secondary_issuance = True

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = [
        {'purpose': 'inflation_utxo', 'psbt': 'existing_psbt'},
    ]
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )

    with patch.object(widget, 'show_ifa_psbt_page') as mock_show:
        widget.handle_ifa_issue()
        mock_show.assert_called_once_with('existing_psbt')


def test_handle_ifa_issue_from_draft(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue when from_draft is True."""
    widget.show()
    widget.secondary_issuance = False
    widget.from_draft = True
    widget.draft_id = '123'

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )
    mocker.patch(
        'src.views.ui_issue_ifa.get_unspent_utxo_count',
        return_value=5,
    )

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_called_once()


def test_validate_issuance_amount_valid(widget: IssueIFAWidget, mocker):
    """Test validate_issuance_amount with valid amount."""
    widget.params = MagicMock(max_amount=1000)
    widget.asset_transactions = MagicMock()
    widget.asset_transactions.asset_balance.spendable = 100
    widget.ifa_form.issue_amount_input.setText('500')
    widget.ifa_form.error_label.hide()

    widget.validate_issuance_amount('500')


def test_validate_issuance_amount_exceeds_max(widget: IssueIFAWidget, mocker):
    """Test validate_issuance_amount when amount exceeds max."""
    widget.params = MagicMock(max_amount=100)
    widget.asset_transactions = MagicMock()
    widget.asset_transactions.asset_balance.spendable = 100
    widget.ifa_form.issue_amount_input.setText('500')
    widget.ifa_form.hide_error()

    widget.validate_issuance_amount('500')
    # Error should be shown for exceeding max - the method sets text and shows error
    assert widget.ifa_form.error_label.text(
    ) != '' or widget.issue_ifa_btn.isEnabled() is False


def test_validate_issuance_amount_non_digit(widget: IssueIFAWidget, mocker):
    """Test validate_issuance_amount with non-digit amount."""
    widget.params = MagicMock(max_amount=1000)
    widget.asset_transactions = MagicMock()
    widget.asset_transactions.asset_balance.spendable = 100

    widget.validate_issuance_amount('abc')
    assert not widget.issue_ifa_btn.isEnabled()


def test_validate_issuance_amount_no_params(widget: IssueIFAWidget, mocker):
    """Test validate_issuance_amount when params has no max_amount."""
    widget.params = MagicMock(max_amount=None)
    widget.asset_transactions = MagicMock()
    widget.asset_transactions.asset_balance.spendable = 100

    widget.validate_issuance_amount('500')


def test_spendable_balance_validation(widget: IssueIFAWidget, mocker):
    """Test spendable_balance_validation."""
    widget.secondary_issuance = True
    widget.params = MagicMock(max_amount=1000)
    widget.asset_transactions = MagicMock()
    widget.asset_transactions.asset_balance.spendable = 100
    widget.ifa_form.issue_amount_input.setText('500')

    widget.spendable_balance_validation()


def test_handle_ifa_issue_hardware_sets_retry(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue sets retry flag for hardware wallet secondary issuance."""
    widget.show()
    widget.secondary_issuance = True
    widget.is_hardware_wallet = True
    widget.is_offline_wallet = False

    mock_svc = MagicMock()
    mock_svc.list_psbt.return_value = []
    mocker.patch(
        'src.views.ui_issue_ifa.WalletDataService.get_session', return_value=mock_svc,
    )
    mocker.patch(
        'src.views.ui_issue_ifa.show_utxo_confirmation_dialog',
        return_value=(True, False),
    )
    mocker.patch(
        'src.views.ui_issue_ifa.get_unspent_utxo_count',
        return_value=5,
    )

    widget.handle_ifa_issue()
    assert widget._retry_after_utxo_inflate is True


def test_handle_ifa_issue_not_visible(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_issue when widget not visible."""
    widget.hide()

    widget.handle_ifa_issue()
    widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_not_called()


def test_show_ifa_psbt_page_not_visible(widget: IssueIFAWidget, mocker):
    """Test show_ifa_psbt_page when widget not visible."""
    widget.hide()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    widget.show_ifa_psbt_page('psbt_base64')


def test_show_inflate_psbt_page_not_visible(widget: IssueIFAWidget, mocker):
    """Test show_inflate_psbt_page when widget not visible."""
    widget.hide()

    widget.show_inflate_psbt_page('psbt_base64')


def test_handle_psbt_posted_to_bridge_not_visible(widget: IssueIFAWidget, mocker):
    """Test handle_psbt_posted_to_bridge when widget not visible."""
    widget.hide()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    widget.handle_psbt_posted_to_bridge()


def test_handle_ifa_utxo_created_not_visible(widget: IssueIFAWidget, mocker):
    """Test handle_ifa_utxo_created when widget not visible."""
    widget.hide()
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_ifa'

    widget.handle_ifa_utxo_created(True)
