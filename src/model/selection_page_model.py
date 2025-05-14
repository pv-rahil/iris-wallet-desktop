# pylint: disable=too-few-public-methods
"""
Module containing models related to the wallet method and transfer type widget.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class AssetDataModel(BaseModel):
    """This model class is used to pass the asset ID to the next page from the selection page."""
    asset_type: str | Enum
    asset_id: str | None = None
    close_page_navigation: str | Enum | None = None
    expiry_time: int | None = None
    expiry_unit: str | None = None
