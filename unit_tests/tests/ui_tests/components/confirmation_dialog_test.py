"""Unit test for confirmation dialog component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtGui import QShowEvent
from PySide6.QtGui import QCloseEvent
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


def test_button_functionality(confirmation_dialog):
    """Test if the buttons emit correct signals when clicked."""
    dialog = confirmation_dialog

    # Create slots to catch the signals for testing
    accepted_signal_emitted = MagicMock()
    rejected_signal_emitted = MagicMock()

    # Connect the signals to the mock functions
    dialog.accepted.connect(accepted_signal_emitted)
    dialog.rejected.connect(rejected_signal_emitted)

    # Simulate clicking the Continue button by emitting its clicked signal
    dialog.confirmation_dialog_continue_button.clicked.emit()
    accepted_signal_emitted.assert_called_once()
    assert dialog.parent_widget.graphicsEffect() is None  # Blur cleared on accept

    # Reset for next test
    accepted_signal_emitted.reset_mock()

    # Simulate clicking the Cancel button
    dialog.confirmation_dialog_cancel_button.clicked.emit()
    rejected_signal_emitted.assert_called_once()


def test_blur_effect_on_show(confirmation_dialog):
    """Test if the blur effect is applied to the parent widget when the dialog is shown."""
    dialog = confirmation_dialog
    parent_widget = dialog.parent_widget

    # Ensure dialog has a parent
    assert parent_widget is not None

    # Ensure no blur effect initially
    assert parent_widget.graphicsEffect() is None

    # Manually trigger showEvent to apply blur effect (simulates show)
    dialog.showEvent(QShowEvent())

    # Check if the blur effect is applied to the parent widget
    assert isinstance(parent_widget.graphicsEffect(), QGraphicsBlurEffect)


def test_remove_blur_effect_on_close(confirmation_dialog):
    """Test if the blur effect is removed from the parent widget when the dialog is closed."""
    dialog = confirmation_dialog
    parent_widget = dialog.parent_widget

    # Manually trigger showEvent to apply blur effect (simulates show)
    dialog.showEvent(QShowEvent())
    assert isinstance(parent_widget.graphicsEffect(), QGraphicsBlurEffect)

    # Manually trigger closeEvent to remove blur effect
    dialog.closeEvent(QCloseEvent())
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


@pytest.fixture
def warning_dialog(qtbot):
    """Fixture for creating a warning-styled ConfirmationDialog with checkbox."""
    dialog = ConfirmationDialog(
        'Sync may overwrite data', None, icon_type='warning',
    )
    qtbot.addWidget(dialog)
    return dialog


def test_warning_initialization(warning_dialog):
    """Warning dialog should show checkbox and have Continue disabled initially."""
    dlg = warning_dialog
    assert dlg.icon_type == 'warning'
    assert dlg.check_box is not None
    assert dlg.confirmation_dialog_continue_button.isEnabled() is False


def test_warning_checkbox_enables_continue(warning_dialog):
    """Checking the checkbox should enable the Continue button; unchecking disables it."""
    dlg = warning_dialog
    # Initially disabled
    assert not dlg.confirmation_dialog_continue_button.isEnabled()
    # Check -> enabled (emit stateChanged signal to trigger handler)
    dlg.check_box.setChecked(True)
    assert dlg.confirmation_dialog_continue_button.isEnabled()
    # Uncheck -> disabled
    dlg.check_box.setChecked(False)
    assert not dlg.confirmation_dialog_continue_button.isEnabled()


def test_warning_retranslate_checkbox_text(warning_dialog):
    """retranslate_ui should also set checkbox text for warning dialog."""
    dlg = warning_dialog
    dlg.retranslate_ui()
    # Ensure some non-empty text is set on checkbox
    assert isinstance(dlg.check_box.text(), str)
    assert dlg.check_box.text() != ''


def test_accept_clears_blur_effect(warning_dialog):
    """accept() should clear blur effect from parent widget."""
    dlg = warning_dialog
    parent_widget = dlg.parent_widget
    # Manually trigger showEvent to apply blur
    dlg.showEvent(QShowEvent())
    assert parent_widget.graphicsEffect() is not None
    # Accept clears effect
    dlg.accept()
    assert parent_widget.graphicsEffect() is None
