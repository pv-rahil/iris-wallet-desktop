# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for `HWDeviceSelectionDialog`."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog


@pytest.fixture
def dialog(qt_app):
    """Provide a fresh `HWDeviceSelectionDialog` instance for each test."""
    d = HWDeviceSelectionDialog(wallet_type='Ledger', parent=None)
    yield d
    d.close()


def test_initial_state(dialog: HWDeviceSelectionDialog):
    """Initial state should have disabled connect button and hidden error label."""
    assert dialog.connect_button.isEnabled() is False
    assert dialog.error_label.isVisible() is False


def test_update_connect_button_state_enables_on_selection(dialog: HWDeviceSelectionDialog, qtbot):
    """Update connect button state should enable on selection."""
    # simulate adding two radio buttons as the dialog would in checking_devices
    rb1 = dialog._create_device_radio_button('Device 1', 'path1')
    rb2 = dialog._create_device_radio_button('Device 2', 'path2')
    dialog.button_group.addButton(rb1)
    dialog.button_group.addButton(rb2)
    rb1.setChecked(True)
    dialog._update_connect_button_state()
    assert dialog.connect_button.isEnabled() is True


def test_map_hwi_error_mapping():
    """Mapping should return translated error message for 0x6985."""
    assert HWDeviceSelectionDialog.map_hwi_error('0x6985') != '0x6985'
    assert HWDeviceSelectionDialog.map_hwi_error('') == ''


def test_error_mapping_unknown_returns_original():
    """Mapping unknown should return original error message."""
    d = HWDeviceSelectionDialog(MagicMock())
    msg = 'some random error'
    assert d.map_hwi_error(msg) == msg


def test_map_model_name_translations_for_ledger_models(qtbot):
    """Mapping should return translated model name for ledger models."""
    d = HWDeviceSelectionDialog(MagicMock())

    def tr(key):
        """Translate key."""
        return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, key)
    assert d.map_model_name('nano_s') == tr('ledger_nano_s')
    assert d.map_model_name('nano_s_plus') == tr('ledger_nano_s_plus')
    assert d.map_model_name('nano_x') == tr('ledger_nano_x')
    assert d.map_model_name('stax') == tr('ledger_stax')
    assert d.map_model_name('flex') == tr('ledger_flex')


def test_map_model_name_unknown_title_cases():
    """Mapping unknown should return original model name."""
    d = HWDeviceSelectionDialog(MagicMock())
    assert d.map_model_name('unknown_model') == 'Unknown_Model'
