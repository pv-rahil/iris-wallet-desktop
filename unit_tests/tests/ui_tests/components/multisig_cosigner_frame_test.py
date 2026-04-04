"""Unit tests for multisig_cosigner_frame."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QWidget

from src.views.components.multisig_cosigner_frame import CosignerFrame


@pytest.fixture
def cosigner_frame(qtbot):
    """Fixture for CosignerFrame."""
    frame = CosignerFrame()
    qtbot.addWidget(frame)
    return frame


def test_cosigner_frame_initialization(cosigner_frame):
    """Test CosignerFrame initializes correctly."""
    # Assert
    assert cosigner_frame.cosigner_rows == []
    assert cosigner_frame.isHidden()


def test_cosigner_frame_add_cosigner_row(cosigner_frame, qtbot):
    """Test add_cosigner_row adds a card to the frame."""
    # Setup
    card = QWidget()
    qtbot.addWidget(card)

    # Execute
    cosigner_frame.add_cosigner_row(card)

    # Assert
    assert len(cosigner_frame.cosigner_rows) == 1
    assert card in cosigner_frame.cosigner_rows


def test_cosigner_frame_add_multiple_rows(cosigner_frame, qtbot):
    """Test add_cosigner_row adds multiple cards."""
    # Setup
    card1 = QWidget()
    card2 = QWidget()
    card3 = QWidget()
    qtbot.addWidget(card1)
    qtbot.addWidget(card2)
    qtbot.addWidget(card3)

    # Execute
    cosigner_frame.add_cosigner_row(card1)
    cosigner_frame.add_cosigner_row(card2)
    cosigner_frame.add_cosigner_row(card3)

    # Assert
    assert len(cosigner_frame.cosigner_rows) == 3


def test_cosigner_frame_clear_cosigner_rows(cosigner_frame, qtbot):
    """Test clear_cosigner_rows removes all cards."""
    # Setup
    card1 = QWidget()
    card2 = QWidget()
    qtbot.addWidget(card1)
    qtbot.addWidget(card2)
    cosigner_frame.add_cosigner_row(card1)
    cosigner_frame.add_cosigner_row(card2)

    # Execute
    cosigner_frame.clear_cosigner_rows()

    # Assert
    assert len(cosigner_frame.cosigner_rows) == 0


def test_cosigner_frame_get_cosigner_rows(cosigner_frame, qtbot):
    """Test get_cosigner_rows returns the list of cards."""
    # Setup
    card1 = QWidget()
    card2 = QWidget()
    qtbot.addWidget(card1)
    qtbot.addWidget(card2)
    cosigner_frame.add_cosigner_row(card1)
    cosigner_frame.add_cosigner_row(card2)

    # Execute
    rows = cosigner_frame.get_cosigner_rows()

    # Assert
    assert rows == cosigner_frame.cosigner_rows
    assert len(rows) == 2
