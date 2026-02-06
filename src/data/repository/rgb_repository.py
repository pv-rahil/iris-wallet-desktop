"""Module containing RgbRepository."""
from __future__ import annotations

from rgb_lib import AssetCfa
from rgb_lib import AssetIfa
from rgb_lib import AssetNia
from rgb_lib import Assets
from rgb_lib import AssetUda
from rgb_lib import Balance
from rgb_lib import Invoice
from rgb_lib import Operation
from rgb_lib import OperationInfo
from rgb_lib import OperationResult
from rgb_lib import PsbtInspection
from rgb_lib import ReceiveData
from rgb_lib import Recipient
from rgb_lib import RefreshedTransfer
from rgb_lib import RespondToOperation
from rgb_lib import RgbInspection
from rgb_lib import Transfer

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
from src.utils.decorators.auto_sync_multisig import auto_sync_multisig
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
    @auto_sync_multisig()
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
    @auto_sync_multisig()
    def rgb_invoice(invoice: RgbInvoiceRequestModel) -> ReceiveData:
        """Get RGB invoice."""
        with repository_custom_context():
            online_kwargs = {
                'online': colored_wallet.online,
            } if colored_wallet.is_multisig else {}
            data: ReceiveData = colored_wallet.wallet.blind_receive(
                **online_kwargs,
                asset_id=invoice.asset_id, assignment=invoice.assignment, duration_seconds=invoice.duration_seconds,
                transport_endpoints=invoice.transport_endpoints, min_confirmations=invoice.min_confirmations,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    @auto_sync_multisig()
    def send_asset(asset_detail: SendAssetRequestModel) -> OperationResult:
        """Send asset."""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=asset_detail.recipient_id,
                witness_data=None,
                assignment=asset_detail.assignment,
                transport_endpoints=asset_detail.transport_endpoints,
            )

            recipient_map = {asset_detail.asset_id: [recipient]}

            data: OperationResult = colored_wallet.wallet.send(
                online=colored_wallet.online, recipient_map=recipient_map, donation=asset_detail.donation,
                fee_rate=asset_detail.fee_rate, min_confirmations=asset_detail.min_confirmations, skip_sync=asset_detail.skip_sync,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @auto_sync_multisig()
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
    @auto_sync_multisig()
    def issue_asset_nia(asset: IssueAssetNiaRequestModel) -> AssetNia:
        """Issue asset."""
        with repository_custom_context():
            online_kwargs = {
                'online': colored_wallet.online,
            } if colored_wallet.is_multisig else {}
            data: AssetNia = colored_wallet.wallet.issue_asset_nia(
                **online_kwargs,
                ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    @auto_sync_multisig()
    def issue_asset_cfa(asset: IssueAssetCfaRequestModel) -> AssetCfa:
        """Issue asset."""
        with repository_custom_context():
            online_kwargs = {
                'online': colored_wallet.online,
            } if colored_wallet.is_multisig else {}
            data: AssetCfa = colored_wallet.wallet.issue_asset_cfa(
                **online_kwargs,
                details=asset.ticker, name=asset.name,
                precision=asset.precision, amounts=asset.amounts, file_path=asset.file_path,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available()
    @auto_sync_multisig()
    def issue_asset_uda(asset: IssueAssetUdaRequestModel) -> AssetUda:
        """Issue asset."""
        with repository_custom_context():
            online_kwargs = {
                'online': colored_wallet.online,
            } if colored_wallet.is_multisig else {}
            data: AssetUda = colored_wallet.wallet.issue_asset_uda(
                **online_kwargs,
                details=asset.ticker, name=asset.name, ticker=asset.ticker,
                precision=asset.precision, media_file_path=asset.file_path, attachments_file_paths=asset.attachments_file_paths,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available(required_utxos=3)
    @auto_sync_multisig()
    def issue_asset_ifa(asset: IssueAssetIfaRequestModel) -> AssetIfa:
        """Issue asset."""
        with repository_custom_context():
            online_kwargs = {
                'online': colored_wallet.online,
            } if colored_wallet.is_multisig else {}
            data: AssetIfa = colored_wallet.wallet.issue_asset_ifa(
                **online_kwargs,
                ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts,
                inflation_amounts=asset.inflation_amounts, replace_rights_num=1, reject_list_url=None,
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
    @auto_sync_multisig()
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
            if wallet_service is not None and not colored_wallet.is_multisig:
                wallet_service.add_psbt(psbt, purpose='send_asset')
            return psbt

    @staticmethod
    @check_colorable_available()
    def send_end(detail: BroadcastPsbtRequestModel) -> OperationResult:
        """broadcast signed psbt of send rgb asset"""
        with repository_custom_context():
            data: OperationResult = colored_wallet.wallet.send_end(
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
    @auto_sync_multisig()
    def inflate(detail: InflateRequestModel) -> OperationResult:
        """Inflate asset."""
        with repository_custom_context():
            data: OperationResult = colored_wallet.wallet.inflate(
                online=colored_wallet.online, asset_id=detail.asset_id, inflation_amounts=detail.inflation_amounts,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @check_colorable_available(required_utxos=3)
    @auto_sync_multisig()
    def inflate_begin(detail: InflateRequestModel) -> str:
        """Create psbt for inflate rgb asset"""
        with repository_custom_context():
            psbt: str = colored_wallet.wallet.inflate_begin(
                online=colored_wallet.online, asset_id=detail.asset_id, inflation_amounts=detail.inflation_amounts,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None and not colored_wallet.is_multisig:
                wallet_service.add_psbt(psbt, purpose='inflate_asset')
            return psbt

    @staticmethod
    def inflate_end(signed_psbt: str) -> OperationResult:
        """broadcast signed psbt of inflate rgb asset"""
        with repository_custom_context():
            data: OperationResult = colored_wallet.wallet.inflate_end(
                online=colored_wallet.online, signed_psbt=signed_psbt,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_psbt(signed_psbt)
                wallet_service.delete_secondary_draft_by_psbt(signed_psbt)
            return data

    @staticmethod
    @auto_sync_multisig()
    def post_send(signed_psbt: str, asset_detail: SendBeginRequestModel) -> None:
        """Post the signed RGB send PSBT + recipient map to the multisig bridge."""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=asset_detail.recipient_id,
                witness_data=None,
                assignment=asset_detail.assignment,
                transport_endpoints=asset_detail.transport_endpoints,
            )
            recipient_map = {asset_detail.asset_id: [recipient]}

            colored_wallet.wallet.post_send(
                online=colored_wallet.online,
                signed_psbt=signed_psbt,
                recipient_map=recipient_map,
            )

    @staticmethod
    @auto_sync_multisig()
    def post_inflation(signed_psbt: str, asset_id: str) -> None:
        """Post the signed inflation PSBT to the multisig bridge."""
        with repository_custom_context():
            colored_wallet.wallet.post_inflation(
                online=colored_wallet.online,
                signed_psbt=signed_psbt,
                asset_id=asset_id,
            )

    @staticmethod
    def sync_with_bridge() -> OperationInfo:
        """Sync with the multisig bridge and get pending operations."""
        with repository_custom_context():
            data: OperationInfo = colored_wallet.wallet.sync_with_bridge(
                online=colored_wallet.online,
            )
            return data

    @staticmethod
    @auto_sync_multisig()
    def respond_to_operation(operation_idx: int, respond_to_operation: RespondToOperation) -> Operation:
        """Respond to a pending operation with a signed PSBT."""
        with repository_custom_context():
            data = colored_wallet.wallet.respond_to_operation(
                online=colored_wallet.online,
                operation_idx=operation_idx,
                respond_to_operation=respond_to_operation,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    def get_my_last_synced_operation_idx() -> int:
        """Get our wallet's last synced operation index (multisig bridge context)."""
        with repository_custom_context():
            data: int = colored_wallet.wallet.get_my_last_synced_operation_idx()
            return data

    @staticmethod
    def get_bridge_last_operation_idx() -> int:
        """Get the bridge's last operation index (authoritative source)."""
        with repository_custom_context():
            data: int = colored_wallet.wallet.get_bridge_last_operation_idx()
            return data

    @staticmethod
    def inspect_psbt(psbt: str) -> PsbtInspection:
        """Inspect PSBT details."""
        with repository_custom_context():
            data: PsbtInspection = colored_wallet.wallet.inspect_psbt(
                psbt=psbt,
            )
            return data

    @staticmethod
    def inspect_rgb_transfer(consignment: list[str], psbt: str, entropy: int) -> RgbInspection:
        """Inspect RGB transfer details."""
        with repository_custom_context():
            data: RgbInspection = colored_wallet.wallet.inspect_rgb_transfer(
                consignment_paths=consignment,
                psbt=psbt,
                entropy=entropy,
            )
            return data
