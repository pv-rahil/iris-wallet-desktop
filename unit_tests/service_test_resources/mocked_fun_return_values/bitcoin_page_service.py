"""Mocks and tests BitcoinPageService.get_btc_transaction for expected response."""
from __future__ import annotations

from unittest.mock import patch

from rgb_lib import BlockTime
from rgb_lib import TransactionType

from src.data.service.bitcoin_page_service import BitcoinPageService
from src.model.btc_model import Balance
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse

# Mock data for testing
mocked_balance = BalanceResponseModel(
    vanilla=Balance(settled=500000, future=1000000, spendable=700000),
    colored=Balance(settled=0, future=0, spendable=0),
)

mocked_transaction_list = TransactionListResponse(
    transactions=[
        Transaction(
            transaction_type=TransactionType.USER,
            txid='tx124unconfirmed',
            received=200000,
            sent=0,
            fee=1500,
            confirmation_time=None,
        ),
        Transaction(
            transaction_type=TransactionType.USER,
            txid='tx123confirmed',
            received=100000,
            sent=50000,
            fee=1000,
            confirmation_time=BlockTime(
                height=150, timestamp=1734929040,
            ),
        ),
    ],
)

# Mocked response you expect from the service
mocked_expected_response = TransactionListWithBalanceResponse(
    transactions=[
        Transaction(
            transaction_type=TransactionType.USER,
            txid='tx124unconfirmed',
            received=200000,
            sent=0,
            fee=1500,
            confirmation_time=None,
        ),
        Transaction(
            transaction_type=TransactionType.USER,
            txid='tx123confirmed',
            received=100000,
            sent=50000,
            fee=1000,
            confirmation_time=BlockTime(
                height=150, timestamp=1734929040,
            ),
        ),
    ],
    balance=BalanceResponseModel(
        vanilla=Balance(
            settled=500000, future=1000000, spendable=700000,
        ),
        colored=Balance(settled=0, future=0, spendable=0),
    ),
)

# Test function


@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction(mock_list_transactions, mock_get_btc_balance):
    """Test that BitcoinPageService.get_btc_transaction returns the expected TransactionListWithBalanceResponse when repository methods are mocked."""
    # Mocking the repository responses
    mock_get_btc_balance.return_value = mocked_balance
    mock_list_transactions.return_value = mocked_transaction_list

    # Calling the service method to get the transaction list
    response = BitcoinPageService.get_btc_transaction()

    # Assertions to verify the correctness of the response
    assert response == mocked_expected_response
