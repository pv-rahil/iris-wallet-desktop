"""Unit tests for RgbLibIncompatibilityDialog.
"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from src.views.components.rgb_lib_incompatibility import RgbLibIncompatibilityDialog


def test_init_configures_dialogs_and_defaults(qtbot):
    """Dialog constructs both QMessageBox dialogs, buttons, and default button."""

    dlg = RgbLibIncompatibilityDialog()

    # Constructed attributes exist
    assert isinstance(dlg.rgb_lib_incompatibility_dialog, QMessageBox)
    assert isinstance(dlg.confirmation_dialog, QMessageBox)

    # Buttons exist
    assert dlg.delete_app_data_button is not None
    assert dlg.close_button is not None
    assert dlg.confirm_delete_button is not None
    assert dlg.cancel is not None

    # Default button is close_button
    assert dlg.rgb_lib_incompatibility_dialog.defaultButton() is dlg.close_button


def test_retranslate_ui_sets_translated_texts(mocker):
    """retranslate_ui sets localized text for dialogs and all buttons."""

    # Patch translate to be deterministic
    tr = mocker.patch(
        'src.views.components.rgb_lib_incompatibility.QCoreApplication.translate',
        side_effect=lambda ctx, key: f'tr:{key}',
    )
    dlg = RgbLibIncompatibilityDialog()
    dlg.retranslate_ui()

    # Dialog texts
    assert dlg.rgb_lib_incompatibility_dialog.text(
    ) == 'tr:rgb_lib_incompatibility_dialog_desc'
    assert dlg.confirmation_dialog.text() == 'tr:confirm_app_data_deletion'
    # Button texts
    assert dlg.delete_app_data_button.text() == 'tr:delete_app_data'
    assert dlg.close_button.text() == 'tr:crash_dialog_close_app'
    assert dlg.confirm_delete_button.text() == 'tr:delete_app_data'
    assert dlg.cancel.text() == 'tr:cancel'
    assert tr.call_count >= 6


def test_show_rgb_lib_incompatibility_dialog_exec_called(mocker):
    """show_rgb_lib_incompatibility_dialog invokes exec() on the warning dialog."""

    dlg = RgbLibIncompatibilityDialog()
    spy = mocker.patch.object(dlg.rgb_lib_incompatibility_dialog, 'exec')
    dlg.show_rgb_lib_incompatibility_dialog()
    spy.assert_called_once_with()


def test_show_confirmation_dialog_exec_called(mocker):
    """show_confirmation_dialog invokes exec() on the confirmation dialog."""

    dlg = RgbLibIncompatibilityDialog()
    spy = mocker.patch.object(dlg.confirmation_dialog, 'exec')
    dlg.show_confirmation_dialog()
    spy.assert_called_once_with()
