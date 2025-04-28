"""Module containing BTC repository."""
from __future__ import annotations

from src.data.repository.wallet_holder import WalletHolder
from src.model.btc_model import AddressResponseModel, BalanceStatus, GetBtcBalanceRequestModel, ListTransactionRequestModel, RgbAllocation, Transaction, Unspent, UnspentListRequestModel
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import SendBtcRequestModel
from src.model.btc_model import SendBtcResponseModel
from src.model.btc_model import TransactionListResponse
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
            if isinstance(data, str):
                data = {'address': data} 
            return AddressResponseModel(**data)

    @staticmethod
    @unlock_required
    def get_btc_balance(param : GetBtcBalanceRequestModel) -> BalanceResponseModel:
        """Get Bitcoin balance."""
        with repository_custom_context():
            payload = param.dict()
            wallet = WalletHolder.get_wallet()
            data = wallet.get_btc_balance(**payload)

            # Dynamic Unpacking using Pydantic's `parse_obj` method
            # Convert `data.vanilla` and `data.colored` to dicts and then parse them into BalanceStatus models
            vanilla_status = BalanceStatus.parse_obj(data.vanilla.__dict__)
            colored_status = BalanceStatus.parse_obj(data.colored.__dict__)

            # Return the response model with dynamically created BalanceStatus instances
            return BalanceResponseModel(
                vanilla=vanilla_status,
                colored=colored_status
            )

    @staticmethod
    @unlock_required
    def list_transactions(param: ListTransactionRequestModel) -> TransactionListResponse:
        """List Bitcoin transactions."""
        with repository_custom_context():
            payload = param.dict()
            wallet = WalletHolder.get_wallet()
            data = wallet.list_transactions(**payload)
            if isinstance(data, list):
                data = [Transaction.model_validate(tx, from_attributes=True) for tx in data]
            else:
                data = []
            return TransactionListResponse(transactions=data)

    @staticmethod
    @unlock_required
    def list_unspents(param: UnspentListRequestModel) -> UnspentsListResponseModel:
        """List unspent Bitcoin."""
        with repository_custom_context():
            payload = param.dict()
            wallet = WalletHolder.get_wallet()
            data = wallet.list_unspents(**payload)

            # Function to convert rgb_lib.Utxo to a dictionary
            def convert_utxo(utxo_obj):
                return {
                    "outpoint": f"{utxo_obj.outpoint.txid}-{utxo_obj.outpoint.vout}",  # Converting Outpoint to string
                    "btc_amount": utxo_obj.btc_amount,
                    "colorable": utxo_obj.colorable
                }

            # Function to convert rgb_allocations (list of RgbAllocation objects) to dictionaries
            def convert_rgb_allocations(rgb_allocations):
                # Iterate through the list of rgb_allocations and convert each to a dictionary
                return [
                    {
                        "asset_id": rgb_allocation.asset_id,
                        "amount": rgb_allocation.amount,
                        "settled": rgb_allocation.settled
                    }
                    for rgb_allocation in rgb_allocations
                ] if rgb_allocations else []

            # Using model_validate() with the transformed data
            response_data = [
                Unspent.model_validate({
                    "utxo": convert_utxo(unspent.utxo),  # Convert the Utxo object to a dictionary
                    "rgb_allocations": convert_rgb_allocations(unspent.rgb_allocations)  # Convert rgb_allocations properly
                })
                for unspent in data
            ]

            # Return the response, letting Pydantic handle everything
            return UnspentsListResponseModel(unspents=response_data)



    @staticmethod
    @unlock_required
    def send_btc(send_btc_value: SendBtcRequestModel) -> SendBtcResponseModel:
        """Send Bitcoin."""
        payload = send_btc_value.dict()
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data = wallet.send_btc(**payload)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            if isinstance(data, str):
                data = {'txid': data} 
            return SendBtcResponseModel(**data)

    @staticmethod
    @unlock_required
    def estimate_fee(blocks: EstimateFeeRequestModel) -> EstimateFeeResponse:
        """Get Estimate Fee"""
        payload = blocks.dict()
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            online_wallet = WalletHolder.get_online()
            data = wallet.get_fee_estimation(online_wallet,**payload)
            return EstimateFeeResponse(**data)
