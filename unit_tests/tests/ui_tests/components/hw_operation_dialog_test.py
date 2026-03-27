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


def test_update_dialog_with_error_status(dialog: HardwareWalletOperationDialog):
    """Update dialog with ERROR status shows cancel button."""
    with patch('src.views.components.hw_device_selection_dialog.HWDeviceSelectionDialog.map_hwi_error', return_value='mapped'):
        dialog.update_dialog('Error occurred', PsbtStatus.ERROR)
        assert not dialog.cancel_button.isHidden()
        assert dialog.done_button.isHidden()


def test_get_instance_singleton(qt_app):
    """Test get_instance returns singleton."""
    with patch('src.views.components.hw_operation_dialog.load_stylesheet', return_value=''):
        d1 = HardwareWalletOperationDialog.get_instance()
        d2 = HardwareWalletOperationDialog.get_instance()
        assert d1 is d2
        d1.close()


def test_accept_closes_dialog(dialog: HardwareWalletOperationDialog):
    """Test accept method closes the dialog."""
    dialog.show()
    dialog.accept()
    assert not dialog.isVisible()


def test_reject_closes_dialog(dialog: HardwareWalletOperationDialog):
    """Test reject method closes the dialog."""
    dialog.show()
    dialog.reject()
    assert not dialog.isVisible()


def test_cancel_button_click_rejects(dialog: HardwareWalletOperationDialog):
    """Test clicking cancel button rejects the dialog."""
    dialog.show()
    dialog.cancel_button.click()
    assert not dialog.isVisible()
