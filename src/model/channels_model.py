# pylint:disable=too-few-public-methods
# Model classes are used to store data and don't require methods.
"""
Module defining Pydantic models for channel operations.

This module contains Pydantic models for representing requests related to channel operations
such as opening and closing channels in a Lightning Network.
"""
from __future__ import annotations

from pydantic import BaseModel

# -------------------- Helper models -----------------------


class StatusModel(BaseModel):
    """Response status model."""

    status: bool


class Channel(BaseModel):
    """Model part of list channels api"""
    channel_id: str
    funding_txid: str | None
    peer_pubkey: str
    peer_alias: str | None
    short_channel_id: int | None = None
    status: str
    ready: bool
    capacity_sat: int
    local_balance_sat: int
    outbound_balance_msat: int | None = None
    inbound_balance_msat: int | None = None
    is_usable: bool
    public: bool
    asset_id: str | None = None
    asset_local_amount: int | None = None
    asset_remote_amount: int | None = None

# -------------------- Request models -----------------------


class CloseChannelRequestModel(BaseModel):
    """Model for closing a channel request."""

    channel_id: str
    peer_pubkey: str
    force: bool = False


class OpenChannelsRequestModel(BaseModel):
    """Model for opening channels request."""

    peer_pubkey_and_opt_addr: str
    capacity_sat: int = 30010
    push_msat: int = 1394000
    asset_amount: int | None = None
    asset_id: str | None = None
    public: bool = True
    with_anchors: bool = True
    fee_base_msat: int = 1000
    fee_proportional_millionths: int = 0


# -------------------- Response models -----------------------

class CloseChannelResponseModel(StatusModel):
    """Close channel response status model."""


class ChannelsListResponseModel(BaseModel):
    """Model representing response of list channels api"""
    channels: list[Channel | None]


class OpenChannelResponseModel(BaseModel):
    """Model representing response of open channel api"""
    temporary_channel_id: str

# ---------------------Insufficient Allocation Slot MOdel ---------------------------


class HandleInsufficientAllocationSlotsModel(BaseModel):
    """Custom request model for handle insufficient allocation slot error"""
    capacity_sat: int
    pub_key: str
    push_msat: int
    asset_id: str
    amount: int

# -------------------Channel Detail Model------------------------


class ChannelDetailDialogModel(BaseModel):
    """Model for Channel detail dialog box"""
    pub_key: str
    channel_id: str
    bitcoin_local_balance: int
    bitcoin_remote_balance: int
