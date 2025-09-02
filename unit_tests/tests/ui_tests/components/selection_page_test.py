# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""Unit tests for SelectionPage (follow common UI test style)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel
from src.views.components.selection_page import SelectionPage


@pytest.fixture
def selection_page_widget(qtbot, monkeypatch):
    """Fixture to create a SelectionPage instance with permissive privileges."""
    # Avoid file I/O for stylesheets
    monkeypatch.setattr(
        'src.views.components.selection_page.load_stylesheet',
        lambda *_a, **_k: '',
    )
    view_model = MagicMock()  # not used by widget logic
    widget = SelectionPage(
        view_model, SelectionPageModel(
            title='Select Wallet',
            logo_1_title=WalletType.ONLINE_TYPE_WALLET.value,
            logo_1_path=':/icons/logo1.png',
            logo_1_info='Info for option 1',
            logo_2_title=WalletType.OFFLINE_TYPE_WALLET.value,
            logo_2_path=':/icons/logo2.png',
            logo_2_info='Info for option 2',
            step_index=0,
        ),
    )
    qtbot.addWidget(widget)
    return widget


def _show_offscreen(w, qtbot):
    """Show widget offscreen."""
    w.setAttribute(Qt.WA_DontShowOnScreen, True)
    w.show()
    qtbot.waitExposed(w)


def test_dialog_initialization(selection_page_widget, qtbot):
    """Dialog initializes with default selection and info visible."""
    w = selection_page_widget
    _show_offscreen(w, qtbot)
    # Default selection should be option 1
    assert w.selected_frame == w.params.logo_1_title
    assert w.info_frame.isVisible() is True
    # Title and option labels should be set
    assert w.title_text.text()
    assert w.option_1_text_label.text() == w.params.logo_1_title
    assert w.option_2_text_label.text() == w.params.logo_2_title
    # Info text corresponds to option 1
    assert w.wallet_connection_info_label.text() == w.params.logo_1_info


def test_handle_frame_click_switches_and_emits(selection_page_widget, qtbot):
    """Clicking a different frame switches selection and emits signal; same click is no-op."""
    w = selection_page_widget
    _show_offscreen(w, qtbot)
    captured = []
    w.selection_changed.connect(
        lambda title, logo: captured.append((title, logo)),
    )

    # Click option 2 (different from current)
    w.handle_frame_click(w.params.logo_2_title)
    assert w.selected_frame == w.params.logo_2_title
    assert w.info_frame.isVisible() is True
    assert captured[-1] == (w.params.logo_2_title, w.params.logo_2_path)

    # Clicking the same should be a no-op (no new emission)
    prev_len = len(captured)
    w.handle_frame_click(w.params.logo_2_title)
    assert len(captured) == prev_len


def test_on_click_frame_applies_stylesheet(selection_page_widget, mocker):
    """on_click_frame applies selected and deselected stylesheets."""
    w = selection_page_widget
    # Return distinct strings to detect updates
    mocker.patch(
        'src.views.components.selection_page.load_stylesheet',
        side_effect=lambda path: f'STYLE::{path}',
    )
    # Select option 2
    w.on_click_frame(w.params.logo_2_title, True)
    assert w.option_2_frame.styleSheet().startswith('STYLE::')
    # Deselect option 2
    w.on_click_frame(w.params.logo_2_title, False)
    assert 'wallet_selection_style.qss' in w.option_2_frame.styleSheet()


@pytest.mark.parametrize(
    'sel, setter_name',
    [
        (WalletType.ONLINE_TYPE_WALLET.value, 'set_wallet_type'),
        (WalletType.OFFLINE_TYPE_WALLET.value, 'set_wallet_type'),
        (WalletAccessType.WITH_PRIVATE_KEY.value, 'set_wallet_access_type'),
        (WalletAccessType.WATCH_ONLY.value, 'set_wallet_access_type'),
        (WalletEntryType.CREATE.value, 'set_wallet_entry_type'),
        (WalletEntryType.LOAD.value, 'set_wallet_entry_type'),
        (KeyStorageType.ON_DEVICE.value, 'set_key_storage_type'),
        (KeyStorageType.HARDWARE_WALLET.value, 'set_key_storage_type'),
    ],
)
def test_on_click_continue_sets_repository(selection_page_widget, mocker, sel, setter_name):
    """on_click_continue should invoke appropriate SettingRepository setter based on selection."""
    w = selection_page_widget
    m_set_wallet_type = mocker.patch(
        'src.views.components.selection_page.SettingRepository.set_wallet_type',
    )
    m_set_wallet_access_type = mocker.patch(
        'src.views.components.selection_page.SettingRepository.set_wallet_access_type',
    )
    m_set_wallet_entry_type = mocker.patch(
        'src.views.components.selection_page.SettingRepository.set_wallet_entry_type',
    )
    m_set_key_storage_type = mocker.patch(
        'src.views.components.selection_page.SettingRepository.set_key_storage_type',
    )

    w.selected_frame = sel
    w.on_click_continue()

    called_map = {
        'set_wallet_type': m_set_wallet_type,
        'set_wallet_access_type': m_set_wallet_access_type,
        'set_wallet_entry_type': m_set_wallet_entry_type,
        'set_key_storage_type': m_set_key_storage_type,
    }
    # Only the expected setter should have been called
    for name, mock in called_map.items():
        if name == setter_name:
            mock.assert_called_once()
        else:
            mock.assert_not_called()


def test_adjust_size_updates_dimensions(selection_page_widget):
    """adjust_size sets expected min/max sizes for key frames."""
    w = selection_page_widget
    w.adjust_size()
    assert w.widget_page.minimumSize() == QSize(580, 450)
    assert w.widget_page.maximumSize() == QSize(580, 560)
    assert w.option_1_frame.minimumSize() == QSize(224, 204)
    assert w.option_1_frame.maximumSize() == QSize(224, 204)
    assert w.option_2_frame.minimumSize() == QSize(224, 204)
    assert w.option_2_frame.maximumSize() == QSize(224, 204)


def test_reset_selection_restores_default(selection_page_widget, qtbot):
    """reset_selection restores option 1 and its info text."""
    w = selection_page_widget
    _show_offscreen(w, qtbot)
    # Move to option 2 first
    w.handle_frame_click(w.params.logo_2_title)
    assert w.selected_frame == w.params.logo_2_title
    # Reset
    w.reset_selection()
    assert w.selected_frame == w.params.logo_1_title
    assert w.info_frame.isVisible() is True
    assert w.wallet_connection_info_label.text() == w.params.logo_1_info
