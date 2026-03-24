# pylint: disable=redefined-outer-name,unused-argument
"""Unit tests for WalletModeSummaryDialog following the common UI test style."""
from __future__ import annotations
from unittest.mock import MagicMock

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QLabel

from src.views.components.wallet_mode_summary_dialog import WalletModeSummaryDialog


def _cfg(mode_name='Mode A', caps=None, lims=None, recs=None):
    return SimpleNamespace(
        mode_name=mode_name,
        capabilities=caps or [],
        limitations=lims or [],
        recommended_for=recs or [],
    )


@pytest.fixture
def wallet_mode_dialog_no_limits(qtbot, monkeypatch):
    """Dialog with caps+recs, but no limitations. Stylesheet loading is patched."""
    monkeypatch.setattr(
        'src.views.components.wallet_mode_summary_dialog.load_stylesheet',
        lambda *_a, **_k: '',
    )
    monkeypatch.setattr(
        'src.views.components.wallet_mode_summary_dialog.get_current_wallet_mode_config',
        lambda: _cfg(
            caps=[{'emoji': '✅', 'text': 'Cap1'}],
            lims=[],
            recs=[{'emoji': '👍', 'text': 'Rec1'}],
        ),
    )
    dlg = WalletModeSummaryDialog()
    qtbot.addWidget(dlg)
    return dlg


def _show_offscreen(widget, qtbot):
    """Show widget offscreen."""
    widget.setAttribute(Qt.WA_DontShowOnScreen, True)
    widget.show()
    qtbot.waitExposed(widget)


def test_initial_load_hides_limitations_when_empty(wallet_mode_dialog_no_limits, qtbot):
    """Dialog loads with limitations hidden when empty."""
    dlg = wallet_mode_dialog_no_limits
    _show_offscreen(dlg, qtbot)
    assert dlg.mode_name.text() == 'Mode A'
    assert dlg.capabilities_frame.isVisible() is True
    assert dlg.recommended_frame.isVisible() is True
    # limitations frame removed from layout and parent
    assert dlg.dialog_box_vertical_layout.indexOf(dlg.limitations_frame) == -1
    assert dlg.limitations_frame.parent() is None
    # capabilities grid contains emoji/text labels
    emoji_labels = dlg.capabilities_frame.findChildren(QLabel, 'emoji_label')
    text_labels = dlg.capabilities_frame.findChildren(QLabel, 'text_label')
    assert len(emoji_labels) == 1
    assert len(text_labels) == 1


def test_reload_adds_limitations_back_and_updates_lists(wallet_mode_dialog_no_limits, qtbot, monkeypatch):
    """Dialog reloads with limitations added back and lists updated."""
    dlg = wallet_mode_dialog_no_limits
    _show_offscreen(dlg, qtbot)
    assert dlg.dialog_box_vertical_layout.indexOf(dlg.limitations_frame) == -1

    # Now change config: limitations present, fewer capabilities, no recommended
    new_cfg = _cfg(
        caps=[{'emoji': '✅', 'text': 'OnlyOne'}],
        lims=[{'emoji': '⚠️', 'text': 'Limit1'}],
        recs=[],
    )
    monkeypatch.setattr(
        'src.views.components.wallet_mode_summary_dialog.get_current_wallet_mode_config',
        lambda: new_cfg,
    )
    dlg.load_configuration()

    assert dlg.dialog_box_vertical_layout.indexOf(dlg.limitations_frame) != -1
    assert dlg.limitations_frame.isVisible() is True
    # capabilities updated; ensure at least one item and the expected text exists
    caps_emojis = dlg.capabilities_frame.findChildren(QLabel, 'emoji_label')
    caps_texts = [
        w.text()
        for w in dlg.capabilities_frame.findChildren(QLabel, 'text_label')
    ]
    assert len(caps_emojis) >= 1
    assert 'OnlyOne' in caps_texts
    # limitations now one item
    lims_emojis = dlg.limitations_frame.findChildren(QLabel, 'emoji_label')
    assert len(lims_emojis) == 1
    # recommended hidden when empty
    assert dlg.recommended_frame.isVisible() is False


def test_retranslate_ui_sets_texts(wallet_mode_dialog_no_limits):
    """Dialog retranslates UI texts."""
    dlg = wallet_mode_dialog_no_limits
    dlg.retranslate_ui()
    assert dlg.capabilities_title.text()
    assert dlg.limitations_title.text()
    assert dlg.recommended_title.text()
    assert dlg.cancel_button.text()
    assert dlg.continue_button.text()


def test_buttons_accept_and_reject_connected(qtbot, monkeypatch):
    """Dialog buttons are connected to accept and reject."""
    monkeypatch.setattr(
        'src.views.components.wallet_mode_summary_dialog.load_stylesheet',
        lambda *_a, **_k: '',
    )
    monkeypatch.setattr(
        'src.views.components.wallet_mode_summary_dialog.get_current_wallet_mode_config',
        _cfg,
    )
    d1 = WalletModeSummaryDialog()
    qtbot.addWidget(d1)
    d1.reject()
    assert d1.result() == QDialog.Rejected

    d2 = WalletModeSummaryDialog()
    qtbot.addWidget(d2)
    d2.accept()
    assert d2.result() == QDialog.Accepted
