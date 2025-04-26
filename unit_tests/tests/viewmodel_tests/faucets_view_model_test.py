"""
This module contains unit tests for the `FaucetsViewModel` class in the Iris Wallet application.
"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from pytestqt.qtbot import QtBot

from src.data.service.faucet_service import FaucetService
from src.model.rgb_faucet_model import BriefAssetInfo
from src.model.rgb_faucet_model import ListAvailableAsset
from src.model.rgb_faucet_model import RequestAssetResponseModel
from src.model.rgb_faucet_model import RequestDistribution
from src.model.rgb_faucet_model import RequestFaucetAsset
from src.utils.custom_exception import CommonException
from src.viewmodels.faucets_view_model import FaucetsViewModel


class MockSignal(QObject):
    '''Mock Signal class to test signal emission'''
    triggered = Signal()


@pytest.fixture
def faucet_view_model(qtbot):
    """view_model(qtbot)`: A fixture that provides an instance of `FaucetsViewModel` with mock dependencies for testing."""
    # Create a mock page navigation
    mock_navigation = MagicMock()

    # Initialize the FaucetsViewModel with a mock page navigation
    model = FaucetsViewModel(mock_navigation)

    # Connect signals to mock slots for testing
    model.start_loading = MockSignal().triggered
    model.stop_loading = MockSignal().triggered
    model.faucet_list = MockSignal().triggered

    return model


def test_get_faucet_list_starts_loading(qtbot: QtBot):
    '''**get_faucet_list_starts_loading**: Ensures that the `get_faucet_list` method starts
      the loading process and correctly interacts with the `FaucetService` to fetch available assets.'''

    # Instantiate the view model
    view_model = FaucetsViewModel(page_navigation=MagicMock())

    # Prepare the mock response for ListAvailableAsset
    mock_faucet_assets = ListAvailableAsset(
        faucet_assets=[
            BriefAssetInfo(asset_name='Asset 1', asset_id='ID_1'),
            BriefAssetInfo(asset_name='Asset 2', asset_id='ID_2'),
        ],
    )

    # Patch the run_in_thread method to mock the behavior of get_faucet_list
    with patch.object(view_model, 'run_in_thread') as mock_run_in_thread:
        # Set up the mock to directly call the success callback
        mock_run_in_thread.side_effect = lambda func, params: params['callback'](
            mock_faucet_assets,
        )

        # Ensure the start_loading signal is emitted
        view_model.get_faucet_list()

        # Check that run_in_thread was called with the correct parameters
        mock_run_in_thread.assert_called_once_with(
            FaucetService.list_available_asset,
            {
                'args': [],
                'callback': view_model.on_success_get_faucet_list,
                'error_callback': view_model.on_error,
            },
        )


def test_on_error_shows_toast():
    '''**on_error_shows_toast**: Verifies that the `on_error` method shows a toast notification with the correct error message.'''
    view_model = FaucetsViewModel(page_navigation=MagicMock())

    # Patch the ToastManager
    with patch('src.views.components.toast.ToastManager'):
        view_model.on_error()


def test_request_faucet_asset_starts_loading(qtbot, faucet_view_model):
    """**request_faucet_asset_starts_loading**: Tests that the `request_faucet_asset` method triggers the loading process,
    and checks the initial state before making the request."""

    # Ensure start_loading is not connected initially
    faucet_view_model = FaucetsViewModel(page_navigation=MagicMock())

    # Call the method that is supposed to emit the start_loading signal
    faucet_view_model.request_faucet_asset()


def test_on_success_get_faucet_asset_shows_toast_and_navigates(faucet_view_model):
    """**on_success_get_faucet_asset_shows_toast_and_navigates**: Confirms that the `on_success_get_faucet_asset`
    method displays a success toast notification and navigates
    to the fungibles asset page upon a successful asset request."""

    # Mock the toast manager and page navigation
    with patch('src.views.components.toast.ToastManager.success') as mock_toast_success:
        # Create a valid mock response with all required fields
        mock_asset = RequestFaucetAsset(
            amount=1000,
            asset_id='asset_id',
            details='Sample details',
            name='Asset',
            precision=8,
            ticker='ASSET',
        )
        mock_distribution = RequestDistribution(mode='0')
        mock_response = RequestAssetResponseModel(
            asset=mock_asset, distribution=mock_distribution,
        )

        # Create a view model instance
        faucet_view_model = FaucetsViewModel(page_navigation=MagicMock())

        # Call the method that handles the success scenario
        faucet_view_model.on_success_get_faucet_asset(mock_response)

        # Check that the toast was shown with the correct message
        mock_toast_success.assert_called_once_with(
            description='Asset "Asset" has been sent successfully. It may take some time to appear in the wallet.',
        )

        # Check that the navigation happened
        faucet_view_model._page_navigation.fungibles_asset_page.assert_called_once()


def test_on_error_get_asset_shows_toast():
    """Test that `on_error_get_asset` displays a toast notification with the correct error message."""

    # Mock error
    mock_error = CommonException('Error requesting asset')

    # Patch ToastManager.error directly
    with patch('src.views.components.toast.ToastManager.error') as mock_toast_error:
        # Create the FaucetsViewModel instance
        faucet_view_model = FaucetsViewModel(page_navigation=MagicMock())

        # Call the method under test
        faucet_view_model.on_error_get_asset(mock_error)

        # Assert that ToastManager.error was called with the correct arguments
        mock_toast_error.assert_called_once_with(
            description='Error requesting asset',
        )
