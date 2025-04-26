""""
Mocked function for payment repository.
"""
from __future__ import annotations

import pytest

# Mock for key_send method


@pytest.fixture
def mock_key_send(mocker):
    """Mocked key_send function."""
    def _mock_key_send(value):
        return mocker.patch(
            'src.data.repository.payments_repository.PaymentRepository.key_send',
            return_value=value,
        )
    return _mock_key_send

# Mock for send_payment method


@pytest.fixture
def mock_send_payment(mocker):
    """Mocked send_payment function."""
    def _mock_send_payment(value):
        return mocker.patch(
            'src.data.repository.payments_repository.PaymentRepository.send_payment',
            return_value=value,
        )
    return _mock_send_payment

# Mock for list_payment method


@pytest.fixture
def mock_list_payment(mocker):
    """Mocked list_payment function."""
    def _mock_list_payment(value):
        return mocker.patch(
            'src.data.repository.payments_repository.PaymentRepository.list_payment',
            return_value=value,
        )
    return _mock_list_payment
