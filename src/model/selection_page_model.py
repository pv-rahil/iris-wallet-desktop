# pylint: disable=too-few-public-methods
"""
Module containing models related to the wallet method and transfer type widget.
"""
from __future__ import annotations

from enum import Enum
from typing import Callable

from pydantic import BaseModel


class SelectionPageModel(BaseModel):
    """This model class used for Selection page widget"""
    title: str
    logo_1_path: str
    logo_1_title: str
    logo_1_info: str
    logo_2_path: str
    logo_2_title: str
    logo_2_info: str
    step_index: int = 0


class AssetDataModel(BaseModel):
    """This model class is used to pass the asset ID to the next page from the selection page."""
    asset_type: str | Enum
    asset_id: str | None = None
    close_page_navigation: str | Enum | None = None
