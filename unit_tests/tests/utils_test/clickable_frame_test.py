# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for clickable frame."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame

from src.utils.clickable_frame import ClickableFrame


@pytest.fixture
def clickable_frame():
    """Create a ClickableFrame instance for testing."""
    return ClickableFrame(
        _id='test_id',
        _name='test_name',
        image_path='test/path.png',
        asset_type='test_type',
    )


def test_initialization(clickable_frame):
    """Test ClickableFrame initialization."""
    assert isinstance(clickable_frame, QFrame)
    assert clickable_frame._id == 'test_id'
    assert clickable_frame._name == 'test_name'
    assert clickable_frame._image_path == 'test/path.png'
    assert clickable_frame._asset_type == 'test_type'
    assert clickable_frame.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_mouse_press_event(clickable_frame):
    """Test mouse press event handling."""
    # Create mock signal handler
    mock_handler = MagicMock()
    clickable_frame.clicked.connect(mock_handler)

    # Create mock mouse event using non-deprecated constructor
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(clickable_frame.pos()),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    # Trigger mouse press event
    clickable_frame.mousePressEvent(event)

    # Verify signal was emitted with correct arguments
    mock_handler.assert_called_once_with(
        'test_id',
        'test_name',
        'test/path.png',
        'test_type',
    )


def test_clickable_frame_without_optional_params():
    """Test ClickableFrame initialization with default values."""
    frame = ClickableFrame()
    assert frame._id is None
    assert frame._name is None
    assert frame._image_path is None
    assert frame._asset_type is None
    assert frame.cursor().shape() == Qt.CursorShape.PointingHandCursor
