"""Unit tests for multisig_threshold_frame."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

import pytest

from src.model.broadcast_transaction_model import MultisigThresholdLabels
from src.views.components.multisig_threshold_frame import ThresholdFrame


@pytest.fixture
def threshold_frame(qtbot):
    """Fixture for ThresholdFrame."""
    frame = ThresholdFrame()
    qtbot.addWidget(frame)
    return frame


def test_threshold_frame_initialization(threshold_frame):
    """Test ThresholdFrame initializes correctly."""
    # Assert
    assert threshold_frame.total_signer_input is not None
    assert threshold_frame.required_signer_input is not None
    assert threshold_frame.total_signer_input.text() == '2'
    assert threshold_frame.required_signer_input.text() == '2'


def test_threshold_frame_get_total_signer(threshold_frame):
    """Test get_total_signer returns correct value."""
    # Setup
    threshold_frame.total_signer_input.setText('5')

    # Execute
    result = threshold_frame.get_total_signer()

    # Assert
    assert result == 5


def test_threshold_frame_get_total_signer_default(threshold_frame):
    """Test get_total_signer returns default value."""
    # Execute
    result = threshold_frame.get_total_signer()

    # Assert
    assert result == 2


def test_threshold_frame_get_total_signer_invalid(threshold_frame):
    """Test get_total_signer returns 0 for invalid input."""
    # Setup
    threshold_frame.total_signer_input.setText('invalid')

    # Execute
    result = threshold_frame.get_total_signer()

    # Assert
    assert result == 0


def test_threshold_frame_get_required_signer(threshold_frame):
    """Test get_required_signer returns correct value."""
    # Setup
    threshold_frame.required_signer_input.setText('3')

    # Execute
    result = threshold_frame.get_required_signer()

    # Assert
    assert result == 3


def test_threshold_frame_get_required_signer_default(threshold_frame):
    """Test get_required_signer returns default value."""
    # Execute
    result = threshold_frame.get_required_signer()

    # Assert
    assert result == 2


def test_threshold_frame_get_required_signer_invalid(threshold_frame):
    """Test get_required_signer returns 0 for invalid input."""
    # Setup
    threshold_frame.required_signer_input.setText('invalid')

    # Execute
    result = threshold_frame.get_required_signer()

    # Assert
    assert result == 0


def test_threshold_frame_set_inputs_enabled_true(threshold_frame):
    """Test set_inputs_enabled enables inputs."""
    # Setup
    threshold_frame.set_inputs_enabled(False)

    # Execute
    threshold_frame.set_inputs_enabled(True)

    # Assert
    assert threshold_frame.total_signer_input.isEnabled()
    assert threshold_frame.required_signer_input.isEnabled()


def test_threshold_frame_set_inputs_enabled_false(threshold_frame):
    """Test set_inputs_enabled disables inputs."""
    # Execute
    threshold_frame.set_inputs_enabled(False)

    # Assert
    assert not threshold_frame.total_signer_input.isEnabled()
    assert not threshold_frame.required_signer_input.isEnabled()


def test_threshold_frame_retranslate_ui(threshold_frame):
    """Test retranslate_ui updates all labels."""
    # Setup
    labels = MultisigThresholdLabels(
        info_title='Info Title',
        info_sub='Info Subtitle',
        tot_lbl='Total Signers',
        tot_help='Enter total signers',
        req_lbl='Required Signers',
        req_help='Enter required signers',
    )

    # Execute
    threshold_frame.retranslate_ui(labels)

    # Assert
    assert threshold_frame.info_title.text() == 'Info Title'
    assert threshold_frame.info_sub.text() == 'Info Subtitle'
    assert threshold_frame.tot_lbl.text() == 'Total Signers'
    assert threshold_frame.total_signer_help.text() == 'Enter total signers'
    assert threshold_frame.req_lbl.text() == 'Required Signers'
    assert threshold_frame.required_signer_help.text() == 'Enter required signers'
