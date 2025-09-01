# pylint: disable=redefined-outer-name,unused-argument
"""UI tests for `BreadcrumbBar` component."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QPushButton

from src.views.components.selection_breadcrumb_widget import BreadcrumbBar


@pytest.fixture
def breadcrumb_widget(qt_app):
    """Provide a fresh `BreadcrumbBar` instance for each test."""
    b = BreadcrumbBar()
    yield b
    b.close()


def test_set_breadcrumbs_click_emits(breadcrumb_widget: BreadcrumbBar, qtbot):
    """Clicking a non-pending crumb should emit `crumb_clicked` with its index."""
    crumbs = [
        {'logo': ':/assets/online.png', 'title': 'online'},
        {'logo': ':/assets/offline.png', 'title': 'offline'},
    ]
    breadcrumb_widget.set_breadcrumbs(crumbs, active_index=0)

    # Expect clicking on index 1 to emit
    with qtbot.waitSignal(breadcrumb_widget.crumb_clicked, timeout=1000) as sig:
        # _crumbs holds frames in order
        frame = breadcrumb_widget.crumbs[1]
        # call the installed mousePressEvent handler
        frame.mousePressEvent(None)
    assert sig.args == [1]


def test_pending_crumb_does_not_emit(breadcrumb_widget: BreadcrumbBar, qtbot):
    """Click on a pending crumb should not emit `crumb_clicked`."""
    crumbs = [
        {'logo': ':/assets/online.png', 'title': 'online'},
        {'logo': ':/assets/offline.png', 'title': 'offline', 'pending': True},
    ]
    breadcrumb_widget.set_breadcrumbs(crumbs, active_index=0)

    emitted: list[int] = []
    breadcrumb_widget.crumb_clicked.connect(emitted.append)

    # Try clicking the pending second crumb
    frame = breadcrumb_widget.crumbs[1]
    frame.mousePressEvent(None)

    assert not emitted


def test_white_logo_path_transforms():
    """`get_white_logo_path` should transform foo.png to white_foo.png, else empty."""
    assert BreadcrumbBar.get_white_logo_path(
        ':/assets/online.png',
    ) == ':/assets/white_online.png'
    assert BreadcrumbBar.get_white_logo_path(
        '/a/b/icon.png',
    ) == '/a/b/white_icon.png'
    assert BreadcrumbBar.get_white_logo_path('') == ''
    assert BreadcrumbBar.get_white_logo_path('not_a_png') == ''


def test_close_button_present(breadcrumb_widget: BreadcrumbBar):
    """Close button should be a `QPushButton` attached to the bar."""
    assert isinstance(breadcrumb_widget.cls_button, QPushButton)
