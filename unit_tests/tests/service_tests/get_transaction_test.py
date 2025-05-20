"""Unit tests for bitcoin page service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access, unused-import
from __future__ import annotations

import pytest

from src.data.service.bitcoin_page_service import BitcoinPageService
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse
from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.utils.constant import NO_OF_UTXO
from src.utils.constant import UTXO_SIZE_SAT
from src.utils.custom_exception import CommonException
from unit_tests.repository_fixture.btc_repository_mock import mock_get_btc_balance
from unit_tests.repository_fixture.btc_repository_mock import mock_list_transactions
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_expected_list_transaction_all
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_list_transaction_all
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_list_transaction_empty
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_type_createutxo
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_type_unknown
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_type_user_receive
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_type_user_send
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_unconfirm_type_createutxos
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_unconfirm_type_user_receive
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mock_data_transaction_unconfirm_type_user_send
from unit_tests.service_test_resources.mocked_fun_return_values.get_transaction_service import mocked_data_balance


def test_list_transaction_all(mock_list_transactions, mock_get_btc_balance):
    """case 1 : When repository return positive response (all)"""
    list_transaction_mock_object = mock_list_transactions(
        mock_data_list_transaction_all,
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()

    for actual, expected in zip(result.transactions, mock_data_expected_list_transaction_all.transactions):
        assert actual.transaction_type == expected.transaction_type
        assert actual.txid == expected.txid
        assert actual.received == expected.received
        assert actual.sent == expected.sent
        assert actual.fee == expected.fee
        assert actual.confirmation_time == expected.confirmation_time

    assert result.balance == mock_data_expected_list_transaction_all.balance

    assert isinstance(result, TransactionListWithBalanceResponse)
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_when_empty_array(mock_list_transactions, mock_get_btc_balance):
    """case 2 : when repository return empty array"""
    list_transaction_mock_object = mock_list_transactions(
        mock_data_list_transaction_empty,
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    assert result == mock_data_list_transaction_empty
    assert isinstance(result, TransactionListWithBalanceResponse)
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_user_unconfirm(mock_list_transactions, mock_get_btc_balance):
    """case 3 : when transaction type is user and unconfirm"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_unconfirm_type_user_send],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    deducted_amount = result.transactions[0].sent - \
        result.transactions[0].received
    assert result.transactions[0].amount == str(-deducted_amount)
    assert result.transactions[0].confirmation_time is None
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.WAITING_CONFIRMATIONS
    )
    assert (
        result.transactions[0].transfer_status
        == TransferStatusEnumModel.ON_GOING_TRANSFER
    )
    assert (
        result.transactions[0].txid
        == mock_data_transaction_unconfirm_type_user_send.txid
    )
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_unconfirm_type_user_send.transaction_type
    )
    assert (
        result.transactions[0].received
        == mock_data_transaction_unconfirm_type_user_send.received
    )
    assert (
        result.transactions[0].sent
        == mock_data_transaction_unconfirm_type_user_send.sent
    )
    assert (
        result.transactions[0].fee == mock_data_transaction_unconfirm_type_user_send.fee
    )
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_user_confirm(mock_list_transactions, mock_get_btc_balance):
    """case 4 : when transaction type is user and confirm"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_type_user_send],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    deducted_amount = result.transactions[0].sent - \
        result.transactions[0].received
    assert result.transactions[0].amount == str(-deducted_amount)
    assert result.transactions[0].confirmation_time.height == int(105)
    assert result.transactions[0].confirmation_time.timestamp == int(
        1717006775,
    )
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.CONFIRMED
    )
    assert result.transactions[0].transfer_status == TransferStatusEnumModel.SENT
    assert result.transactions[0].txid == mock_data_transaction_type_user_send.txid
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_type_user_send.transaction_type
    )
    assert (
        result.transactions[0].received == mock_data_transaction_type_user_send.received
    )
    assert result.transactions[0].sent == mock_data_transaction_type_user_send.sent
    assert result.transactions[0].fee == mock_data_transaction_type_user_send.fee
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_internal_unconfirm(mock_list_transactions, mock_get_btc_balance):
    """case 5 : when transaction type is create utxos and unconfirm"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_unconfirm_type_createutxos],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    deducted_amount = (UTXO_SIZE_SAT * NO_OF_UTXO) + result.transactions[0].fee
    assert result.transactions[0].amount == str(-deducted_amount)
    assert result.transactions[0].confirmation_time is None
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.WAITING_CONFIRMATIONS
    )
    assert (
        result.transactions[0].transfer_status
        == TransferStatusEnumModel.ON_GOING_TRANSFER
    )
    assert (
        result.transactions[0].txid
        == mock_data_transaction_unconfirm_type_createutxos.txid
    )
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_unconfirm_type_createutxos.transaction_type
    )
    assert (
        result.transactions[0].received
        == mock_data_transaction_unconfirm_type_createutxos.received
    )
    assert (
        result.transactions[0].sent
        == mock_data_transaction_unconfirm_type_createutxos.sent
    )
    assert (
        result.transactions[0].fee
        == mock_data_transaction_unconfirm_type_createutxos.fee
    )
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_internal_confirm(mock_list_transactions, mock_get_btc_balance):
    """case 6 : when transaction type is create utxos and confirm"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_type_createutxo],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )

    result = BitcoinPageService.get_btc_transaction()
    deducted_amount = (UTXO_SIZE_SAT * NO_OF_UTXO) + result.transactions[0].fee
    assert result.transactions[0].amount == str(-deducted_amount)
    assert result.transactions[0].confirmation_time.height == int(106)
    assert result.transactions[0].confirmation_time.timestamp == int(
        1717006902,
    )
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.CONFIRMED
    )
    assert result.transactions[0].transfer_status == TransferStatusEnumModel.INTERNAL
    assert result.transactions[0].txid == mock_data_transaction_type_createutxo.txid
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_type_createutxo.transaction_type
    )
    assert (
        result.transactions[0].received
        == mock_data_transaction_type_createutxo.received
    )
    assert result.transactions[0].sent == mock_data_transaction_type_createutxo.sent
    assert result.transactions[0].fee == mock_data_transaction_type_createutxo.fee
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_user_receive_unconfirm(mock_list_transactions, mock_get_btc_balance):
    """case 7 : when transaction type is user receive and unconfirm receive"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_unconfirm_type_user_receive],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    received_amount = result.transactions[0].received
    formatted_received_amount = f'{received_amount:+}'
    assert result.transactions[0].amount == formatted_received_amount
    assert result.transactions[0].confirmation_time is None
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.WAITING_CONFIRMATIONS
    )
    assert (
        result.transactions[0].transfer_status
        == TransferStatusEnumModel.ON_GOING_TRANSFER
    )
    assert (
        result.transactions[0].txid
        == mock_data_transaction_unconfirm_type_user_receive.txid
    )
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_unconfirm_type_user_receive.transaction_type
    )
    assert (
        result.transactions[0].received
        == mock_data_transaction_unconfirm_type_user_receive.received
    )
    assert result.transactions[0].sent == mock_data_transaction_unconfirm_type_user_receive.sent
    assert result.transactions[0].fee == mock_data_transaction_unconfirm_type_user_receive.fee
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_user_receive_confirm(mock_list_transactions, mock_get_btc_balance):
    """case 8 : when transaction type is user receive and confirm receive"""
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_type_user_receive],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )
    result = BitcoinPageService.get_btc_transaction()
    received_amount = result.transactions[0].received
    formatted_received_amount = f'{received_amount:+}'
    assert result.transactions[0].amount == formatted_received_amount
    assert result.transactions[0].confirmation_time.height == int(104)
    assert result.transactions[0].confirmation_time.timestamp == int(
        1717006478,
    )
    assert (
        result.transactions[0].transaction_status
        == TransactionStatusEnumModel.CONFIRMED
    )
    assert result.transactions[0].transfer_status == TransferStatusEnumModel.RECEIVED
    assert result.transactions[0].txid == mock_data_transaction_type_user_receive.txid
    assert (
        result.transactions[0].transaction_type
        == mock_data_transaction_type_user_receive.transaction_type
    )
    assert (
        result.transactions[0].received
        == mock_data_transaction_type_user_receive.received
    )
    assert result.transactions[0].sent == mock_data_transaction_type_user_receive.sent
    assert result.transactions[0].fee == mock_data_transaction_type_user_receive.fee
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def test_list_transaction_type_unknown(mock_list_transactions, mock_get_btc_balance):
    """Case 9: when transaction type is unknown, it should raise an error."""
    # Setup the mock as necessary, if additional code setup is needed, ensure it is correct here
    list_transaction_mock_object = mock_list_transactions(
        TransactionListResponse(
            transactions=[mock_data_transaction_type_unknown],
        ),
    )
    balance_mock_object = mock_get_btc_balance(
        mocked_data_balance,
    )

    # Execute the function under test and expect CommonException instead
    with pytest.raises(CommonException) as exc_info:
        BitcoinPageService.get_btc_transaction()
    # Assert the exception message is as expected
    assert str(exc_info.value) == 'Unable to calculate amount None'
    list_transaction_mock_object.assert_called_once()
    balance_mock_object.assert_called_once()


def mock_json_response():
    """Mock json response"""
    if mock_data_list_transaction_all is None:
        return {
            'transactions': [],
        }

    transactions = []
    for tx in mock_data_list_transaction_all.transactions:
        if tx.transaction_type == 'CreateUtxos':
            tx.amount = '-130114'
        transactions.append(tx)
    return {
        'transactions': transactions,
    }
