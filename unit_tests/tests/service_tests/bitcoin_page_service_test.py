"""Unit tests for bitcoin page service"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from rgb_lib import BlockTime
from rgb_lib import TransactionType

from src.data.service.bitcoin_page_service import BitcoinPageService
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_balance
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_expected_response
from unit_tests.service_test_resources.mocked_fun_return_values.bitcoin_page_service import mocked_transaction_list


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_success(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """Test successful retrieval of BTC transactions with balance"""
    # Mocking the repository responses
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
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


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_skips_none_transactions_and_formats_time(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """Transactions list may contain None; service should skip them and format date/time for confirmed ones."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance
    tx_confirmed = Transaction(
        transaction_type=TransactionType.USER,
        txid='tx_confirmed', received=1, sent=0, fee=0,
        confirmation_time=BlockTime(height=10, timestamp=1734929040),
    )
    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[None, tx_confirmed],
    )

    response = BitcoinPageService.get_btc_transaction()
    assert isinstance(response, TransactionListWithBalanceResponse)
    assert len(response.transactions) == 1
    tx = response.transactions[0]
    # formatted strings present
    assert tx.confirmation_date == '2024-12-23'  # 1734929040 UTC epoch date
    assert isinstance(tx.confirmation_normal_time, str)


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
@patch('src.data.service.bitcoin_page_service.calculate_transaction_amount')
def test_amount_none_raises_common_exception(mock_calc_amount, mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """If helper returns None for amount, service must raise CommonException via handle_exceptions."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance
    mock_calc_amount.return_value = None
    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[
            Transaction(
                transaction_type=TransactionType.USER,
                txid='tx1', received=0, sent=0, fee=0, confirmation_time=None,
            ),
        ],
    )

    try:
        BitcoinPageService.get_btc_transaction()
        assert False, 'Expected CommonException'
    except CommonException as exc:
        assert 'Unable to calculate amount' in exc.message


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
@patch('src.data.service.bitcoin_page_service.calculate_transaction_amount')
@patch('src.data.service.bitcoin_page_service.get_transaction_status')
def test_status_none_raises_common_exception(mock_get_status, mock_calc_amount, mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """If helper returns (None, None) status, service must raise CommonException."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance
    mock_calc_amount.return_value = '+0'
    mock_get_status.return_value = (None, None)
    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[
            Transaction(
                transaction_type=TransactionType.USER,
                txid='tx1', received=0, sent=0, fee=0, confirmation_time=None,
            ),
        ],
    )

    try:
        BitcoinPageService.get_btc_transaction()
        assert False, 'Expected CommonException'
    except CommonException as exc:
        assert 'Unable to get transaction status' in exc.message


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_missing_timestamp_raises_common_exception(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """If confirmation_time.timestamp is None, it should raise CommonException."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance
    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[
            Transaction(
                transaction_type=TransactionType.USER,
                txid='tx2', received=1, sent=0, fee=0,
                confirmation_time=BlockTime(height=1, timestamp=None),
            ),
        ],
    )

    try:
        BitcoinPageService.get_btc_transaction()
        assert False, 'Expected CommonException'
    except CommonException as exc:
        assert 'Confirmation time is missing a timestamp' in exc.message


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_attribute_error_in_confirmation_block(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """If confirmation_time lacks attribute access, AttributeError path is covered."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance

    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[
            Transaction(
                transaction_type=TransactionType.USER,
                txid='tx3', received=1, sent=0, fee=0,
                confirmation_time=1,
            ),
        ],
    )

    try:
        BitcoinPageService.get_btc_transaction()
        assert False, 'Expected CommonException'
    except CommonException as exc:
        assert 'AttributeError:' in exc.message


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_general_exception_in_confirmation_block(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """Cause a general exception inside datetime conversion to hit the generic except path."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance

    mock_list_transactions.return_value = TransactionListResponse(
        transactions=[
            Transaction(
                transaction_type=TransactionType.USER,
                txid='tx4', received=1, sent=0, fee=0,
                confirmation_time=BlockTime(
                    height=1, timestamp='not-a-number',
                ),
            ),
        ],
    )

    try:
        BitcoinPageService.get_btc_transaction()
        assert False, 'Expected CommonException'
    except CommonException as exc:
        assert 'An error occurred:' in exc.message


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_online_wallet_uses_repository(mock_get_wallet_type, mock_list_transactions, mock_get_btc_balance, mock_refresh_transfer):
    """Test online wallet uses repository"""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    mock_get_btc_balance.return_value = mocked_balance
    mock_list_transactions.return_value = mocked_transaction_list

    response = BitcoinPageService.get_btc_transaction()
    assert isinstance(response, TransactionListWithBalanceResponse)


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_offline_wallet_without_session_returns_zero_balances(mock_get_wallet_type, mock_get_session):
    """Test offline wallet without session returns zero balances"""
    mock_get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_session.return_value = None

    # Call the private fetcher via service to keep flow consistent
    with patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance') as _gb, \
            patch('src.data.repository.btc_repository.BtcRepository.list_transactions') as _lt:
        # repo should not be used in offline path with no session
        response = BitcoinPageService.get_btc_transaction()
        assert isinstance(response, TransactionListWithBalanceResponse)
        assert response.balance.vanilla.settled == 0
        assert len(response.transactions) == 0


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_offline_wallet_with_session_calls_session_methods(mock_get_wallet_type, mock_get_session):
    """Test offline wallet with session calls session methods"""
    mock_get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    session = MagicMock()
    session.get_btc_balance.return_value = mocked_balance
    session.list_transactions.return_value = mocked_transaction_list
    mock_get_session.return_value = session

    response = BitcoinPageService.get_btc_transaction()
    assert isinstance(response, TransactionListWithBalanceResponse)
    session.get_btc_balance.assert_called_once()
    session.list_transactions.assert_called_once()
    assert response.balance.vanilla.settled == 500000
    assert response.balance.vanilla.future == 1000000
    assert response.balance.vanilla.spendable == 700000


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_empty_list(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """Test when transaction list is empty"""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
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


@patch('src.data.service.bitcoin_page_service.RgbRepository.refresh_transfer')
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.repository.btc_repository.BtcRepository.get_btc_balance')
@patch('src.data.repository.btc_repository.BtcRepository.list_transactions')
def test_get_btc_transaction_sorting(mock_list_transactions, mock_get_btc_balance, mock_get_wallet_type, mock_refresh_transfer):
    """Test that transactions are properly sorted"""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
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
