"""Unit test for bitcoin view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.btc_model import Balance
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListWithBalanceResponse
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_FAILED_TO_GET_BALANCE
from src.utils.error_message import ERROR_NAVIGATION_BITCOIN_PAGE
from src.utils.error_message import ERROR_NAVIGATION_RECEIVE_BITCOIN_PAGE
from src.utils.error_message import ERROR_TITLE
from src.viewmodels.bitcoin_view_model import BitcoinViewModel
from src.views.components.toast import ToastManager


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture for creating a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def bitcoin_view_model(mock_page_navigation):
    """Fixture for creating an instance of bitcoin_view_model with a mock page navigation object."""
    return BitcoinViewModel(mock_page_navigation)


def test_on_send_bitcoin_click(bitcoin_view_model, mock_page_navigation):
    """Test for send bitcoin button clicked work as expected"""
    bitcoin_view_model.on_send_bitcoin_click()
    mock_page_navigation.send_bitcoin_page.assert_called_once()


def test_on_receive_bitcoin_click(bitcoin_view_model, mock_page_navigation):
    """Test for receive bitcoin button clicked work as expected"""
    bitcoin_view_model.on_receive_bitcoin_click()
    mock_page_navigation.receive_bitcoin_page.assert_called_once()


def test_on_send_bitcoin_click_exception(bitcoin_view_model, mock_page_navigation, mocker):
    """Test for handling exceptions when sending bitcoin."""
    mock_toast = mocker.patch.object(ToastManager, 'error')
    mock_page_navigation.send_bitcoin_page.side_effect = CommonException(
        'Navigation error',
    )

    bitcoin_view_model.on_send_bitcoin_click()

    mock_page_navigation.send_bitcoin_page.assert_called_once()
    mock_toast.assert_called_once_with(
        parent=None,
        title=ERROR_TITLE,
        description=ERROR_NAVIGATION_BITCOIN_PAGE.format('Navigation error'),
    )


def test_on_receive_bitcoin_click_exception(bitcoin_view_model, mock_page_navigation, mocker):
    """Test for handling exceptions when receiving bitcoin."""
    mock_toast = mocker.patch.object(ToastManager, 'error')
    mock_page_navigation.receive_bitcoin_page.side_effect = CommonException(
        'Navigation error',
    )

    bitcoin_view_model.on_receive_bitcoin_click()

    mock_page_navigation.receive_bitcoin_page.assert_called_once()
    mock_toast.assert_called_once_with(
        parent=None,
        title=ERROR_TITLE,
        description=ERROR_NAVIGATION_RECEIVE_BITCOIN_PAGE.format(
            'Navigation error',
        ),
    )


@patch('src.data.service.bitcoin_page_service.BitcoinPageService.get_btc_transaction')
def test_get_transaction_list_success(mock_bitcoin_page_service, bitcoin_view_model, mocker):
    """Test for get transaction list work as expected in success scenario"""
    mock_transaction_list = TransactionListWithBalanceResponse(
        transactions=[
            Transaction(
                txid='12345', received=1000, sent=0, fee=0, transaction_type='receive', confirmation_time=14785965447,
            ),
        ],
        balance=BalanceResponseModel(
            vanilla=Balance(
                settled=1000, future=1000, spendable=150000000,
            ),
            colored=Balance(
                settled=2000, future=1000, spendable=30000000,
            ),
        ),
    )
    mock_loading_started = Mock()
    mock_loading_finished = Mock()
    mock_transaction_loaded = Mock()
    mock_cache = mocker.patch.object(Cache, 'get_cache_session')
    mock_cache_instance = Mock()
    mock_cache_instance.fetch_cache.return_value = (None, False)
    mock_cache.return_value = mock_cache_instance

    bitcoin_view_model.loading_started.connect(mock_loading_started)
    bitcoin_view_model.loading_finished.connect(mock_loading_finished)
    bitcoin_view_model.transaction_loaded.connect(mock_transaction_loaded)

    mock_bitcoin_page_service.return_value = mock_transaction_list
    bitcoin_view_model.get_transaction_list(bitcoin_txn_hard_refresh=True)

    # Simulate worker completion with both result and cache validity flag
    bitcoin_view_model.worker.result.emit(mock_transaction_list, True)

    mock_cache_instance.invalidate_cache.assert_called_once()
    mock_loading_started.assert_called_once_with(True)
    mock_loading_finished.assert_called_once_with(False)
    mock_transaction_loaded.assert_called_once()

    assert bitcoin_view_model.transaction == mock_transaction_list.transactions
    assert bitcoin_view_model.spendable_bitcoin_balance_with_suffix == '150000000 SATS'
    assert bitcoin_view_model.total_bitcoin_balance_with_suffix == '1000 SATS'


@patch('src.data.service.bitcoin_page_service.BitcoinPageService.get_btc_transaction')
def test_get_transaction_list_failure(mock_bitcoin_page_service, bitcoin_view_model, mocker):
    """Test for get transaction list work as expected in failure scenario"""
    mock_loading_started = Mock()
    mock_loading_finished = Mock()
    mock_error = Mock()
    mock_toast = mocker.patch.object(ToastManager, 'error')
    mock_cache = mocker.patch.object(Cache, 'get_cache_session')
    mock_cache_instance = Mock()
    mock_cache_instance.fetch_cache.return_value = (None, False)
    mock_cache.return_value = mock_cache_instance

    bitcoin_view_model.loading_started.connect(mock_loading_started)
    bitcoin_view_model.loading_finished.connect(mock_loading_finished)
    bitcoin_view_model.error.connect(mock_error)

    error = CommonException('API error')
    mock_bitcoin_page_service.side_effect = error
    bitcoin_view_model.get_transaction_list(bitcoin_txn_hard_refresh=True)

    # Simulate worker error
    bitcoin_view_model.worker.error.emit(error)

    mock_cache_instance.invalidate_cache.assert_called_once()
    mock_loading_started.assert_called_once_with(True)
    mock_loading_finished.assert_called_once_with(False)
    mock_error.assert_called_once_with('API error')
    mock_toast.assert_called_once_with(
        parent=None,
        title=ERROR_TITLE,
        description=ERROR_FAILED_TO_GET_BALANCE.format('API error'),
    )
    assert bitcoin_view_model.transaction == []
    assert bitcoin_view_model.spendable_bitcoin_balance_with_suffix == '0'
    assert bitcoin_view_model.total_bitcoin_balance_with_suffix == '0'


def test_on_hard_refresh_success(bitcoin_view_model, mocker):
    """Test for on_hard_refresh method when successful"""
    mock_get_transaction_list = mocker.patch.object(
        bitcoin_view_model, 'get_transaction_list',
    )

    bitcoin_view_model.on_hard_refresh()

    mock_get_transaction_list.assert_called_once_with(
        bitcoin_txn_hard_refresh=True,
    )


def test_on_hard_refresh_failure(bitcoin_view_model, mocker):
    """Test for on_hard_refresh method when it fails"""
    error = CommonException('Test error')
    mock_get_transaction_list = mocker.patch.object(
        bitcoin_view_model,
        'get_transaction_list',
        side_effect=error,
    )
    mock_toast = mocker.patch.object(ToastManager, 'error')

    bitcoin_view_model.on_hard_refresh()

    mock_get_transaction_list.assert_called_once_with(
        bitcoin_txn_hard_refresh=True,
    )
    mock_toast.assert_called_once_with(description=error.message)
