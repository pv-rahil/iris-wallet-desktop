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
