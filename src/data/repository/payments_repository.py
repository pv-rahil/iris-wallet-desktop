"""Module containing PaymentRepository."""
from __future__ import annotations

from src.model.payments_model import KeySendRequestModel
from src.model.payments_model import KeysendResponseModel
from src.model.payments_model import ListPaymentResponseModel
from src.model.payments_model import SendPaymentRequestModel
from src.model.payments_model import SendPaymentResponseModel
from src.utils.cache import Cache
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import KEY_SEND_ENDPOINT
from src.utils.endpoints import LIST_PAYMENTS_ENDPOINT
from src.utils.endpoints import SEND_PAYMENT_ENDPOINT
from src.utils.request import Request


class PaymentRepository:
    """Repository for handling payments."""

    @staticmethod
    @unlock_required
    def key_send(key_send: KeySendRequestModel) -> KeysendResponseModel:
        """Send payment with a key."""
        payload = key_send.dict()
        with repository_custom_context():
            response = Request.post(KEY_SEND_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return KeysendResponseModel(**data)

    @staticmethod
    @unlock_required
    def send_payment(send_payment_detail: SendPaymentRequestModel) -> SendPaymentResponseModel:
        """Send a payment."""
        payload = send_payment_detail.dict()
        with repository_custom_context():
            response = Request.post(SEND_PAYMENT_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
            return SendPaymentResponseModel(**data)

    @staticmethod
    @unlock_required
    def list_payment() -> ListPaymentResponseModel:
        """List payments."""
        with repository_custom_context():

            response = Request.get(LIST_PAYMENTS_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return ListPaymentResponseModel(**data)
