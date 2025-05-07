"""Unit test for bitcoin transaction ui"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QTextDocument

from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.transaction_detail_page_model import TransactionDetailPageModel
from src.utils.common_utils import network_info
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.helpers import load_stylesheet
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_bitcoin_transaction import BitcoinTransactionDetail


@pytest.fixture
def mock_bitcoin_transaction_detail_view_model():
    """Fixture to create a MainViewModel instance."""
    return MainViewModel(MagicMock())


@pytest.fixture
def bitcoin_transaction_detail_widget(mock_bitcoin_transaction_detail_view_model, qtbot):
    """Fixture to initialize the BitcoinTransactionDetail widget."""

    # Create a mock for TransactionDetailPageModel with required attributes
    params = MagicMock(spec=TransactionDetailPageModel)
    params.tx_id = 'abcd1234'
    params.amount = '0.1 BTC'
    params.asset_id = 'asset_123'
    params.image_path = None
    params.asset_name = 'Bitcoin'
    params.confirmation_date = '2024-08-30'
    params.confirmation_time = '10:30 AM'
    params.transaction_status = TransferStatusEnumModel.SENT
    params.transfer_status = TransferStatusEnumModel.SENT
    params.consignment_endpoints = []
    params.recipient_id = 'recipient_123'
    params.receive_utxo = 'utxo_123'
    params.change_utxo = 'utxo_456'
    params.asset_type = 'crypto'

    widget = BitcoinTransactionDetail(
        mock_bitcoin_transaction_detail_view_model, params,
    )
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(bitcoin_transaction_detail_widget, qtbot):
    """Test the retranslate_ui method."""
    # Set up initial state
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network') as mock_network:
        mock_network.return_value = NetworkEnumModel.MAINNET
        bitcoin_transaction_detail_widget.network = 'mainnet'
        bitcoin_transaction_detail_widget.tx_id = 'test_tx_id'
        bitcoin_transaction_detail_widget.params.tx_id = 'test_tx_id'
        bitcoin_transaction_detail_widget.retranslate_ui()

        # Test bitcoin_text construction
        expected_bitcoin_text = f'{
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, "bitcoin", None
            )
        } (mainnet)'
        assert bitcoin_transaction_detail_widget.bitcoin_text == expected_bitcoin_text

        # Test URL construction
        assert bitcoin_transaction_detail_widget.url == 'https://mempool.space/tx/test_tx_id'

        # Test all label texts
        assert bitcoin_transaction_detail_widget.tx_id_label.text(
        ) == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id', None)
        assert bitcoin_transaction_detail_widget.btc_amount_label.text(
        ) == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount', None)
        assert bitcoin_transaction_detail_widget.date_label.text(
        ) == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'date', None)
        assert bitcoin_transaction_detail_widget.bitcoin_title_value.text() == expected_bitcoin_text

        # Test tx_id_value text for mainnet
        expected_tx_link = f"<a style='color: #03CA9B;' href='{bitcoin_transaction_detail_widget.url}'>" \
            f"{bitcoin_transaction_detail_widget.tx_id}</a>"
        assert bitcoin_transaction_detail_widget.bitcoin_tx_id_value.text() == expected_tx_link

        # Test for REGTEST network
        mock_network.return_value = NetworkEnumModel.REGTEST
        bitcoin_transaction_detail_widget.retranslate_ui()
        assert bitcoin_transaction_detail_widget.bitcoin_tx_id_value.text(
        ) == bitcoin_transaction_detail_widget.tx_id


def test_set_btc_tx_value_sent_status(bitcoin_transaction_detail_widget, qtbot):
    """Test the set_btc_tx_value method when the transfer status is SENT."""
    bitcoin_transaction_detail_widget.params.transfer_status = TransferStatusEnumModel.SENT
    bitcoin_transaction_detail_widget.params.amount = '0.1 BTC'
    bitcoin_transaction_detail_widget.params.tx_id = 'abcd1234'
    bitcoin_transaction_detail_widget.params.confirmation_date = '2024-08-30'
    bitcoin_transaction_detail_widget.params.confirmation_time = '10:30 AM'
    bitcoin_transaction_detail_widget.params.transaction_status = 'Confirmed'

    # Call the method to update the UI
    bitcoin_transaction_detail_widget.set_btc_tx_value()

    # Test the amount value text
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.text() == '0.1 BTC'

    # Check if the stylesheet has been applied for SENT status
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.styleSheet(
    ) == load_stylesheet('views/qss/q_label.qss')

    # Test the tx_id value (make sure it matches)
    html_content = bitcoin_transaction_detail_widget.bitcoin_tx_id_value.text()
    doc = QTextDocument()
    doc.setHtml(html_content)
    bitcoin_tx_id_value = doc.toPlainText()
    assert bitcoin_tx_id_value == 'abcd1234'

    # Test the date value for SENT status
    assert bitcoin_transaction_detail_widget.date_value.text() == '2024-08-30 | 10:30 AM'


def test_set_btc_tx_value_ongoing_transfer_status(bitcoin_transaction_detail_widget, qtbot):
    """Test the set_btc_tx_value method when the transfer status is ON_GOING_TRANSFER."""
    bitcoin_transaction_detail_widget.params.transfer_status = TransferStatusEnumModel.ON_GOING_TRANSFER
    bitcoin_transaction_detail_widget.params.amount = '0.2 BTC'
    bitcoin_transaction_detail_widget.params.tx_id = 'abcd1234'
    bitcoin_transaction_detail_widget.params.confirmation_date = None
    bitcoin_transaction_detail_widget.params.confirmation_time = None
    bitcoin_transaction_detail_widget.params.transaction_status = 'Pending'

    # Call the method to update the UI
    bitcoin_transaction_detail_widget.set_btc_tx_value()

    # Test the amount value text
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.text() == '0.2 BTC'

    # Check if the specific stylesheet for ON_GOING_TRANSFER has been applied
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.styleSheet() == """QLabel#amount_value{
                font: 24px "Inter";
                color: #959BAE;
                background: transparent;
                border: none;
                font-weight: 600;
                }"""

    # Test the tx_id value (ensure it's correct)
    html_content = bitcoin_transaction_detail_widget.bitcoin_tx_id_value.text()
    doc = QTextDocument()
    doc.setHtml(html_content)
    bitcoin_tx_id_value = doc.toPlainText()
    assert bitcoin_tx_id_value == 'abcd1234'

    # Check if the status text appears in the date value
    assert bitcoin_transaction_detail_widget.date_label.text(
    ) == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'status', None)
    assert bitcoin_transaction_detail_widget.date_value.text() == 'Pending'


def test_set_btc_tx_value_internal_status(bitcoin_transaction_detail_widget, qtbot):
    """Test the set_btc_tx_value method when the transfer status is INTERNAL."""
    bitcoin_transaction_detail_widget.params.transfer_status = TransferStatusEnumModel.INTERNAL
    bitcoin_transaction_detail_widget.params.amount = '0.3 BTC'
    bitcoin_transaction_detail_widget.params.tx_id = 'abcd1234'
    bitcoin_transaction_detail_widget.params.confirmation_date = '2024-09-01'
    bitcoin_transaction_detail_widget.params.confirmation_time = '12:00 PM'
    bitcoin_transaction_detail_widget.params.transaction_status = 'Confirmed'

    # Call the method to update the UI
    bitcoin_transaction_detail_widget.set_btc_tx_value()

    # Test the amount value text
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.text() == '0.3 BTC'

    # Test if the SENT style has been applied
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.styleSheet(
    ) == load_stylesheet('views/qss/q_label.qss')

    # Test the tx_id value (make sure it matches)
    html_content = bitcoin_transaction_detail_widget.bitcoin_tx_id_value.text()
    doc = QTextDocument()
    doc.setHtml(html_content)
    bitcoin_tx_id_value = doc.toPlainText()
    assert bitcoin_tx_id_value == 'abcd1234'

    # Test the date value for INTERNAL status
    assert bitcoin_transaction_detail_widget.date_value.text() == '2024-09-01 | 12:00 PM'


def test_set_btc_tx_value_missing_confirmation(bitcoin_transaction_detail_widget, qtbot):
    """Test the set_btc_tx_value method when confirmation date/time is missing."""
    bitcoin_transaction_detail_widget.params.transfer_status = TransferStatusEnumModel.SENT
    bitcoin_transaction_detail_widget.params.amount = '0.4 BTC'
    bitcoin_transaction_detail_widget.params.tx_id = 'mnop3456'
    bitcoin_transaction_detail_widget.params.confirmation_date = None
    bitcoin_transaction_detail_widget.params.confirmation_time = None
    bitcoin_transaction_detail_widget.params.transaction_status = 'Unconfirmed'

    # Call the method to update the UI
    bitcoin_transaction_detail_widget.set_btc_tx_value()

    # Test the amount value text
    assert bitcoin_transaction_detail_widget.bitcoin_amount_value.text() == '0.4 BTC'

    # Ensure that the date label and value reflect 'Unconfirmed'
    assert bitcoin_transaction_detail_widget.date_label.text(
    ) == QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'status', None)
    assert bitcoin_transaction_detail_widget.date_value.text() == 'Unconfirmed'


def test_handle_close(bitcoin_transaction_detail_widget, qtbot):
    """Test the handle_close method."""
    bitcoin_transaction_detail_widget.handle_close()

    assert bitcoin_transaction_detail_widget._view_model.page_navigation.bitcoin_page.called


def test_network_info_success(bitcoin_transaction_detail_widget, mocker):
    """Test the network_info method with successful network retrieval."""
    mock_network = mocker.patch(
        'src.data.repository.setting_repository.SettingRepository.get_wallet_network',
    )
    mock_network.return_value.value = 'mainnet'
    network_info(bitcoin_transaction_detail_widget)
    assert bitcoin_transaction_detail_widget.network == 'mainnet'


def test_network_info_common_exception(bitcoin_transaction_detail_widget, qtbot):
    """Test the network_info method when a CommonException is raised."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', side_effect=CommonException('Test error')), \
            patch('src.views.components.toast.ToastManager.error') as mock_toast, \
            patch('src.utils.logging.logger.error') as mock_logger:

        network_info(bitcoin_transaction_detail_widget)
        mock_logger.assert_called_once()
        mock_toast.assert_called_once_with(
            parent=None, title=None, description='',
        )


def test_network_info_general_exception(bitcoin_transaction_detail_widget, qtbot):
    """Test the network_info method when a general Exception is raised."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_network', side_effect=Exception('Test exception')), \
            patch('src.views.components.toast.ToastManager.error') as mock_toast, \
            patch('src.utils.logging.logger.error') as mock_logger:

        network_info(bitcoin_transaction_detail_widget)

        mock_logger.assert_called_once()
        mock_toast.assert_called_once_with(
            parent=None, title=None, description=ERROR_SOMETHING_WENT_WRONG,
        )
