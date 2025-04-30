"""Module containing RgbRepository."""
from __future__ import annotations

from typing import List

import requests
import rgb_lib
from rgb_lib import AssetCfa
from rgb_lib import AssetNia
from rgb_lib import Assets
from rgb_lib import Balance
from rgb_lib import Transfer

from src.data.repository.wallet_holder import WalletHolder
from src.model.rgb_model import AssetBalanceResponseModel
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import CreateUtxosRequestModel
from src.model.rgb_model import CreateUtxosResponseModel
from src.model.rgb_model import DecodeRgbInvoiceRequestModel
from src.model.rgb_model import DecodeRgbInvoiceResponseModel
from src.model.rgb_model import FailTransferRequestModel
from src.model.rgb_model import FailTransferResponseModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import GetAssetMediaModelRequestModel
from src.model.rgb_model import GetAssetMediaModelResponseModel
from src.model.rgb_model import GetAssetResponseModel
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetCfaRequestModelWithDigest
from src.model.rgb_model import IssueAssetNiaRequestModel
from src.model.rgb_model import IssueAssetResponseModel
from src.model.rgb_model import IssueAssetUdaRequestModel
from src.model.rgb_model import ListTransferAssetResponseModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import PostAssetMediaModelResponseModel
from src.model.rgb_model import RefreshRequestModel
from src.model.rgb_model import RefreshTransferResponseModel
from src.model.rgb_model import RgbInvoiceDataResponseModel
from src.model.rgb_model import RgbInvoiceRequestModel
from src.model.rgb_model import SendAssetRequestModel
from src.model.rgb_model import SendAssetResponseModel
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.check_colorable_available import check_colorable_available
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import ASSET_BALANCE_ENDPOINT
from src.utils.endpoints import DECODE_RGB_INVOICE_ENDPOINT
from src.utils.endpoints import FAIL_TRANSFER_ENDPOINT
from src.utils.endpoints import GET_ASSET_MEDIA
from src.utils.endpoints import ISSUE_ASSET_ENDPOINT_CFA
from src.utils.endpoints import ISSUE_ASSET_ENDPOINT_UDA
from src.utils.endpoints import LIST_TRANSFERS_ENDPOINT
from src.utils.endpoints import POST_ASSET_MEDIA
from src.utils.endpoints import RGB_INVOICE_ENDPOINT
from src.utils.endpoints import SEND_ASSET_ENDPOINT
from src.utils.request import Request


class RgbRepository:
    """Repository for handling RGB-related operations."""

    @staticmethod
    @unlock_required
    def get_asset_balance(
        asset_balance: AssetIdModel,
    ) -> AssetBalanceResponseModel:
        """Get asset balance."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: Balance = wallet.get_asset_balance(
                asset_id=asset_balance.asset_id)

            return data

    @staticmethod
    @unlock_required
    def decode_invoice(invoice: DecodeRgbInvoiceRequestModel):
        """Decode RGB invoice."""
        payload = invoice.dict()
        with repository_custom_context():
            response = Request.post(DECODE_RGB_INVOICE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return DecodeRgbInvoiceResponseModel(**data)

    @staticmethod
    @unlock_required
    def list_transfers(asset_id: ListTransfersRequestModel):
        """List transfers."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: list[Transfer] = wallet.list_transfers(
                asset_id=asset_id.asset_id)
            return data

    @staticmethod
    @unlock_required
    def refresh_transfer():
        """Refresh transfers."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            online = WalletHolder.get_online()
            wallet.refresh(online=online, asset_id=None,
                           filter=[], skip_sync=False)
            return RefreshTransferResponseModel(status=True)

    @staticmethod
    @unlock_required
    @check_colorable_available()
    def rgb_invoice(invoice: RgbInvoiceRequestModel):
        """Get RGB invoice."""
        payload = invoice.dict()
        with repository_custom_context():
            response = Request.post(RGB_INVOICE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return RgbInvoiceDataResponseModel(**data)

    @staticmethod
    @unlock_required
    @check_colorable_available()
    def send_asset(asset_detail: SendAssetRequestModel):
        """Send asset."""
        payload = asset_detail.dict()
        with repository_custom_context():
            response = Request.post(SEND_ASSET_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return SendAssetResponseModel(**data)

    @staticmethod
    @unlock_required
    def get_assets(filter_asset_request_model: FilterAssetRequestModel) -> Assets:
        """Get assets."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: Assets = wallet.list_assets(
                filter_asset_schemas=filter_asset_request_model)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @unlock_required
    @check_colorable_available()
    def issue_asset_nia(asset: IssueAssetNiaRequestModel) -> AssetNia:
        """Issue asset."""
        with repository_custom_context():
            wallet = WalletHolder.get_wallet()
            data: AssetNia = wallet.issue_asset_nia(
                online=asset.online, ticker=asset.ticker, name=asset.name, precision=asset.precision, amounts=asset.amounts)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @unlock_required
    @check_colorable_available()
    def issue_asset_cfa(asset: IssueAssetCfaRequestModel) -> AssetCfa:
        """Issue asset."""
        with repository_custom_context():
            # response = Request.post(ISSUE_ASSET_ENDPOINT_CFA, payload)
            # response.raise_for_status()  # Raises an exception for HTTP errors
            # data = response.json()
            # asset_data = data['asset']
            wallet = WalletHolder.get_wallet()
            print(1)
            data: AssetCfa = wallet.issue_asset_cfa(online=asset.online, details=asset.ticker, name=asset.name,
                                                    precision=asset.precision, amounts=asset.amounts, file_path=asset.file_path)
            print('------------>', data)
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return data

    @staticmethod
    @unlock_required
    @check_colorable_available()
    def issue_asset_uda(asset: IssueAssetUdaRequestModel) -> IssueAssetResponseModel:
        """Issue asset."""
        payload = asset.dict()
        with repository_custom_context():
            response = Request.post(ISSUE_ASSET_ENDPOINT_UDA, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            asset_data = data['asset']
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return IssueAssetResponseModel(**asset_data)

    @staticmethod
    @unlock_required
    def get_asset_media_hex(digest: GetAssetMediaModelRequestModel) -> GetAssetMediaModelResponseModel:
        """Get asset media hex from digest"""
        payload = digest.dict()
        with repository_custom_context():
            response = Request.post(GET_ASSET_MEDIA, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return GetAssetMediaModelResponseModel(**data)

    @staticmethod
    @unlock_required
    def post_asset_media(files) -> PostAssetMediaModelResponseModel:
        """return digest for given image"""
        with repository_custom_context():
            response = Request.post(POST_ASSET_MEDIA, files=files)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return PostAssetMediaModelResponseModel(**data)

    @staticmethod
    @unlock_required
    def fail_transfer(transfer: FailTransferRequestModel) -> FailTransferResponseModel:
        """Mark the specified transfer as failed."""
        payload = transfer.dict()
        with repository_custom_context():
            response = Request.post(FAIL_TRANSFER_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return FailTransferResponseModel(**data)
