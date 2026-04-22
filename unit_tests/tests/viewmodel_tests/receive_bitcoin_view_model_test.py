"""Unit test for issue receive bitcoin view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.btc_model import AddressResponseModel
from src.utils.custom_exception import CommonException
from src.viewmodels.receive_bitcoin_view_model import ReceiveBitcoinViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def receive_bitcoin_view_model(mock_page_navigation):
    """Fixture to create an instance of the ReceiveBitcoinViewModel class."""
    return ReceiveBitcoinViewModel(mock_page_navigation)


@patch('src.data.repository.btc_repository.BtcRepository.get_address')
def test_get_bitcoin_address_success(mock_get_address, receive_bitcoin_view_model, qtbot):
    """Test for successfully retrieving a bitcoin address."""
    mock_address_signal = Mock()
    receive_bitcoin_view_model.address.connect(mock_address_signal)
    mock_address_response = AddressResponseModel(
        address='bcrt1pwg4nq0umz800wjgda87ed399k4yy8cvmm2zy0826hscq95gqs7hslurlja',
    )
    mock_get_address.return_value = mock_address_response
    receive_bitcoin_view_model.get_bitcoin_address()

    # Keep reference to worker to prevent garbage collection
    worker = receive_bitcoin_view_model.worker
    assert worker is not None, 'Worker should be created'

    # Manually emit result to test signal connection
    worker.result.emit(mock_address_response)

    # Process events to ensure signal is delivered
    qtbot.wait(100)

    mock_address_signal.assert_called_once_with(mock_address_response.address)


@patch('src.data.repository.btc_repository.BtcRepository.get_address')
def test_get_bitcoin_address_error(mock_get_address, receive_bitcoin_view_model, qtbot):
    """Test for getting error while retrieving a bitcoin address."""
    mock_error_signal = Mock()
    mock_loading_signal = Mock()
    receive_bitcoin_view_model.error.connect(mock_error_signal)
    receive_bitcoin_view_model.is_loading.connect(mock_loading_signal)
    mock_address_exception = CommonException('Error while getting address')
    mock_get_address.side_effect = mock_address_exception
    receive_bitcoin_view_model.get_bitcoin_address()

    # Keep reference to worker to prevent garbage collection
    worker = receive_bitcoin_view_model.worker
    assert worker is not None, 'Worker should be created'

    worker.error.emit(mock_address_exception)
    qtbot.wait(100)

    mock_error_signal.assert_called_once_with(mock_address_exception.message)
    mock_loading_signal.assert_called()


@patch('src.data.repository.btc_repository.BtcRepository.get_address')
def test_get_bitcoin_address_with_hard_refresh(mock_get_address, receive_bitcoin_view_model, qtbot):
    """Test for successfully retrieving a bitcoin address with hard refresh."""
    mock_address_signal = Mock()
    receive_bitcoin_view_model.address.connect(mock_address_signal)
    mock_address_response = AddressResponseModel(
        address='bcrt1pwg4nq0umz800wjgda87ed399k4yy8cvmm2zy0826hscq95gqs7hslurlja',
    )
    mock_get_address.return_value = mock_address_response
    receive_bitcoin_view_model.get_bitcoin_address(is_hard_refresh=True)

    # Keep reference to worker to prevent garbage collection
    worker = receive_bitcoin_view_model.worker
    assert worker is not None, 'Worker should be created'

    worker.result.emit(mock_address_response)
    qtbot.wait(100)

    mock_address_signal.assert_called_once_with(mock_address_response.address)
