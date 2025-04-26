# pylint: disable=too-few-public-methods
"""Module containing models related to payments."""
from __future__ import annotations

from pydantic import BaseModel

from src.model.invoices_model import DecodeInvoiceResponseModel

# -------------------- Helper models -----------------------


class BaseTimeStamps(BaseModel):
    """
    Base class to hold common timestamp attributes.
    """
    created_at: int
    updated_at: int
    created_at_date: str | None = None  # for UI purpose
    created_at_time: str | None = None  # for UI purpose
    updated_at_date: str | None = None  # for UI purpose
    updated_at_time: str | None = None  # for UI purpose


class Payment(BaseTimeStamps):
    """this Model part of list payments"""
    amt_msat: int
    asset_amount: int | None = None
    asset_amount_status: str | None = None  # this for ui purpose
    asset_id: str | None = None
    payment_hash: str
    inbound: bool
    status: str
    payee_pubkey: str


# -------------------- Request models -----------------------
class KeySendRequestModel(BaseModel):
    """Request model for sending payments via key send."""

    dest_pubkey: str
    amt_msat: int = 3000000
    asset_id: str
    assert_amount: int


class SendPaymentRequestModel(BaseModel):
    """Request model for sending payments using Lightning Network invoices."""

    invoice: str

# -------------------- Response models -----------------------


class KeysendResponseModel(BaseModel):
    """Response model for ln invoice"""
    payment_hash: str
    payment_secret: str
    status: str


class ListPaymentResponseModel(BaseModel):
    """Response model for list payments"""
    payments: list[Payment | None] | None = []


class SendPaymentResponseModel(KeysendResponseModel):
    """Response model for send payment"""


class CombinedDecodedModel(BaseModel):
    """CombinedDecodedModel for offchain service response"""
    send: KeysendResponseModel
    decode: DecodeInvoiceResponseModel
