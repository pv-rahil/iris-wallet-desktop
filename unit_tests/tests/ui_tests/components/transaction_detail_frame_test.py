"""Unit test for transaction detail frame component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.model.transaction_detail_page_model import TransactionDetailPageModel
from src.views.components.transaction_detail_frame import TransactionDetailFrame


@pytest.fixture
def transaction_detail_frame():
    """Fixture to create a TransactionDetailFrame with the required fields."""
    # Providing the missing required fields in TransactionDetailPageModel
    params = TransactionDetailPageModel(
        tx_id='12345',  # Example transaction ID
        transaction_date='2024-12-25',
        transaction_time='12:00 PM',
        transaction_amount='100.00',
        transaction_type='Transfer',
        amount='100.00',  # Add missing 'amount' field
        transaction_status='Completed',  # Add missing 'transaction_status' field
    )
    frame = TransactionDetailFrame(params=params)
    frame.show()
    return frame


def test_initialization(transaction_detail_frame):
    """Test the initialization of the TransactionDetailFrame."""
    frame = transaction_detail_frame

    assert frame.frame_grid_layout is not None


def test_click_behavior(transaction_detail_frame, qtbot):
    """Test that the frame emits the click_frame signal when clicked."""

    # Create a mock params object
    mock_params = MagicMock()
    mock_params.transaction_date = '2024-12-25'
    mock_params.transaction_time = '12:00 PM'
    mock_params.transaction_amount = '100.00'
    mock_params.transaction_type = 'Transfer'

    # Assign the mock params to the frame
    frame = transaction_detail_frame
    frame.params = mock_params

    # Use qtbot to wait for the click_frame signal
    with qtbot.waitSignal(frame.click_frame, timeout=1000) as blocker:
        qtbot.mouseClick(frame, Qt.LeftButton)

    # Assert that the signal was emitted with the correct params
    assert blocker.args == [mock_params]


def test_no_transaction_frame():
    """Test the no_transaction_frame when no transactions are present."""
    frame = TransactionDetailFrame()

    # Simulate a scenario where there are no transactions
    no_transaction_widget = frame.no_transaction_frame()

    # Ensure the no transaction message is displayed
    assert no_transaction_widget is not None
    assert no_transaction_widget.findChild(
        QLabel,
    ).text() == 'no_transfer_history'

    # Verify that the transfer type button is hidden
    assert frame.transfer_type.isHidden()
