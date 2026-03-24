# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `WatchOnlyDialog`.

"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.local_store import local_store
from src.views.components.watch_only_dialog import WatchOnlyDialog


@pytest.fixture
def dialog(qt_app):
    """Provide a `WatchOnlyDialog` instance and ensure cleanup after each test."""
    d = WatchOnlyDialog()
    yield d
    d.close()


def test_continue_disabled_until_valid_and_checked(dialog: WatchOnlyDialog, qtbot, monkeypatch):
    """Continue remains disabled until fields valid and checkbox checked."""
    # Ensure xpub validation passes for test inputs
    monkeypatch.setattr(
        'src.views.components.watch_only_dialog.validate_xpub', lambda *_args, **_kwargs: True,
    )
    dialog.xpub_vanilla_input.setText('xpub_test_valid_vanilla')
    dialog.xpub_colored_input.setText('xpub_test_valid_colored')
    dialog.fingerprint_input.setText('a1b2c3d4')
    # not checked yet
    dialog.handle_continue_button()
    assert dialog.continue_btn.isEnabled() is False
    dialog.check_box.setChecked(True)
    dialog.handle_continue_button()
    assert dialog.continue_btn.isEnabled() is True
    # When valid, error hidden and min size reduced
    assert dialog.error_label.isVisible() is False
    assert dialog.minimumSize().width() == 480
    assert dialog.minimumSize().height() == 420


def test_handle_submit_saves_to_local_store(dialog: WatchOnlyDialog, monkeypatch):
    """Submitting stores xpubs and fingerprint in local store when valid."""
    monkeypatch.setattr(
        'src.views.components.watch_only_dialog.validate_xpub', lambda *_args, **_kwargs: True,
    )
    dialog.xpub_vanilla_input.setText('xpub_test_valid_vanilla')
    dialog.xpub_colored_input.setText('xpub_test_valid_colored')
    dialog.fingerprint_input.setText('a1b2c3d4')
    dialog.check_box.setChecked(True)
    dialog.handle_continue_button()
    dialog.handle_submit()
    assert local_store.get_value(ACCOUNT_XPUB_VANILLA)
    assert local_store.get_value(ACCOUNT_XPUB_COLORED)
    assert local_store.get_value(MASTER_FINGERPRINT)


def test_handle_continue_shows_error_when_fields_missing(dialog: WatchOnlyDialog, monkeypatch, qtbot):
    """Empty fields trigger error, disable continue, uncheck checkbox, and increase min size."""
    # Leave colored empty
    monkeypatch.setattr(
        'src.views.components.watch_only_dialog.validate_xpub', lambda *_args, **_kwargs: True,
    )
    dialog.xpub_vanilla_input.setText('xpub_valid')
    dialog.xpub_colored_input.setText('')
    dialog.fingerprint_input.setText('a1b2c3d4')
    dialog.check_box.setChecked(True)
    dialog.handle_continue_button()
    # show offscreen so visibility reflects child visibility state
    dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
    dialog.show()
    qtbot.waitExposed(dialog)
    assert dialog.error_label.isVisible() is True
    assert dialog.continue_btn.isEnabled() is False
    assert dialog.check_box.isChecked() is False
    assert dialog.minimumSize().width() == 480
    assert dialog.minimumSize().height() == 490


def test_handle_continue_invalid_xpub_disables_and_shows_error(dialog: WatchOnlyDialog, monkeypatch, qtbot):
    """Invalid xpub validation shows error and disables continue."""
    # Force validate_xpub to return False
    monkeypatch.setattr(
        'src.views.components.watch_only_dialog.validate_xpub', lambda *_args, **_kwargs: False,
    )
    dialog.xpub_vanilla_input.setText('xpub_invalid')
    dialog.xpub_colored_input.setText('xpub_invalid')
    dialog.fingerprint_input.setText('a1b2c3d4')
    dialog.check_box.setChecked(True)
    dialog.handle_continue_button()
    dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
    dialog.show()
    qtbot.waitExposed(dialog)
    assert dialog.error_label.isVisible() is True
    assert dialog.continue_btn.isEnabled() is False
    assert dialog.check_box.isChecked() is False
    assert dialog.minimumSize().height() == 490


def test_handle_continue_invalid_fingerprint_shows_error(dialog: WatchOnlyDialog, monkeypatch, qtbot):
    """Fingerprint must be 8 hex chars; otherwise error shown and continue disabled."""
    monkeypatch.setattr(
        'src.views.components.watch_only_dialog.validate_xpub', lambda *_args, **_kwargs: True,
    )
    dialog.xpub_vanilla_input.setText('xpub_test_valid_vanilla')
    dialog.xpub_colored_input.setText('xpub_test_valid_colored')
    dialog.fingerprint_input.setText('badZZZZZ')  # invalid hex/length
    dialog.check_box.setChecked(True)
    dialog.handle_continue_button()
    dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
    dialog.show()
    qtbot.waitExposed(dialog)
    assert dialog.error_label.isVisible() is True
    assert dialog.continue_btn.isEnabled() is False
    assert dialog.check_box.isChecked() is False
    assert dialog.minimumSize().height() == 490
