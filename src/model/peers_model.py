"""
Peers Model Module
==================

This module defines models for connecting and disconnecting peers.
"""
# pylint: disable=too-few-public-methods
from __future__ import annotations

from pydantic import BaseModel

# -------------------- Helper models -----------------------


class StatusModel(BaseModel):
    """Response status model."""

    status: bool


class Peer(BaseModel):
    """this model part of list peer response model"""
    pubkey: str

# -------------------- Request models -----------------------


class ConnectPeerRequestModel(BaseModel):
    """Model for representing a request to connect to a peer."""

    peer_pubkey_and_addr: str


class DisconnectPeerRequestModel(BaseModel):
    """Model for representing a request to disconnect from a peer."""

    peer_pubkey: str

# -------------------- Response models -----------------------


class ConnectPeerResponseModel(StatusModel):
    """Response model for connect peer"""


class DisconnectResponseModel(StatusModel):
    """Response model for disconnect peer"""


class ListPeersResponseModel(BaseModel):
    """Response model for list peer"""
    peers: list[Peer | None]
