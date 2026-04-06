"""Unit tests for BTC repository"""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import Balance
from rgb_lib import BtcBalance
from rgb_lib import InitOperationResult
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
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.rgb_model import CreateUtxosRequestModel


@pytest.fixture
def mock_wallet():
    """Fixture for mocking the colored wallet"""
    with patch('src.data.repository.btc_repository.colored_wallet') as mock_colored_wallet, \
            patch('src.utils.decorators.auto_sync_multisig.colored_wallet') as mock_decorator_wallet:
        mock_wallet = MagicMock()
        mock_colored_wallet.wallet = mock_wallet
        mock_colored_wallet.online = True
        # Disable multisig sync in decorator to avoid sync_with_bridge calls during tests
        mock_decorator_wallet.is_multisig = False
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
    assert result.tx_id == 'txid123456'
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
        assert result.tx_id == 'txid123456'
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


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_begin_with_session(mock_get_session, mock_wallet):
    """send_btc_begin should call wallet.send_btc_begin and add_psbt on session with purpose 'send_btc'."""
    mock_wallet.send_btc_begin.return_value = 'psbt_base64'
    svc = MagicMock()
    mock_get_session.return_value = svc
    req = SendBtcRequestModel(
        address='addr', amount=10, fee_rate=2, skip_sync=False,
    )
    psbt = BtcRepository.send_btc_begin(req)
    assert psbt == 'psbt_base64'
    mock_wallet.send_btc_begin.assert_called_once_with(
        online=True, address='addr', amount=10, fee_rate=2, skip_sync=False,
    )
    # Verify add_psbt was called with PsbtData object
    call_args = svc.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_base64'
    assert psbt_data.purpose == 'send_btc'


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_begin_without_session(mock_get_session, mock_wallet):
    """send_btc_begin should not fail when no session; returns psbt and no add_psbt calls."""
    mock_wallet.send_btc_begin.return_value = 'psbt_base64'
    mock_get_session.return_value = None
    req = SendBtcRequestModel(
        address='addr', amount=10, fee_rate=2, skip_sync=True,
    )
    psbt = BtcRepository.send_btc_begin(req)
    assert psbt == 'psbt_base64'
    mock_wallet.send_btc_begin.assert_called_once()


@patch('src.data.repository.btc_repository.Cache')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_end_with_session_and_cache(mock_get_session, mock_cache, mock_wallet):
    """send_btc_end should delete psbt from session and invalidate cache, returning tx id model."""
    mock_wallet.send_btc_end.return_value = 'txid999'
    svc = MagicMock()
    mock_get_session.return_value = svc
    cache = MagicMock()
    mock_cache.get_cache_session.return_value = cache
    res = BtcRepository.send_btc_end(
        BroadcastPsbtRequestModel(signed_psbt='abc', skip_sync=False),
    )
    assert isinstance(res, SendBtcResponseModel)
    assert res.tx_id == 'txid999'
    svc.delete_psbt.assert_called_once_with('abc')
    cache.invalidate_cache.assert_called_once()


@patch('src.data.repository.btc_repository.Cache')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_end_without_session_no_cache(mock_get_session, mock_cache, mock_wallet):
    """send_btc_end should work without session and without cache."""
    mock_wallet.send_btc_end.return_value = 'txid777'
    mock_get_session.return_value = None
    mock_cache.get_cache_session.return_value = None
    res = BtcRepository.send_btc_end(
        BroadcastPsbtRequestModel(signed_psbt='zzz', skip_sync=True),
    )
    assert res.tx_id == 'txid777'
    mock_wallet.send_btc_end.assert_called_once()


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_begin_with_session(mock_get_session, mock_wallet):
    """create_utxos_begin should add psbt with provided purpose when session exists."""
    mock_wallet.create_utxos_begin.return_value = 'psbt_colorable'
    svc = MagicMock()
    mock_get_session.return_value = svc
    req = CreateUtxosRequestModel(
        online=True, up_to=False, num=2, size=546, fee_rate=3, skip_sync=False,
    )
    psbt = BtcRepository.create_utxos_begin(req, purpose='create_utxos')
    assert psbt == 'psbt_colorable'
    mock_wallet.create_utxos_begin.assert_called_once_with(
        online=True, up_to=False, num=2, size=546, fee_rate=3, skip_sync=False,
    )
    # Verify add_psbt was called with PsbtData object
    call_args = svc.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'psbt_colorable'
    assert psbt_data.purpose == 'create_utxos'


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_begin_without_session(mock_get_session, mock_wallet):
    """create_utxos_begin should not call add_psbt when session is None."""
    mock_wallet.create_utxos_begin.return_value = 'psbt_colorable'
    mock_get_session.return_value = None
    req = CreateUtxosRequestModel(
        online=True, up_to=False, num=1, size=546, fee_rate=1, skip_sync=True,
    )
    psbt = BtcRepository.create_utxos_begin(req)
    assert psbt == 'psbt_colorable'


@patch('src.data.repository.btc_repository.Cache')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_end_with_session_and_cache(mock_get_session, mock_cache, mock_wallet):
    """create_utxos_end should delete psbt and invalidate cache, returning count."""
    mock_wallet.create_utxos_end.return_value = 3
    svc = MagicMock()
    mock_get_session.return_value = svc
    cache = MagicMock()
    mock_cache.get_cache_session.return_value = cache
    count = BtcRepository.create_utxos_end(
        BroadcastPsbtRequestModel(signed_psbt='psbt', skip_sync=False),
    )
    assert count == 3
    svc.delete_psbt.assert_called_once_with('psbt')
    cache.invalidate_cache.assert_called_once()


@patch('src.data.repository.btc_repository.Cache')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_end_without_session_no_cache(mock_get_session, mock_cache, mock_wallet):
    """create_utxos_end should still return value without session and without cache."""
    mock_wallet.create_utxos_end.return_value = 1
    mock_get_session.return_value = None
    mock_cache.get_cache_session.return_value = None
    count = BtcRepository.create_utxos_end(
        BroadcastPsbtRequestModel(signed_psbt='p', skip_sync=True),
    )
    assert count == 1


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_init_with_session(mock_get_session, mock_wallet):
    """send_btc_init stores result.psbt in session with purpose 'send_btc' and returns InitOperationResult."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'btc_init_psbt'
    mock_wallet.send_btc_init.return_value = result_obj
    svc = MagicMock()
    mock_get_session.return_value = svc

    req = SendBtcRequestModel(
        address='addr', amount=5000, fee_rate=1, skip_sync=False,
    )
    res = BtcRepository.send_btc_init(req)

    assert res == result_obj
    mock_wallet.send_btc_init.assert_called_once_with(
        online=True, address='addr', amount=5000, fee_rate=1, skip_sync=False,
    )
    # Verify add_psbt was called with PsbtData object
    call_args = svc.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'btc_init_psbt'
    assert psbt_data.purpose == 'send_btc'


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_btc_init_without_session(mock_get_session, mock_wallet):
    """send_btc_init should not fail when session is None."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'btc_init_psbt'
    mock_wallet.send_btc_init.return_value = result_obj
    mock_get_session.return_value = None

    req = SendBtcRequestModel(
        address='addr', amount=1000, fee_rate=2, skip_sync=True,
    )
    res = BtcRepository.send_btc_init(req)

    assert res == result_obj
    mock_wallet.send_btc_init.assert_called_once()


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_init_with_session(mock_get_session, mock_wallet):
    """create_utxos_init stores result.psbt in session with provided purpose."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'utxo_init_psbt'
    mock_wallet.create_utxos_init.return_value = result_obj
    svc = MagicMock()
    mock_get_session.return_value = svc

    req = CreateUtxosRequestModel(
        online=True, up_to=True, num=3, size=546, fee_rate=2, skip_sync=False,
    )
    res = BtcRepository.create_utxos_init(req, purpose='create_utxos')

    assert res == result_obj
    mock_wallet.create_utxos_init.assert_called_once_with(
        online=True, up_to=True, num=3, size=546, fee_rate=2, skip_sync=False,
    )
    # Verify add_psbt was called with PsbtData object
    call_args = svc.add_psbt.call_args
    assert call_args is not None
    psbt_data = call_args[0][0]
    assert psbt_data.psbt_base64 == 'utxo_init_psbt'
    assert psbt_data.purpose == 'create_utxos'


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_create_utxos_init_without_session(mock_get_session, mock_wallet):
    """create_utxos_init should not fail when session is None."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'utxo_init_psbt'
    mock_wallet.create_utxos_init.return_value = result_obj
    mock_get_session.return_value = None

    req = CreateUtxosRequestModel(
        online=True, up_to=False, num=1, size=300, fee_rate=1, skip_sync=True,
    )
    res = BtcRepository.create_utxos_init(req)

    assert res == result_obj
    mock_wallet.create_utxos_init.assert_called_once()
