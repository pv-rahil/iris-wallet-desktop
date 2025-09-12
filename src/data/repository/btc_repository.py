"""Module containing BTC repository."""
from __future__ import annotations

from rgb_lib import BtcBalance
from rgb_lib import Transaction
from rgb_lib import Unspent

from src.data.repository.colored_wallet import colored_wallet
from src.data.service.wallet_data_service import WalletDataService
from src.model.btc_model import AddressResponseModel
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel
from src.model.common_operation_model import BroadcastPsbtRequestModel
from src.model.rgb_model import CreateUtxosRequestModel
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context


class BtcRepository:
    """Repository for handling Bitcoin-related operations."""

    @staticmethod
    def get_address() -> AddressResponseModel:
        """Get a Bitcoin address."""
        with repository_custom_context():
            data = colored_wallet.wallet.get_address()
            return AddressResponseModel(address=data)

    @staticmethod
    def get_btc_balance() -> BalanceResponseModel:
        """Get Bitcoin balance."""
        with repository_custom_context():
            data: BtcBalance = colored_wallet.wallet.get_btc_balance(
                online=colored_wallet.online, skip_sync=False,
            )

            return BalanceResponseModel(
                vanilla=data.vanilla,
                colored=data.colored,
            )

    @staticmethod
    def list_transactions() -> TransactionListResponse:
        """List Bitcoin transactions."""
        with repository_custom_context():
            data: list[Transaction] = colored_wallet.wallet.list_transactions(
                online=colored_wallet.online, skip_sync=False,
            )
            return TransactionListResponse(transactions=data)

    @staticmethod
    def list_unspents(param: UnspentListRequestModel) -> UnspentsListResponseModel:
        """List unspent Bitcoin."""
        with repository_custom_context():
            data: list[Unspent] = colored_wallet.wallet.list_unspents(
                online=colored_wallet.online, skip_sync=param.skip_sync, settled_only=param.settled_only,
            )

            return UnspentsListResponseModel(unspents=data)

    @staticmethod
    def send_btc(param: SendBtcRequestModel) -> SendBtcResponseModel:
        """Send Bitcoin."""
        with repository_custom_context():
            data = colored_wallet.wallet.send_btc(
                online=colored_wallet.online, skip_sync=param.skip_sync,
                address=param.address, amount=param.amount, fee_rate=param.fee_rate,
            )
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return SendBtcResponseModel(tx_id=data)

    @staticmethod
    def estimate_fee(param: EstimateFeeRequestModel) -> EstimateFeeResponse:
        """Get Estimate Fee"""
        with repository_custom_context():
            data = colored_wallet.wallet.get_fee_estimation(
                online=colored_wallet.online, blocks=param.blocks,
            )
            return EstimateFeeResponse(fee_rate=data)

    @staticmethod
    def send_btc_begin(param: SendBtcRequestModel) -> str:
        """Creates psbt for bitcoin."""
        with repository_custom_context():
            psbt = colored_wallet.wallet.send_btc_begin(
                online=colored_wallet.online,
                address=param.address,
                amount=param.amount,
                fee_rate=param.fee_rate,
                skip_sync=param.skip_sync,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.add_psbt(psbt, purpose='send_btc')
            return psbt

    @staticmethod
    def send_btc_end(detail: BroadcastPsbtRequestModel) -> SendBtcResponseModel:
        """Broadcast the signed psbt"""
        with repository_custom_context():
            data = colored_wallet.wallet.send_btc_end(
                online=colored_wallet.online, signed_psbt=detail.signed_psbt, skip_sync=detail.skip_sync,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.delete_psbt(detail.signed_psbt)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return SendBtcResponseModel(tx_id=data)

    @staticmethod
    def create_utxos_begin(param: CreateUtxosRequestModel, purpose: str | None = None) -> str:
        """Creates colorable utxo psbt."""
        with repository_custom_context():
            psbt = colored_wallet.wallet.create_utxos_begin(
                online=colored_wallet.online, up_to=param.up_to, num=param.num, size=param.size, fee_rate=param.fee_rate,
                skip_sync=param.skip_sync,
            )
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                wallet_service.add_psbt(psbt, purpose=purpose)
            return psbt

    @staticmethod
    def create_utxos_end(detail: BroadcastPsbtRequestModel) -> int:
        """Broadcast the colorable utxo psbt."""
        with repository_custom_context():
            data: int = colored_wallet.wallet.create_utxos_end(
                online=colored_wallet.online, signed_psbt=detail.signed_psbt, skip_sync=detail.skip_sync,
            )
            wallet_data_service = WalletDataService.get_session()
            if wallet_data_service is not None:
                wallet_data_service.delete_psbt(detail.signed_psbt)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data
