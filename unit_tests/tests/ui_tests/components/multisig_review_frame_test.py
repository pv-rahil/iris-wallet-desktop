"""Unit tests for multisig_review_frame."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

import pytest

from src.views.components.multisig_review_frame import DetailField
from src.views.components.multisig_review_frame import ReviewFrame


@pytest.fixture
def review_frame(qtbot):
    """Fixture for ReviewFrame."""
    frame = ReviewFrame()
    qtbot.addWidget(frame)
    return frame


def test_review_frame_initialization(review_frame):
    """Test ReviewFrame initializes correctly."""
    # Assert
    assert review_frame.isHidden()


def test_review_frame_clear_fields(review_frame):
    """Test clear_fields clears all field values."""
    # Setup
    review_frame.fp_value_widget.setText('fingerprint')
    review_frame.keychain_value_widget.setText('keychain')
    review_frame.path_value_widget.setText('path')
    review_frame.xpub_vanilla_value_widget.setText('vanilla_xpub')
    review_frame.xpub_colored_value_widget.setText('colored_xpub')
    review_frame.cosigner_string_value_widget.setText('cosigner_string')

    # Execute
    review_frame.clear_fields()

    # Assert
    assert review_frame.fp_value_widget.text() == ''
    assert review_frame.keychain_value_widget.text() == ''
    assert review_frame.path_value_widget.text() == ''
    assert review_frame.xpub_vanilla_value_widget.text() == ''
    assert review_frame.xpub_colored_value_widget.text() == ''
    assert review_frame.cosigner_string_value_widget.text() == ''


def test_review_frame_populate(review_frame):
    """Test populate sets all field values."""
    # Setup
    data = {
        'master_fingerprint': 'fp123',
        'keychain': 'kc456',
        'derivation_path': 'm/44h/0h/0h',
        'account_xpub_vanilla': 'xpub_vanilla',
        'account_xpub_colored': 'xpub_colored',
        'cosigner_string': 'cosigner_str',
    }

    # Execute
    review_frame.populate(data)

    # Assert
    assert review_frame.fp_value_widget.text() == 'fp123'
    assert review_frame.keychain_value_widget.text() == 'kc456'
    assert review_frame.path_value_widget.text() == 'm/44h/0h/0h'
    assert review_frame.xpub_vanilla_value_widget.text() == 'xpub_vanilla'
    assert review_frame.xpub_colored_value_widget.text() == 'xpub_colored'
    assert review_frame.cosigner_string_value_widget.text() == 'cosigner_str'


def test_review_frame_populate_with_missing_data(review_frame):
    """Test populate handles missing data gracefully."""
    # Setup
    data = {
        'master_fingerprint': 'fp123',
    }

    # Execute
    review_frame.populate(data)

    # Assert
    assert review_frame.fp_value_widget.text() == 'fp123'
    assert review_frame.keychain_value_widget.text() == ''
    assert review_frame.path_value_widget.text() == ''
    assert review_frame.xpub_vanilla_value_widget.text() == ''
    assert review_frame.xpub_colored_value_widget.text() == ''
    assert review_frame.cosigner_string_value_widget.text() == ''


def test_detail_field_create_without_copy_button():
    """Test DetailField.create without copy button."""
    # Execute
    _, inp, copy_btn = DetailField.create(
        title='Test Field:',
        placeholder='Enter value',
        show_copy_btn=False,
    )

    # Assert
    assert copy_btn is None
    assert inp is not None


def test_detail_field_create_with_copy_button():
    """Test DetailField.create with copy button."""
    # Execute
    _, _, copy_btn = DetailField.create(
        title='Test Field:',
        placeholder='Enter value',
        show_copy_btn=True,
    )

    # Assert
    assert copy_btn is not None
    assert copy_btn.objectName() == 'copy_button'


def test_detail_field_create_with_info_text():
    """Test DetailField.create with info text."""
    # Execute
    _, inp, _ = DetailField.create(
        title='Test Field:',
        placeholder='Enter value',
        info_text='This is helpful info',
    )

    # Assert
    assert inp is not None


def test_detail_field_create_full_width():
    """Test DetailField.create with full_width=True."""
    # Execute
    _, inp, _ = DetailField.create(
        title='Test Field:',
        placeholder='Enter value',
        full_width=True,
    )

    # Assert
    assert inp is not None
