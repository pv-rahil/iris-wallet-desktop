# pylint: disable=redefined-outer-name, unused-argument
"""Unit tests for bitcoin page helper."""
import pytest
from unittest.mock import MagicMock
from rgb_lib import TransactionType
from src.data.service.helpers.bitcoin_page_helper import (
    calculate_transaction_amount,
    get_transaction_status
)
from src.model.btc_model import Transaction
from src.utils.custom_exception import ServiceOperationException
from src.model.enums.enums_model import TransactionStatusEnumModel, TransferStatusEnumModel
from src.utils.constant import NO_OF_UTXO, UTXO_SIZE_SAT


def test_calculate_transaction_amount_rgb_send():
    """Test calculation for RGB_SEND transaction type."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = str(TransactionType.RGB_SEND.value)
    transaction.sent = 1000
    transaction.received = 200

    # This covers line 20 (conversion from string)
    result = calculate_transaction_amount(transaction)
    assert result == '-800'
    assert transaction.transaction_type == TransactionType.RGB_SEND


def test_calculate_transaction_amount_received():
    """Test calculation for received user transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.USER
    transaction.sent = 0
    transaction.received = 500
    result = calculate_transaction_amount(transaction)
    assert result == '+500'


def test_calculate_transaction_amount_create_utxos():
    """Test calculation for CREATE_UTXOS transaction type."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.CREATE_UTXOS
    transaction.fee = 50
    result = calculate_transaction_amount(transaction)
    expected = f'-{(UTXO_SIZE_SAT * NO_OF_UTXO) + 50}'
    assert result == expected


def test_calculate_transaction_amount_none():
    """Test calculation for unknown transaction type returns None."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = 999 # Unknown type
    result = calculate_transaction_amount(transaction)
    assert result is None


def test_calculate_transaction_amount_exception():
    """Test exception handling in calculate_transaction_amount (covers lines 36-38)."""
    transaction = None # Will cause AttributeError or similar
    with pytest.raises(ServiceOperationException) as excinfo:
        calculate_transaction_amount(transaction)
    assert 'Failed' in str(excinfo.value) or 'NoneType' in str(excinfo.value)


def test_get_transaction_status_confirmed_sent():
    """Test status for confirmed sent transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.USER
    transaction.confirmation_time = 123456
    transaction.sent = 1000
    result = get_transaction_status(transaction)
    assert result == (TransferStatusEnumModel.SENT, TransactionStatusEnumModel.CONFIRMED)


def test_get_transaction_status_confirmed_received():
    """Test status for confirmed received transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.RGB_SEND
    transaction.confirmation_time = 123456
    transaction.sent = 0
    result = get_transaction_status(transaction)
    assert result == (TransferStatusEnumModel.RECEIVED, TransactionStatusEnumModel.CONFIRMED)


def test_get_transaction_status_pending():
    """Test status for pending transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.USER
    transaction.confirmation_time = None
    result = get_transaction_status(transaction)
    assert result == (TransferStatusEnumModel.ON_GOING_TRANSFER, TransactionStatusEnumModel.WAITING_CONFIRMATIONS)


def test_get_transaction_status_create_utxos_confirmed():
    """Test status for confirmed CREATE_UTXOS transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.CREATE_UTXOS
    transaction.confirmation_time = 123456
    result = get_transaction_status(transaction)
    assert result == (TransferStatusEnumModel.INTERNAL, TransactionStatusEnumModel.CONFIRMED)


def test_get_transaction_status_create_utxos_pending():
    """Test status for pending CREATE_UTXOS transaction."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = TransactionType.CREATE_UTXOS
    transaction.confirmation_time = None
    result = get_transaction_status(transaction)
    assert result == (TransferStatusEnumModel.ON_GOING_TRANSFER, TransactionStatusEnumModel.WAITING_CONFIRMATIONS)


def test_get_transaction_status_unknown():
    """Test status for unknown transaction type."""
    transaction = MagicMock(spec=Transaction)
    transaction.transaction_type = 999
    result = get_transaction_status(transaction)
    assert result == (None, None)


def test_get_transaction_status_exception():
    """Test exception handling in get_transaction_status (covers lines 78-81)."""
    transaction = None
    with pytest.raises(ServiceOperationException) as excinfo:
        get_transaction_status(transaction)
    assert 'Failed' in str(excinfo.value) or 'NoneType' in str(excinfo.value)
