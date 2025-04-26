"""unit test for is_node_initialized decorator"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.custom_exception import CommonException
from src.utils.decorators.is_node_initialized import is_node_initialized


@patch('src.utils.page_navigation_events.PageNavigationEventManager.get_instance')
@patch('PySide6.QtCore.QCoreApplication.translate')
def test_is_node_initialized(mock_translate, mock_event_manager):
    """Test the is_node_initialized decorator."""

    # Mock the translated error message
    mock_translate.return_value = 'node_is_already_initialized'

    # Mock the signal emission
    mock_signal = MagicMock()
    mock_event_manager.return_value.enter_wallet_password_page_signal = mock_signal

    # Define a mock function to be wrapped
    @is_node_initialized
    def mock_function():
        raise CommonException('node_is_already_initialized')

    # Test when the exception matches the translated message
    with pytest.raises(CommonException, match='node_is_already_initialized'):
        mock_function()

    # Assert that the signal was emitted
    mock_signal.emit.assert_called_once()

    # Test when the exception does not match the translated message
    mock_signal.emit.reset_mock()

    @is_node_initialized
    def mock_function_different_error():
        raise CommonException('some_other_error')

    with pytest.raises(CommonException, match='some_other_error'):
        mock_function_different_error()

    # Assert that the signal was not emitted
    mock_signal.emit.assert_not_called()
