"""Module containing RgbRepository."""
from __future__ import annotations

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

from src.data.repository.wallet_holder import colored_wallet
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FailTransferResponseModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetNiaRequestModel
from src.model.rgb_model import IssueAssetUdaRequestModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RefreshTransferResponseModel
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel
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
    def refresh_transfer():
        """Refresh transfers."""
        with repository_custom_context():
            colored_wallet.wallet.refresh(
                online=colored_wallet.online, asset_id=None,
                filter=[], skip_sync=False,
            )
            return RefreshTransferResponseModel(status=True)

    @staticmethod
    @check_colorable_available()
    def rgb_invoice(invoice: RgbInvoiceRequestModel) -> ReceiveData:
        """Get RGB invoice."""
        with repository_custom_context():
            data: ReceiveData = colored_wallet.wallet.blind_receive(
                asset_id=invoice.asset_id, amount=None, duration_seconds=invoice.duration_seconds,
                transport_endpoints=invoice.transport_endpoints, min_confirmations=invoice.min_confirmations,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    def send_asset(asset_detail: SendAssetRequestModel):
        """Send asset."""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=asset_detail.recipient_id,
                witness_data=None,
                amount=asset_detail.amount,
                transport_endpoints=asset_detail.transport_endpoints,
            )

            recipient_map = {asset_detail.asset_id: [recipient]}

            data: SendResult = colored_wallet.wallet.send(
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
                online=colored_wallet.online, ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts,
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
                online=colored_wallet.online, details=asset.ticker, name=asset.name,
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
                online=colored_wallet.online, details=asset.ticker, name=asset.name, ticker=asset.ticker,
                precision=asset.precision, media_file_path=asset.file_path, attachments_file_paths=asset.attachments_file_paths,
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
