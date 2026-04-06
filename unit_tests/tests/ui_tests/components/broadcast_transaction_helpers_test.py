"""Unit tests for broadcast_transaction_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.views.components.broadcast_transaction_helpers import HwDialogUIHandler
from src.views.components.broadcast_transaction_helpers import InspectionUIHandler
from src.views.components.broadcast_transaction_helpers import MultisigUIHandler
from src.views.components.broadcast_transaction_helpers import PsbtFileHandler


@pytest.fixture
def mock_widget():
    """Create a mock widget for testing handlers."""
    widget = MagicMock()
    widget.is_multisig = False
    widget.is_watch_only = False
    widget.is_psbt_validated = False
    widget.programmatic_psbt_set = False
    widget.last_inspected_psbt = None
    widget.inspection_epoch = 0
    widget.psbt_details = None
    widget.rgb_details = None
    widget.rgb_expected = False
    widget.is_inflation_context = False
    widget.pending_transfer_type = None
    widget.current_operation = None
    widget.stored_context = None
    widget.is_initiator_of_pending = False
    widget.pending_operation = None
    widget.min_psbt_len = 10
    widget.broadcast_transaction_input = MagicMock()
    widget.broadcast_transaction_input.toPlainText.return_value = ''
    widget.broadcast_transaction_input.setPlainText = MagicMock()
    widget.broadcast_transaction_input.clear = MagicMock()
    widget.broadcast_transaction_input.setReadOnly = MagicMock()
    widget.inspection_details = MagicMock()
    widget.sign_status_label = MagicMock()
    widget.loading_overlay = MagicMock()
    widget.hw_dialog = MagicMock()
    widget.hw_dialog.isVisible.return_value = False
    widget.hw_dialog.cancel_button = MagicMock()
    widget.hw_dialog.cancel_button.clicked = MagicMock()
    widget.broadcast_button = MagicMock()
    widget.view_model = MagicMock()
    widget.view_model.broadcast_transaction_view_model = MagicMock()
    widget.isVisible.return_value = True
    widget.handle_button_enable = MagicMock()
    return widget


# InspectionUIHandler tests

def test_handle_psbt_text_changed_returns_false_when_not_multisig(mock_widget):
    """Test that handle_psbt_text_changed returns False when not multisig."""
    mock_widget.is_multisig = False
    handler = InspectionUIHandler(mock_widget)

    result = handler.handle_psbt_text_changed()

    assert result is False


def test_handle_psbt_text_changed_handles_programmatic_set(mock_widget):
    """Test that handle_psbt_text_changed handles programmatic set flag."""
    mock_widget.is_multisig = True
    mock_widget.programmatic_psbt_set = True
    handler = InspectionUIHandler(mock_widget)

    handler.handle_psbt_text_changed()

    assert mock_widget.programmatic_psbt_set is False


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_handle_psbt_text_changed_triggers_inspection(mock_service, mock_widget):
    """Test that handle_psbt_text_changed triggers inspection when conditions met."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt:send:abc123'

    mock_context = MagicMock()
    mock_context.is_same_as_last = False
    mock_context.should_inspect = True
    mock_context.psbt_body = 'abc123'
    mock_context.is_rgb = False
    mock_context.is_inflation = False
    mock_context.purpose = 'send'
    mock_service.prepare_psbt_text_changed_state.return_value = mock_context

    handler = InspectionUIHandler(mock_widget)
    result = handler.handle_psbt_text_changed()

    assert result is True
    mock_widget.loading_overlay.start.assert_called_once()
    mock_widget.view_model.broadcast_transaction_view_model.fetch_pending_operation.assert_called_once()


def test_handle_psbt_inspection_result_with_none_details(mock_widget):
    """Test handle_psbt_inspection_result with None details."""
    handler = InspectionUIHandler(mock_widget)

    handler.handle_psbt_inspection_result(None)

    mock_widget.inspection_details.show_inspection_details.assert_called_with(
        False,
    )
    assert mock_widget.is_psbt_validated is False


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_handle_psbt_inspection_result_with_details(mock_service, mock_widget):
    """Test handle_psbt_inspection_result with valid details."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'test_psbt'

    mock_details = MagicMock()
    mock_service.resolve_transfer_type.return_value = 'send'

    handler = InspectionUIHandler(mock_widget)
    handler.handle_psbt_inspection_result(mock_details)

    assert mock_widget.psbt_details == mock_details
    assert mock_widget.is_psbt_validated is True
    mock_widget.inspection_details.update_psbt_details.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_handle_rgb_transfer_inspection_result(mock_service, mock_widget):
    """Test handle_rgb_transfer_inspection_result."""
    mock_widget.current_operation = None
    mock_widget.stored_context = None
    mock_service.rgb_transfer_inspection_summary.return_value = MagicMock(
        asset_id='asset1', amount='100', transfer_type_key='send',
    )

    handler = InspectionUIHandler(mock_widget)
    handler.handle_rgb_transfer_inspection_result(MagicMock())

    assert mock_widget.rgb_details is not None


# MultisigUIHandler tests

def test_on_pending_operation_ready_returns_when_not_multisig(mock_widget):
    """Test on_pending_operation_ready returns early when not multisig."""
    mock_widget.is_multisig = False
    handler = MultisigUIHandler(mock_widget)

    handler.on_pending_operation_ready({'test': 'data'})

    mock_widget.broadcast_transaction_input.toPlainText.assert_not_called()


def test_on_pending_operation_ready_returns_when_no_op_info(mock_widget):
    """Test on_pending_operation_ready returns early when op_info is None."""
    mock_widget.is_multisig = True
    handler = MultisigUIHandler(mock_widget)

    handler.on_pending_operation_ready(None)

    mock_widget.broadcast_transaction_input.toPlainText.assert_not_called()


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_on_pending_operation_ready_processes_match(mock_service, mock_widget):
    """Test on_pending_operation_ready processes matching operation."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'test_psbt'

    mock_service.parse_psbt_input.return_value = MagicMock(psbt='parsed_psbt')
    mock_service.match_pending_operation.return_value = None
    mock_service.process_pending_operation_match.return_value = None

    handler = MultisigUIHandler(mock_widget)
    handler.on_pending_operation_ready({'operation': 'test'})

    mock_service.process_pending_operation_match.assert_called_once()


def test_on_signature_count_ready(mock_widget):
    """Test _on_signature_count_ready updates UI correctly."""
    mock_widget.is_multisig = True
    mock_widget.is_watch_only = False
    mock_widget.is_initiator_of_pending = False

    handler = MultisigUIHandler(mock_widget)
    handler.on_signature_count_ready(2, 3)

    mock_widget.sign_status_label.setText.assert_called_once()
    mock_widget.sign_status_label.show.assert_called_once()


# PsbtFileHandler tests

@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_import_psbt_success(mock_service, mock_dialog, mock_widget):
    """Test import_psbt with successful file selection."""
    mock_dialog.getOpenFileName.return_value = ('/path/to/file.psbt', '')
    mock_service.read_psbt_from_file.return_value = ('psbt_content', None)

    handler = PsbtFileHandler(mock_widget)
    handler.import_psbt()

    mock_widget.broadcast_transaction_input.setPlainText.assert_called_with(
        'psbt_content',
    )
    mock_widget.handle_button_enable.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
def test_import_psbt_cancelled(mock_dialog, mock_widget):
    """Test import_psbt when user cancels file dialog."""
    mock_dialog.getOpenFileName.return_value = ('', '')

    handler = PsbtFileHandler(mock_widget)
    handler.import_psbt()

    mock_widget.broadcast_transaction_input.setPlainText.assert_not_called()


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
@patch('src.views.components.broadcast_transaction_helpers.ToastManager')
def test_import_psbt_with_error(mock_toast, mock_service, mock_dialog, mock_widget):
    """Test import_psbt with read error."""
    mock_dialog.getOpenFileName.return_value = ('/path/to/file.psbt', '')
    mock_service.read_psbt_from_file.return_value = (
        None, 'Error reading file',
    )

    handler = PsbtFileHandler(mock_widget)
    handler.import_psbt()

    mock_toast.error.assert_called_with(description='Error reading file')


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
@patch('src.views.components.broadcast_transaction_helpers.ToastManager')
def test_export_psbt_success(mock_toast, mock_service, mock_dialog, mock_widget):
    """Test export_psbt with successful save."""
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='psbt_content', purpose='send',
    )
    mock_service.format_psbt_export.return_value = 'formatted_psbt'
    mock_dialog.getSaveFileName.return_value = ('/path/to/save.psbt', '')

    handler = PsbtFileHandler(mock_widget)

    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.write = MagicMock()
        handler.export_psbt()

    mock_toast.success.assert_called_with(
        description='PSBT exported successfully',
    )


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
@patch('src.views.components.broadcast_transaction_helpers.ToastManager')
def test_export_psbt_no_psbt(mock_toast, mock_service, mock_dialog, mock_widget):
    """Test export_psbt when no PSBT content."""
    mock_widget.broadcast_transaction_input.toPlainText.return_value = ''
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='', purpose=None,
    )

    handler = PsbtFileHandler(mock_widget)
    handler.export_psbt()

    mock_toast.error.assert_called_with(description='No PSBT to export')


def test_clear_psbt(mock_widget):
    """Test clear_psbt resets UI state."""
    handler = PsbtFileHandler(mock_widget)
    handler.clear_psbt()

    mock_widget.broadcast_transaction_input.clear.assert_called_once()
    mock_widget.broadcast_transaction_input.setReadOnly.assert_called_with(
        False,
    )
    assert mock_widget.current_operation is None
    assert mock_widget.pending_operation is None
    assert mock_widget.psbt_details is None
    assert mock_widget.rgb_details is None
    assert mock_widget.is_psbt_validated is False


# HwDialogUIHandler tests

def test_handle_hw_dialog_when_not_visible(mock_widget):
    """Test handle_hw_dialog when widget is not visible."""
    mock_widget.isVisible.return_value = False
    handler = HwDialogUIHandler(mock_widget)

    handler.handle_hw_dialog('message', MagicMock())

    mock_widget.broadcast_button.stop_loading.assert_not_called()


def test_handle_hw_dialog_when_visible(mock_widget):
    """Test handle_hw_dialog when widget is visible."""
    mock_widget.isVisible.return_value = True
    mock_widget.hw_dialog.isVisible.return_value = False

    handler = HwDialogUIHandler(mock_widget)
    handler.handle_hw_dialog('message', MagicMock())

    mock_widget.broadcast_button.stop_loading.assert_called_once()
    mock_widget.hw_dialog.show.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.hardware_client_store')
def test_reset_button_states(mock_store, mock_widget):
    """Test reset_button_states resets UI correctly."""
    handler = HwDialogUIHandler(mock_widget)
    handler.reset_button_states()

    mock_store.stop_client.assert_called_once()
    mock_widget.broadcast_button.stop_loading.assert_called_once()
    mock_widget.handle_button_enable.assert_called_once()


# Additional tests for better coverage

def test_handle_psbt_text_changed_with_programmatic_flag_reset(mock_widget):
    """Test that programmatic flag is reset to False."""
    mock_widget.is_multisig = True
    mock_widget.programmatic_psbt_set = True
    handler = InspectionUIHandler(mock_widget)

    result = handler.handle_psbt_text_changed()

    assert mock_widget.programmatic_psbt_set is False
    assert result is False


def test_handle_psbt_text_changed_same_as_last(mock_widget):
    """Test that inspection is skipped when PSBT is same as last."""
    mock_widget.is_multisig = True
    mock_widget.last_inspected_psbt = 'abc123'
    mock_widget.inspection_epoch = 1
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt:send:abc123'

    mock_context = MagicMock()
    mock_context.is_same_as_last = True
    mock_context.should_inspect = False
    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService.prepare_psbt_text_changed_state', return_value=mock_context):
        handler = InspectionUIHandler(mock_widget)
        result = handler.handle_psbt_text_changed()

        assert result is False


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_handle_psbt_inspection_result_updates_details(mock_service, mock_widget):
    """Test PSBT inspection result updates widget state."""
    mock_widget.is_multisig = True
    mock_details = MagicMock()
    mock_service.resolve_transfer_type.return_value = 'send_btc'

    handler = InspectionUIHandler(mock_widget)
    handler.handle_psbt_inspection_result(mock_details)

    assert mock_widget.psbt_details == mock_details
    assert mock_widget.is_psbt_validated is True


def test_handle_rgb_transfer_inspection_result_with_none(mock_widget):
    """Test RGB inspection result with None clears state."""
    mock_widget.current_operation = None
    mock_widget.stored_context = None

    handler = InspectionUIHandler(mock_widget)
    handler.handle_rgb_transfer_inspection_result(None)

    assert mock_widget.rgb_details is None


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_handle_rgb_transfer_inspection_result_with_details(mock_service, mock_widget):
    """Test RGB inspection result with valid details."""
    mock_widget.current_operation = None
    mock_widget.stored_context = None
    mock_widget.pending_transfer_type = 'send_asset'

    mock_summary = MagicMock()
    mock_summary.asset_id = 'asset1'
    mock_summary.amount = '100'
    mock_summary.transfer_type_key = 'send_asset'
    mock_service.rgb_transfer_inspection_summary.return_value = mock_summary
    mock_service.get_transfer_type_label.return_value = 'Send Asset'

    handler = InspectionUIHandler(mock_widget)
    handler.handle_rgb_transfer_inspection_result(MagicMock())

    assert mock_widget.rgb_details is not None


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_on_pending_operation_ready_with_matching_psbt(mock_service, mock_widget):
    """Test pending operation ready with matching PSBT."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_service.parse_psbt_input.return_value = MagicMock(psbt='psbt_content')

    mock_pending = MagicMock()
    mock_service.match_pending_operation.return_value = mock_pending

    mock_match = MagicMock()
    mock_match.operation = 'op'
    mock_match.pending_operation = 'pending'
    mock_match.transfer_type = 'send_btc'
    mock_match.is_inflation = False
    mock_match.should_trigger_rgb_inspection = False
    mock_match.ack_count = 1
    mock_match.threshold = 3
    mock_match.is_initiator = False
    mock_service.process_pending_operation_match.return_value = mock_match

    handler = MultisigUIHandler(mock_widget)
    handler.on_pending_operation_ready(MagicMock())

    assert mock_widget.current_operation == 'op'


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_on_pending_operation_ready_with_txid_match(mock_service, mock_widget):
    """Test pending operation ready with txid fallback match."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_widget.psbt_details = MagicMock(txid='txid123')
    mock_widget.view_model.broadcast_transaction_view_model.get_pending_psbt_txid.return_value = 'txid123'

    mock_service.parse_psbt_input.return_value = MagicMock(psbt='psbt_content')
    mock_service.match_pending_operation.return_value = None

    mock_pending = MagicMock()
    mock_service.match_pending_operation_by_txid.return_value = mock_pending

    mock_match = MagicMock()
    mock_match.operation = 'op'
    mock_match.pending_operation = 'pending'
    mock_match.transfer_type = 'send_btc'
    mock_match.is_inflation = False
    mock_match.should_trigger_rgb_inspection = False
    mock_match.ack_count = 1
    mock_match.threshold = 3
    mock_match.is_initiator = False
    mock_service.process_pending_operation_match.return_value = mock_match

    handler = MultisigUIHandler(mock_widget)
    handler.on_pending_operation_ready(MagicMock())

    mock_service.match_pending_operation_by_txid.assert_called_once()


def test_on_signature_count_ready_with_threshold(mock_widget):
    """Test signature count display with threshold."""
    mock_widget.is_multisig = True
    mock_widget.is_watch_only = False
    mock_widget.is_initiator_of_pending = False
    mock_widget.inspection_details.btn_primary = MagicMock()
    mock_widget.inspection_details.btn_reject = MagicMock()

    handler = MultisigUIHandler(mock_widget)
    handler.on_signature_count_ready(2, 3)

    mock_widget.sign_status_label.setText.assert_called_once()
    mock_widget.sign_status_label.show.assert_called_once()


def test_on_signature_count_ready_initiator(mock_widget):
    """Test signature count display for initiator."""
    mock_widget.is_multisig = True
    mock_widget.is_watch_only = False
    mock_widget.is_initiator_of_pending = True
    mock_widget.inspection_details.btn_primary = MagicMock()
    mock_widget.inspection_details.btn_reject = MagicMock()

    handler = MultisigUIHandler(mock_widget)
    handler.on_signature_count_ready(2, 3)

    mock_widget.inspection_details.btn_primary.hide.assert_called_once()
    mock_widget.inspection_details.btn_reject.hide.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_import_psbt_multisig(mock_service, mock_dialog, mock_widget):
    """Test import_psbt in multisig mode triggers signature progress."""
    mock_widget.is_multisig = True
    mock_dialog.getOpenFileName.return_value = ('/path/to/file.psbt', '')
    mock_service.read_psbt_from_file.return_value = ('psbt_content', None)

    handler = PsbtFileHandler(mock_widget)
    handler.import_psbt()

    mock_widget.broadcast_transaction_input.setPlainText.assert_called_with(
        'psbt_content',
    )
    assert mock_widget.programmatic_psbt_set is True


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.ToastManager')
def test_export_psbt_file_write_error(mock_toast, mock_dialog, mock_widget):
    """Test export_psbt handles file write error."""
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_dialog.getSaveFileName.return_value = ('/path/to/save.psbt', '')

    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService') as mock_service:
        mock_service.parse_psbt_input.return_value = MagicMock(
            psbt='psbt_content', purpose='send',
        )
        mock_service.format_psbt_export.return_value = 'formatted_psbt'

        handler = PsbtFileHandler(mock_widget)
        with patch('builtins.open', side_effect=Exception('write error')):
            handler.export_psbt()

        mock_toast.error.assert_called()


def test_clear_psbt_multisig(mock_widget):
    """Test clear_psbt in multisig mode."""
    mock_widget.is_multisig = True
    mock_widget.sign_status_label = MagicMock()

    handler = PsbtFileHandler(mock_widget)
    handler.clear_psbt()

    mock_widget.broadcast_transaction_input.clear.assert_called_once()
    mock_widget.sign_status_label.hide.assert_called_once()


def test_clear_psbt_multisig_exception(mock_widget):
    """Test clear_psbt handles exception when hiding sign_status_label."""
    mock_widget.is_multisig = True
    mock_widget.sign_status_label = MagicMock()
    mock_widget.sign_status_label.hide.side_effect = Exception('test error')

    handler = PsbtFileHandler(mock_widget)
    handler.clear_psbt()  # Should not raise

    mock_widget.broadcast_transaction_input.clear.assert_called_once()


def test_handle_hw_dialog_with_visible_hw_dialog(mock_widget):
    """Test handle_hw_dialog when hw_dialog is already visible."""
    mock_widget.isVisible.return_value = True
    mock_widget.hw_dialog.isVisible.return_value = True

    handler = HwDialogUIHandler(mock_widget)
    handler.handle_hw_dialog('message', MagicMock())

    # Should not call show since already visible
    mock_widget.hw_dialog.show.assert_not_called()


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_trigger_inspection_with_operation(mock_service, mock_widget):
    """Test _trigger_inspection with operation containing fascia_path."""
    mock_widget.rgb_expected = True
    mock_widget.is_inflation_context = False
    mock_widget.stored_context = None
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='psbt_body', purpose='send',
    )
    mock_service.resolve_inspection_context.return_value = MagicMock(
        rgb_expected=True, is_inflation=False,
    )

    mock_operation = MagicMock()
    mock_operation.details.fascia_path = 'path/to/fascia'
    mock_operation.details.entropy = 123

    handler = InspectionUIHandler(mock_widget)
    handler.trigger_inspection(mock_operation, 'psbt_text')

    mock_widget.view_model.broadcast_transaction_view_model.inspect_rgb_transfer.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
@patch('src.views.components.broadcast_transaction_helpers.SettingRepository')
def test_trigger_inspection_offline_wallet(mock_repo, mock_service, mock_widget):
    """Test _trigger_inspection for offline wallet with stored context."""
    mock_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_widget.rgb_expected = False
    mock_widget.is_inflation_context = False
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='psbt_body', purpose='send',
    )
    mock_service.resolve_inspection_context.return_value = MagicMock(
        rgb_expected=False, is_inflation=False,
    )
    mock_service.get_psbt_rgb_context.return_value = {
        'fascia_path': 'path/to/fascia',
        'entropy': 456,
    }

    handler = InspectionUIHandler(mock_widget)
    handler.trigger_inspection(None, 'psbt_text')

    mock_service.get_psbt_rgb_context.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_update_signature_progress_no_valid_psbt(mock_service, mock_widget):
    """Test _update_signature_progress when no valid PSBT."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = ''
    mock_service.parse_psbt_input.return_value = MagicMock(psbt='')
    mock_service.prepare_signature_progress_ui_state.return_value = MagicMock(
        has_valid_psbt=False,
    )

    handler = InspectionUIHandler(mock_widget)
    handler.update_signature_progress()

    mock_widget.broadcast_transaction_input.setReadOnly.assert_called_with(
        False,
    )


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
@patch('src.views.components.broadcast_transaction_helpers.SettingRepository')
def test_update_signature_progress_offline_mode(mock_repo, mock_service, mock_widget):
    """Test _update_signature_progress in offline mode."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_widget.current_operation = None
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='psbt_content', purpose=None,
    )
    mock_service.prepare_signature_progress_ui_state.return_value = MagicMock(
        has_valid_psbt=True, should_trigger_direct=False,
    )
    mock_repo.get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY
    mock_service.get_psbt_purpose_from_storage.return_value = 'send_btc'

    handler = InspectionUIHandler(mock_widget)
    with patch.object(handler, 'trigger_inspection') as mock_trigger:
        handler.update_signature_progress()
        mock_trigger.assert_called()


def test_refresh_multisig_state_and_sync(mock_widget):
    """Test _refresh_multisig_state_and_sync updates signature count."""
    mock_widget.is_multisig = True
    mock_widget.current_operation = MagicMock()
    mock_widget.current_operation.status.acked_by = ['sig1', 'sig2']
    mock_widget.current_operation.status.threshold = 3

    handler = InspectionUIHandler(mock_widget)
    handler.refresh_multisig_state_and_sync()

    mock_widget.view_model.broadcast_transaction_view_model.fetch_pending_operation.assert_called_once()


def test_handle_psbt_inspection_result_none_multisig(mock_widget):
    """Test PSBT inspection result with None in multisig mode."""
    mock_widget.is_multisig = True
    mock_widget.sign_status_label = MagicMock()

    handler = InspectionUIHandler(mock_widget)
    handler.handle_psbt_inspection_result(None)

    mock_widget.sign_status_label.hide.assert_called_once()
    assert mock_widget.is_psbt_validated is False


def test_handle_rgb_transfer_inspection_result_with_operation(mock_widget):
    """Test RGB inspection result with operation context."""
    mock_widget.current_operation = MagicMock()
    mock_widget.current_operation.details.min_confirmations = 6
    mock_widget.stored_context = None
    mock_widget.pending_transfer_type = 'send_asset'

    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService') as mock_service:
        mock_summary = MagicMock()
        mock_summary.asset_id = 'asset1'
        mock_summary.amount = '100'
        mock_summary.transfer_type_key = 'send_asset'
        mock_service.rgb_transfer_inspection_summary.return_value = mock_summary
        mock_service.get_transfer_type_label.return_value = 'Send Asset'

        handler = InspectionUIHandler(mock_widget)
        handler.handle_rgb_transfer_inspection_result(MagicMock())

        mock_widget.inspection_details.update_rgb_details.assert_called_once()


def test_handle_rgb_transfer_inspection_result_with_stored_context(mock_widget):
    """Test RGB inspection result with stored context."""
    mock_widget.current_operation = None
    mock_widget.stored_context = {'min_confirmations': 3}
    mock_widget.pending_transfer_type = 'send_asset'

    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService') as mock_service:
        mock_summary = MagicMock()
        mock_summary.asset_id = 'asset1'
        mock_summary.amount = '100'
        mock_summary.transfer_type_key = 'send_asset'
        mock_service.rgb_transfer_inspection_summary.return_value = mock_summary
        mock_service.get_transfer_type_label.return_value = 'Send Asset'

        handler = InspectionUIHandler(mock_widget)
        handler.handle_rgb_transfer_inspection_result(MagicMock())

        mock_widget.inspection_details.update_rgb_details.assert_called_once()


def test_trigger_inspection_empty_psbt(mock_widget):
    """Test _trigger_inspection with empty PSBT returns early."""
    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService') as mock_service:
        mock_service.parse_psbt_input.return_value = MagicMock(psbt='')

        handler = InspectionUIHandler(mock_widget)
        handler.trigger_inspection(None, '')

        mock_widget.view_model.broadcast_transaction_view_model.inspect_psbt.assert_not_called()


def test_on_pending_operation_ready_no_psbt(mock_widget):
    """Test on_pending_operation_ready when no PSBT in input."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = ''

    with patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService') as mock_service:
        mock_service.parse_psbt_input.return_value = MagicMock(psbt='')

        handler = MultisigUIHandler(mock_widget)
        handler.on_pending_operation_ready(MagicMock())

        mock_widget.current_operation = None  # Should not be set


@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_on_pending_operation_ready_triggers_rgb_inspection(mock_service, mock_widget):
    """Test on_pending_operation_ready triggers RGB inspection when needed."""
    mock_widget.is_multisig = True
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_service.parse_psbt_input.return_value = MagicMock(psbt='psbt_content')

    mock_pending = MagicMock()
    mock_service.match_pending_operation.return_value = mock_pending

    mock_match = MagicMock()
    mock_match.operation = 'op'
    mock_match.pending_operation = 'pending'
    mock_match.transfer_type = 'send_asset'
    mock_match.is_inflation = False
    mock_match.should_trigger_rgb_inspection = True
    mock_match.fascia_path = 'path/to/fascia'
    mock_match.entropy = 123
    mock_match.ack_count = 1
    mock_match.threshold = 3
    mock_match.is_initiator = False
    mock_service.process_pending_operation_match.return_value = mock_match

    handler = MultisigUIHandler(mock_widget)
    handler.on_pending_operation_ready(MagicMock())

    mock_widget.view_model.broadcast_transaction_view_model.inspect_rgb_transfer.assert_called_once()


@patch('src.views.components.broadcast_transaction_helpers.QFileDialog')
@patch('src.views.components.broadcast_transaction_helpers.BroadcastTransactionService')
def test_export_psbt_cancelled(mock_service, mock_dialog, mock_widget):
    """Test export_psbt when user cancels file dialog."""
    mock_widget.broadcast_transaction_input.toPlainText.return_value = 'psbt_content'
    mock_service.parse_psbt_input.return_value = MagicMock(
        psbt='psbt_content', purpose='send',
    )
    mock_dialog.getSaveFileName.return_value = ('', '')  # User cancelled

    handler = PsbtFileHandler(mock_widget)
    handler.export_psbt()

    # Should not attempt to write file
    assert not hasattr(handler, '_file_written')


def test_on_signature_count_ready_no_threshold(mock_widget):
    """Test signature count display with no threshold."""
    mock_widget.is_multisig = True
    mock_widget.is_watch_only = False
    mock_widget.is_initiator_of_pending = False
    mock_widget.inspection_details.btn_primary = MagicMock()
    mock_widget.inspection_details.btn_reject = MagicMock()

    handler = MultisigUIHandler(mock_widget)
    handler.on_signature_count_ready(2, None)

    mock_widget.sign_status_label.setText.assert_called_once()


def test_inspection_handler_on_signature_count_ready_initiator(mock_widget):
    """Test InspectionUIHandler signature count display for initiator."""
    mock_widget.is_multisig = True
    mock_widget.is_watch_only = False
    mock_widget.is_initiator_of_pending = True
    mock_widget.inspection_details.btn_primary = MagicMock()
    mock_widget.inspection_details.btn_reject = MagicMock()

    handler = InspectionUIHandler(mock_widget)
    handler.on_signature_count_ready(2, 3)

    mock_widget.inspection_details.btn_primary.hide.assert_called_once()
    mock_widget.inspection_details.btn_reject.hide.assert_called_once()
