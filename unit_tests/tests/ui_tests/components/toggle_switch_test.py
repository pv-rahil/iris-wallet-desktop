"""Unit test for toggle switch component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter

from src.views.components.toggle_switch import ToggleSwitch


@pytest.fixture
def toggle_switch():
    """Fixture to create a ToggleSwitch widget."""
    widget = ToggleSwitch()
    return widget


def test_toggle_switch_initial_state(toggle_switch):
    """Test the initial state of the ToggleSwitch widget."""
    assert toggle_switch.isChecked() is False
    assert toggle_switch.handle_toggle_position == 0
    assert toggle_switch.sizeHint() == QSize(58, 45)


def test_toggle_switch_state_change(toggle_switch):
    """Test that the state changes correctly and handle position updates."""
    # Simulate toggling the switch
    toggle_switch.setChecked(True)
    toggle_switch.handle_state_change(1)

    # Assert the switch is checked and handle position is updated
    assert toggle_switch.isChecked() is True
    assert toggle_switch.handle_toggle_position == 1


def test_toggle_switch_state_change_unchecked(toggle_switch):
    """Test the state change when unchecked and handle position resets."""
    toggle_switch.setChecked(False)
    toggle_switch.handle_state_change(0)

    # Assert the switch is unchecked and handle position is reset
    assert toggle_switch.isChecked() is False
    assert toggle_switch.handle_toggle_position == 0


def test_toggle_switch_set_scale(toggle_switch):
    """Test the scale setters for horizontal and vertical scaling."""
    toggle_switch.setH_scale(1.5)
    toggle_switch.setV_scale(2.0)

    # Ensure the scaling updates
    assert toggle_switch._h_scale == 1.5
    assert toggle_switch._v_scale == 2.0


def test_toggle_switch_font_size(toggle_switch):
    """Test the font size setter."""
    toggle_switch.setFontSize(12)

    # Ensure the font size is updated
    assert toggle_switch._fontSize == 12


def test_toggle_switch_hit_button(toggle_switch):
    """Test if the toggle switch correctly detects a click inside its boundaries."""
    pos = toggle_switch.contentsRect().center(
    )  # Get the center point of the toggle switch
    assert toggle_switch.hitButton(pos) is True

    # Simulate a click outside of the toggle's button area
    outside_pos = QPoint(-1, -1)  # Point outside the button's area
    assert toggle_switch.hitButton(outside_pos) is False


@pytest.fixture
def mock_painter():
    """Fixture to create and return a mocked QPainter."""
    mock_painter = MagicMock(spec=QPainter)
    # Mock the begin and end methods to simulate the painter being active
    mock_painter.begin = MagicMock()
    mock_painter.end = MagicMock()
    return mock_painter


def test_paint_event_checked(toggle_switch):
    """Test the paintEvent when the switch is checked."""
    # Set the switch to checked
    toggle_switch.setChecked(True)

    # Set the geometry for the widget (simulate the widget's dimensions)
    toggle_switch.setGeometry(0, 0, 100, 50)

    # Create a QPainter object for the widget itself
    painter = QPainter(toggle_switch)

    # Begin painting
    painter.begin(toggle_switch)

    # Call the paintEvent method with the real QPainter
    toggle_switch.paintEvent(painter)

    # End painting
    painter.end()


def test_paint_event_unchecked(toggle_switch):
    """Test the paintEvent when the switch is unchecked."""

    # Set the switch to checked
    toggle_switch.setChecked(False)

    # Set the geometry for the widget (simulate the widget's dimensions)
    toggle_switch.setGeometry(0, 0, 100, 50)

    # Create a QPainter object for the widget itself
    painter = QPainter(toggle_switch)

    # Begin painting
    painter.begin(toggle_switch)

    # Call the paintEvent method with the real QPainter
    toggle_switch.paintEvent(painter)

    # End painting
    painter.end()


def test_handle_position_update(toggle_switch):
    """Test the handle_position setter to ensure the position is updated and the widget repaints."""

    # Set an initial handle position
    initial_pos = 0.5
    toggle_switch.handle_position = initial_pos

    # Mock the update method to check if it's called
    toggle_switch.update = MagicMock()

    # Set a new handle position and check if the update method is called
    new_pos = 0.8
    toggle_switch.handle_position = new_pos

    # Check if the handle position is updated correctly
    assert toggle_switch._handle_position == new_pos

    # Verify that the update method is called after setting the new position
    toggle_switch.update.assert_called_once()
