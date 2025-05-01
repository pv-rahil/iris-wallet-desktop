"""This module is contain methods for faucet"""
from __future__ import annotations

from src.data.repository.faucet_repository import FaucetRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.helpers.faucet_service_helper import generate_sha256_hash
from src.data.service.helpers.faucet_service_helper import get_faucet_url
from src.model.enums.enums_model import NetworkEnumModel
from src.model.rgb_faucet_model import BriefAssetInfo
from src.model.rgb_faucet_model import ConfigWalletResponse
from src.model.rgb_faucet_model import ListAssetResponseModel
from src.model.rgb_faucet_model import ListAvailableAsset
from src.model.rgb_faucet_model import RequestAssetResponseModel
from src.model.rgb_faucet_model import RequestFaucetAssetModel
from src.model.rgb_model import RgbInvoiceDataResponseModel
from src.model.rgb_model import RgbInvoiceRequestModel
from src.utils.custom_exception import CommonException
from src.utils.handle_exception import handle_exceptions
# from src.data.repository.common_operations_repository import CommonOperationRepository
# from src.model.common_operation_model import NodeInfoResponseModel


class FaucetService:
    """Service class for faucet"""
    @staticmethod
    def list_available_asset() -> ListAvailableAsset | None:
        """Service to list all faucet assets"""
        try:
            network: NetworkEnumModel = SettingRepository.get_wallet_network()
            response: ListAssetResponseModel = FaucetRepository.list_available_faucet_asset(
                get_faucet_url(network=network),
            )
            # Ensure assets are not None and are in a valid format
            if not hasattr(response, 'assets') or not response.assets:
                return None
            short_asset_detail: list[BriefAssetInfo] = []
            for key, asset in response.assets.items():
                if asset:  # Check if asset exists
                    short_asset_detail.append(
                        BriefAssetInfo(
                            asset_id=key, asset_name=asset.name,
                        ),
                    )
            return ListAvailableAsset(faucet_assets=short_asset_detail)
        except Exception as exc:
            return handle_exceptions(exc=exc)

    @staticmethod
    def request_asset_from_faucet() -> RequestAssetResponseModel:
        """Request asset from faucet"""
        try:
            network: NetworkEnumModel = SettingRepository.get_wallet_network()
            # node_info: NodeInfoResponseModel = CommonOperationRepository.node_info()
            # xpub_key: str = node_info.onchain_pubkey
            xpub_key = 's kvj'
            hashed_value = generate_sha256_hash(xpub_key)
            invoice: RgbInvoiceDataResponseModel = RgbRepository.rgb_invoice(
                RgbInvoiceRequestModel(),
            )
            config: ConfigWalletResponse = FaucetRepository.config_wallet(
                get_faucet_url(network=network), hashed_value,
            )
            if not config.groups:
                raise CommonException('Unable to get asset group of faucet')
            asset_group = list(config.groups.keys())[0]
            response: RequestAssetResponseModel = FaucetRepository.request_asset(
                get_faucet_url(network=network), RequestFaucetAssetModel(
                    wallet_id=hashed_value,
                    invoice=invoice.invoice,
                    asset_group=asset_group,
                ),
            )
            return response
        except Exception as exc:
            return handle_exceptions(exc=exc)
