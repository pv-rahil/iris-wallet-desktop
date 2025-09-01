# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `SelectionPage`."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel
from src.views.components.selection_page import SelectionPage


@pytest.fixture
def widget(qt_app):
    """Provide a `SelectionPage` with mocked view model and params; ensure cleanup."""
    vm = MagicMock()
    params = SelectionPageModel(
        title='select_wallet_mode',
        logo_1_path=':/assets/online.png',
        logo_1_title=WalletType.ONLINE_TYPE_WALLET.value,
        logo_1_info='online_wallet_info',
        logo_2_path=':/assets/offline.png',
        logo_2_title=WalletType.OFFLINE_TYPE_WALLET.value,
        logo_2_info='offline_wallet_info',
    )
    w = SelectionPage(vm, params)
    yield w
    w.close()


def test_initial_selection_and_signal(widget: SelectionPage, qtbot):
    """Default selection should be logo_1; changing emits `selection_changed`."""
    # Default selects logo_1
    assert widget.selected_frame == widget.params.logo_1_title
    with qtbot.waitSignal(widget.selection_changed, timeout=1000):
        widget.handle_frame_click(widget.params.logo_2_title)


@pytest.mark.parametrize(
    'title,setter',
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
def test_on_click_continue_sets_settings(title, setter, qt_app):
    """Clicking continue should call the appropriate SettingRepository setter."""
    vm = MagicMock()
    params = SelectionPageModel(
        title='t',
        logo_1_path=':/assets/a.png',
        logo_1_title=title,
        logo_1_info='i1',
        logo_2_path=':/assets/b.png',
        logo_2_title=title,
        logo_2_info='i2',
    )
    w = SelectionPage(vm, params)
    try:
        w.selected_frame = title
        with patch(f'src.views.components.selection_page.SettingRepository.{setter}') as setter_mock:
            w.on_click_continue()
            assert setter_mock.called
    finally:
        w.close()
