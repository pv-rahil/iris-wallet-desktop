# pylint: disable=too-few-public-methods
"""
This module provides the service for the main asset page.
"""
from __future__ import annotations

from rgb_lib import AssetCfa
from rgb_lib import AssetNia
from rgb_lib import AssetSchema
from rgb_lib import AssetUda

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.helpers import main_asset_page_helper
from src.data.service.wallet_data_service import WalletDataService
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import OfflineAsset
from src.model.common_operation_model import MainPageDataResponseModel
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import GetAssetResponseModel
from src.model.rgb_model import ListTransfersRequestModel
from src.model.rgb_model import RefreshFailureItem
from src.utils.handle_exception import handle_exceptions
from src.utils.page_navigation_events import PageNavigationEventManager


class MainAssetPageDataService:
    """
    Service class for main asset page data.
    """

    @staticmethod
    def get_assets() -> MainPageDataResponseModel:
        """
        Get assets for the main asset page.

        Returns:
            MainPageDataResponseModel: The assets for the main asset page.
        """
        try:
            is_offline_wallet = SettingRepository.get_wallet_type(
            ) == WalletType.OFFLINE_TYPE_WALLET
            btc_balance = MainAssetPageDataService().get_btc_balance(is_offline_wallet)

            asset_detail: GetAssetResponseModel = RgbRepository.get_assets(
                FilterAssetRequestModel(
                    filter_asset_schemas=[
                        AssetSchema.NIA,
                        AssetSchema.CFA, AssetSchema.UDA,
                    ],
                ),
            )

            asset_detail = MainAssetPageDataService().filter_exhausted_assets(asset_detail)

            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()
            btc_ticker = main_asset_page_helper.get_offline_asset_ticker(
                network=stored_network,
            )
            btc_name = main_asset_page_helper.get_asset_name(
                network=stored_network,
            )

            return MainPageDataResponseModel(
                nia=asset_detail.nia or [],
                cfa=asset_detail.cfa or [],
                uda=asset_detail.uda or [],
                vanilla=OfflineAsset(
                    ticker=btc_ticker,
                    balance=btc_balance.vanilla,
                    name=btc_name,
                ),
            )

        except Exception as exc:
            return handle_exceptions(exc)

    def get_btc_balance(self, is_offline_wallet: bool) -> BalanceResponseModel:
        """
        Fetch and return BTC balance.

        Args:
            is_offline_wallet (bool): Whether the wallet is offline.

        Returns:
            BalanceResponseModel: The BTC balance.
        """
        if is_offline_wallet:
            wallet_service = WalletDataService.get_session()
            return wallet_service.get_btc_balance() if wallet_service else BtcRepository.get_btc_balance()

        # Online wallet
        refresh_data = RgbRepository.refresh_transfer()
        if refresh_data:
            self.handle_refresh_failures(refresh_data)
        return BtcRepository.get_btc_balance()

    def handle_refresh_failures(self, refresh_data: dict):
        """
        Handle refresh failures.

        Args:
            refresh_data (dict): The refresh data.
        """
        failures_only = {
            k: v for k, v in refresh_data.items()
            if v.failure is not None
        }
        if not failures_only:
            return

        all_assets = self.get_all_assets()
        items: list[RefreshFailureItem] = []

        for failed_id, failed_entry in failures_only.items():
            found_asset_id = self.find_asset_for_failed_transfer(
                failed_id, all_assets,
            )
            if found_asset_id and failed_entry.failure:
                items.append(
                    RefreshFailureItem(
                        asset_id=found_asset_id, failure=failed_entry.failure,
                    ),
                )

        if items:
            PageNavigationEventManager.get_instance(
            ).refresh_transfer_result_dialog_signal.emit(items)

    def get_all_assets(self) -> list[AssetNia | AssetCfa | AssetUda | None]:
        """
        Get all assets.

        Returns:
            list[AssetNia | AssetCfa | AssetUda | None]: The list of assets.
        """
        asset_detail = RgbRepository.get_assets(
            FilterAssetRequestModel(
                filter_asset_schemas=[
                    AssetSchema.NIA,
                    AssetSchema.CFA, AssetSchema.UDA,
                ],
            ),
        )
        return (asset_detail.nia or []) + (asset_detail.cfa or []) + (asset_detail.uda or [])

    def find_asset_for_failed_transfer(self, failed_id: str, assets: list) -> str | None:
        """
        Find the asset for the failed transfer.

        Args:
            failed_id (str): The failed transfer ID.
            assets (list): The list of assets.

        Returns:
            str | None: The asset ID for the failed transfer.
        """
        for a in assets:
            if a is None:
                continue
            try:
                transfers = RgbRepository.list_transfers(
                    ListTransfersRequestModel(asset_id=a.asset_id),
                )
                if any(int(t.idx) == int(failed_id) for t in transfers if t.idx is not None):
                    return a.asset_id
            except Exception:
                continue
        return None

    def filter_exhausted_assets(self, asset_detail: GetAssetResponseModel) -> GetAssetResponseModel:
        """
        Filter out exhausted assets.

        Args:
            asset_detail (GetAssetResponseModel): The asset detail.

        Returns:
            GetAssetResponseModel: The filtered asset detail.
        """
        is_exhausted_enabled = SettingRepository.is_exhausted_asset_enabled().is_enabled

        if not is_exhausted_enabled:
            return asset_detail

        def has_non_zero(asset):
            return asset is not None and not asset.balance.future == 0

        asset_detail.nia = [
            a for a in (
                asset_detail.nia or []
            ) if has_non_zero(a)
        ]
        asset_detail.cfa = [
            a for a in (
                asset_detail.cfa or []
            ) if has_non_zero(a)
        ]
        asset_detail.uda = [
            a for a in (
                asset_detail.uda or []
            ) if has_non_zero(a)
        ]
        return asset_detail
