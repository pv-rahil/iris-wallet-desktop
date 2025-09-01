# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `WatchOnlyDialog`.

"""
from __future__ import annotations

import pytest

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
