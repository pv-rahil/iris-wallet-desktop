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
from rgb_lib import Assignment
from rgb_lib import Balance
from rgb_lib import InitOperationResult
from rgb_lib import Invoice
from rgb_lib import OperationInfo
from rgb_lib import OperationResult
from rgb_lib import PsbtInspection
from rgb_lib import ReceiveData
from rgb_lib import Recipient
from rgb_lib import RespondToOperation
from rgb_lib import RgbInspection
from rgb_lib import SendBeginResult
from rgb_lib import Transfer

from src.data.repository.rgb_repository import RgbRepository
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import InflateRequestModel
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetIfaRequestModel
from src.model.rgb_model import IssueAssetNiaRequestModel
from src.model.rgb_model import IssueAssetUdaRequestModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RgbContextResult
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel
from src.model.rgb_model import SendBeginRequestModel


@pytest.fixture
def mock_wallet():
    """Fixture for mocking the colored wallet"""
    with patch('src.data.repository.rgb_repository.colored_wallet') as mock_colored_wallet:
        mock_wallet = MagicMock()
        mock_colored_wallet.wallet = mock_wallet
        mock_colored_wallet.online = True
        # Disable online= conditional branches by default
        mock_colored_wallet.is_multisig = False
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
    # Setup
    mock_wallet.refresh.return_value = {}
    # Execute
    result = RgbRepository.refresh_transfer()

    # Assert
    assert result == {}
    mock_wallet.refresh.assert_called_once_with(
        online=True, asset_id=None, filter=[], skip_sync=False,
    )


def test_rgb_invoice(mock_wallet, mock_cache):
    """Test rgb_invoice method — non-multisig uses witness_receive without online=."""
    # Setup
    mock_receive_data = MagicMock(spec=ReceiveData)
    mock_wallet.witness_receive.return_value = mock_receive_data

    # Execute
    _assignment = Assignment.__new__(Assignment)
    request = RgbInvoiceRequestModel(
        asset_id='test_asset_id',
        duration_seconds=3600,
        transport_endpoints=['test_endpoint'],
        min_confirmations=1,
        assignment=_assignment,
    )
    result = RgbRepository.rgb_invoice(request)

    # Assert
    assert result == mock_receive_data
    mock_wallet.witness_receive.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_ifa(mock_wallet, mock_cache):
    """Test issue_asset_ifa method — no online= when not multisig, reject_list_url=None."""
    # Setup
    mock_asset_ifa = MagicMock()
    mock_wallet.issue_asset_ifa.return_value = mock_asset_ifa

    # Execute
    request = IssueAssetIfaRequestModel(
        ticker='IFAT',
        name='IFA Asset',
        precision=0,
        amounts=[1000],
        inflation_amounts=[500],
    )
    result = RgbRepository.issue_asset_ifa(request)

    # Assert
    assert result == mock_asset_ifa
    mock_wallet.issue_asset_ifa.assert_called_once_with(
        ticker='IFAT', name='IFA Asset', precision=0, amounts=[1000],
        inflation_amounts=[500], reject_list_url=None,
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_inflate(mock_wallet, mock_cache):
    """Test inflate method"""
    # Setup
    mock_transfer_res = MagicMock()
    mock_wallet.inflate.return_value = mock_transfer_res

    # Execute
    request = InflateRequestModel(
        asset_id='aid', inflation_amounts=[123], fee_rate=2, min_confirmations=1,
    )
    result = RgbRepository.inflate(request)

    # Assert
    assert result == mock_transfer_res
    mock_wallet.inflate.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_inflate_begin_with_session(mock_get_session, mock_wallet):
    """Test inflate_begin adds psbt to session with purpose and returns psbt."""
    # Setup
    psbt = 'psbt_string'
    mock_wallet.inflate_begin.return_value = psbt
    svc = MagicMock()
    mock_get_session.return_value = svc

    # Execute
    req = InflateRequestModel(
        asset_id='aid', inflation_amounts=[10], fee_rate=3, min_confirmations=2,
    )
    result = RgbRepository.inflate_begin(req)

    # Assert
    assert result == psbt
    mock_wallet.inflate_begin.assert_called_once()
    svc.add_psbt.assert_called_once_with(psbt, purpose='inflate_asset')


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_inflate_end_with_session_and_cache(mock_get_session, mock_wallet, mock_cache):
    """Test inflate_end invalidates cache and deletes psbt in session."""
    # Setup
    transfer_result = MagicMock()
    mock_wallet.inflate_end.return_value = transfer_result
    svc = MagicMock()
    mock_get_session.return_value = svc

    # Execute
    res = RgbRepository.inflate_end('psbt_final')

    # Assert
    assert res == transfer_result
    mock_wallet.inflate_end.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()
    svc.delete_psbt.assert_called_once_with('psbt_final')


@patch('src.data.repository.rgb_repository.Recipient')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_begin_with_session(mock_get_session, mock_recipient_cls, mock_wallet):
    """Test send_begin adds psbt to session with purpose and returns psbt."""
    # Setup Recipient and send_begin return
    mock_recipient = MagicMock(spec=Recipient)
    mock_recipient_cls.return_value = mock_recipient
    psbt_result = MagicMock(spec=SendBeginResult)
    psbt_result.psbt = 'the_psbt_string'
    mock_wallet.send_begin.return_value = psbt_result

    svc = MagicMock()
    mock_get_session.return_value = svc

    # Execute
    _assignment = Assignment.__new__(Assignment)
    req = SendBeginRequestModel(
        asset_id='aid', assignment=_assignment, recipient_id='rid', donation=False,
        fee_rate=2, min_confirmations=1, transport_endpoints=['te1'],
    )
    result = RgbRepository.send_begin(req)

    # Assert
    assert result == psbt_result
    mock_recipient_cls.assert_called_once()
    mock_wallet.send_begin.assert_called_once()
    svc.add_psbt.assert_called_once_with(
        'the_psbt_string', purpose='send_asset',
    )


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_send_end_with_session_and_cache(mock_get_session, mock_wallet, mock_cache):
    """Test send_end invalidates cache and deletes psbt in session."""
    send_result = MagicMock(spec=OperationResult)
    mock_wallet.send_end.return_value = send_result
    svc = MagicMock()
    mock_get_session.return_value = svc

    res = RgbRepository.send_end(
        BroadcastPsbtRequestModel(
            signed_psbt='psbt_s', skip_sync=False,
        ),
    )

    assert res == send_result
    mock_wallet.send_end.assert_called_once()
    mock_cache.invalidate_cache.assert_called_once()
    svc.delete_psbt.assert_called_once_with('psbt_s')


def test_send_asset(mock_wallet, mock_cache):
    """Test send_asset method"""
    # Setup
    mock_send_result = MagicMock(spec=OperationResult)
    mock_wallet.send.return_value = mock_send_result

    with patch('src.data.repository.rgb_repository.Recipient') as mock_recipient_class:
        mock_recipient = MagicMock(spec=Recipient)
        mock_recipient_class.return_value = mock_recipient

        # Execute
        _assignment = Assignment.__new__(Assignment)
        request = SendAssetRequestModel(
            asset_id='test_asset_id',
            recipient_id='test_recipient_id',
            assignment=_assignment,
            transport_endpoints=['test_endpoint'],
            donation=False,
            fee_rate=5,
            min_confirmations=1,
            skip_sync=False,
        )
        result = RgbRepository.send_asset(request)

        # Assert
        assert result == mock_send_result
        mock_recipient_class.assert_called_once()
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
    """Test issue_asset_nia method — no online= when not multisig."""
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
        ticker='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_nia_multisig(mock_wallet, mock_cache):
    """When is_multisig=True, online= is added to issue_asset_nia call."""
    with patch('src.data.repository.rgb_repository.colored_wallet') as mock_cw:
        mock_cw.wallet = mock_wallet
        mock_cw.online = True
        mock_cw.is_multisig = True
        mock_wallet.issue_asset_nia.return_value = MagicMock(spec=AssetNia)
        request = IssueAssetNiaRequestModel(
            ticker='T', name='N', precision=0, amounts=[1],
        )
        RgbRepository.issue_asset_nia(request)
        call_kwargs = mock_wallet.issue_asset_nia.call_args.kwargs
        assert call_kwargs.get('online') is True


def test_issue_asset_cfa(mock_wallet, mock_cache):
    """Test issue_asset_cfa method — no online= when not multisig."""
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
        details='TEST',
        name='Test Asset',
        precision=8,
        amounts=[1000],
        file_path='/test/path.jpg',
    )
    mock_cache.invalidate_cache.assert_called_once()


def test_issue_asset_uda(mock_wallet, mock_cache):
    """Test issue_asset_uda method — no online= when not multisig."""
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


@patch('src.data.repository.rgb_repository.RgbRepository._sync_and_get_rgb_context')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.rgb_repository.Recipient')
def test_send_init_with_session(mock_recipient_cls, mock_get_session, mock_sync_rgb, mock_wallet):
    """send_init stores psbt and deletes draft_transfer for asset when session exists."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'init_psbt'
    mock_wallet.send_init.return_value = result_obj
    mock_recipient_cls.return_value = MagicMock()
    mock_sync_rgb.return_value = RgbContextResult(
        fascia_path='/path/fascia.rgb', entropy=123, min_confirmations=1,
    )

    svc = MagicMock()
    mock_get_session.return_value = svc

    _assignment = Assignment.__new__(Assignment)
    req = SendBeginRequestModel(
        asset_id='aid', assignment=_assignment, recipient_id='rid',
        donation=False, fee_rate=2, min_confirmations=1, transport_endpoints=['te1'],
    )
    res = RgbRepository.send_init(req)

    assert res == result_obj
    mock_wallet.send_init.assert_called_once()
    svc.delete_draft_transfer.assert_called_once_with('aid')
    svc.add_psbt.assert_called_once_with(
        'init_psbt', purpose='send_asset',
        fascia_path='/path/fascia.rgb', entropy=123, min_confirmations=1,
    )


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
@patch('src.data.repository.rgb_repository.Recipient')
def test_send_init_without_session(mock_recipient_cls, mock_get_session, mock_wallet):
    """send_init should not fail when session is None."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'init_psbt'
    mock_wallet.send_init.return_value = result_obj
    mock_recipient_cls.return_value = MagicMock()
    mock_get_session.return_value = None

    _assignment = Assignment.__new__(Assignment)
    req = SendBeginRequestModel(
        asset_id='aid', assignment=_assignment, recipient_id='rid',
        donation=False, fee_rate=2, min_confirmations=1, transport_endpoints=['te1'],
    )
    res = RgbRepository.send_init(req)

    assert res == result_obj
    mock_wallet.send_init.assert_called_once()


@patch('src.data.repository.rgb_repository.RgbRepository._sync_and_get_rgb_context')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_inflate_init_with_session(mock_get_session, mock_sync_rgb, mock_wallet):
    """inflate_init deletes secondary draft, stores psbt with 'inflate_asset' purpose."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'inflate_init_psbt'
    mock_wallet.inflate_init.return_value = result_obj
    mock_sync_rgb.return_value = RgbContextResult(
        fascia_path='/path/fascia.rgb', entropy=456, min_confirmations=2,
    )

    svc = MagicMock()
    mock_get_session.return_value = svc

    req = InflateRequestModel(
        asset_id='aid', inflation_amounts=[10], fee_rate=3, min_confirmations=2,
    )
    res = RgbRepository.inflate_init(req)

    assert res == result_obj
    mock_wallet.inflate_init.assert_called_once()
    svc.delete_secondary_draft_by_psbt.assert_called_once_with(asset_id='aid')
    svc.add_psbt.assert_called_once_with(
        'inflate_init_psbt', purpose='inflate_asset',
        fascia_path='/path/fascia.rgb', entropy=456, min_confirmations=2,
    )


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_inflate_init_without_session(mock_get_session, mock_wallet):
    """inflate_init should work without a session."""
    result_obj = MagicMock(spec=InitOperationResult)
    result_obj.psbt = 'inflate_init_psbt'
    mock_wallet.inflate_init.return_value = result_obj
    mock_get_session.return_value = None

    req = InflateRequestModel(
        asset_id='aid', inflation_amounts=[10], fee_rate=3, min_confirmations=2,
    )
    res = RgbRepository.inflate_init(req)

    assert res == result_obj


def test_sync_with_bridge(mock_wallet):
    """sync_with_bridge should call wallet.sync_with_bridge with online= and return OperationInfo."""
    mock_info = MagicMock(spec=OperationInfo)
    mock_wallet.sync_with_bridge.return_value = mock_info

    result = RgbRepository.sync_with_bridge()

    assert result == mock_info
    mock_wallet.sync_with_bridge.assert_called_once_with(online=True)


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_respond_to_operation_ack_deletes_psbt(mock_get_session, mock_wallet, mock_cache):
    """When respond is ACK, psbt is deleted from session and cache is invalidated."""
    mock_info = MagicMock(spec=OperationInfo)
    mock_wallet.respond_to_operation.return_value = mock_info
    svc = MagicMock()
    mock_get_session.return_value = svc

    respond = MagicMock(spec=RespondToOperation)
    respond.is_ack.return_value = True
    respond.signed_psbt = 'signed_psbt_string'

    result = RgbRepository.respond_to_operation(1, respond)

    assert result == mock_info
    mock_wallet.respond_to_operation.assert_called_once_with(
        online=True, operation_idx=1, respond_to_operation=respond,
    )
    svc.delete_psbt.assert_called_once_with('signed_psbt_string')
    mock_cache.invalidate_cache.assert_called_once()


@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_respond_to_operation_nack_no_delete(mock_get_session, mock_wallet, mock_cache):
    """When respond is NACK, psbt is not deleted but cache is still invalidated."""
    mock_info = MagicMock(spec=OperationInfo)
    mock_wallet.respond_to_operation.return_value = mock_info
    svc = MagicMock()
    mock_get_session.return_value = svc

    respond = MagicMock(spec=RespondToOperation)
    respond.is_ack.return_value = False

    result = RgbRepository.respond_to_operation(2, respond)

    assert result == mock_info
    svc.delete_psbt.assert_not_called()
    mock_cache.invalidate_cache.assert_called_once()


def test_inspect_psbt(mock_wallet):
    """inspect_psbt forwards the psbt string to the wallet and returns PsbtInspection."""
    mock_inspection = MagicMock(spec=PsbtInspection)
    mock_wallet.inspect_psbt.return_value = mock_inspection

    result = RgbRepository.inspect_psbt('raw_psbt_base64')

    assert result == mock_inspection
    mock_wallet.inspect_psbt.assert_called_once_with(psbt='raw_psbt_base64')


def test_inspect_rgb_transfer(mock_wallet):
    """inspect_rgb_transfer forwards fascia_path/psbt/entropy and returns RgbInspection."""
    mock_rgb_inspection = MagicMock(spec=RgbInspection)
    mock_wallet.inspect_rgb_transfer.return_value = mock_rgb_inspection

    result = RgbRepository.inspect_rgb_transfer(
        '/path/to/fascia', 'psbt_str', 1234,
    )

    assert result == mock_rgb_inspection
    mock_wallet.inspect_rgb_transfer.assert_called_once_with(
        fascia_path='/path/to/fascia',
        psbt='psbt_str',
        entropy=1234,
    )
