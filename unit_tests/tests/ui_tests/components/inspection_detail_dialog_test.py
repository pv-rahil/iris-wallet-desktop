# pylint: disable=redefined-outer-name, protected-access, invalid-name
"""Unit tests for the InspectionDetailDialog component."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.views.components.buttons import PrimaryButton
from src.views.components.inspection_detail_dialog import InspectionDetailDialog


@pytest.fixture
def mock_psbt_details():
    """Returns a simplified mock of PSBT details."""
    details = MagicMock()
    details.txid = 'abc123txid'
    details.total_input_sat = 50000
    details.total_output_sat = 48000
    details.fee_sat = 2000
    details.inputs = []
    details.outputs = []
    return details


@pytest.fixture
def mock_rgb_details():
    """Returns a simplified mock of RGB details."""
    details = MagicMock()
    details.operations = []
    return details


def test_initialization(qtbot, mock_psbt_details):
    """Test the dialog initializes properly and sets window states."""
    with patch('src.views.components.inspection_detail_dialog.load_stylesheet', return_value=''):
        dialog = InspectionDetailDialog(psbt_details=mock_psbt_details)
        qtbot.addWidget(dialog)

        assert dialog.objectName() == 'inspection_detail_dialog'
        assert bool(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
        assert dialog.isModal() is True


def test_overview_card_rendering(qtbot, mock_psbt_details):
    """Verify standard PSBT attributes build the overview card cleanly."""
    with patch('src.views.components.inspection_detail_dialog.load_stylesheet', return_value=''):
        dialog = InspectionDetailDialog(psbt_details=mock_psbt_details)
        qtbot.addWidget(dialog)

        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]

        assert 'abc123txid' in texts
        assert '50,000 sats' in texts
        assert '48,000 sats' in texts
        assert '2,000 sats' in texts


def test_bitcoin_io_sections(qtbot, mock_psbt_details):
    """Verify inputs and outputs build standard rows correctly, skipping zero amounts."""
    # Set up realistic inputs and outputs
    inp = MagicMock()
    inp.amount_sat = 15000
    inp.outpoint.txid = 'inp_txid'

    out_valid = MagicMock()
    out_valid.amount_sat = 9000
    out_valid.address = 'address_valid'

    out_zero = MagicMock()
    out_zero.amount_sat = 0
    out_zero.address = 'address_metadata'

    mock_psbt_details.inputs = [inp]
    mock_psbt_details.outputs = [out_valid, out_zero]

    with patch('src.views.components.inspection_detail_dialog.load_stylesheet', return_value=''):
        dialog = InspectionDetailDialog(psbt_details=mock_psbt_details)
        qtbot.addWidget(dialog)

        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]

        # Verify input was rendered
        assert '15,000 sats' in texts
        assert 'inp_txid' in texts

        # Verify output was rendered
        assert '9,000 sats' in texts
        assert 'address_valid' in texts

        # Verify internal skipped outputs logic
        assert '0 sats' not in texts
        assert 'address_metadata' not in texts


def test_rgb_section_rendering(qtbot, mock_psbt_details, mock_rgb_details):
    """Verify RGB operations handle FUNGIBLE and INFLATION types seamlessly."""
    assign_fungible = MagicMock()
    assign_fungible.is_FUNGIBLE.return_value = True
    assign_fungible.amount = 300

    assign_inflation = MagicMock()
    assign_inflation.is_FUNGIBLE.return_value = False
    assign_inflation.is_INFLATION_RIGHT.return_value = True
    assign_inflation.amount = 500

    ri = MagicMock()
    ri.assignment = assign_fungible

    ro = MagicMock()
    ro.assignment = assign_inflation
    ro.is_concealed = True

    trans = MagicMock()
    trans.type = 'TYPEOFTRANSITION.INFLATE'
    trans.inputs = [ri]
    trans.outputs = [ro]

    op = MagicMock()
    op.asset_id = 'rgb_asset_1'
    op.transitions = [trans]

    mock_rgb_details.operations = [op]

    with patch('src.views.components.inspection_detail_dialog.load_stylesheet', return_value=''):
        dialog = InspectionDetailDialog(
            psbt_details=mock_psbt_details, rgb_details=mock_rgb_details,
        )
        qtbot.addWidget(dialog)

        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]

        # Check title inclusion
        assert any('rgb_asset_1' in text for text in texts)

        # Checking values correctly dispatched
        assert '300' in texts
        assert '500' in texts

        # Make sure mapping successfully recognized the type
        assert any('Inflation' in text for text in texts)


def test_close_button_accepts(qtbot, mock_psbt_details):
    """Verify the close button triggers dialog accept."""
    with patch('src.views.components.inspection_detail_dialog.load_stylesheet', return_value=''):
        dialog = InspectionDetailDialog(psbt_details=mock_psbt_details)
        qtbot.addWidget(dialog)

        close_btn = dialog.findChild(QLabel, '')
        close_btn = None
        for child in dialog.children():
            # In deeper children loop, searching close_btn
            if hasattr(child, 'objectName') and child.objectName() == 'close_btn':
                close_btn = child
                break

        # To avoid complex nested Qt traversals, we can fetch object exactly:
        close_btn = dialog.findChild(PrimaryButton, 'close_btn')

        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            qtbot.mouseClick(close_btn, Qt.MouseButton.LeftButton)
