"""Module containing BTC repository."""
from __future__ import annotations

from rgb_lib import BtcBalance
from rgb_lib import Transaction
from rgb_lib import Unspent

from src.data.repository.wallet_holder import colored_wallet
from src.model.btc_model import AddressResponseModel
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel
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
            return SendBtcResponseModel(txid=data)

    @staticmethod
    def estimate_fee(param: EstimateFeeRequestModel) -> EstimateFeeResponse:
        """Get Estimate Fee"""
        with repository_custom_context():
            data = colored_wallet.wallet.get_fee_estimation(
                online=colored_wallet.online, blocks=param.blocks,
            )
            return EstimateFeeResponse(fee_rate=data)
