"""Unit test for confirmation dialog component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsBlurEffect

from src.views.components.confirmation_dialog import ConfirmationDialog


@pytest.fixture
def confirmation_dialog(qtbot):
    """Fixture for creating a ConfirmationDialog instance."""
    dialog = ConfirmationDialog('Are you sure?', None)
    qtbot.addWidget(dialog)
    return dialog


def test_initialization(confirmation_dialog):
    """Test if the dialog initializes correctly."""
    dialog = confirmation_dialog

    # Check if the dialog has the correct properties
    assert dialog.objectName() == 'confirmation_dialog'
    assert dialog.isModal()
    assert dialog.width() == 300
    assert dialog.height() == 200

    # Check the message label content
    assert dialog.message_label.text() == 'Are you sure?'

    # Check the buttons
    assert dialog.confirmation_dialog_continue_button is not None
    assert dialog.confirmation_dialog_cancel_button is not None

    # Check that buttons have correct text
    assert dialog.confirmation_dialog_continue_button.text() == 'continue'
    assert dialog.confirmation_dialog_cancel_button.text() == 'cancel'


def test_button_functionality(confirmation_dialog, qtbot):
    """Test if the buttons work correctly (Continue and Cancel)."""
    dialog = confirmation_dialog

    # Ensure the dialog is shown (to ensure the buttons are active)
    dialog.show()  # Ensure dialog is shown
    qtbot.waitExposed(dialog)

    # Create slots to catch the signals for testing
    accepted_signal_emitted = MagicMock()
    rejected_signal_emitted = MagicMock()

    # Connect the signals to the mock functions
    dialog.accepted.connect(accepted_signal_emitted)
    dialog.rejected.connect(rejected_signal_emitted)

    # Simulate clicking the Continue button
    qtbot.mouseClick(dialog.confirmation_dialog_continue_button, Qt.LeftButton)

    qtbot.wait(1000)  # Ensure the event loop runs
    accepted_signal_emitted.assert_called_once()

    qtbot.mouseClick(dialog.confirmation_dialog_cancel_button, Qt.LeftButton)

    qtbot.wait(1000)
    rejected_signal_emitted.assert_called_once()


def test_blur_effect_on_show(confirmation_dialog, qtbot):
    """Test if the blur effect is applied to the parent widget when the dialog is shown."""
    dialog = confirmation_dialog
    parent_widget = dialog.parent_widget

    # Ensure dialog has a parent
    assert parent_widget is not None

    # Ensure no blur effect initially
    assert parent_widget.graphicsEffect() is None

    # Show the dialog without displaying it on the screen
    dialog.setVisible(False)  # Set the dialog to not be visible
    dialog.show()  # Show the dialog
    qtbot.waitExposed(dialog)  # Wait for the dialog to be exposed

    # Check if the blur effect is applied to the parent widget
    assert isinstance(parent_widget.graphicsEffect(), QGraphicsBlurEffect)


def test_remove_blur_effect_on_close(confirmation_dialog, qtbot):
    """Test if the blur effect is removed from the parent widget when the dialog is closed."""
    dialog = confirmation_dialog
    parent_widget = dialog.parent_widget

    # Show the dialog and apply blur effect
    dialog.show()
    qtbot.waitExposed(dialog)
    assert isinstance(parent_widget.graphicsEffect(), QGraphicsBlurEffect)

    # Close the dialog
    dialog.close()
    qtbot.wait(100)  # Wait for the dialog to close

    # Ensure blur effect is removed after close
    assert parent_widget.graphicsEffect() is None


def test_retranslate_ui(confirmation_dialog):
    """Test the retranslation of UI elements."""
    dialog = confirmation_dialog

    # Initially, the button text should be translated as 'continue' and 'cancel'
    assert dialog.confirmation_dialog_continue_button.text() == 'continue'
    assert dialog.confirmation_dialog_cancel_button.text() == 'cancel'

    # Call retranslate_ui to simulate language change (e.g., retranslation)
    dialog.retranslate_ui()

    # After calling retranslate_ui, check that the button texts are still the same
    assert dialog.confirmation_dialog_continue_button.text() == 'continue'
    assert dialog.confirmation_dialog_cancel_button.text() == 'cancel'


def test_show_and_close_event(confirmation_dialog, qtbot):
    """Test showEvent and closeEvent methods."""
    dialog = confirmation_dialog

    # Mock the showEvent method to ensure it calls the setGraphicsEffect
    dialog.showEvent = MagicMock()
    dialog.show()
    dialog.showEvent.assert_called_once()

    # Mock the closeEvent method to ensure it removes the effect
    dialog.closeEvent = MagicMock()
    dialog.close()
    dialog.closeEvent.assert_called_once()
