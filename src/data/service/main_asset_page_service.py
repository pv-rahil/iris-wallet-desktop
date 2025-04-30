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
from src.data.repository.wallet_holder import WalletHolder
from src.data.service.helpers import main_asset_page_helper
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import GetBtcBalanceRequestModel
from src.model.btc_model import OfflineAsset
from src.model.common_operation_model import MainPageDataResponseModel
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import AssetModel
from src.model.rgb_model import FilterAssetRequestModel
from src.model.rgb_model import GetAssetResponseModel
from src.model.setting_model import IsHideExhaustedAssetEnabled
from src.utils.handle_exception import handle_exceptions


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
            online_wallet = WalletHolder.get_online()
            wallet_type: WalletType = SettingRepository.get_wallet_type()
            request_model = [
                AssetSchema.NIA,
                AssetSchema.CFA,
                AssetSchema.UDA,
            ]

            filtered_assets: list[AssetNia | AssetCfa | AssetUda | None] = []
            RgbRepository.refresh_transfer()
            asset_detail: GetAssetResponseModel = RgbRepository.get_assets(
                request_model,
            )
            btc_balance: BalanceResponseModel = BtcRepository.get_btc_balance(
                GetBtcBalanceRequestModel(online=online_wallet))
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

            if WalletType.REMOTE_TYPE_WALLET.value == wallet_type.value and asset_detail.cfa is not None:
                for asset in asset_detail.cfa:
                    if asset is None:
                        continue
                    filtered_asset: AssetModel = main_asset_page_helper.convert_digest_to_hex(
                        asset,
                    )
                    filtered_assets.append(filtered_asset)

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
