"""Unit tests for bitcoin page service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument
from __future__ import annotations

from unittest.mock import patch

from src.data.service.bitcoin_page_service import BitcoinPageService
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_balance
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_expected_response
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_transaction_list


@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_success(mock_list_transactions, mock_get_btc_balance):
    """Test successful retrieval of BTC transactions with balance"""
    # Mocking the repository responses
    mock_get_btc_balance.return_value = mocked_balance
    mock_list_transactions.return_value = mocked_transaction_list

    # Call the service method
    response = BitcoinPageService.get_btc_transaction()

    # Verify the response
    assert isinstance(response, TransactionListWithBalanceResponse)
    assert len(response.transactions) == 2
    # Unconfirmed transactions first
    assert response.transactions[0].txid == 'tx124unconfirmed'
    assert response.transactions[1].txid == 'tx123confirmed'
    assert response.balance.vanilla.settled == 500000
    assert response.balance.vanilla.future == 1000000
    assert response.balance.vanilla.spendable == 700000


@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_empty_list(mock_list_transactions, mock_get_btc_balance):
    """Test when transaction list is empty"""
    # Mocking the repository responses
    mock_get_btc_balance.return_value = mocked_balance
    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[],
    )

    # Call the service method
    response = BitcoinPageService.get_btc_transaction()

    # Verify the response
    assert isinstance(response, TransactionListWithBalanceResponse)
    assert len(response.transactions) == 0
    assert response.balance.vanilla.settled == 500000


@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_sorting(mock_list_transactions, mock_get_btc_balance):
    """Test that transactions are properly sorted"""
    # Mocking the repository responses
    mock_get_btc_balance.return_value = mocked_balance

    # Create transactions with different confirmation times
    mock_list_transactions.return_value = mocked_expected_response

    # Call the service method
    response = BitcoinPageService.get_btc_transaction()

    # Verify sorting: unconfirmed first, then confirmed in reverse timestamp order
    assert len(response.transactions) == 2
    assert response.transactions[0].txid == 'tx124unconfirmed'
    assert response.transactions[1].txid == 'tx123confirmed'
