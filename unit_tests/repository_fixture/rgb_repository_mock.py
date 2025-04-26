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


# Mock for create_utxo method
@pytest.fixture
def mock_create_utxo(mocker):
    """Mocked create_utxo function."""
    def _mock_create_utxo(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.create_utxo',
            return_value=value,
        )
    return _mock_create_utxo

# Mock for get_asset_balance method


@pytest.fixture
def mock_get_asset_balance(mocker):
    """Mocked get_asset_balance function."""
    def _mock_get_asset_balance(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.get_asset_balance',
            return_value=value,
        )
    return _mock_get_asset_balance

# Mock for decode_invoice method


@pytest.fixture
def mock_decode_invoice(mocker):
    """Mocked decode_invoice function."""
    def _mock_decode_invoice(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.decode_invoice',
            return_value=value,
        )
    return _mock_decode_invoice

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

# Mock for rgb_invoice method


@pytest.fixture
def mock_rgb_invoice(mocker):
    """Mocked rgb_invoice function."""
    def _mock_rgb_invoice(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.rgb_invoice',
            return_value=value,
        )
    return _mock_rgb_invoice

# Mock for send_asset method


@pytest.fixture
def mock_send_asset(mocker):
    """Mocked send_asset function."""
    def _mock_send_asset(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.send_asset',
            return_value=value,
        )
    return _mock_send_asset

# Mock for issue_asset_nia method


@pytest.fixture
def mock_issue_asset_nia(mocker):
    """Mocked issue_asset_nia function."""
    def _mock_issue_asset_nia(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.issue_asset_nia',
            return_value=value,
        )
    return _mock_issue_asset_nia

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

# Mock for issue_asset_uda method


@pytest.fixture
def mock_issue_asset_uda(mocker):
    """Mocked issue_asset_uda function."""
    def _mock_issue_asset_uda(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.issue_asset_uda',
            return_value=value,
        )
    return _mock_issue_asset_uda


@pytest.fixture
def mock_post_asset_media(mocker):
    """Mocked issue_asset_uda function."""
    def _mock_post_asset_media(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.post_asset_media',
            return_value=value,
        )
    return _mock_post_asset_media


@pytest.fixture
def mock_fail_transfer(mocker):
    """Mocked fail transfer function"""
    def _mock_fail_transfer(value):
        return mocker.patch(
            'src.data.repository.rgb_repository.RgbRepository.fail_transfer',
            return_value=value,
        )
    return _mock_fail_transfer
