"""
Model definitions for broadcast transaction functionality.
"""
# pylint: disable=too-few-public-methods
from __future__ import annotations

from pydantic import BaseModel
from rgb_lib import Operation


class PrimaryActionContext(BaseModel):
    """Context for determining primary action button state."""

    psbt_text: str
    can_broadcast: bool
    is_multisig: bool
    is_psbt_validated: bool
    pending_operation_present: bool
    is_watch_only: bool
    selector_index: int
    selector_visible: bool
    is_offline_mode: bool
    min_psbt_len: int


class MultisigThresholdLabels(BaseModel):
    """Labels for multisig threshold frame UI."""

    info_title: str
    info_sub: str
    tot_lbl: str
    tot_help: str
    req_lbl: str
    req_help: str


class PsbtDraftItem(BaseModel):
    """
    Model for PSBT draft item.
    """
    id: str
    psbt: str
    signed: bool
    purpose: str | None
    fascia_path: str | None = None
    entropy: int | None = None
    min_confirmations: int | None = None


class PsbtParsed(BaseModel):
    """
    Model for parsed PSBT.
    """
    psbt: str
    purpose: str | None


class MultisigPendingContext(BaseModel):
    """
    Model for multisig pending context.
    """
    psbt: str
    is_initiator: bool
    operation: Operation

    class Config:
        """
        Configuration for Pydantic model.
        """
        arbitrary_types_allowed = True


class RgbTransferInspectionSummary(BaseModel):
    """
    Model for RGB transfer inspection summary.
    """
    asset_id: str | None
    amount: int
    transfer_type_key: str | None


class PendingOperationMatchResult(BaseModel):
    """
    Model for pending operation match result.
    """
    operation: Operation | None
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
        """
        Configuration for Pydantic model.
        """
        arbitrary_types_allowed = True


class InspectionContext(BaseModel):
    """
    Model for inspection context.
    """
    is_inflation: bool
    rgb_expected: bool


class PsbtTextChangedContext(BaseModel):
    """
    Model for PSBT text changed context.
    """
    is_same_as_last: bool
    should_inspect: bool
    psbt_body: str | None
    is_rgb: bool
    is_inflation: bool
    purpose: str | None


class RenderInspectionResult(BaseModel):
    """
    Model for render inspection result.
    """
    should_render: bool
    should_show_sign_status: bool


class SignatureProgressContext(BaseModel):
    """
    Model for signature progress context.
    """
    has_valid_psbt: bool
    should_trigger_direct: bool
