# pylint: disable=too-few-public-methods
"""
Module containing models related to the wallet method and transfer type widget.
"""
from __future__ import annotations

from enum import Enum
from typing import Callable

from pydantic import BaseModel

from src.model.rgb_model import RgbAssetPageLoadModel


class SelectionPageModel(BaseModel):
    """This model class used for Selection page widget"""
    title: str
    logo_1_path: str
    logo_1_title: str
    logo_2_path: str
    logo_2_title: str
    asset_id: str | None = None
    asset_name: str | None = None
    callback: str | None = None
    back_page_navigation: Callable | None = None
    rgb_asset_page_load_model: RgbAssetPageLoadModel | None = None


class AssetDataModel(BaseModel):
    """This model class is used to pass the asset ID to the next page from the selection page."""
    asset_type: str | Enum
    asset_id: str | None = None
    close_page_navigation: str | Enum | None = None
    expiry_time: int | None = None
    expiry_unit: str | None = None
