# pylint: disable=too-few-public-methods
"""
Module containing models related to the transaction detail page.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from rgb_lib import BlockTime
from rgb_lib import Outpoint
from rgb_lib import TransferTransportEndpoint

from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel


class TransactionDetailPageModel(BaseModel):
    """
    This model is used extensively across the codebase to ensure a consistent structure
    for transaction-related data for transaction detail page. It serves as the standard format for passing transaction
    details into methods and for structuring responses from methods that deal with transaction
    information.
    """
    tx_id: str
    amount: str
    asset_id: str | None = None
    image_path: str | None = None
    asset_name: str | None = None
    confirmation_date: BlockTime | str | None = None
    confirmation_time: BlockTime | str | None = None
    updated_date: str | None = None
    updated_time: str | None = None
    transaction_status: TransactionStatusEnumModel | str
    transfer_status: TransferStatusEnumModel | None = None
    consignment_endpoints: list[TransferTransportEndpoint | None] | None = []
    recipient_id: str | None = None
    receive_utxo: Outpoint | None = None
    change_utxo: Outpoint | None = None
    asset_type: Enum | None = None
    inbound: bool | None = None

    class Config:
        """Pydantic configuration class allowing arbitrary types."""
        arbitrary_types_allowed = True
