"""Unit tests for BTC repository"""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import Balance
from rgb_lib import BtcBalance
from rgb_lib import Transaction
from rgb_lib import Unspent

from src.data.repository.btc_repository import BtcRepository
from src.model.btc_model import AddressResponseModel
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel


@pytest.fixture
def mock_wallet():
    """Fixture for mocking the colored wallet"""
    with patch('src.data.repository.btc_repository.colored_wallet') as mock_colored_wallet:
        mock_wallet = MagicMock()
        mock_colored_wallet.wallet = mock_wallet
        mock_colored_wallet.online = True
        yield mock_wallet


@pytest.fixture
def mock_cache():
    """Fixture for mocking the cache"""
    with patch('src.data.repository.btc_repository.Cache') as mock_cache:
        mock_cache_session = MagicMock()
        mock_cache.get_cache_session.return_value = mock_cache_session
        yield mock_cache_session


def test_get_address(mock_wallet):
    """Test get_address method"""
    # Setup
    mock_wallet.get_address.return_value = 'bc1qxyz123'

    # Execute
    result = BtcRepository.get_address()

    # Assert
    assert isinstance(result, AddressResponseModel)
    assert result.address == 'bc1qxyz123'
    mock_wallet.get_address.assert_called_once()


def test_get_btc_balance(mock_wallet):
    """Test get_btc_balance method"""
    # Setup
    mock_balance = MagicMock(spec=BtcBalance)

    # Create proper Balance objects with spec instead of just MagicMocks
    mock_vanilla_balance = MagicMock(spec=Balance)
    mock_colored_balance = MagicMock(spec=Balance)

    mock_balance.vanilla = mock_vanilla_balance
    mock_balance.colored = mock_colored_balance
    mock_wallet.get_btc_balance.return_value = mock_balance

    # Execute
    result = BtcRepository.get_btc_balance()

    # Assert
    assert isinstance(result, BalanceResponseModel)
    assert result.vanilla == mock_vanilla_balance
    assert result.colored == mock_colored_balance
    mock_wallet.get_btc_balance.assert_called_once_with(
        online=True, skip_sync=False,
    )


def test_list_transactions(mock_wallet):
    """Test list_transactions method"""
    # Setup
    mock_tx1 = MagicMock(spec=Transaction)
    mock_tx2 = MagicMock(spec=Transaction)
    mock_wallet.list_transactions.return_value = [mock_tx1, mock_tx2]

    # Execute
    result = BtcRepository.list_transactions()

    # Assert
    assert isinstance(result, TransactionListResponse)
    assert len(result.transactions) == 2
    assert result.transactions[0] == mock_tx1
    assert result.transactions[1] == mock_tx2
    mock_wallet.list_transactions.assert_called_once_with(
        online=True, skip_sync=False,
    )


def test_list_unspents(mock_wallet):
    """Test list_unspents method"""
    # Setup
    mock_unspent1 = MagicMock(spec=Unspent)
    mock_unspent2 = MagicMock(spec=Unspent)
    mock_wallet.list_unspents.return_value = [mock_unspent1, mock_unspent2]

    # Execute
    request = UnspentListRequestModel(skip_sync=True, settled_only=True)
    result = BtcRepository.list_unspents(request)

    # Assert
    assert isinstance(result, UnspentsListResponseModel)
    assert len(result.unspents) == 2
    assert result.unspents[0] == mock_unspent1
    assert result.unspents[1] == mock_unspent2
    mock_wallet.list_unspents.assert_called_once_with(
        online=True, skip_sync=True, settled_only=True,
    )


def test_send_btc(mock_wallet, mock_cache):
    """Test send_btc method"""
    # Setup
    mock_wallet.send_btc.return_value = 'txid123456'

    # Execute
    request = SendBtcRequestModel(
        address='bc1qxyz123',
        amount=50000,
        fee_rate=5,
        skip_sync=False,
    )
    result = BtcRepository.send_btc(request)

    # Assert
    assert isinstance(result, SendBtcResponseModel)
    assert result.txid == 'txid123456'
    mock_wallet.send_btc.assert_called_once_with(
        online=True,
        skip_sync=False,
        address='bc1qxyz123',
        amount=50000,
        fee_rate=5,
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_send_btc_no_cache(mock_wallet):
    """Test send_btc method when cache is None"""
    # Setup
    mock_wallet.send_btc.return_value = 'txid123456'

    with patch('src.data.repository.btc_repository.Cache') as mock_cache:
        mock_cache.get_cache_session.return_value = None

        # Execute
        request = SendBtcRequestModel(
            address='bc1qxyz123',
            amount=50000,
            fee_rate=5,
            skip_sync=False,
        )
        result = BtcRepository.send_btc(request)

        # Assert
        assert isinstance(result, SendBtcResponseModel)
        assert result.txid == 'txid123456'
        mock_wallet.send_btc.assert_called_once()
        # No assertion for invalidate_cache as it shouldn't be called


def test_estimate_fee(mock_wallet):
    """Test estimate_fee method"""
    # Setup
    # Return expected_fee directly as a number instead of a dictionary
    mock_wallet.get_fee_estimation.return_value = 5

    # Execute
    request = EstimateFeeRequestModel(blocks=6)
    result = BtcRepository.estimate_fee(request)

    # Assert
    assert isinstance(result, EstimateFeeResponse)
    assert result.fee_rate == 5  # Check fee_rate instead of individual fields
    mock_wallet.get_fee_estimation.assert_called_once_with(
        online=True, blocks=6,
    )
