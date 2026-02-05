# pylint: disable=too-few-public-methods
"""Models for PSBT selection and pending operation display."""
from __future__ import annotations

from pydantic import BaseModel


class PsbtSelectionItemModel(BaseModel):
    """Pre-processed PSBT item for UI selection."""

    id: str = ''
    purpose: str = 'psbt'
    psbt: str = ''
    display_title: str = ''

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class PendingOperationDisplayModel(BaseModel):
    """Pre-processed pending operation data for UI display."""

    psbt: str = ''
    is_initiator: bool = False
    operation: object | None = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
