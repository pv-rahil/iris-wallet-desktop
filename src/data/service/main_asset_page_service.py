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
from src.model.setting_model import IsHideExhaustedAssetEnabled
from src.utils.handle_exception import handle_exceptions
from src.utils.page_navigation_events import PageNavigationEventManager


class MainAssetPageDataService:
    """
    Service class for main asset page data.
    """

    @staticmethod
    def get_assets() -> MainPageDataResponseModel:
        """
        Fetch and return main page data including asset details and BTC balance.

        Returns:
            MainPageDataResponseModel: The main page data containing asset details and BTC balance.
        """
        try:
            request_model = FilterAssetRequestModel(
                filter_asset_schemas=[
                    AssetSchema.NIA,
                    AssetSchema.CFA,
                    AssetSchema.UDA,
                ],
            )

            filtered_assets: list[AssetNia | AssetCfa | AssetUda | None] = []
            asset_detail: GetAssetResponseModel = RgbRepository.get_assets(
                request_model,
            )
            is_offline_wallet = SettingRepository.get_wallet_type(
            ) == WalletType.OFFLINE_TYPE_WALLET

            btc_balance: BalanceResponseModel
            if is_offline_wallet:
                wallet_service = WalletDataService.get_session()
                if wallet_service is not None:
                    btc_balance = wallet_service.get_btc_balance()
                else:
                    btc_balance = BtcRepository.get_btc_balance()
            else:
                refresh_data = RgbRepository.refresh_transfer()
                if refresh_data:
                    failures_only = {
                        k: v for k, v in refresh_data.items() if v.failure is not None
                    }
                    if failures_only:
                        items: list[RefreshFailureItem] = []
                        all_assets: list[AssetNia | AssetCfa | AssetUda | None] = (
                            (asset_detail.nia or []) +
                            (asset_detail.cfa or []) + (asset_detail.uda or [])
                        )
                        for failed_id, failed_entry in failures_only.items():
                            found_asset_id: str | None = None
                            for a in all_assets:
                                if a is None:
                                    continue
                                try:
                                    transfers = RgbRepository.list_transfers(
                                        ListTransfersRequestModel(
                                            asset_id=a.asset_id,
                                        ),
                                    )
                                    if any(int(t.idx) == int(failed_id) for t in transfers if t.idx is not None):
                                        found_asset_id = a.asset_id
                                        break
                                except Exception:
                                    continue
                            if found_asset_id is not None and failed_entry.failure is not None:
                                items.append(
                                    RefreshFailureItem(
                                        asset_id=found_asset_id, failure=failed_entry.failure,
                                    ),
                                )
                        if items:
                            PageNavigationEventManager.get_instance(
                            ).refresh_transfer_result_dialog_signal.emit(items)
                btc_balance = BtcRepository.get_btc_balance()

            stored_network: NetworkEnumModel = SettingRepository.get_wallet_network()
            btc_ticker: str = main_asset_page_helper.get_offline_asset_ticker(
                network=stored_network,
            )
            btc_name: str = main_asset_page_helper.get_asset_name(
                network=stored_network,
            )
            is_exhausted_asset_enabled: IsHideExhaustedAssetEnabled = SettingRepository.is_exhausted_asset_enabled()

            def has_non_zero_balance(asset: AssetNia | AssetCfa | AssetUda | None) -> bool:
                if asset is None:
                    return False
                balance = asset.balance
                return not balance.future == 0

            if is_exhausted_asset_enabled.is_enabled:
                if asset_detail.nia:
                    asset_detail.nia = [
                        asset for asset in asset_detail.nia if has_non_zero_balance(asset)
                    ]
                if asset_detail.uda:
                    asset_detail.uda = [
                        asset for asset in asset_detail.uda if has_non_zero_balance(asset)
                    ]
                if asset_detail.cfa:
                    asset_detail.cfa = [
                        asset for asset in asset_detail.cfa if has_non_zero_balance(asset)
                    ]

            if len(filtered_assets) > 0:
                asset_detail.cfa = filtered_assets

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
