"""Unit tests for setting_card_repository_mocked.py"""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_get_wallet_type(mocker):
    """Mocked get wallet type"""
    def _mock_get_wallet_type(value):
        return mocker.patch(
            'src.data.repository.setting_repository.SettingRepository.get_wallet_type',
            return_value=value,
        )

    return _mock_get_wallet_type


@pytest.fixture
def mock_get_wallet_network(mocker):
    """Mocked get wallet network"""
    def _mock_get_wallet_network(value):
        return mocker.patch(
            'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
            return_value=value,
        )

    return _mock_get_wallet_network


@pytest.fixture
def mock_is_exhausted_asset_enabled(mocker):
    """Mocked is exhausted asset enabled"""
    def _mock_is_exhausted_asset_enabled(value):
        return mocker.patch(
            'src.data.repository.setting_repository.SettingRepository.is_exhausted_asset_enabled',
            return_value=value,
        )

    return _mock_is_exhausted_asset_enabled


@pytest.fixture
def mock_set_value(mocker):
    """Mocked set value"""
    def _mock_set_value(value):
        return mocker.patch(
            'src.utils.keyring_storage.set_value',
            return_value=value,
        )

    return _mock_set_value


@pytest.fixture
def mock_handle_exceptions(mocker):
    """Mocked handle exceptions"""
    def _mock_handle_exceptions(value):
        return mocker.patch(
            'src.utils.handle_exception.handle_exceptions',
            return_value=value,
        )

    return _mock_handle_exceptions
