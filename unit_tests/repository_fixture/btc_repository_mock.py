""""
Mocked function for BTC repository.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_get_btc_balance(mocker):
    """Mocked get btc balance function"""
    def _mock_get_btc_balance(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.get_btc_balance',
            return_value=value,
        )

    return _mock_get_btc_balance


@pytest.fixture
def mock_list_transactions(mocker):
    """Mocked list transactions function"""
    def _mock_list_transactions(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.list_transactions',
            return_value=value,
        )

    return _mock_list_transactions


@pytest.fixture
def mock_get_address(mocker):
    """Mock the get_address method of BtcRepository."""
    def _mock_get_address(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.get_address',
            return_value=value,
        )
    return _mock_get_address


@pytest.fixture
def mock_list_unspents(mocker):
    """Mock the list_unspents method of BtcRepository."""
    def _mock_list_unspents(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.list_unspents',
            return_value=value,
        )
    return _mock_list_unspents


@pytest.fixture
def mock_send_btc(mocker):
    """Mock the send_btc method of BtcRepository."""
    def _mock_send_btc(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.send_btc',
            return_value=value,
        )
    return _mock_send_btc


@pytest.fixture
def mock_estimate_fee(mocker):
    """Mock the send_btc method of BtcRepository."""
    def _mock_estimate_fee(value):
        return mocker.patch(
            'src.data.repository.btc_repository.BtcRepository.estimate_fee',
            return_value=value,
        )
    return _mock_estimate_fee
