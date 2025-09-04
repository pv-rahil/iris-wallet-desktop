# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `HardwareWalletOperationDialog`"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.model.enums.enums_model import PsbtStatus
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog


@pytest.fixture
def dialog(qt_app):
    """Provide `HardwareWalletOperationDialog` instance and clean up after."""
    d = HardwareWalletOperationDialog(message='', dialog_type=None)
    yield d
    d.close()


def test_retranslate_sets_button_texts(dialog: HardwareWalletOperationDialog):
    """Retranslate should populate cancel/done button texts."""
    dialog.retranslate_ui()
    assert dialog.cancel_button.text()
    assert dialog.done_button.text()


def test_set_loading(dialog: HardwareWalletOperationDialog):
    """Loading state shows message, cancel button, and icon; hides done button."""
    dialog.set_loading('Signing...')
    assert dialog.message_label.text() == 'Signing...'
    assert not dialog.cancel_button.isHidden()
    assert dialog.done_button.isHidden()
    assert not dialog.icon_label.isHidden()


@patch('src.views.components.hw_device_selection_dialog.HWDeviceSelectionDialog.map_hwi_error', return_value='mapped')
@patch('src.views.components.hw_device_selection_dialog.HWDeviceSelectionDialog.__init__', return_value=None)
def test_set_error_maps_and_shows_buttons(_init, _map, dialog: HardwareWalletOperationDialog):
    """Error state maps message, shows cancel, hides done button."""
    dialog.set_error('raw')
    assert dialog.message_label.text() == 'mapped'
    assert not dialog.cancel_button.isHidden()
    assert dialog.done_button.isHidden()


def test_update_dialog_switches_states(dialog: HardwareWalletOperationDialog):
    """Update dialog should switch UI according to status enum."""
    dialog.update_dialog('x', PsbtStatus.SIGNING)
    assert not dialog.cancel_button.isHidden()
