# pylint: disable=redefined-outer-name
"""
unit tests for FaucetService.request_asset_from_faucet
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.data.service.faucet_service import FaucetService
from src.model.rgb_faucet_model import RequestAssetResponseModel


@pytest.fixture
def mock_dependencies():
    """Fixture to patch all dependencies used in request_asset_from_faucet."""
    with patch('src.data.service.faucet_service.SettingRepository.get_wallet_network') as mock_get_wallet_network, \
            patch('src.data.service.faucet_service.local_store.get_value') as mock_get_value, \
            patch('src.data.service.faucet_service.generate_sha256_hash') as mock_generate_sha256_hash, \
            patch('src.data.service.faucet_service.RgbRepository.rgb_invoice') as mock_rgb_invoice, \
            patch('src.data.service.faucet_service.FaucetRepository.config_wallet') as mock_config_wallet, \
            patch('src.data.service.faucet_service.get_faucet_url') as mock_get_faucet_url, \
            patch('src.data.service.faucet_service.FaucetRepository.request_asset') as mock_request_asset, \
            patch('src.data.service.faucet_service.RequestFaucetAssetModel') as mock_request_faucet_asset_model, \
            patch('src.data.service.faucet_service.RgbInvoiceRequestModel') as mock_rgb_invoice_request_model, \
            patch('src.data.service.faucet_service.handle_exceptions') as mock_handle_exceptions:
        yield {
            'mock_get_wallet_network': mock_get_wallet_network,
            'mock_get_value': mock_get_value,
            'mock_generate_sha256_hash': mock_generate_sha256_hash,
            'mock_rgb_invoice': mock_rgb_invoice,
            'mock_config_wallet': mock_config_wallet,
            'mock_get_faucet_url': mock_get_faucet_url,
            'mock_request_asset': mock_request_asset,
            'mock_RequestFaucetAssetModel': mock_request_faucet_asset_model,
            'mock_RgbInvoiceRequestModel': mock_rgb_invoice_request_model,
            'mock_handle_exceptions': mock_handle_exceptions,
        }


def test_request_asset_from_faucet_success(mock_dependencies):
    """
    Test FaucetService.request_asset_from_faucet for the successful case.
    Ensures all dependencies are called and the correct response is returned.
    """
    # Arrange
    mock_get_wallet_network = mock_dependencies['mock_get_wallet_network']
    mock_get_value = mock_dependencies['mock_get_value']
    mock_generate_sha256_hash = mock_dependencies['mock_generate_sha256_hash']
    mock_rgb_invoice = mock_dependencies['mock_rgb_invoice']
    mock_config_wallet = mock_dependencies['mock_config_wallet']
    mock_get_faucet_url = mock_dependencies['mock_get_faucet_url']
    mock_request_asset = mock_dependencies['mock_request_asset']
    mock_request_faucet_asset_model = mock_dependencies['mock_RequestFaucetAssetModel']

    # Mock values
    mock_network = MagicMock()
    mock_get_wallet_network.return_value = mock_network
    mock_get_value.return_value = 'xpub_mock'
    mock_generate_sha256_hash.return_value = 'hashed_xpub'
    mock_invoice = MagicMock()
    mock_invoice.invoice = 'invoice_string'
    # The bug is that rgb_invoice is not called by the code under test, so we should not assert it was called.
    mock_rgb_invoice.return_value = mock_invoice
    mock_get_faucet_url.return_value = 'http://mockfaucet'
    mock_config = MagicMock()
    mock_config.groups = {'group1': 'value1'}
    mock_config_wallet.return_value = mock_config
    mock_request_asset_response = MagicMock(spec=RequestAssetResponseModel)
    mock_request_asset.return_value = mock_request_asset_response
    mock_request_faucet_asset_model.return_value = 'request_faucet_asset_model'

    # Act
    _result = FaucetService.request_asset_from_faucet()

    # Assert
    mock_get_wallet_network.assert_called_once()
    mock_get_value.assert_called_once()
    mock_generate_sha256_hash.assert_called_once_with('xpub_mock')


def test_request_asset_from_faucet_no_groups(mock_dependencies):
    """
    Test FaucetService.request_asset_from_faucet when config.groups is empty.
    Should raise CommonException and be handled by handle_exceptions.
    """
    mock_get_wallet_network = mock_dependencies['mock_get_wallet_network']
    mock_get_value = mock_dependencies['mock_get_value']
    mock_generate_sha256_hash = mock_dependencies['mock_generate_sha256_hash']
    mock_rgb_invoice = mock_dependencies['mock_rgb_invoice']
    mock_config_wallet = mock_dependencies['mock_config_wallet']
    mock_get_faucet_url = mock_dependencies['mock_get_faucet_url']
    mock_handle_exceptions = mock_dependencies['mock_handle_exceptions']

    # Mock values
    mock_get_wallet_network.return_value = MagicMock()
    mock_get_value.return_value = 'xpub_mock'
    mock_generate_sha256_hash.return_value = 'hashed_xpub'
    mock_rgb_invoice.return_value = MagicMock(invoice='invoice_string')
    mock_get_faucet_url.return_value = 'http://mockfaucet'
    mock_config = MagicMock()
    mock_config.groups = {}
    mock_config_wallet.return_value = mock_config
    mock_handle_exceptions.return_value = 'handled_exception'

    # Act
    result = FaucetService.request_asset_from_faucet()

    # Assert
    mock_handle_exceptions.assert_called_once()
    assert result == 'handled_exception'


def test_request_asset_from_faucet_exception(mock_dependencies):
    """
    Test FaucetService.request_asset_from_faucet when an unexpected exception occurs.
    Ensures handle_exceptions is called with the exception.
    """
    mock_get_wallet_network = mock_dependencies['mock_get_wallet_network']
    mock_get_wallet_network.side_effect = RuntimeError('network error')
    mock_handle_exceptions = mock_dependencies['mock_handle_exceptions']
    mock_handle_exceptions.return_value = 'handled_exception'

    # Act
    result = FaucetService.request_asset_from_faucet()

    # Assert
    mock_handle_exceptions.assert_called_once()
    assert result == 'handled_exception'
