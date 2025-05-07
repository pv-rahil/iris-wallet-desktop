"""Unit tests for main asset page service helper"""
from __future__ import annotations

from enum import Enum

import pytest

from src.data.service.helpers.main_asset_page_helper import get_asset_name
from src.data.service.helpers.main_asset_page_helper import get_offline_asset_ticker
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.custom_exception import ServiceOperationException
# Test cases for get_offline_asset_ticker helper of service


def test_get_offline_asset_ticker():
    """Case 1 : Test all network"""
    response_net_regtest = get_offline_asset_ticker(NetworkEnumModel.REGTEST)
    response_net_testnet = get_offline_asset_ticker(NetworkEnumModel.TESTNET)
    response_net_mainnet = get_offline_asset_ticker(NetworkEnumModel.MAINNET)
    assert response_net_mainnet == 'BTC'
    assert response_net_testnet == 'tBTC'
    assert response_net_regtest == 'rBTC'


def test_get_offline_asset_ticker_when_invalid_argument():
    """Case 2 : Test when invalid argument to get_offline_asset_ticker helper"""
    with pytest.raises(ServiceOperationException, match='FAILED_TO_GET_ASSET_TICKER'):
        get_offline_asset_ticker('random')


def test_get_offline_asset_ticker_when_invalid_network():
    """Case 3 : Test when invalid network to get_offline_asset_ticker helper"""
    class MockedNetworkEnumModel(str, Enum):
        """Mocked network enum to test code"""
        RANDOM = 'random'
    with pytest.raises(ServiceOperationException, match='INVALID_NETWORK_CONFIGURATION'):
        get_offline_asset_ticker(MockedNetworkEnumModel.RANDOM)

# Test cases for get_asset_name helper of service


def test_get_asset_name():
    'Case 4 : Test for all network to get asset name for bitcoin'
    response_net_regtest = get_asset_name(NetworkEnumModel.REGTEST)
    response_net_testnet = get_asset_name(NetworkEnumModel.TESTNET)
    response_net_mainnet = get_asset_name(NetworkEnumModel.MAINNET)
    assert response_net_mainnet == 'Bitcoin'
    assert response_net_testnet == 'tBitcoin'
    assert response_net_regtest == 'rBitcoin'


def test_get_asset_name_when_invalid_argument():
    """Case 5 : Test when invalid argument to get_asset_name helper"""
    with pytest.raises(ServiceOperationException, match='FAILED_TO_GET_ASSET_NAME'):
        get_asset_name('random')


def test_get_asset_name_when_invalid_network():
    """Case 6 : Test when invalid network to get_asset_name helper"""
    class MockedNetworkEnumModel(str, Enum):
        """Mocked network enum to test code"""
        RANDOM = 'random'
    with pytest.raises(ServiceOperationException, match='INVALID_NETWORK_CONFIGURATION'):
        get_asset_name(MockedNetworkEnumModel.RANDOM)
