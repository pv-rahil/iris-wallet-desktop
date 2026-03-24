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


class PendingOperationMatchResult(BaseModel):
    operation: object | None
    pending_operation: object | None
    transfer_type: str | None
    is_inflation: bool
    should_trigger_rgb_inspection: bool
    fascia_path: str | None
    entropy: int
    is_initiator: bool
    ack_count: int
    threshold: int | None

    class Config:
        arbitrary_types_allowed = True


class InspectionContext(BaseModel):
    is_inflation: bool
    rgb_expected: bool


class PsbtTextChangedContext(BaseModel):
    is_same_as_last: bool
    should_inspect: bool
    psbt_body: str | None
    is_rgb: bool
    is_inflation: bool
    purpose: str | None


class RenderInspectionResult(BaseModel):
    should_render: bool
    should_show_sign_status: bool


class SignatureProgressContext(BaseModel):
    has_valid_psbt: bool
    should_trigger_direct: bool
