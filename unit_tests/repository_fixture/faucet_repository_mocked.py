""""
Mocked function for faucet repository.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def mocked_list_available_faucet_asset(mocker):
    """Mocked list available faucet asset"""
    def _mocked_list_available_faucet_asset(value):
        return mocker.patch(
            'src.data.repository.faucet_repository.FaucetRepository.list_available_faucet_asset',
            return_value=value,
        )
    return _mocked_list_available_faucet_asset
