"""Module containing RgbRepository."""
from __future__ import annotations

from rgb_lib import AssetCfa
from rgb_lib import AssetIfa
from rgb_lib import AssetNia
from rgb_lib import Assets
from rgb_lib import AssetUda
from rgb_lib import Balance
from rgb_lib import Invoice
from rgb_lib import ReceiveData
from rgb_lib import Recipient
from rgb_lib import RefreshedTransfer
from rgb_lib import Transfer
from rgb_lib import TransferResult

from src.data.repository.colored_wallet import colored_wallet
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FailTransferResponseModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import InflateRequestModel
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetIfaRequestModel
from src.model.rgb_model import IssueAssetNiaRequestModel
from src.model.rgb_model import IssueAssetUdaRequestModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel
from src.model.rgb_model import SendBeginRequestModel
from src.model.rgb_model import SendBeginResult
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.check_colorable_available import check_colorable_available


class RgbRepository:
    """Repository for handling RGB-related operations."""

    @staticmethod
    def get_asset_balance(
        asset_balance: AssetIdModel,
    ) -> Balance:
        """Get asset balance."""
        with repository_custom_context():
            data: Balance = colored_wallet.wallet.get_asset_balance(
                asset_id=asset_balance.asset_id,
            )

            return data

    @staticmethod
    def decode_invoice(invoice: DecodeRgbInvoiceRequestModel):
        """Decode RGB invoice."""
        with repository_custom_context():
            invoice = Invoice(invoice.invoice)
            data = invoice.invoice_data()
            return data

    @staticmethod
    def list_transfers(asset_id: ListTransfersRequestModel) -> list[Transfer]:
        """List transfers."""
        with repository_custom_context():
            data: list[Transfer] = colored_wallet.wallet.list_transfers(
                asset_id=asset_id.asset_id,
            )
            return data

    @staticmethod
    def refresh_transfer(asset_id=None) -> dict[int, RefreshedTransfer]:
        """Refresh transfers."""
        with repository_custom_context():
            result = colored_wallet.wallet.refresh(
                online=colored_wallet.online,
                asset_id=asset_id,
                filter=[],
                skip_sync=False,
            )
            return result

    @staticmethod
    @check_colorable_available()
    def rgb_invoice(invoice: RgbInvoiceRequestModel) -> ReceiveData:
        """Get RGB invoice."""
        with repository_custom_context():
            data: ReceiveData = colored_wallet.wallet.blind_receive(
                asset_id=invoice.asset_id, assignment=invoice.assignment, duration_seconds=invoice.duration_seconds,
                transport_endpoints=invoice.transport_endpoints, min_confirmations=invoice.min_confirmations,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def send_asset(asset_detail: SendAssetRequestModel) -> TransferResult:
        """Send asset."""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=asset_detail.recipient_id,
                witness_data=None,
                assignment=asset_detail.assignment,
                transport_endpoints=asset_detail.transport_endpoints,
            )

            recipient_map = {asset_detail.asset_id: [recipient]}

            data: TransferResult = colored_wallet.wallet.send(
                online=colored_wallet.online, recipient_map=recipient_map, donation=asset_detail.donation,
                fee_rate=asset_detail.fee_rate, min_confirmations=asset_detail.min_confirmations, skip_sync=asset_detail.skip_sync,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    def get_assets(filter_asset_request_model: FilterAssetRequestModel) -> Assets:
        """Get assets."""
        with repository_custom_context():
            data: Assets = colored_wallet.wallet.list_assets(
                filter_asset_schemas=filter_asset_request_model.filter_asset_schemas,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def issue_asset_nia(asset: IssueAssetNiaRequestModel) -> AssetNia:
        """Issue asset."""
        with repository_custom_context():
            data: AssetNia = colored_wallet.wallet.issue_asset_nia(
                ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def issue_asset_cfa(asset: IssueAssetCfaRequestModel) -> AssetCfa:
        """Issue asset."""
        with repository_custom_context():
            data: AssetCfa = colored_wallet.wallet.issue_asset_cfa(
                details=asset.ticker, name=asset.name,
                precision=asset.precision, amounts=asset.amounts, file_path=asset.file_path,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def issue_asset_uda(asset: IssueAssetUdaRequestModel) -> AssetUda:
        """Issue asset."""
        with repository_custom_context():
            data: AssetUda = colored_wallet.wallet.issue_asset_uda(
                details=asset.ticker, name=asset.name, ticker=asset.ticker,
                precision=asset.precision, media_file_path=asset.file_path, attachments_file_paths=asset.attachments_file_paths,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def issue_asset_ifa(asset: IssueAssetIfaRequestModel) -> AssetIfa:
        """Issue asset."""
        with repository_custom_context():
            data: AssetIfa = colored_wallet.wallet.issue_asset_ifa(
                ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts,
                inflation_amounts=asset.inflation_amounts, replace_rights_num=asset.replace_rights_num,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    def fail_transfer(transfer: FailTransferRequestModel) -> FailTransferResponseModel:
        """Mark the specified transfer as failed."""
        with repository_custom_context():
            data = colored_wallet.wallet.fail_transfers(
                online=colored_wallet.online, batch_transfer_idx=transfer.batch_transfer_idx, no_asset_only=transfer.no_asset_only, skip_sync=transfer.skip_sync,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return FailTransferResponseModel(transfers_changed=data)

    @staticmethod
    @check_colorable_available()
    def send_begin(detail: SendBeginRequestModel) -> SendBeginResult:
        """Create psbt for send rgb asset"""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=detail.recipient_id,
                witness_data=None,
                assignment=detail.assignment,
                transport_endpoints=detail.transport_endpoints,
            )
            recipient_map = {detail.asset_id: [recipient]}
            psbt: SendBeginResult = colored_wallet.wallet.send_begin(
                online=colored_wallet.online, recipient_map=recipient_map, donation=detail.donation,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.add_psbt(psbt, purpose='send_asset')
            return psbt

    @staticmethod
    @check_colorable_available()
    def send_end(detail: BroadcastPsbtRequestModel) -> TransferResult:
        """broadcast signed psbt of send rgb asset"""
        with repository_custom_context():
            data: TransferResult = colored_wallet.wallet.send_end(
                online=colored_wallet.online, signed_psbt=detail.signed_psbt, skip_sync=detail.skip_sync,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_psbt(detail.signed_psbt)
            return data

    @staticmethod
    @check_colorable_available(required_utxos=3)
    def inflate(detail: InflateRequestModel) -> TransferResult:
        """Inflate asset."""
        with repository_custom_context():
            data: TransferResult = colored_wallet.wallet.inflate(
                online=colored_wallet.online, asset_id=detail.asset_id, inflation_amounts=detail.inflation_amounts,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available(required_utxos=3)
    def inflate_begin(detail: InflateRequestModel) -> str:
        """Create psbt for inflate rgb asset"""
        with repository_custom_context():
            psbt: str = colored_wallet.wallet.inflate_begin(
                online=colored_wallet.online, asset_id=detail.asset_id, inflation_amounts=detail.inflation_amounts,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.add_psbt(psbt, purpose='inflate_asset')
            return psbt

    @staticmethod
    @check_colorable_available(required_utxos=0)
    def inflate_end(signed_psbt: str) -> TransferResult:
        """broadcast signed psbt of inflate rgb asset"""
        with repository_custom_context():
            data: TransferResult = colored_wallet.wallet.inflate_end(
                online=colored_wallet.online, signed_psbt=signed_psbt,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_psbt(signed_psbt)
            return data
