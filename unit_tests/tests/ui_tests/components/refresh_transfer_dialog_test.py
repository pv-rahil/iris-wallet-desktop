# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for RefreshTransferDialog component."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from rgb_lib import RgbLibError

from src.model.rgb_model import RefreshFailureItem
from src.views.components.refresh_transfer_dialog import RefreshTransferDialog


@pytest.fixture
def dialog(qt_app):
    """Create a RefreshTransferDialog instance."""
    return RefreshTransferDialog(parent=None, payload=None)


def test_populate_single_item_shrinks_and_sets_texts(dialog: RefreshTransferDialog):
    """Single item should hide scrollbar and adjust size; labels should be populated."""
    item = RefreshFailureItem(
        asset_id='aid1', failure=MagicMock(spec=RgbLibError),
    )
    dialog.populate([item])

    # Title set and one card exists (layout count includes stretch at end)
    assert dialog.title_label.text()
    # Verify scroll area policies for single card path
    assert dialog.scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    # Ensure the card widgets exist and show expected asset id
    # The first added widget is the card frame
    # Traverse layout to find the QLabel with objectName 'asset_id_value_label'
    found_asset_id = False
    for i in range(dialog.cards_layout.count()):
        w = dialog.cards_layout.itemAt(i).widget()
        if not w:
            continue
        for child in w.findChildren(QLabel):
            if child.objectName() == 'asset_id_value_label' and child.text() == 'aid1':
                found_asset_id = True
                break
    assert found_asset_id


def test_populate_multiple_items_restores_scroll(dialog: RefreshTransferDialog):
    """Multiple items should restore scroll behavior and sizing."""
    items = [
        RefreshFailureItem(asset_id='a1', failure=MagicMock(spec=RgbLibError)),
        RefreshFailureItem(asset_id='a2', failure=MagicMock(spec=RgbLibError)),
    ]
    dialog.populate(items)
    assert dialog.scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    # Cards layout should have widgets plus stretch
    assert dialog.cards_layout.count() >= 3
