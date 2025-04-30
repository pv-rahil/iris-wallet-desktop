"""Module containing BTC repository."""
from __future__ import annotations

from typing import List

from rgb_lib import BtcBalance
from rgb_lib import Transaction
from rgb_lib import Unspent

from src.data.repository.wallet_holder import WalletHolder
from src.model.btc_model import AddressResponseModel
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import BalanceStatus
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import GetBtcBalanceRequestModel
from src.model.btc_model import ListTransactionRequestModel
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.unlock_required import unlock_required


class BtcRepository:
    """Repository for handling Bitcoin-related operations."""

    @staticmethod
    @unlock_required
    def get_address() -> AddressResponseModel:
        """Get a Bitcoin address."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data = wallet.get_address()
            return AddressResponseModel(address=data)

    @staticmethod
    @unlock_required
    def get_btc_balance(param: GetBtcBalanceRequestModel) -> BalanceResponseModel:
        """Get Bitcoin balance."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: BtcBalance = wallet.get_btc_balance(
                online=param.online, skip_sync=param.skip_sync)

            return BalanceResponseModel(
                vanilla=data.vanilla,
                colored=data.colored,
            )

    @staticmethod
    @unlock_required
    def list_transactions(param: ListTransactionRequestModel) -> TransactionListResponse:
        """List Bitcoin transactions."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: list[Transaction] = wallet.list_transactions(
                online=param.online, skip_sync=param.skip_sync)
            return TransactionListResponse(transactions=data)

    @staticmethod
    @unlock_required
    def list_unspents(param: UnspentListRequestModel) -> UnspentsListResponseModel:
        """List unspent Bitcoin."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: list[Unspent] = wallet.list_unspents(
                online=param.online, skip_sync=param.skip_sync, settled_only=param.settled_only)

            return UnspentsListResponseModel(unspents=data)

    @staticmethod
    @unlock_required
    def send_btc(param: SendBtcRequestModel) -> SendBtcResponseModel:
        """Send Bitcoin."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data = wallet.send_btc(online=param.online, skip_sync=param.skip_sync,
                                   address=param.address, amount=param.amount, fee_rate=param.fee_rate)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return SendBtcResponseModel(txid=data)

    @staticmethod
    @unlock_required
    def estimate_fee(param: EstimateFeeRequestModel) -> EstimateFeeResponse:
        """Get Estimate Fee"""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data = wallet.get_fee_estimation(
                online=param.online, blocks=param.blocks)
            return EstimateFeeResponse(**data)
