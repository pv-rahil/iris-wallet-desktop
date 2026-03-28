# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for `HWDeviceSelectionDialog`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

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
    # Create radios via public API
    devices = [
        {'model': 'nano_s', 'fingerprint': 'fp1'},
        {'model': 'nano_x', 'fingerprint': 'fp2'},
    ]
    dialog.populate_devices(devices)
    # select first radio
    dialog.radio_buttons[0].setChecked(True)
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


def test_populate_devices_no_devices_shows_label_and_hides_error(dialog: HWDeviceSelectionDialog):
    """Populate with no devices should show no-device label and hide error label."""
    dialog.populate_devices([])
    # layout should contain a no_device_label
    found = False
    for i in range(dialog.device_frame.layout().count()):
        w = dialog.device_frame.layout().itemAt(i).widget()
        if w and w.objectName() == 'no_device_label':
            found = True
            break
    assert found is True
    assert dialog.error_label.isVisible() is False


def test_populate_devices_with_error_disables_radios_and_shows_error(dialog: HWDeviceSelectionDialog, qtbot):
    """Populate with error shows mapped error and disables radios."""
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    devices = [{'model': 'nano_s', 'fingerprint': 'fp1'}]
    dialog.populate_devices(devices, error_message='0x6985')
    assert dialog.error_label.isVisible() is True
    assert dialog.error_label.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_operation_cancelled',
    )
    assert all(rb.isEnabled() is False for rb in dialog.radio_buttons)


def test_on_connect_no_selection_restarts_poll_timer(dialog: HWDeviceSelectionDialog):
    """On connect with no selection stops then restarts poll timer and returns."""
    # Ensure there are no radios selected
    dialog.populate_devices([])
    assert dialog.poll_timer.isActive() is True
    dialog._on_connect()
    # Should be active again after early return path
    assert dialog.poll_timer.isActive() is True


def test_on_connect_device_not_found_shows_toast_and_resets(dialog: HWDeviceSelectionDialog, qtbot):
    """On connect with unmatched selection should show toast and reset loader."""
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    devices = [{'model': 'nano_s', 'fingerprint': 'fp1'}]
    dialog.populate_devices(devices)
    # select first
    dialog.radio_buttons[0].setChecked(True)
    with patch('src.views.components.hw_device_selection_dialog.enumerate_ledger_devices', return_value=[{'fingerprint': 'other'}]) as _enum, \
            patch('src.views.components.hw_device_selection_dialog.ToastManager.error') as mock_toast:
        dialog._on_connect()
        mock_toast.assert_called_once()
        # After reset, connect button should be visible again
        assert dialog.connect_button.isVisible() is True


def test_on_connect_device_locked_shows_toast_and_resets(dialog: HWDeviceSelectionDialog, qtbot):
    """On connect with matched device having error shows device_locked toast and resets."""
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    devices = [{'model': 'nano_s', 'fingerprint': 'fp1'}]
    dialog.populate_devices(devices)
    dialog.radio_buttons[0].setChecked(True)
    with patch('src.views.components.hw_device_selection_dialog.enumerate_ledger_devices', return_value=[{'fingerprint': 'fp1', 'error': 'locked'}]), \
            patch('src.views.components.hw_device_selection_dialog.ToastManager.error') as mock_toast:
        dialog._on_connect()
        # Should be called with translated device_locked
        mock_toast.assert_called_once()
        assert dialog.connect_button.isVisible() is True


def test_on_connect_success_calls_view_model_connect(dialog: HWDeviceSelectionDialog):
    """On connect should call view model with path and network when device found and ok."""
    devices = [{'model': 'nano_s', 'fingerprint': 'fp1'}]
    dialog.populate_devices(devices)
    dialog.radio_buttons[0].setChecked(True)
    with patch('src.views.components.hw_device_selection_dialog.enumerate_ledger_devices', return_value=[{'fingerprint': 'fp1', 'path': 'usb://dev1'}]), \
            patch('src.views.components.hw_device_selection_dialog.SettingRepository.get_wallet_network', return_value='MAINNET') as _net, \
            patch.object(dialog._device_selection_view_model, 'connect_to_device') as mock_connect:
        dialog._on_connect()
        mock_connect.assert_called_once_with(
            {'fingerprint': 'fp1', 'path': 'usb://dev1'}, 'MAINNET',
        )


def test_set_error_updates_loader_and_shows_cancel(dialog: HWDeviceSelectionDialog, qtbot):
    """set_error should map text, stop movie, and show cancel button and loader label."""
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    dialog._show_connecting_loader()
    dialog.set_error('0x6985')
    assert dialog._loader_text.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_operation_cancelled',
    )
    assert dialog.cancel_button.isVisible() is True
    assert dialog._loader_label.isVisible() is True


def test_get_selected_device_returns_text_or_none(dialog: HWDeviceSelectionDialog):
    """get_selected_device should return selected radio text or None."""
    assert dialog.get_selected_device() is None
    devices = [{'model': 'nano_s', 'fingerprint': 'fp1'}]
    dialog.populate_devices(devices)
    dialog.radio_buttons[0].setChecked(True)
    assert dialog.get_selected_device() is not None


def test_checking_devices_preserves_selection(dialog: HWDeviceSelectionDialog):
    """checking_devices should reselect previously selected fingerprint if still present."""
    devices = [
        {'model': 'nano_s', 'fingerprint': 'keep'},
    ]
    dialog.populate_devices(devices)
    dialog.radio_buttons[0].setChecked(True)
    with patch(
        'src.views.components.hw_device_selection_dialog.enumerate_ledger_devices', return_value=[
            {'model': 'nano_s', 'fingerprint': 'keep'},
            {'model': 'nano_x', 'fingerprint': 'new'},
        ],
    ):
        dialog.checking_devices()
        # previously selected should remain selected
        checked = dialog.button_group.checkedButton()
        assert checked is not None
        assert checked.property('fingerprint') == 'keep'


def test_reject_stops_timer(dialog: HWDeviceSelectionDialog):
    """reject should stop poll timer."""
    assert dialog.poll_timer.isActive() is True
    dialog.reject()
    assert dialog.poll_timer.isActive() is False


def test_close_event_stops_timer(dialog: HWDeviceSelectionDialog, qtbot):
    """closeEvent should stop poll timer."""
    assert dialog.poll_timer.isActive() is True
    dialog.close()
    assert dialog.poll_timer.isActive() is False
