"""Unit tests for the configuration functionality of the SettingViewModel.

This test module focuses on the configurable settings cards in the SettingViewModel, including:
- Fee rate configuration
- Lightning invoice expiry time configuration
- Minimum confirmation configuration
- Proxy endpoint configuration
- Indexer URL configuration
- Bitcoin RPC host/port configuration
- Lightning node announcement settings

The tests are separated from the main SettingViewModel tests due to the large number
of test cases and to maintain better organization.
"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from rgb_lib import RgbLibError
from rgb_lib import TransportType

from src.model.setting_model import IsDefaultEndpointSet
from src.model.setting_model import IsDefaultFeeRateSet
from src.model.setting_model import IsDefaultMinConfirmationSet
from src.utils.constant import FEE_RATE
from src.utils.constant import MIN_CONFIRMATION
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.error_message import ERROR_UNABLE_TO_SET_FEE
from src.utils.error_message import ERROR_UNABLE_TO_SET_MIN_CONFIRMATION
from src.utils.info_message import INFO_SET_MIN_CONFIRMATION_SUCCESSFULLY
from src.viewmodels.setting_view_model import SettingViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def setting_view_model(mock_page_navigation):
    """Fixture to create an instance of the SettingViewModel class."""
    return SettingViewModel(mock_page_navigation)


@patch('src.viewmodels.setting_view_model.SettingCardRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_set_default_fee_rate_true(mock_toast_manager, mock_setting_card_repository, setting_view_model):
    """Test the set_default_fee_rate method when success fully set."""
    mock_setting_card_repository.set_default_fee_rate.return_value = IsDefaultFeeRateSet(
        is_enabled=True,
    )

    # Connect the signal to a mock slot
    fee_rate_set_event_slot = Mock()
    setting_view_model.fee_rate_set_event.connect(fee_rate_set_event_slot)

    setting_view_model.set_default_fee_rate('0.5')

    mock_setting_card_repository.set_default_fee_rate.assert_called_once_with(
        '0.5',
    )
    fee_rate_set_event_slot.assert_called_once_with('0.5')

    # Test exception handling
    mock_setting_card_repository.set_default_fee_rate.side_effect = CommonException(
        'Error',
    )
    setting_view_model.set_default_fee_rate('0.5')
    fee_rate_set_event_slot.assert_called_with(str(FEE_RATE))
    mock_toast_manager.error.assert_called_with(
        description='Error',
    )

    mock_setting_card_repository.set_default_fee_rate.side_effect = Exception
    setting_view_model.set_default_fee_rate('0.5')
    fee_rate_set_event_slot.assert_called_with(str(FEE_RATE))
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingCardRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_set_default_fee_rate_false(mock_toast_manager, mock_setting_card_repository, setting_view_model):
    """Test the set_default_fee_rate method when not set."""
    mock_setting_card_repository.set_default_fee_rate.return_value = IsDefaultFeeRateSet(
        is_enabled=False,
    )

    # Connect the signal to a mock slot
    fee_rate_set_event_slot = Mock()
    setting_view_model.fee_rate_set_event.connect(fee_rate_set_event_slot)

    setting_view_model.set_default_fee_rate('0.5')

    mock_setting_card_repository.set_default_fee_rate.assert_called_once_with(
        '0.5',
    )
    fee_rate_set_event_slot.assert_called_once_with(str(FEE_RATE))

    mock_toast_manager.error.assert_called_with(
        description=ERROR_UNABLE_TO_SET_FEE,
    )


@patch('src.viewmodels.setting_view_model.SettingCardRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_set_min_confirmation_success(mock_toast_manager, mock_setting_card_repository, setting_view_model):
    """Test set_min_confirmation method success case."""
    setting_view_model.min_confirmation_set_event = Mock()
    setting_view_model.on_page_load = Mock()
    mock_setting_card_repository.set_default_min_confirmation.return_value = IsDefaultMinConfirmationSet(
        is_enabled=True,
    )

    setting_view_model.set_min_confirmation(6)

    mock_setting_card_repository.set_default_min_confirmation.assert_called_once_with(
        6,
    )
    mock_toast_manager.success.assert_called_once_with(
        description=INFO_SET_MIN_CONFIRMATION_SUCCESSFULLY,
    )
    setting_view_model.min_confirmation_set_event.emit.assert_called_once_with(
        6,
    )
    setting_view_model.on_page_load.assert_called_once()

    # Test CommonException handling
    mock_setting_card_repository.set_default_min_confirmation.side_effect = CommonException(
        'Error',
    )
    setting_view_model.set_min_confirmation(6)
    setting_view_model.min_confirmation_set_event.emit.assert_called_with(
        MIN_CONFIRMATION,
    )
    mock_toast_manager.error.assert_called_with(description='Error')

    # Test generic Exception handling
    mock_setting_card_repository.set_default_min_confirmation.side_effect = Exception()
    setting_view_model.set_min_confirmation(6)
    setting_view_model.min_confirmation_set_event.emit.assert_called_with(
        MIN_CONFIRMATION,
    )
    mock_toast_manager.error.assert_called_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )


@patch('src.viewmodels.setting_view_model.SettingCardRepository')
@patch('src.viewmodels.setting_view_model.ToastManager')
def test_set_min_confirmation_failure(mock_toast_manager, mock_setting_card_repository, setting_view_model):
    """Test set_min_confirmation method failure case."""
    setting_view_model.min_confirmation_set_event = Mock()
    mock_setting_card_repository.set_default_min_confirmation.return_value = IsDefaultMinConfirmationSet(
        is_enabled=False,
    )

    setting_view_model.set_min_confirmation(6)

    setting_view_model.min_confirmation_set_event.emit.assert_called_once_with(
        MIN_CONFIRMATION,
    )
    mock_toast_manager.error.assert_called_once_with(
        description=ERROR_UNABLE_TO_SET_MIN_CONFIRMATION,
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.SettingCardRepository.set_default_endpoints')
@patch('src.viewmodels.setting_view_model.colored_wallet.go_online_again')
def test_check_indexer_url_endpoint_success(mock_go_online, mock_set_endpoints, mock_toast, setting_view_model):
    """Test successful indexer URL endpoint check."""
    mock_signal = MagicMock()
    setting_view_model.is_loading = MagicMock()
    setting_view_model.indexer_url_set_event = mock_signal
    mock_set_endpoints.return_value = IsDefaultEndpointSet(is_enabled=True)

    setting_view_model.check_indexer_url_endpoint(' http://localhost:3000 ')

    mock_go_online.assert_called_once_with(indexer_url='http://localhost:3000')
    mock_set_endpoints.assert_called_once()
    mock_signal.emit.assert_called_once_with('http://localhost:3000')
    setting_view_model.is_loading.emit.assert_any_call(True)
    setting_view_model.is_loading.emit.assert_any_call(False)
    mock_toast.success.assert_called_once()


@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.colored_wallet.go_online_again', side_effect=RgbLibError.InvalidIndexer('The indexer endpoint is invalid'))
def test_check_indexer_url_endpoint_failure(mock_go_online, mock_toast, setting_view_model):
    """Test indexer URL endpoint check failure."""
    setting_view_model.is_loading = MagicMock()

    setting_view_model.check_indexer_url_endpoint('http://bad-url')

    setting_view_model.is_loading.emit.assert_any_call(True)
    setting_view_model.is_loading.emit.assert_any_call(False)
    mock_toast.error.assert_called_once_with(
        description='The indexer endpoint is invalid',
    )


@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.SettingCardRepository.set_default_endpoints')
@patch('src.viewmodels.setting_view_model.TransportEndpoint')
def test_check_proxy_endpoint_success(mock_transport, mock_set_endpoints, mock_toast, setting_view_model):
    """Test successful proxy endpoint check."""
    mock_endpoint_instance = MagicMock()
    mock_endpoint_instance.transport_type.return_value = TransportType.JSON_RPC
    mock_transport.return_value = mock_endpoint_instance
    mock_set_endpoints.return_value = IsDefaultEndpointSet(is_enabled=True)

    setting_view_model.is_loading = MagicMock()
    setting_view_model.proxy_endpoint_set_event = MagicMock()

    setting_view_model.check_proxy_endpoint(' http://proxy.local ')

    mock_transport.assert_called_once_with('http://proxy.local')
    mock_set_endpoints.assert_called_once()
    setting_view_model.proxy_endpoint_set_event.emit.assert_called_once_with(
        'http://proxy.local',
    )
    setting_view_model.is_loading.emit.assert_any_call(True)
    setting_view_model.is_loading.emit.assert_any_call(False)
    mock_toast.success.assert_called_once()


@patch('src.viewmodels.setting_view_model.ToastManager')
@patch('src.viewmodels.setting_view_model.TransportEndpoint', side_effect=ValueError('Invalid transport'))
def test_check_proxy_endpoint_failure(mock_transport, mock_toast, setting_view_model):
    """Test proxy endpoint check failure."""
    setting_view_model.is_loading = MagicMock()

    setting_view_model.check_proxy_endpoint('http://bad-proxy')

    setting_view_model.is_loading.emit.assert_any_call(True)
    setting_view_model.is_loading.emit.assert_any_call(False)
    mock_toast.error.assert_called_once_with(description='Invalid transport')
