""""
Mocked function for invoice repository.
"""
from __future__ import annotations

import pytest

# Mock for decode_ln_invoice method


@pytest.fixture
def mock_decode_ln_invoice(mocker):
    """Mocked decode_ln_invoice function."""
    def _mock_decode_ln_invoice(value):
        return mocker.patch(
            'src.data.repository.invoices_repository.InvoiceRepository.decode_ln_invoice',
            return_value=value,
        )
    return _mock_decode_ln_invoice

# Mock for invoice_status method


@pytest.fixture
def mock_invoice_status(mocker):
    """Mocked invoice_status function."""
    def _mock_invoice_status(value):
        return mocker.patch(
            'src.data.repository.invoices_repository.InvoiceRepository.invoice_status',
            return_value=value,
        )
    return _mock_invoice_status

# Mock for ln_invoice method


@pytest.fixture
def mock_ln_invoice(mocker):
    """Mocked ln_invoice function."""
    def _mock_ln_invoice(value):
        return mocker.patch(
            'src.data.repository.invoices_repository.InvoiceRepository.ln_invoice',
            return_value=value,
        )
    return _mock_ln_invoice
