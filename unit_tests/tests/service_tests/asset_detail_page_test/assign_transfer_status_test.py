# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for AssetDetailPageService.assign_transfer_status."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from rgb_lib import TransferKind

from src.data.service.asset_detail_page_services import AssetDetailPageService
from src.model.enums.enums_model import TransferStatusEnumModel
from src.utils.custom_exception import ServiceOperationException


def _tx(kind, assignment_amount=None, requested_amount=None):
    """Helper to build a minimal transaction-like object for tests."""
    tx = MagicMock()
    tx.kind = kind
    # assignments: list with .amount
    if assignment_amount is not None:
        a = MagicMock()
        a.amount = assignment_amount
        tx.assignments = [a]
    else:
        tx.assignments = []
    # requested_assignment with .amount
    if requested_amount is not None:
        ra = MagicMock()
        ra.amount = requested_amount
        tx.requested_assignment = ra
    else:
        tx.requested_assignment = None
    # fields under test will be set by service
    tx.transfer_Status = None
    tx.amount_status = None
    return tx


def test_assign_status_issuance_uses_internal_and_plus_amount():
    """Test that issuance uses internal and plus amount."""
    tx = _tx(TransferKind.ISSUANCE, assignment_amount=5)

    AssetDetailPageService.assign_transfer_status(tx)

    assert tx.transfer_Status == TransferStatusEnumModel.INTERNAL
    assert tx.amount_status == '+5'


def test_assign_status_receive_blind_prefers_assignment_then_requested():
    """Test that receive blind prefers assignment then requested."""
    # Case 1: assignment amount present
    tx1 = _tx(TransferKind.RECEIVE_BLIND, assignment_amount=7)
    AssetDetailPageService.assign_transfer_status(tx1)
    assert tx1.transfer_Status == TransferStatusEnumModel.RECEIVED
    assert tx1.amount_status == '+7'

    # Case 2: no assignment, use requested amount
    tx2 = _tx(
        TransferKind.RECEIVE_BLIND,
        assignment_amount=None, requested_amount=3,
    )
    AssetDetailPageService.assign_transfer_status(tx2)
    assert tx2.transfer_Status == TransferStatusEnumModel.RECEIVED
    assert tx2.amount_status == '+3'

    # Case 3: neither present => +0
    tx3 = _tx(TransferKind.RECEIVE_BLIND)
    AssetDetailPageService.assign_transfer_status(tx3)
    assert tx3.transfer_Status == TransferStatusEnumModel.RECEIVED
    assert tx3.amount_status == '+0'


def test_assign_status_receive_witness_behaves_like_receive_blind():
    """Test that receive witness behaves like receive blind."""
    tx = _tx(TransferKind.RECEIVE_WITNESS, assignment_amount=11)
    AssetDetailPageService.assign_transfer_status(tx)
    assert tx.transfer_Status == TransferStatusEnumModel.RECEIVED
    assert tx.amount_status == '+11'


def test_assign_status_send_sets_minus_and_sent():
    """Test that send sets minus and sent."""
    tx = _tx(TransferKind.SEND, requested_amount=9)
    AssetDetailPageService.assign_transfer_status(tx)
    assert tx.transfer_Status == TransferStatusEnumModel.SENT
    assert tx.amount_status == '-9'


def test_assign_status_inflation_sets_plus_and_inflation():
    """Test that inflation sets plus and inflation."""
    tx = _tx(TransferKind.INFLATION, requested_amount=4)
    AssetDetailPageService.assign_transfer_status(tx)
    assert tx.transfer_Status == TransferStatusEnumModel.INFLATION
    assert tx.amount_status == '+4'


def test_assign_status_unknown_kind_raises():
    """Test that unknown kind raises."""
    class DummyKind:
        pass
    tx = _tx(DummyKind())
    with pytest.raises(ServiceOperationException):
        AssetDetailPageService.assign_transfer_status(tx)
