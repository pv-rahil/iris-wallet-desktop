"""Module containing InvoiceRepository."""
from __future__ import annotations

from src.model.invoices_model import DecodeInvoiceResponseModel
from src.model.invoices_model import DecodeLnInvoiceRequestModel
from src.model.invoices_model import InvoiceStatusRequestModel
from src.model.invoices_model import InvoiceStatusResponseModel
from src.model.invoices_model import LnInvoiceRequestModel
from src.model.invoices_model import LnInvoiceResponseModel
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import DECODE_LN_INVOICE_ENDPOINT
from src.utils.endpoints import INVOICE_STATUS_ENDPOINT
from src.utils.endpoints import LN_INVOICE_ENDPOINT
from src.utils.request import Request


class InvoiceRepository:
    """Repository for handling invoices."""

    @staticmethod
    @unlock_required
    def decode_ln_invoice(invoice: DecodeLnInvoiceRequestModel) -> DecodeInvoiceResponseModel:
        """Decode LN invoice."""
        payload = invoice.dict()
        with repository_custom_context():
            response = Request.post(DECODE_LN_INVOICE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return DecodeInvoiceResponseModel(**data)

    @staticmethod
    @unlock_required
    def invoice_status(invoice: InvoiceStatusRequestModel) -> InvoiceStatusResponseModel:
        """Get invoice status."""
        payload = invoice.dict()
        with repository_custom_context():
            response = Request.post(INVOICE_STATUS_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return InvoiceStatusResponseModel(**data)

    @staticmethod
    @unlock_required
    def ln_invoice(invoice: LnInvoiceRequestModel) -> LnInvoiceResponseModel:
        """Create LN invoice."""
        payload = invoice.dict()
        with repository_custom_context():
            response = Request.post(LN_INVOICE_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return LnInvoiceResponseModel(**data)
