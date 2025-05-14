# pylint: disable=too-few-public-methods
"""Service class for issue asset in case of more then two api call"""
from __future__ import annotations

import os

from src.data.repository.rgb_repository import RgbRepository
from src.model.rgb_model import IssueAssetCfaRequestModel
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_IMAGE_PATH_NOT_EXITS
from src.utils.handle_exception import handle_exceptions


class IssueAssetService:
    """
    Service class for issue asset
    """
    @staticmethod
    def issue_asset_cfa(new_asset_detail: IssueAssetCfaRequestModel) -> IssueAssetResponseModel | None:
        """This function issue cfa asset"""
        try:
            if not os.path.exists(new_asset_detail.file_path):
                raise CommonException(ERROR_IMAGE_PATH_NOT_EXITS)
            issued_asset: IssueAssetResponseModel = RgbRepository.issue_asset_cfa(
                IssueAssetCfaRequestModel(
                    amounts=new_asset_detail.amounts,
                    ticker=new_asset_detail.ticker,
                    name=new_asset_detail.name,
                    file_path=new_asset_detail.file_path,
                ),
            )
            return issued_asset
        except Exception as exc:
            return handle_exceptions(exc)
