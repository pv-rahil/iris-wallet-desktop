from __future__ import annotations

from pydantic import BaseModel


class PsbtDraftItem(BaseModel):
    id: str
    psbt: str
    signed: bool
    purpose: str | None


class PsbtParsed(BaseModel):
    psbt: str
    purpose: str | None


class MultisigPendingContext(BaseModel):
    psbt: str
    is_initiator: bool
    operation: object

    class Config:
        arbitrary_types_allowed = True


class RgbTransferInspectionSummary(BaseModel):
    asset_id: str | None
    amount: int
    transfer_type_key: str | None
