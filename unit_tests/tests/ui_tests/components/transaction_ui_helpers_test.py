"""Unit tests for transaction_ui_helpers."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock

from rgb_lib import TransferKind
from rgb_lib import TransferStatus

from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.views.components.transaction_ui_helpers import apply_transaction_style_by_status
from src.views.components.transaction_ui_helpers import configure_transaction_time_display
from src.views.components.transaction_ui_helpers import handle_transaction_type_display
from src.views.components.transaction_ui_helpers import map_transfer_status


def test_map_transfer_status_waiting_counterparty():
    """Test map_transfer_status for WAITING_COUNTERPARTY."""
    # Execute
    result = map_transfer_status(TransferStatus.WAITING_COUNTERPARTY)

    # Assert
    assert result == TransactionStatusEnumModel.WAITING_COUNTERPARTY.value


def test_map_transfer_status_waiting_confirmations():
    """Test map_transfer_status for WAITING_CONFIRMATIONS."""
    # Execute
    result = map_transfer_status(TransferStatus.WAITING_CONFIRMATIONS)

    # Assert
    assert result == TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value


def test_map_transfer_status_failed():
    """Test map_transfer_status for FAILED."""
    # Execute
    result = map_transfer_status(TransferStatus.FAILED)

    # Assert
    assert result == TransactionStatusEnumModel.FAILED.value


def test_map_transfer_status_unknown_returns_failed():
    """Test map_transfer_status returns FAILED for unknown status."""
    # Execute
    result = map_transfer_status(None)

    # Assert
    assert result == TransactionStatusEnumModel.FAILED.value


def test_apply_transaction_style_by_status_sent():
    """Test apply_transaction_style_by_status for SENT status."""
    # Setup
    frame = MagicMock()

    # Execute
    apply_transaction_style_by_status(
        frame, TransferStatusEnumModel.SENT.value, '2024-01-01',
    )

    # Assert
    frame.transaction_amount.setStyleSheet.assert_called_once()


def test_apply_transaction_style_by_status_received():
    """Test apply_transaction_style_by_status for RECEIVED status."""
    # Setup
    frame = MagicMock()

    # Execute
    apply_transaction_style_by_status(
        frame, TransferStatusEnumModel.RECEIVED.value, '2024-01-01',
    )

    # Assert
    frame.transaction_amount.setStyleSheet.assert_called_once()


def test_apply_transaction_style_by_status_failed():
    """Test apply_transaction_style_by_status for FAILED status."""
    # Setup
    frame = MagicMock()

    # Execute
    apply_transaction_style_by_status(
        frame, TransferStatusEnumModel.SENT.value, TransactionStatusEnumModel.FAILED,
    )

    # Assert
    assert frame.transaction_amount.setStyleSheet.call_count >= 1


def test_configure_transaction_time_display_settled():
    """Test configure_transaction_time_display for settled transfer."""
    # Setup
    frame = MagicMock()

    # Execute
    configure_transaction_time_display(
        frame, '12:00', '2024-01-01', TransferStatus.SETTLED,
    )

    # Assert
    frame.transaction_time.setText.assert_called_once_with('12:00')
    frame.transaction_date.setText.assert_called_once_with('2024-01-01')
    frame.transaction_time.setStyleSheet.assert_not_called()


def test_configure_transaction_time_display_not_settled():
    """Test configure_transaction_time_display for non-settled transfer."""
    # Setup
    frame = MagicMock()

    # Execute
    configure_transaction_time_display(
        frame, '12:00', '2024-01-01', TransferStatus.WAITING_CONFIRMATIONS,
    )

    # Assert
    frame.transaction_time.setStyleSheet.assert_called_once()


def test_handle_transaction_type_display_inflation():
    """Test handle_transaction_type_display for INFLATION status."""
    # Setup
    frame = MagicMock()
    transaction_type = MagicMock()

    # Execute
    handle_transaction_type_display(
        frame, TransferStatusEnumModel.INFLATION.value, transaction_type,
    )

    # Assert
    frame.transaction_type.setText.assert_called_once_with('INFLATION')
    frame.transaction_type.show.assert_called_once()
    frame.transfer_type.hide.assert_called_once()


def test_handle_transaction_type_display_internal_issuance():
    """Test handle_transaction_type_display for INTERNAL ISSUANCE."""
    # Setup
    frame = MagicMock()
    transaction_type = TransferKind.ISSUANCE

    # Execute
    handle_transaction_type_display(
        frame, TransferStatusEnumModel.INTERNAL.value, transaction_type,
    )

    # Assert
    frame.transaction_type.setText.assert_called_once_with('ISSUANCE')
    frame.transaction_type.show.assert_called_once()
    frame.transfer_type.hide.assert_called_once()


def test_handle_transaction_type_display_other():
    """Test handle_transaction_type_display for other status."""
    # Setup
    frame = MagicMock()
    transaction_type = MagicMock()

    # Execute
    handle_transaction_type_display(
        frame, TransferStatusEnumModel.SENT.value, transaction_type,
    )

    # Assert
    frame.transfer_type.show.assert_called_once()
    frame.transaction_type.hide.assert_called_once()
