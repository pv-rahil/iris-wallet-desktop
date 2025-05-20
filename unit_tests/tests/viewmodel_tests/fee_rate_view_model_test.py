"""Unit test for fee rate view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.btc_model import EstimateFeeResponse
from src.utils.common_utils import TRANSACTION_SPEEDS
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_CUSTOM_FEE_RATE
from src.viewmodels.fee_rate_view_model import EstimateFeeViewModel


@pytest.fixture
def fee_rate_view_model():
    """Fixture for creating an instance of EstimateFeeViewModel."""
    return EstimateFeeViewModel()


@pytest.fixture(autouse=True)
def mock_toast_manager(mocker):
    """Mock ToastManager to avoid main window requirement"""
    mocker.patch('src.views.components.toast.ToastManager._create_toast')


def test_on_success_fee_estimation(fee_rate_view_model):
    """Test on_success_fee_estimation method."""
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)
    mock_fee_estimation_success = Mock()
    fee_rate_view_model.fee_estimation_success.connect(
        mock_fee_estimation_success,
    )

    test_fee_rate = 10.5
    response = EstimateFeeResponse(fee_rate=test_fee_rate)

    fee_rate_view_model.on_success_fee_estimation(response)

    mock_loading_status.assert_called_once_with(False, True)
    mock_fee_estimation_success.assert_called_once_with(test_fee_rate)


def test_on_estimate_fee_error(fee_rate_view_model, mocker):
    """Test on_estimate_fee_error method."""
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.info',
    )
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)
    mock_fee_estimation_error = Mock()
    fee_rate_view_model.fee_estimation_error.connect(mock_fee_estimation_error)

    fee_rate_view_model.on_estimate_fee_error()

    mock_loading_status.assert_called_once_with(False, True)
    mock_fee_estimation_error.assert_called_once()
    mock_toast_manager.assert_called_once_with(
        description=INFO_CUSTOM_FEE_RATE.format(ERROR_SOMETHING_WENT_WRONG),
    )


@patch('src.data.repository.btc_repository.BtcRepository.estimate_fee')
def test_get_fee_rate_success(mock_estimate_fee, fee_rate_view_model):
    """Test get_fee_rate successful execution."""
    # Arrange
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)
    mock_fee_rate = 10.5
    mock_estimate_fee.return_value = EstimateFeeResponse(
        fee_rate=mock_fee_rate,
    )

    # Mock run_in_thread to simulate async behavior
    def mock_run_in_thread(func, kwargs):
        kwargs['callback'](EstimateFeeResponse(fee_rate=mock_fee_rate))
    fee_rate_view_model.run_in_thread = mock_run_in_thread

    # Act
    fee_rate_view_model.get_fee_rate('slow_checkBox')

    # Assert
    mock_loading_status.assert_has_calls([call(True, True), call(False, True)])
    assert fee_rate_view_model.blocks == TRANSACTION_SPEEDS['slow_checkBox']


def test_get_fee_rate_invalid_speed(fee_rate_view_model, mocker):
    """Test get_fee_rate with invalid transaction speed."""
    # Arrange
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.info',
    )
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)

    # Act
    fee_rate_view_model.get_fee_rate('invalid_speed')

    # Assert
    mock_toast_manager.assert_called_once_with(
        description='Invalid transaction speed selected.',
    )
    mock_loading_status.assert_not_called()
    assert fee_rate_view_model.blocks == 0


def test_get_fee_rate_connection_error(fee_rate_view_model, mocker):
    """Test get_fee_rate handling of ConnectionError."""
    # Arrange
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)

    # Mock run_in_thread to raise ConnectionError
    def mock_run_in_thread(*args, **kwargs):
        raise ConnectionError()

    with patch.object(fee_rate_view_model, 'run_in_thread', side_effect=mock_run_in_thread):
        # Act
        fee_rate_view_model.get_fee_rate('slow_checkBox')

    # Assert
    mock_loading_status.assert_has_calls([call(True, True), call(False, True)])
    mock_toast_manager.assert_called_once_with(
        description='Network error. Please check your connection.',
    )


def test_get_fee_rate_generic_exception(fee_rate_view_model, mocker):
    """Test get_fee_rate handling of generic Exception."""
    # Arrange
    mock_toast_manager = mocker.patch(
        'src.views.components.toast.ToastManager.error',
    )
    mock_loading_status = Mock()
    fee_rate_view_model.loading_status.connect(mock_loading_status)
    error_message = 'Test error'

    # Mock run_in_thread to raise generic Exception
    def mock_run_in_thread(*args, **kwargs):
        raise RuntimeError(error_message)

    with patch.object(fee_rate_view_model, 'run_in_thread', side_effect=mock_run_in_thread):
        # Act
        fee_rate_view_model.get_fee_rate('slow_checkBox')

    # Assert
    mock_loading_status.assert_has_calls([call(True, True), call(False, True)])
    mock_toast_manager.assert_called_once_with(
        description=f"An unexpected error occurred: {error_message}",
    )
