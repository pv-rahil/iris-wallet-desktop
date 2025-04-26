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


@pytest.fixture
def mocked_config_wallet(mocker):
    """Mocked config wallet"""
    def _mocked_config_wallet(value):
        return mocker.patch(
            'src.data.repository.faucet_repository.FaucetRepository.config_wallet',
            return_value=value,
        )
    return _mocked_config_wallet


@pytest.fixture
def mocked_request_asset(mocker):
    """Mocked request asset"""
    def _mocked_request_asset(value):
        return mocker.patch(
            'src.data.repository.faucet_repository.FaucetRepository.request_asset',
            return_value=value,
        )
    return _mocked_request_asset
