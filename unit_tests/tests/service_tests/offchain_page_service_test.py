"""Unit test for offchain page services"""
from __future__ import annotations

import unittest
from unittest.mock import patch

import pytest

from src.data.repository.invoices_repository import InvoiceRepository
from src.data.repository.payments_repository import PaymentRepository
from src.data.service.offchain_page_service import OffchainService
from src.model.invoices_model import DecodeInvoiceResponseModel
from src.model.invoices_model import DecodeLnInvoiceRequestModel
from src.model.payments_model import SendPaymentRequestModel
from src.model.payments_model import SendPaymentResponseModel
from src.utils.custom_exception import CommonException


class TestOffchainService(unittest.TestCase):
    """
    Unit tests for OffchainService class.
    """

    @patch.object(PaymentRepository, 'send_payment')
    @patch.object(InvoiceRepository, 'decode_ln_invoice')
    def test_send_success(self, mock_decode_ln_invoice, mock_send_payment):
        """
        Test case for successful sending of payment through OffchainService.

        This test verifies that OffchainService correctly handles sending a payment
        and decoding a Lightning Network invoice.

        Mocks:
        - PaymentRepository.send_payment: Simulates sending a payment and returns mock_send_response.
        - InvoiceRepository.decode_ln_invoice: Simulates decoding a LN invoice and returns mock_decode_response.
        """
        # Mock data
        mock_encoded_invoice = 'lnbcrt30u1pjv6yzndqud3jxktt5w46x7unfv9kz6mn0v3jsnp4qdpc280eur52luxppv6f3nnj8l6vnd9g2hnv3qv6mjhmhvlzf6327pp5tjjasx6g9dqptea3fhm6yllq5wxzycnnvp8l6wcq3d6j2uvpryuqsp5l8az8x3g8fe05dg7cmgddld3da09nfjvky8xftwsk4cj8p2l7kfq9qyysgqcqpcxqzdylzlwfnkyw3jv344x4rzwgkk53ng0fhxy5rdduk4g5tpvea8xa6rfckkza35va28xjn2tqkhgarcxep5umm4x5k56wfcdvu95eq7qzp20vrl4xz76syapsa3c09j7lg5gerkaj63llj0ark7ph8hfketn6fkqzm8laf66dhsncm23wkwm5l5377we9e8lnlknnkwje5eefkccusqm6rqt8'  # pylint:disable=line-too-long
        mock_send_response = SendPaymentResponseModel(
            payment_hash='3febfae1e68b190c15461f4c2a3290f9af1dae63fd7d620d2bd61601869026cd',
            payment_secret='777a7756c620868199ed5fdc35bee4095b5709d543e5c2bf0494396bf27d2ea2', status='Pending',
        )
        mock_decode_response = DecodeInvoiceResponseModel(
            amt_msat=3000000,
            expiry_sec=420,
            timestamp=1691160659,
            asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
            asset_amount=42, payment_hash='5ca5d81b482b4015e7b14df7a27fe0a38c226273604ffd3b008b752571811938',
            payment_secret='f9fa239a283a72fa351ec6d0d6fdb16f5e59a64cb10e64add0b57123855ff592',
            payee_pubkey='0343851df9e0e8aff0c10b3498ce723ff4c9b4a855e6c8819adcafbbb3e24ea2af',
            network='Regtest',
        )

        # Configure mocks
        mock_send_payment.return_value = mock_send_response
        mock_decode_ln_invoice.return_value = mock_decode_response

        # Call the method under test
        result = OffchainService.send(mock_encoded_invoice)

        # Assert that the repositories were called with the correct arguments
        mock_send_payment.assert_called_once_with(
            SendPaymentRequestModel(invoice=mock_encoded_invoice),
        )
        mock_decode_ln_invoice.assert_called_once_with(
            DecodeLnInvoiceRequestModel(invoice=mock_encoded_invoice),
        )

        # Assert the combined result
        self.assertEqual(result.send, mock_send_response)
        self.assertEqual(result.decode, mock_decode_response)

    @patch.object(PaymentRepository, 'send_payment')
    def test_send_exception_handling(self, mock_send_payment):
        """
        Test case for exception handling in OffchainService.send.

        This test verifies that OffchainService properly raises a CommonException
        when an exception occurs during the payment sending process.
        """
        # Mock data
        mock_encoded_invoice = 'lnbcrt30u1pjv6yzndqud3jxktt5w46x7unfv9kz6mn0v3jsnp4qdpc280eur52luxppv6f3nnj8l6vnd9g2hnv3qv6mjhmhvlzf6327pp5tjjasx6g9dqptea3fhm6yllq5wxzycnnvp8l6wcq3d6j2uvpryuqsp5l8az8x3g8fe05dg7cmgddld3da09nfjvky8xftwsk4cj8p2l7kfq9qyysgqcqpcxqzdylzlwfnkyw3jv344x4rzwgkk53ng0fhxy5rdduk4g5tpvea8xa6rfckkza35va28xjn2tqkhgarcxep5umm4x5k56wfcdvu95eq7qzp20vrl4xz76syapsa3c09j7lg5gerkaj63llj0ark7ph8hfketn6fkqzm8laf66dhsncm23wkwm5l5377we9e8lnlknnkwje5eefkccusqm6rqt8'  # pylint:disable=line-too-long

        mock_send_payment.side_effect = CommonException(
            'Unable to connect to node',
        )
        with pytest.raises(CommonException) as exc_info:
            # Call the method under test
            OffchainService.send(mock_encoded_invoice)

        assert str(
            exc_info.value,
        ) in ('Unable to connect to node')
