"""Unit test for toast component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.model.enums.enums_model import ToastPreset
from src.views.components.toast import ToastManager


@pytest.fixture(scope='session', autouse=True)
def toast_app():
    """Ensure QApplication is initialized."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def mock_toaster_ui():
    """Mock the ToasterUi class globally."""
    with patch('src.views.components.toast.ToasterUi', autospec=True) as mock:
        yield mock


def test_create_toast_with_parent(mock_toaster_ui):
    """Test _create_toast with a parent widget."""
    description = 'Test Description'
    preset = ToastPreset.SUCCESS
    parent = MagicMock()

    ToastManager._create_toast(description, preset, parent=parent)

    # Verify ToasterUi was called correctly
    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=preset,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_create_toast_without_parent(mock_toaster_ui):
    """Test _create_toast without a parent widget."""
    description = 'Test Description'
    preset = ToastPreset.ERROR

    ToastManager._create_toast(description, preset)

    # Verify ToasterUi was called correctly
    mock_toaster_ui.assert_called_once_with(description=description)
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=preset,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_success_toast(mock_toaster_ui):
    """Test success toast creation with and without a parent."""
    description = 'Success!'

    # Case 1: Toast without a parent (kwargs['parent'] is None)
    ToastManager.success(description, parent=None)

    # Ensure 'parent' was excluded from the initialization call
    mock_toaster_ui.assert_called_once_with(description=description)
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.SUCCESS,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()

    # Reset the mock for the next case
    mock_toaster_ui.reset_mock()

    # Case 2: Toast with a parent
    parent = MagicMock()
    ToastManager.success(description, parent=parent)

    # Ensure 'parent' was included in the initialization call
    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.SUCCESS,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_error_toast(mock_toaster_ui):
    """Test error toast creation."""
    description = 'Error!'

    ToastManager.error(description)

    mock_toaster_ui.assert_called_once_with(description=description)
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.ERROR,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_warning_toast(mock_toaster_ui):
    """Test warning toast creation."""
    description = 'Warning!'

    ToastManager.warning(description)

    mock_toaster_ui.assert_called_once_with(description=description)
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.WARNING,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_info_toast(mock_toaster_ui):
    """Test info toast creation."""
    description = 'Info!'

    ToastManager.info(description)

    mock_toaster_ui.assert_called_once_with(description=description)
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.INFORMATION,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_show_toast_success(mock_toaster_ui):
    """Test show_toast with SUCCESS preset."""
    description = 'Success Toast'
    parent = MagicMock()

    ToastManager.show_toast(parent, ToastPreset.SUCCESS, description)

    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.SUCCESS,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_show_toast_error(mock_toaster_ui):
    """Test show_toast with ERROR preset."""
    description = 'Error Toast'
    parent = MagicMock()

    ToastManager.show_toast(parent, ToastPreset.ERROR, description)

    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.ERROR,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_show_toast_warning(mock_toaster_ui):
    """Test show_toast with ERROR preset."""
    description = 'Error Toast'
    parent = MagicMock()

    ToastManager.show_toast(parent, ToastPreset.WARNING, description)

    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.WARNING,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_show_toast_information(mock_toaster_ui):
    """Test show_toast with ERROR preset."""
    description = 'Error Toast'
    parent = MagicMock()

    ToastManager.show_toast(parent, ToastPreset.INFORMATION, description)

    mock_toaster_ui.assert_called_once_with(
        parent=parent, description=description,
    )
    mock_toaster_ui.return_value.apply_preset.assert_called_once_with(
        preset=ToastPreset.INFORMATION,
    )
    mock_toaster_ui.return_value.show_toast.assert_called_once()


def test_show_toast_invalid_preset():
    """Test show_toast with an invalid preset."""
    description = 'Invalid Toast'
    parent = MagicMock()

    with pytest.raises(ValueError):
        ToastManager.show_toast(parent, 'INVALID_PRESET', description)
