""""
Mocked function for rgb repository.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_get_asset(mocker):
    """Mocked get asset function"""
    def _mock_get_asset(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.get_assets',
            return_value=value,
        )

    return _mock_get_asset


@pytest.fixture
def mock_get_asset_balance(mocker):
    """Mocked get_asset_balance function."""
    def _mock_get_asset_balance(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.get_asset_balance',
            return_value=value,
        )
    return _mock_get_asset_balance

# Mock for list_transfers method


@pytest.fixture
def mock_list_transfers(mocker):
    """Mocked list_transfers function."""
    def _mock_list_transfers(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.list_transfers',
            return_value=value,
        )
    return _mock_list_transfers

# Mock for refresh_transfer method


@pytest.fixture
def mock_refresh_transfer(mocker):
    """Mocked refresh_transfer function."""
    def _mock_refresh_transfer(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.refresh_transfer',
            return_value=value,
        )
    return _mock_refresh_transfer

# Mock for issue_asset_cfa method


@pytest.fixture
def mock_issue_asset_cfa(mocker):
    """Mocked issue_asset_cfa function."""
    def _mock_issue_asset_cfa(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.issue_asset_cfa',
            return_value=value,
        )
    return _mock_issue_asset_cfa
