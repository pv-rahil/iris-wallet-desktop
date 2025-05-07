"""Unit test for issue RGB20 view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.model.rgb_model import Balance
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.issue_rgb20_view_model import IssueRGB20ViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def issue_rgb20_view_model(mock_page_navigation):
    """Fixture to create an instance of the IssueRGB20ViewModel class."""
    return IssueRGB20ViewModel(mock_page_navigation)


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.repository.rgb_repository.RgbRepository.issue_asset_nia')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_on_issue_click_success(
    mock_run_in_thread, mock_issue_asset_nia, mock_toast_error,
    issue_rgb20_view_model, mock_page_navigation,
):
    """Test for successful issuing of RGB20 asset."""
    # Mock the asset issuance response
    mock_issue_asset_nia.return_value = IssueAssetResponseModel(
        asset_id='asset_id',
        asset_iface='interface',
        ticker='ticker',
        name='name',
        details='details',
        precision=2,
        issued_supply=4000,
        timestamp=123456789,
        added_at=123456789,
        balance=Balance(
            spendable=10, future=10, settled=12,
        ),
    )

    # Mock signals
    mock_issue_button_clicked = Mock()
    issue_rgb20_view_model.issue_button_clicked.connect(
        mock_issue_button_clicked,
    )

    # Mock worker
    mock_worker = MagicMock()
    issue_rgb20_view_model.worker = mock_worker
    mock_worker.result.emit = Mock()

    # Perform the action
    issue_rgb20_view_model.on_issue_click(
        'short_identifier', 'asset_name', '100',
    )

    # Simulate the successful callback from the worker
    mock_worker.result.emit(mock_issue_asset_nia.return_value)

    # Assertions
    mock_issue_button_clicked.assert_called_once()
    mock_toast_error.assert_not_called()


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.repository.rgb_repository.RgbRepository.issue_asset_nia')
@patch('src.data.repository.setting_repository.SettingRepository.native_authentication')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_on_success_native_auth(
    mock_run_in_thread, mock_native_authentication, mock_issue_asset_nia,
    mock_toast_error, issue_rgb20_view_model, mock_page_navigation,
):
    """Test for successful native authentication and asset issuance."""
    # Mock native authentication and asset issuance
    mock_native_authentication.return_value = True
    mock_issue_asset_nia.return_value = IssueAssetResponseModel(
        asset_id='asset_id',
        asset_iface='interface',
        ticker='ticker',
        name='name',
        details='details',
        precision=2,
        issued_supply=1000,
        timestamp=123556789,
        added_at=123456789,
        balance=Balance(
            spendable=10, future=10, settled=12,
        ),
    )

    # Connect signals to mocks
    mock_issue_button_clicked = MagicMock()
    issue_rgb20_view_model.issue_button_clicked.connect(
        mock_issue_button_clicked,
    )
    mock_is_issued = MagicMock()
    issue_rgb20_view_model.is_issued.connect(mock_is_issued)

    # Set test data
    issue_rgb20_view_model.token_amount = '100'
    issue_rgb20_view_model.asset_name = 'asset_name'
    issue_rgb20_view_model.short_identifier = 'short_identifier'

    # Simulate success callback for native authentication
    issue_rgb20_view_model.on_success_native_auth_rgb20(success=True)

    # Simulate worker behavior
    mock_worker = MagicMock()
    issue_rgb20_view_model.worker = mock_worker

    mock_worker.result.emit(mock_issue_asset_nia.return_value)
    mock_toast_error.assert_not_called()


def test_on_success_native_auth_generic_exception(
    issue_rgb20_view_model,
):
    """Test for handling generic Exception in on_success_native_auth."""
    # Setup
    with patch('src.views.components.toast.ToastManager.error') as mock_show_toast:

        # Trigger the exception
        issue_rgb20_view_model.on_success_native_auth_rgb20(success=False)

        # Verify the call to show_toast
        mock_show_toast.assert_called_once_with(
            description='Authentication failed',
        )


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_rgb20_missing_value(mock_toast_manager, issue_rgb20_view_model):
    """Test on_success_native_auth_rgb25 when an unexpected exception occurs"""

    # Set all required attributes
    # This will cause an exception when converting to int
    issue_rgb20_view_model.amount = ''
    issue_rgb20_view_model.asset_name = 'Test Asset'
    issue_rgb20_view_model.asset_ticker = 'TEST'

    issue_rgb20_view_model.on_success_native_auth_rgb20(True)

    mock_toast_manager.assert_called_once_with(
        description='Few fields missing',
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_rgb20_exception(mock_toast_manager, issue_rgb20_view_model):
    """Test on_success_native_auth_rgb25 when an unexpected exception occurs"""
    issue_rgb20_view_model.issue_button_clicked = MagicMock()

    # Set required attributes
    issue_rgb20_view_model.token_amount = '100'
    issue_rgb20_view_model.asset_name = 'Test Asset'
    issue_rgb20_view_model.short_identifier = 'TEST'

    # Mock run_in_thread to raise an exception
    def mock_run_in_thread(*args, **kwargs):
        raise RuntimeError('Test exception')

    # Patch run_in_thread method
    with patch.object(issue_rgb20_view_model, 'run_in_thread', side_effect=mock_run_in_thread):
        issue_rgb20_view_model.on_success_native_auth_rgb20(True)

    mock_toast_manager.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    issue_rgb20_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error_native_auth_rgb20_common_exception(mock_toast_manager, issue_rgb20_view_model):
    """Test on_error_native_auth_rgb20 with CommonException"""
    issue_rgb20_view_model.issue_button_clicked = MagicMock()
    test_message = 'Test error message'
    test_error = CommonException(message=test_message)

    issue_rgb20_view_model.on_error_native_auth_rgb20(test_error)

    mock_toast_manager.assert_called_once_with(description=test_message)
    issue_rgb20_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error_native_auth_rgb20_generic_exception(mock_toast_manager, issue_rgb20_view_model):
    """Test on_error_native_auth_rgb20 with generic Exception"""
    issue_rgb20_view_model.issue_button_clicked = MagicMock()
    test_error = Exception('Test error')

    issue_rgb20_view_model.on_error_native_auth_rgb20(test_error)

    mock_toast_manager.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    issue_rgb20_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error(mock_toast_manager, issue_rgb20_view_model):
    """Test on_error method for RGB20 issue page"""
    # Setup
    issue_rgb20_view_model.issue_button_clicked = MagicMock()
    test_message = 'Test error message'
    test_error = MagicMock()
    test_error.message = test_message

    # Execute
    issue_rgb20_view_model.on_error(test_error)

    # Assert
    mock_toast_manager.assert_called_once_with(description=test_message)
    issue_rgb20_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )
