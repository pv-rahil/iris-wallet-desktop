"""Unit tests for RgbRepository."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import AssetCfa
from rgb_lib import AssetNia
from rgb_lib import Assets
from rgb_lib import AssetUda
from rgb_lib import Balance
from rgb_lib import Invoice
from rgb_lib import ReceiveData
from rgb_lib import Recipient
from rgb_lib import SendResult
from rgb_lib import Transfer

from src.data.repository.rgb_repository import RgbRepository
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetNiaRequestModel
from src.model.rgb_model import IssueAssetUdaRequestModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel


@pytest.fixture
def mock_wallet():
    """Fixture for mocking the colored wallet"""
    with patch('src.data.repository.rgb_repository.colored_wallet') as mock_colored_wallet:
        mock_wallet = MagicMock()
        mock_colored_wallet.wallet = mock_wallet
        mock_colored_wallet.online = True
        yield mock_wallet


@pytest.fixture
def mock_cache():
    """Fixture for mocking the cache"""
    with patch('src.data.repository.rgb_repository.Cache') as mock_cache:
        mock_cache_session = MagicMock()
        mock_cache.get_cache_session.return_value = mock_cache_session
        yield mock_cache_session


def test_get_asset_balance(mock_wallet):
    """Test get_asset_balance method"""
    # Setup
    mock_balance = MagicMock(spec=Balance)
    mock_wallet.get_asset_balance.return_value = mock_balance

    # Execute
    asset_id_model = AssetIdModel(asset_id='test_asset_id')
    result = RgbRepository.get_asset_balance(asset_id_model)

    # Assert
    assert result == mock_balance
    mock_wallet.get_asset_balance.assert_called_once_with(
        asset_id='test_asset_id',
    )


def test_decode_invoice(mock_wallet):
    """Test decode_invoice method"""
    # Setup
    mock_invoice_data = MagicMock()

    with patch('src.data.repository.rgb_repository.Invoice') as mock_invoice_class:
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.invoice_data.return_value = mock_invoice_data
        mock_invoice_class.return_value = mock_invoice

        # Execute
        request = DecodeRgbInvoiceRequestModel(invoice='test_invoice')
        result = RgbRepository.decode_invoice(request)

        # Assert
        assert result == mock_invoice_data
        mock_invoice_class.assert_called_once_with('test_invoice')
        mock_invoice.invoice_data.assert_called_once()


def test_list_transfers(mock_wallet):
    """Test list_transfers method"""
    # Setup
    mock_transfer1 = MagicMock(spec=Transfer)
    mock_transfer2 = MagicMock(spec=Transfer)
    mock_wallet.list_transfers.return_value = [mock_transfer1, mock_transfer2]

    # Execute
    request = ListTransfersRequestModel(asset_id='test_asset_id')
    result = RgbRepository.list_transfers(request)

    # Assert
    assert len(result) == 2
    assert result[0] == mock_transfer1
    assert result[1] == mock_transfer2
    mock_wallet.list_transfers.assert_called_once_with(
        asset_id='test_asset_id',
    )


def test_refresh_transfer(mock_wallet):
    """Test refresh_transfer method"""
    # Execute
    result = RgbRepository.refresh_transfer()

    # Assert
    assert result.status is True
    mock_wallet.refresh.assert_called_once_with(
        online=True, asset_id=None, filter=[], skip_sync=False,
    )


def test_rgb_invoice(mock_wallet, mock_cache):
    """Test rgb_invoice method"""
    # Setup
    mock_receive_data = MagicMock(spec=ReceiveData)
    mock_wallet.blind_receive.return_value = mock_receive_data

    # Execute
    request = RgbInvoiceRequestModel(
        asset_id='test_asset_id',
        duration_seconds=3600,
        transport_endpoints=['test_endpoint'],
        min_confirmations=1,
    )
    result = RgbRepository.rgb_invoice(request)

    # Assert
    assert result == mock_receive_data
    mock_wallet.blind_receive.assert_called_once_with(
        asset_id='test_asset_id',
        amount=None,
        duration_seconds=3600,
        transport_endpoints=['test_endpoint'],
        min_confirmations=1,
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_send_asset(mock_wallet, mock_cache):
    """Test send_asset method"""
    # Setup
    mock_send_result = MagicMock(spec=SendResult)
    mock_wallet.send.return_value = mock_send_result

    with patch('src.data.repository.rgb_repository.Recipient') as mock_recipient_class:
        mock_recipient = MagicMock(spec=Recipient)
        mock_recipient_class.return_value = mock_recipient

        # Execute
        request = SendAssetRequestModel(
            asset_id='test_asset_id',
            recipient_id='test_recipient_id',
            amount=1000,
            transport_endpoints=['test_endpoint'],
            donation=False,
            fee_rate=5,
            min_confirmations=1,
            skip_sync=False,
        )
        result = RgbRepository.send_asset(request)

        # Assert
        assert result == mock_send_result
        mock_recipient_class.assert_called_once_with(
            recipient_id='test_recipient_id',
            witness_data=None,
            amount=1000,
            transport_endpoints=['test_endpoint'],
        )
        mock_wallet.send.assert_called_once()
        mock_cache.invalidate_cache.assert_called_once()


def test_get_assets(mock_wallet, mock_cache):
    """Test get_assets method"""
    # Setup
    mock_assets = MagicMock(spec=Assets)
    mock_wallet.list_assets.return_value = mock_assets

    # Execute
    filter_request = FilterAssetRequestModel(filter_asset_schemas=[])
    result = RgbRepository.get_assets(filter_request)

    # Assert
    assert result == mock_assets
    mock_wallet.list_assets.assert_called_once_with(
        filter_asset_schemas=filter_request.filter_asset_schemas,
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_nia(mock_wallet, mock_cache):
    """Test issue_asset_nia method"""
    # Setup
    mock_asset_nia = MagicMock(spec=AssetNia)
    mock_wallet.issue_asset_nia.return_value = mock_asset_nia

    # Execute
    request = IssueAssetNiaRequestModel(
        ticker='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
    )
    result = RgbRepository.issue_asset_nia(request)

    # Assert
    assert result == mock_asset_nia
    mock_wallet.issue_asset_nia.assert_called_once_with(
        online=True,
        ticker='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_cfa(mock_wallet, mock_cache):
    """Test issue_asset_cfa method"""
    # Setup
    mock_asset_cfa = MagicMock(spec=AssetCfa)
    mock_wallet.issue_asset_cfa.return_value = mock_asset_cfa

    # Execute
    request = IssueAssetCfaRequestModel(
        ticker='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
        file_path='/test/path.jpg',
    )
    result = RgbRepository.issue_asset_cfa(request)

    # Assert
    assert result == mock_asset_cfa
    mock_wallet.issue_asset_cfa.assert_called_once_with(
        online=True,
        details='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
        file_path='/test/path.jpg',
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_uda(mock_wallet, mock_cache):
    """Test issue_asset_uda method"""
    # Setup
    mock_asset_uda = MagicMock(spec=AssetUda)
    mock_wallet.issue_asset_uda.return_value = mock_asset_uda

    # Execute
    request = IssueAssetUdaRequestModel(
        ticker='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
        file_path='/test/path.jpg',
        attachments_file_paths=[['/test/attachment.txt']],
    )
    result = RgbRepository.issue_asset_uda(request)

    # Assert
    assert result == mock_asset_uda
    mock_wallet.issue_asset_uda.assert_called_once_with(
        online=True,
        details='TEST',
        name='Test Asset',
        ticker='TEST',
        precision=8,
        media_file_path='/test/path.jpg',
        attachments_file_paths=[['/test/attachment.txt']],
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_fail_transfer(mock_wallet, mock_cache):
    """Test fail_transfer method"""
    # Setup
    mock_wallet.fail_transfers.return_value = True

    # Execute
    request = FailTransferRequestModel(
        batch_transfer_idx=123,
        no_asset_only=False,
        skip_sync=False,
    )
    result = RgbRepository.fail_transfer(request)

    # Assert
    assert result.transfers_changed is True
    mock_wallet.fail_transfers.assert_called_once_with(
        online=True,
        batch_transfer_idx=123,
        no_asset_only=False,
        skip_sync=False,
    )
    mock_cache.invalidate_cache.assert_called_once()
