"""Module containing RgbRepository."""
from __future__ import annotations

from rgb_lib import AssetCfa
from rgb_lib import AssetIfa
from rgb_lib import AssetNia
from rgb_lib import Assets
from rgb_lib import AssetUda
from rgb_lib import Balance
from rgb_lib import ExpirationRelative
from rgb_lib import InitOperationResult
from rgb_lib import Invoice
from rgb_lib import OperationInfo
from rgb_lib import OperationResult
from rgb_lib import PsbtInspection
from rgb_lib import ReceiveData
from rgb_lib import Recipient
from rgb_lib import RefreshedTransfer
from rgb_lib import RespondToOperation
from rgb_lib import RgbInspection
from rgb_lib import SendBeginResult
from rgb_lib import Transfer
from rgb_lib import WitnessData

from src.data.repository.colored_wallet import colored_wallet
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.common_operation_model import PsbtData
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
from src.model.rgb_model import RgbContextResult
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel
from src.model.rgb_model import SendBeginRequestModel
from src.utils.cache import Cache
from src.utils.constant import UTXO_SIZE_SAT
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
            data: ReceiveData
            if colored_wallet.is_multisig:
                data = colored_wallet.wallet.witness_receive(
                    **online_kwargs,
                    asset_id=invoice.asset_id, assignment=invoice.assignment, duration_seconds=invoice.duration_seconds,
                    transport_endpoints=invoice.transport_endpoints, min_confirmations=invoice.min_confirmations,
                )
            else:
                expiration = ExpirationRelative(
                    duration_seconds=invoice.duration_seconds, exact=True,
                )
                data = colored_wallet.wallet.witness_receive(
                    asset_id=invoice.asset_id, assignment=invoice.assignment, expiration=expiration,
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
                witness_data=WitnessData(
                    amount_sat=UTXO_SIZE_SAT, blinding=None,
                ),
                assignment=asset_detail.assignment,
                transport_endpoints=asset_detail.transport_endpoints,
            )

            recipient_map = {asset_detail.asset_id: [recipient]}
            expiration = ExpirationRelative(
                duration_seconds=asset_detail.duration_seconds, exact=True,
            )

            data: OperationResult = colored_wallet.wallet.send(
                online=colored_wallet.online, recipient_map=recipient_map, donation=asset_detail.donation,
                fee_rate=asset_detail.fee_rate, min_confirmations=asset_detail.min_confirmations, skip_sync=asset_detail.skip_sync,
                expiration=expiration,
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
                inflation_amounts=asset.inflation_amounts, reject_list_url=None,
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
    @auto_sync_multisig(check_pending_ops=True)
    @check_colorable_available()
    def send_begin(detail: SendBeginRequestModel) -> SendBeginResult:
        """Create psbt for send rgb asset"""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=detail.recipient_id,
                witness_data=WitnessData(
                    amount_sat=UTXO_SIZE_SAT, blinding=None,
                ),
                assignment=detail.assignment,
                transport_endpoints=detail.transport_endpoints,
            )
            recipient_map = {detail.asset_id: [recipient]}
            expiration = ExpirationRelative(
                duration_seconds=detail.duration_seconds, exact=True,
            )
            result: SendBeginResult = colored_wallet.wallet.send_begin(
                online=colored_wallet.online, recipient_map=recipient_map, donation=detail.donation,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations, expiration=expiration,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.add_psbt(
                    PsbtData(psbt_base64=result.psbt, purpose='send_asset'),
                )
            return result

    @staticmethod
    def _sync_and_get_rgb_context(
        psbt: str,
        min_confirmations: int | None = None,
    ) -> RgbContextResult:
        """Sync with bridge and extract RGB context for a PSBT.

        Args:
            psbt: The PSBT to match in operation results
            min_confirmations: Min confirmations to include in context

        Returns:
            RgbContextResult with fascia_path, entropy, min_confirmations
        """
        with repository_custom_context():
            fascia_path = None
            entropy = None
            sync_result = colored_wallet.wallet.sync_with_bridge(
                online=colored_wallet.online,
            )
            if sync_result:
                operations = sync_result if isinstance(
                    sync_result, list,
                ) else [sync_result]
                for op_info in operations:
                    if op_info and op_info.operation:
                        op = op_info.operation
                        if op and op.psbt == psbt:
                            op_details = op.details
                            if op_details:
                                fascia_path = op_details.fascia_path
                                entropy = op_details.entropy
                            break
            return RgbContextResult(
                fascia_path=fascia_path,
                entropy=entropy,
                min_confirmations=min_confirmations,
            )

    @staticmethod
    @auto_sync_multisig(check_pending_ops=True)
    @check_colorable_available()
    def send_init(detail: SendBeginRequestModel) -> InitOperationResult:
        """Init multisig psbt for send rgb asset"""
        with repository_custom_context():
            recipient = Recipient(
                recipient_id=detail.recipient_id,
                witness_data=WitnessData(
                    amount_sat=UTXO_SIZE_SAT, blinding=None,
                ),
                assignment=detail.assignment,
                transport_endpoints=detail.transport_endpoints,
            )
            recipient_map = {detail.asset_id: [recipient]}
            result: InitOperationResult = colored_wallet.wallet.send_init(
                online=colored_wallet.online, recipient_map=recipient_map, donation=detail.donation,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations, duration_seconds=detail.duration_seconds,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_draft_transfer(detail.asset_id)
                # Immediately sync to get RGB context (fascia_path, entropy) for USB sync
                rgb_context = RgbRepository._sync_and_get_rgb_context(
                    result.psbt, detail.min_confirmations,
                )
                wallet_service.add_psbt(
                    PsbtData(
                        psbt_base64=result.psbt,
                        purpose='send_asset',
                        fascia_path=rgb_context.fascia_path,
                        entropy=rgb_context.entropy,
                        min_confirmations=rgb_context.min_confirmations,
                    ),
                )
            return result

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
    @auto_sync_multisig(check_pending_ops=True)
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
                wallet_service.add_psbt(
                    PsbtData(
                        psbt_base64=psbt, purpose='inflate_asset',
                    ),
                )
            return psbt

    @staticmethod
    @auto_sync_multisig(check_pending_ops=True)
    @check_colorable_available()
    def inflate_init(detail: InflateRequestModel) -> InitOperationResult:
        """Init multisig psbt for inflation"""
        with repository_custom_context():
            result: InitOperationResult = colored_wallet.wallet.inflate_init(
                online=colored_wallet.online, asset_id=detail.asset_id, inflation_amounts=detail.inflation_amounts,
                fee_rate=detail.fee_rate, min_confirmations=detail.min_confirmations,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_secondary_draft_by_psbt(
                    asset_id=detail.asset_id,
                )
                # Immediately sync to get RGB context (fascia_path, entropy) for USB sync
                rgb_context = RgbRepository._sync_and_get_rgb_context(
                    result.psbt, detail.min_confirmations,
                )
                wallet_service.add_psbt(
                    PsbtData(
                        psbt_base64=result.psbt,
                        purpose='inflate_asset',
                        fascia_path=rgb_context.fascia_path,
                        entropy=rgb_context.entropy,
                        min_confirmations=rgb_context.min_confirmations,
                    ),
                )
            return result

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
    def sync_with_bridge() -> OperationInfo:
        """Sync with the multisig bridge and get pending operations."""
        with repository_custom_context():
            data: OperationInfo = colored_wallet.wallet.sync_with_bridge(
                online=colored_wallet.online,
            )
            return data

    @staticmethod
    @auto_sync_multisig()
    def respond_to_operation(operation_idx: int, respond_to_operation: RespondToOperation) -> OperationInfo:
        """Respond to a pending operation with a signed PSBT."""
        with repository_custom_context():
            data: OperationInfo = colored_wallet.wallet.respond_to_operation(
                online=colored_wallet.online,
                operation_idx=operation_idx,
                respond_to_operation=respond_to_operation,
            )
            if respond_to_operation.is_ack():
                wallet_service = WalletDataService.get_session()
                if wallet_service is not None:
                    wallet_service.delete_psbt(
                        respond_to_operation.signed_psbt,
                    )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
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
    def inspect_rgb_transfer(fascia_path: str, psbt: str, entropy: int) -> RgbInspection:
        """Inspect RGB transfer details."""
        with repository_custom_context():
            data: RgbInspection = colored_wallet.wallet.inspect_rgb_transfer(
                fascia_path=fascia_path,
                psbt=psbt,
                entropy=entropy,
            )
            return data
