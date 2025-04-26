"""Unit test for SwapWidget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_swap import SwapWidget


@pytest.fixture
def swap_widget(qtbot):
    """Fixture to create and return an instance of SwapWidget."""
    mock_navigation = MagicMock()
    view_model = MagicMock(MainViewModel(mock_navigation))
    widget = SwapWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(swap_widget: SwapWidget):
    """Test the retranslation of UI elements in SwapWidget."""
    swap_widget.retranslate_ui()

    assert swap_widget.from_label.text() == 'From'
    assert swap_widget.swap_title_label.text() == 'Swap'
