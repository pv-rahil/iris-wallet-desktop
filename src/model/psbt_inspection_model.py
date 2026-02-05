# pylint: disable=too-few-public-methods
"""Module containing models for PSBT inspection."""
from __future__ import annotations

from pydantic import BaseModel


class PsbtInspectionResponseModel(BaseModel):
    """Response model for processed PSBT inspection data."""

    txid: str = ''
    txid_display: str = ''
    fee_sats: int | None = None
    fee_display: str = ''
    signature_count: int = 0
    is_valid: bool = False

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class RgbInspectionResponseModel(BaseModel):
    """Response model for processed RGB inspection data."""

    asset_id: str | None = None
    asset_id_display: str | None = None
    send_amount: int = 0
    inflation_amount: int = 0
    amount_display: str | None = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class OperationContextModel(BaseModel):
    """Processed operation context model."""

    asset_id: str | None = None
    amount: int | None = None
    min_confirmations: int | None = None
    transfer_type: str | None = None
    transfer_type_display: str = ''
    consignment_paths: list[str] | None = None
    entropy: str | None = None
    psbt: str | None = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class PsbtDisplayDataModel(BaseModel):
    """Complete pre-processed data ready for UI display."""

    # Core transaction info
    txid: str = ''
    txid_display: str = ''
    fee_sats: int | None = None
    fee_display: str = ''
    signature_count: int = 0
    is_valid: bool = False

    # Transfer type info
    transfer_type: str | None = None
    transfer_type_display: str = ''

    # RGB-specific
    asset_id: str | None = None
    asset_id_display: str | None = None
    amount: int | None = None
    amount_display: str | None = None
    min_confirmations: int | None = None

    # UI visibility flags
    show_asset_tile: bool = False
    show_amount_tile: bool = False
    show_destination_tile: bool = False
    show_fee_tile: bool = False
    show_type_tile: bool = False
    show_minconf_tile: bool = False
    is_btc_only: bool = True
    is_inflation_context: bool = False

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
