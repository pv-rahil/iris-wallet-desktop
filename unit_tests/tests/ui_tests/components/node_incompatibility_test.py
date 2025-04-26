"""Unit tests for node incompatibility dialog box"""
from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtWidgets import QMessageBox

from src.views.components.node_incompatibility import NodeIncompatibilityDialog


def test_node_incompatibility_dialog_initialization():
    """Tests the initialization of the node incompatibility dialog."""
    dialog = NodeIncompatibilityDialog()

    # Verify main dialog properties
    assert dialog.node_incompatibility_dialog.icon() == QMessageBox.Icon.Warning
    assert dialog.node_incompatibility_dialog.text() is not None
    assert dialog.delete_app_data_button is not None
    assert dialog.close_button is not None
    assert dialog.node_incompatibility_dialog.defaultButton() == dialog.close_button

    # Verify confirmation dialog properties
    assert dialog.confirmation_dialog.icon() == QMessageBox.Icon.Critical
    assert dialog.confirmation_dialog.text() is not None
    assert dialog.confirm_delete_button is not None
    assert dialog.cancel is not None


def test_show_node_incompatibility_dialog(monkeypatch):
    """Tests the display of the node incompatibility dialog."""
    # Mock the exec method of the main dialog
    mock_exec = MagicMock()
    monkeypatch.setattr(QMessageBox, 'exec', mock_exec)

    dialog = NodeIncompatibilityDialog()
    dialog.show_node_incompatibility_dialog()

    # Verify the dialog was shown
    mock_exec.assert_called_once()


def test_show_confirmation_dialog(monkeypatch):
    """Tests the confirmation dialog for app data deletion."""
    # Mock the exec method of the confirmation dialog
    mock_exec = MagicMock()
    monkeypatch.setattr(QMessageBox, 'exec', mock_exec)

    dialog = NodeIncompatibilityDialog()
    dialog.show_confirmation_dialog()

    # Verify the confirmation dialog was shown
    mock_exec.assert_called_once()


def test_retranslate_ui():
    """Tests the UI translation functionality."""
    dialog = NodeIncompatibilityDialog()

    # Verify button texts are set
    assert dialog.delete_app_data_button.text() is not None
    assert dialog.close_button.text() is not None
    assert dialog.confirm_delete_button.text() is not None
    assert dialog.cancel.text() is not None

    # Verify dialog texts are set
    assert dialog.node_incompatibility_dialog.text() is not None
    assert dialog.confirmation_dialog.text() is not None
