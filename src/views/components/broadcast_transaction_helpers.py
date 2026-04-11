# pylint: disable=too-many-instance-attributes, too-few-public-methods
"""
Helper functions for broadcast transaction UI operations.
Contains UI logic extracted from the main view to follow MVVM pattern.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QFileDialog

from src.data.repository.setting_repository import SettingRepository
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.hardware_client_store import hardware_client_store
from src.views.components.toast import ToastManager


class InspectionUIHandler:
    """Handles inspection-related UI operations for broadcast transaction."""

    def __init__(self, widget):
        self._widget = widget

    def handle_psbt_text_changed(self) -> bool:
        """
        Handle PSBT text changes and trigger inspection if needed.
        Returns True if inspection was triggered.
        """
        if self._widget.programmatic_psbt_set:
            self._widget.programmatic_psbt_set = False

        if not self._widget.is_multisig:
            return False

        psbt_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        context = BroadcastTransactionService.prepare_psbt_text_changed_state(
            psbt_text, self._widget.last_inspected_psbt, self._widget.min_psbt_len,
        )

        if context.is_same_as_last:
            return False

        if context.should_inspect:
            self._widget.last_inspected_psbt = context.psbt_body
            self._widget.inspection_details.show_inspection_details(False)
            if self._widget.is_multisig:
                self._widget.sign_status_label.hide()
            self._widget.loading_overlay.start()
            self._widget.loading_overlay.make_parent_disabled_during_loading(
                True,
            )

            self._widget.inspection_epoch += 1
            self._widget.psbt_details = None
            self._widget.rgb_details = None
            self._widget.rgb_expected = context.is_rgb
            self._widget.is_inflation_context = context.is_inflation
            self._widget.pending_transfer_type = context.purpose

            if self._widget.is_multisig:
                self.update_signature_progress()
                self._widget.view_model.broadcast_transaction_view_model.fetch_pending_operation()
            return True
        self._widget.last_inspected_psbt = None
        self._widget.inspection_details.show_inspection_details(False)
        if self._widget.is_multisig:
            self._widget.sign_status_label.hide()
        self._widget.loading_overlay.stop()
        self._widget.handle_button_enable()
        return False

    def render_inspection_if_ready(self) -> bool:
        """
        Check if both inspections are complete and render the UI.
        Returns True if rendering was done.
        """
        current_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        current_psbt = BroadcastTransactionService.parse_psbt_input(
            current_text,
        ).psbt

        is_offline_wallet = (
            SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET
        )

        render_result = BroadcastTransactionService.prepare_render_inspection_state(
            self._widget.psbt_details, bool(
                self._widget.is_multisig and self._widget.rgb_expected,
            ), self._widget.rgb_details,
            is_offline_wallet, current_psbt, self._widget.min_psbt_len,
        )

        if not render_result.should_render:
            return False

        self._widget.inspection_details.inspect_loading.hide()
        self._widget.inspection_details.show_inspection_details(True)
        self._widget.is_psbt_validated = True
        self._widget.handle_button_enable()

        if self._widget.is_multisig:
            if render_result.should_show_sign_status:
                self._widget.sign_status_label.show()

            self._widget.broadcast_transaction_input.setStyleSheet(
                self._widget.psbt_input_base_style +
                '\nQPlainTextEdit#broadcast_transaction_input { font: 12px "JetBrains Mono", monospace; }',
            )

        self._widget.loading_overlay.stop()
        self._widget.loading_overlay.make_parent_disabled_during_loading(
            False,
        )
        return True

    def handle_psbt_inspection_result(self, details: dict | None) -> None:
        """Handle the async PSBT inspection result from the signal."""
        if details is None:
            self._widget.inspection_details.show_inspection_details(False)
            self._widget.is_psbt_validated = False
            self._widget.handle_button_enable()
            if self._widget.is_multisig:
                self._widget.sign_status_label.hide()
            # Stop loading overlay so UI doesn't stay disabled
            self._widget.loading_overlay.stop()
            self._widget.loading_overlay.make_parent_disabled_during_loading(False)
            return

        self._widget.psbt_details = details
        self._widget.is_psbt_validated = True

        current_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        pending_key = BroadcastTransactionService.resolve_transfer_type(
            psbt_text=current_text,
            is_multisig=self._widget.is_multisig,
            explicit_type=self._widget.pending_transfer_type,
            is_inflation=self._widget.is_inflation_context,
        )

        self._widget.inspection_details.update_psbt_details(
            details, self._widget.is_inflation_context, self._widget.rgb_expected, pending_key,
        )
        self.render_inspection_if_ready()
        self._widget.refresh_multisig_state_and_sync()

    def handle_rgb_transfer_inspection_result(self, rgb_details: dict | None) -> None:
        """Handle the async RGB transfer inspection result."""
        if rgb_details is None:
            # Inspection failed - reset state and stop loading
            self._widget.rgb_details = None
            self._widget.loading_overlay.stop()
            self._widget.loading_overlay.make_parent_disabled_during_loading(False)
            self._widget.handle_button_enable()
            return

        self._widget.rgb_details = rgb_details
        summary = BroadcastTransactionService.rgb_transfer_inspection_summary(
            rgb_details, self._widget.pending_transfer_type,
        )

        min_conf = None
        if self._widget.current_operation and hasattr(
            self._widget.current_operation, 'details',
        ) and self._widget.current_operation.details:
            min_conf = self._widget.current_operation.details.min_confirmations
        elif self._widget.stored_context:
            min_conf = self._widget.stored_context.get('min_confirmations')

        self._widget.inspection_details.update_rgb_details(
            asset_id=summary.asset_id,
            amount=summary.amount,
            transfer_type_label=BroadcastTransactionService.get_transfer_type_label(
                summary.transfer_type_key,
            ),
            min_conf=min_conf,
            result=rgb_details,
        )
        self.render_inspection_if_ready()
        self._widget.refresh_multisig_state_and_sync()

    def update_signature_progress(self) -> None:
        """Update the signature progress label for multisig."""
        self._widget.is_psbt_validated = False
        self._widget.handle_button_enable()

        current_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        parsed = BroadcastTransactionService.parse_psbt_input(current_text)
        current_psbt = parsed.psbt

        progress_ctx = BroadcastTransactionService.prepare_signature_progress_ui_state(
            current_psbt, self._widget.min_psbt_len, self._widget.current_operation,
        )

        if not progress_ctx.has_valid_psbt:
            self._widget.sign_status_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'signature_count',
                ).format(0, '?'),
            )
            self._widget.inspection_details.btn_import.setEnabled(True)
            self._widget.inspection_details.btn_import.show()
            self._widget.inspection_details.btn_clear.setEnabled(False)
            self._widget.inspection_details.btn_clear.hide()
            self._widget.broadcast_transaction_input.setReadOnly(False)
            self._widget.inspection_details.show_inspection_details(False)
            return

        if self._widget.is_multisig:
            self._widget.inspection_details.btn_import.hide()
            self._widget.inspection_details.btn_clear.show()
            self._widget.inspection_details.btn_clear.setEnabled(True)
            self._widget.broadcast_transaction_input.setReadOnly(True)

        if self._widget.is_multisig:
            if progress_ctx.should_trigger_direct:
                self.trigger_inspection(
                    self._widget.current_operation, current_psbt,
                )
                return

            offline_mode = (
                SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET
                or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
            )
            if offline_mode and current_psbt:
                stored_purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(
                    current_psbt,
                )
                if parsed.purpose or stored_purpose or len(current_psbt) >= self._widget.min_psbt_len:
                    self.trigger_inspection(None, current_psbt)

    def trigger_inspection(self, operation, psbt_text: str) -> None:
        """Helper to trigger the transaction inspection (BTC and RGB)."""
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        psbt_body = parsed.psbt
        if not psbt_body:
            return

        self._widget.view_model.broadcast_transaction_view_model.inspect_psbt(
            psbt_body,
        )

        ctx = BroadcastTransactionService.resolve_inspection_context(
            operation, parsed.purpose, psbt_body, self._widget.rgb_expected,
        )

        is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET
        self._widget.stored_context = None
        if is_offline_wallet:
            self._widget.stored_context = BroadcastTransactionService.get_psbt_rgb_context(
                psbt_body,
            )

        rgb_expected = ctx.rgb_expected
        if is_offline_wallet:
            rgb_expected = bool(
                self._widget.stored_context and self._widget.stored_context.get(
                    'fascia_path',
                ),
            )

        self._widget.inspection_details.show_inspection_details(True)
        self._widget.rgb_expected = rgb_expected
        self._widget.is_inflation_context = ctx.is_inflation

        if rgb_expected:
            if operation:
                op_ctx = operation.details
                if op_ctx and bool(op_ctx.fascia_path):
                    entropy = op_ctx.entropy if op_ctx.entropy is not None else 0
                    self._widget.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                        op_ctx.fascia_path,
                        psbt_body,
                        entropy,
                    )
            elif self._widget.stored_context:
                self._widget.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                    self._widget.stored_context['fascia_path'],
                    psbt_body,
                    self._widget.stored_context.get('entropy') or 0,
                )

    def on_signature_count_ready(self, count: int, threshold: int | None) -> None:
        """Update signature progress display for InspectionUIHandler."""
        total_disp = threshold if threshold is not None else '?'
        self._widget.sign_status_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'signature_count',
            ).format(count, total_disp),
        )
        self._widget.sign_status_label.show()
        if self._widget.is_multisig:
            self._widget.inspection_details.btn_primary.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'post_to_multisig' if self._widget.is_watch_only else 'sign_psbt',
                ),
            )
            if self._widget.is_initiator_of_pending:
                self._widget.inspection_details.btn_primary.hide()
                self._widget.inspection_details.btn_reject.hide()
            else:
                self._widget.inspection_details.btn_primary.show()
                self._widget.inspection_details.btn_reject.show()

        self._widget.handle_button_enable()

    def refresh_multisig_state_and_sync(self) -> None:
        """Update signature progress and trigger bridge sync."""
        if self._widget.is_multisig and self._widget.current_operation:
            if self._widget.current_operation.status is not None and \
                    self._widget.current_operation.status.acked_by is not None and self._widget.current_operation.status.threshold is not None:
                ack_count = len(
                    self._widget.current_operation.status.acked_by,
                )
                self.on_signature_count_ready(
                    ack_count, self._widget.current_operation.status.threshold,
                )
        if self._widget.is_multisig:
            self._widget.view_model.broadcast_transaction_view_model.fetch_pending_operation()


class MultisigUIHandler:
    """Handles multisig-specific UI operations for broadcast transaction."""

    def __init__(self, widget):
        self._widget = widget

    def on_pending_operation_ready(self, op_info) -> None:
        """Callback when bridge sync returns a pending operation."""
        if not self._widget.is_multisig or not op_info:
            return

        current_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        current_psbt = BroadcastTransactionService.parse_psbt_input(
            current_text,
        ).psbt
        if not current_psbt:
            return

        pending = BroadcastTransactionService.match_pending_operation(
            op_info, current_psbt,
        )

        if pending is None and self._widget.psbt_details:
            pending_txid = self._widget.view_model.broadcast_transaction_view_model.get_pending_psbt_txid()
            if pending_txid and pending_txid == self._widget.psbt_details.txid:
                pending = BroadcastTransactionService.match_pending_operation_by_txid(
                    op_info, pending_txid,
                )

        match_result = BroadcastTransactionService.process_pending_operation_match(
            pending, op_info, self._widget.is_watch_only,
        )
        if not match_result:
            return

        self._widget.current_operation = match_result.operation
        self._widget.pending_operation = match_result.pending_operation
        self._widget.pending_transfer_type = match_result.transfer_type
        self._widget.is_inflation_context = match_result.is_inflation

        if self._widget.psbt_details is not None:
            new_label = BroadcastTransactionService.get_transfer_type_label(
                self._widget.pending_transfer_type,
            )
            self._widget.inspection_details.update_transfer_type_label(
                new_label,
            )

        if match_result.should_trigger_rgb_inspection:
            self._widget.rgb_expected = True
            self._widget.rgb_details = None
            self._widget.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                match_result.fascia_path, current_psbt, match_result.entropy,
            )

        self._widget.is_initiator_of_pending = match_result.is_initiator
        self.on_signature_count_ready(
            match_result.ack_count, match_result.threshold,
        )
        self._widget.handle_button_enable()

    def on_signature_count_ready(self, count: int, threshold: int | None) -> None:
        """Update signature progress display."""
        total_disp = threshold if threshold is not None else '?'
        self._widget.sign_status_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'signature_count',
            ).format(count, total_disp),
        )
        self._widget.sign_status_label.show()
        if self._widget.is_multisig:
            self._widget.inspection_details.btn_primary.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'post_to_multisig' if self._widget.is_watch_only else 'sign_psbt',
                ),
            )
            if self._widget.is_initiator_of_pending:
                self._widget.inspection_details.btn_primary.hide()
                self._widget.inspection_details.btn_reject.hide()
            else:
                self._widget.inspection_details.btn_primary.show()
                self._widget.inspection_details.btn_reject.show()

        self._widget.handle_button_enable()


class PsbtFileHandler:
    """Handles PSBT file operations for broadcast transaction."""

    def __init__(self, widget):
        self._widget = widget

    def import_psbt(self) -> None:
        """Import a PSBT from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self._widget, 'Import PSBT', '', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        psbt_only, error = BroadcastTransactionService.read_psbt_from_file(
            file_path,
        )
        if error:
            ToastManager.error(description=error)
            return

        self._widget.programmatic_psbt_set = True
        self._widget.broadcast_transaction_input.setPlainText(psbt_only)

        if self._widget.is_multisig:
            self.update_signature_progress()
        self._widget.handle_button_enable()

    def export_psbt(self) -> None:
        """Export the current PSBT to file."""
        current_text = self._widget.broadcast_transaction_input.toPlainText().strip()
        parsed = BroadcastTransactionService.parse_psbt_input(current_text)
        purpose = parsed.purpose
        current_psbt = parsed.psbt
        if not current_psbt:
            ToastManager.error(description='No PSBT to export')
            return

        export_text = BroadcastTransactionService.format_psbt_export(
            current_psbt, purpose,
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self._widget, 'Export PSBT', 'transaction.psbt', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(export_text)
            ToastManager.success(description='PSBT exported successfully')
        except Exception as e:
            ToastManager.error(
                description=f'Failed to write PSBT file: {e}',
            )

    def clear_psbt(self) -> None:
        """Clear the current PSBT and reset UI state."""
        self._widget.broadcast_transaction_input.clear()
        self._widget.broadcast_transaction_input.setReadOnly(False)
        self._widget.current_operation = None
        self._widget.pending_operation = None
        self._widget.psbt_details = None
        self._widget.rgb_details = None
        self._widget.rgb_expected = False
        self._widget.is_inflation_context = False
        self._widget.is_psbt_validated = False
        self._widget.inspection_details.hide()
        if self._widget.is_multisig:
            try:
                self._widget.sign_status_label.hide()
            except Exception:
                pass
        self._widget.handle_button_enable()

    def update_signature_progress(self) -> None:
        """Update signature progress - delegates to widget's inspection handler."""
        self._widget.update_signature_progress()


class HwDialogUIHandler:
    """Handles hardware wallet dialog UI operations."""

    def __init__(self, widget):
        self._widget = widget

    def handle_hw_dialog(self, message: str, dialog_type) -> None:
        """Centralized hardware wallet dialog update handler."""
        if not self._widget.isVisible():
            return
        self._widget.broadcast_button.stop_loading()
        self._widget.broadcast_button.setEnabled(True)
        self._widget.hw_dialog.update_dialog(message, dialog_type)
        self._widget.hw_dialog.cancel_button.clicked.connect(
            self.reset_button_states,
        )
        if not self._widget.hw_dialog.isVisible():
            self._widget.hw_dialog.show()

    def reset_button_states(self) -> None:
        """Reset all button states after HW dialog is cancelled."""
        hardware_client_store.stop_client()
        self._widget.broadcast_button.stop_loading()
        self._widget.broadcast_button.setEnabled(True)
        self._widget.inspection_details.btn_reject.setEnabled(True)
        self._widget.inspection_details.btn_clear.setEnabled(True)
        self._widget.handle_button_enable()
