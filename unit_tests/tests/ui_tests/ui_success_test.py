"""Unit test for SuccessWidget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.model.success_model import SuccessPageModel
from src.views.ui_success import SuccessWidget


@pytest.fixture
def success_widget(qtbot):
    """Fixture to create and return an instance of SuccessWidget."""
    callback = MagicMock()
    params = SuccessPageModel(
        header='test_header_text',
        title='test_title',
        description='test_desc',
        button_text='test_button_text',
        callback=callback,
    )

    widget = SuccessWidget(params)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(success_widget: SuccessWidget):
    """Test the retranslation of UI elements in SuccessWidget."""
    success_widget.retranslate_ui()

    assert success_widget.home_button.text() == 'test_button_text'
    assert success_widget.success_page_header.text() == 'test_header_text'
