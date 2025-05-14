"""Unit test for configurable card component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from src.model.common_operation_model import ConfigurableCardModel
from src.views.components.configurable_card import ConfigurableCardFrame


@pytest.fixture
def card_model():
    """Fixture to create a ConfigurableCardModel instance."""
    return ConfigurableCardModel(
        title_label='Test Title',
        title_desc='Test Description',
        suggestion_desc='Suggested Value',
        placeholder_value=100.0,
    )


@pytest.fixture
def configurable_card_frame(qtbot, card_model):
    """Fixture to create and return a ConfigurableCardFrame instance."""
    card_frame = ConfigurableCardFrame(None, card_model)
    qtbot.addWidget(card_frame)
    return card_frame


def test_initial_state(configurable_card_frame):
    """Test the initial state of the ConfigurableCardFrame."""
    card_frame = configurable_card_frame

    # Test the title label and description
    assert card_frame.title_label.text() == 'Test Title'
    assert card_frame.title_desc.text() == 'Test Description'
    assert card_frame.suggestion_desc is None
    assert card_frame.input_value is None
    assert not card_frame.is_expanded


def test_toggle_expand(configurable_card_frame, qtbot):
    """Test the toggle_expand method of the ConfigurableCardFrame."""
    card_frame = configurable_card_frame

    # Initial state, should not be expanded
    assert not card_frame.is_expanded

    # Simulate clicking to expand the frame
    qtbot.mouseClick(card_frame, Qt.LeftButton)
    assert card_frame.is_expanded
    assert card_frame.suggestion_desc is not None
    assert card_frame.input_value is not None
    assert not card_frame.save_button.isHidden()

    # Simulate clicking again to collapse the frame
    qtbot.mouseClick(card_frame, Qt.LeftButton)
    assert not card_frame.is_expanded
    assert card_frame.suggestion_desc.isHidden()
    assert card_frame.input_value.isHidden()
    assert card_frame.save_button.isHidden()


def test_check_input_and_toggle_save_button(configurable_card_frame, qtbot):
    """Test if the save button is enabled/disabled based on input_value."""
    card_frame = configurable_card_frame

    card_frame.expand_frame()

    assert card_frame.input_value is not None

    card_frame.save_button.setDisabled(True)

    assert card_frame.input_value.text().strip() == ''
    assert not card_frame.save_button.isEnabled()
    card_frame.input_value.setText('Some input text')

    card_frame.check_input_and_toggle_save_button()

    assert card_frame.save_button.isEnabled()

    card_frame.input_value.clear()

    card_frame.check_input_and_toggle_save_button()

    assert not card_frame.save_button.isEnabled()


def test_toggle_expanded_frame_update(configurable_card_frame, qtbot):
    """Test if collapsing other expanded frame works when toggling expansion."""

    # Create a valid ConfigurableCardModel instance
    card_model = ConfigurableCardModel(
        title_label='Test Title',
        title_desc='Test Description',
        suggestion_label='Suggestion',
        suggestion_desc='Suggested value',
        placeholder_value='Some placeholder',
    )

    card_frame = configurable_card_frame
    # Pass the card_model instance to create another card frame
    # Create another card frame with a valid model instance
    another_card_frame = ConfigurableCardFrame(None, card_model)
    qtbot.addWidget(another_card_frame)

    # Simulate expanding the first frame
    qtbot.mouseClick(card_frame, Qt.LeftButton)
    assert card_frame.is_expanded
    assert ConfigurableCardFrame._expanded_frame == card_frame

    # Simulate expanding the second frame (should collapse the first frame)
    qtbot.mouseClick(another_card_frame, Qt.LeftButton)
    assert another_card_frame.is_expanded
    assert ConfigurableCardFrame._expanded_frame == another_card_frame
    assert not card_frame.is_expanded  # The first frame should be collapsed
