# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""
This module contains unit tests for the LnOffchainViewModel
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import PaymentStatus
from src.model.invoices_model import DecodeInvoiceResponseModel
from src.model.invoices_model import LnInvoiceResponseModel
from src.model.payments_model import CombinedDecodedModel
from src.model.payments_model import KeysendResponseModel
from src.model.payments_model import ListPaymentResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.ln_offchain_view_model import LnOffChainViewModel


@pytest.fixture
def ln_offchain_view_model(mocker):
    """Fixture for LnOffChainViewModel"""
    mock_page_navigation = mocker.Mock()
    return LnOffChainViewModel(mock_page_navigation)


def test_on_error_common_exception(ln_offchain_view_model):
    """Test error handling for CommonException"""
    with patch('src.views.components.toast.ToastManager.error') as mock_show_toast:
        exc = CommonException('Custom error message')
        ln_offchain_view_model._handle_error(exc)
        mock_show_toast.assert_called_once_with(
            description='Custom error message',
        )


def test_on_error_generic_exception(ln_offchain_view_model):
    """Test error handling for generic exception"""
    with patch('src.views.components.toast.ToastManager.error') as mock_show_toast:
        exc = Exception('Unexpected error')
        ln_offchain_view_model._handle_error(exc)
        mock_show_toast.assert_called_once_with(
            description=ERROR_SOMETHING_WENT_WRONG,
        )


def test_on_success_get_invoice(ln_offchain_view_model):
    """Test successful retrieval of an invoice"""
    with patch('src.views.components.toast.ToastManager.show_toast') as mock_show_toast:
        encoded_invoice = LnInvoiceResponseModel(invoice='encoded_invoice')
        ln_offchain_view_model.invoice_get_event = Mock()
        ln_offchain_view_model.on_success_get_invoice(encoded_invoice)
        ln_offchain_view_model.invoice_get_event.emit.assert_called_once_with(
            'encoded_invoice',
        )
        mock_show_toast.assert_not_called()


def test_on_success_send_asset_failed(ln_offchain_view_model):
    """Test successful send asset with failure status"""
    with patch('src.views.components.toast.ToastManager.error') as mock_show_toast:
        response = CombinedDecodedModel(
            send=KeysendResponseModel(
                payment_hash='dfvfvfvf',
                status=PaymentStatus.FAILED.value,  # Ensure status indicates failure
                payment_secret='dcdcdcvvdf',
            ),
            decode=DecodeInvoiceResponseModel(
                amt_msat=3000000,
                expiry_sec=420,
                timestamp=1691160659,
                asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
                asset_amount=42,
                payment_hash='5ca5d81b482b4015e7b14df7a27fe0a38c226273604ffd3b008b752571811938',
                payment_secret='f9fa239a283a72fa351ec6d0d6fdb16f5e59a64cb10e64add0b57123855ff592',
                payee_pubkey='0343851df9e0e8aff0c10b3498ce723ff4c9b4a855e6c8819adcafbbb3e24ea2af',
                network='Regtest',
            ),
        )
        ln_offchain_view_model._page_navigation.fungibles_asset_page = Mock()
        ln_offchain_view_model.on_success_send_asset(response)
        mock_show_toast.assert_called_once_with(
            description='Unable to send assets, a path to fulfill the required payment could not be found',
        )
        ln_offchain_view_model._page_navigation.fungibles_asset_page.assert_not_called()


def test_on_success_send_asset_success(ln_offchain_view_model):
    """Test successful send asset with success status"""
    with patch('src.views.components.toast.ToastManager.success') as mock_show_toast:
        response = CombinedDecodedModel(
            send=KeysendResponseModel(
                payment_hash='dfvfvfvf',
                status=PaymentStatus.SUCCESS.value,  # Ensure status indicates success
                payment_secret='dcdcdcvvdf',
            ),
            decode=DecodeInvoiceResponseModel(
                amt_msat=3000000,
                expiry_sec=420,
                timestamp=1691160659,
                asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
                asset_amount=42,
                payment_hash='5ca5d81b482b4015e7b14df7a27fe0a38c226273604ffd3b008b752571811938',
                payment_secret='f9fa239a283a72fa351ec6d0d6fdb16f5e59a64cb10e64add0b57123855ff592',
                payee_pubkey='0343851df9e0e8aff0c10b3498ce723ff4c9b4a855e6c8819adcafbbb3e24ea2af',
                network='Regtest',
            ),
        )
        ln_offchain_view_model.on_success_send_asset(response)

        mock_show_toast.assert_called_once_with(
            description='Asset sent successfully',
        )


def test_get_invoice(ln_offchain_view_model):
    """Test the get_invoice method"""
    with patch('src.data.repository.invoices_repository.InvoiceRepository.ln_invoice') as mock_ln_invoice:
        with patch('src.viewmodels.ln_offchain_view_model.LnOffChainViewModel.on_success_get_invoice') as mock_success_get_invoice:
            with patch('src.viewmodels.ln_offchain_view_model.LnOffChainViewModel._handle_error') as mock_on_error:
                # Ensure that the mock for ln_invoice returns None, or adjust if necessary
                mock_ln_invoice.return_value = None

                # Call the method under test
                ln_offchain_view_model.get_invoice(
                    amount=1000, expiry=3600, asset_id='asset_id', amount_msat='32000',
                )

                # Verify that the callbacks are not called initially
                mock_success_get_invoice.assert_not_called()
                mock_on_error.assert_not_called()


def test_on_success_of_list(ln_offchain_view_model):
    """Test handling successful retrieval of a list of payments."""
    ln_offchain_view_model.is_loading = MagicMock()
    ln_offchain_view_model.payment_list_event = MagicMock()
    mock_payments = ListPaymentResponseModel()  # Create a mock response model

    ln_offchain_view_model.on_success_of_list(mock_payments)

    # Assert that loading is set to false
    ln_offchain_view_model.is_loading.emit.assert_called_once_with(False)

    # Assert that the payment list event is emitted with the correct payments
    ln_offchain_view_model.payment_list_event.emit.assert_called_once_with(
        mock_payments,
    )


def test_on_success_decode_invoice(ln_offchain_view_model):
    """Test handling successful decoding of an invoice."""
    ln_offchain_view_model.is_invoice_valid = MagicMock()
    ln_offchain_view_model.invoice_detail = MagicMock()
    decoded_invoice = DecodeInvoiceResponseModel(
        amt_msat=3000000,
        expiry_sec=420,
        timestamp=1691160659,
        asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
        asset_amount=42,
        payment_hash='5ca5d81b482b4015e7b14df7a27fe0a38c226273604ffd3b008b752571811938',
        payment_secret='f9fa239a283a72fa351ec6d0d6fdb16f5e59a64cb10e64add0b57123855ff592',
        payee_pubkey='0343851df9e0e8aff0c10b3498ce723ff4c9b4a855e6c8819adcafbbb3e24ea2af',
        network='Regtest',
    )

    ln_offchain_view_model.on_success_decode_invoice(decoded_invoice)

    # Assert that invoice validity is set to true
    ln_offchain_view_model.is_invoice_valid.emit.assert_called_once_with(True)

    # Assert that the invoice detail event is emitted with the correct invoice
    ln_offchain_view_model.invoice_detail.emit.assert_called_once_with(
        decoded_invoice,
    )


def test_send_asset_offchain_loading(ln_offchain_view_model, mocker):
    """Test that loading is set to true when sending an asset offchain."""
    ln_offchain_view_model.is_loading = MagicMock()
    mocker.patch(
        'src.viewmodels.ln_offchain_view_model.LnOffChainViewModel.run_in_thread',
    )
    ln_invoice = 'lnbc1234567890'  # Example invoice
    ln_offchain_view_model.send_asset_offchain(ln_invoice)

    # Assert that loading is set to true
    ln_offchain_view_model.is_loading.emit.assert_called_once_with(True)


def test_list_ln_payment_loading(ln_offchain_view_model, mocker):
    """Test that loading is set to true when listing LN payments and verify all interactions."""
    # Mock all dependencies
    ln_offchain_view_model.is_loading = MagicMock()
    ln_offchain_view_model.run_in_thread = MagicMock()
    ln_offchain_view_model.on_success_of_list = MagicMock()
    ln_offchain_view_model._handle_error = MagicMock()
    mocker.patch('src.viewmodels.ln_offchain_view_model.PaymentRepository')

    ln_offchain_view_model.list_ln_payment()

    # Assert that loading is set to true
    ln_offchain_view_model.is_loading.emit.assert_called_once_with(True)
