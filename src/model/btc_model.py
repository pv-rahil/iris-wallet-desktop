# pylint:disable=too-few-public-methods
# Model classes are used to store data and don't require methods.
"""
Bitcoin Model Module
====================

This module defines Pydantic models related to Bitcoin transactions and addresses.
"""
from __future__ import annotations

from pydantic import BaseModel
from rgb_lib import Balance
from rgb_lib import Transaction
from rgb_lib import Unspent

# -------------------- Helper models -----------------------


class OfflineAsset(BaseModel):
    """Model for offline asset"""
    asset_id: str | None = None
    ticker: str
    balance: Balance
    name: str
    asset_iface: str = 'BITCOIN'

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


# -------------------- Request Models -----------------------

class EstimateFeeRequestModel(BaseModel):
    """Model for estimated fee"""
    blocks: int


class SendBtcRequestModel(BaseModel):
    """Model representing a request to send bitcoin."""
    amount: int
    address: str
    fee_rate: int
    skip_sync: bool = False


class UnspentListRequestModel (BaseModel):
    """Model representing a request to list unspent."""
    settled_only: bool = False
    skip_sync: bool = False


# -------------------- Response Models -----------------------


class TransactionListResponse(BaseModel):
    """Model representing response of list transaction api"""
    transactions: list[Transaction | None]

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


class TransactionListWithBalanceResponse(TransactionListResponse):
    """Model representing response of list transaction api"""
    balance: BalanceResponseModel


class UnspentsListResponseModel(BaseModel):
    """Model representing response of list unspents api"""
    unspents: list[Unspent | None]

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


class SendBtcResponseModel(BaseModel):
    """Model representing response of sendbtc api"""
    txid: str


class BalanceResponseModel(BaseModel):
    """Model representing a response containing Bitcoin balance information."""

    vanilla: Balance
    colored: Balance

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True


class AddressResponseModel(BaseModel):
    """Model representing a response containing a Bitcoin address."""

    address: str


class EstimateFeeResponse(BaseModel):
    """Model representing a response containing the estimated fee_rate"""
    fee_rate: float
