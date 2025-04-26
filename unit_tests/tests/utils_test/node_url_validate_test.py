"""Unit test for node url validation"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import pytest
from PySide6.QtGui import QValidator

from src.utils.node_url_validator import NodeValidator
# Adjust the import path as needed


@pytest.fixture
def validator():
    """Fixture to create a NodeValidator instance."""
    return NodeValidator()


def test_validate_valid_input(validator):
    """Test the validator with a valid node URL."""
    valid_input = '03b79a4bc1ec365524b4fab9a39eb133753646babb5a1da5c4bc94c53110b7795d@localhost:9736'
    result, input_str, pos = validator.validate(valid_input, 0)
    assert result == QValidator.Acceptable, f"Expected QValidator.Acceptable, got {
        result
    } for input '{valid_input}'"
    assert input_str == valid_input
    assert pos == 0


def test_validate_intermediate_input(validator):
    """Test the validator with an empty input string."""
    empty_input = ''
    result, input_str, pos = validator.validate(empty_input, 0)
    assert result == QValidator.Intermediate, f"Expected QValidator.Intermediate, got {
        result
    } for input '{empty_input}'"
    assert input_str == empty_input
    assert pos == 0


def test_validate_invalid_input(validator):
    """Test the validator with invalid node URLs."""
    invalid_inputs = [
        '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef@hostname',
        '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef@hostname:abcd',
        '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef@hostname:1234:extra',
        'invalid_input_string',
    ]

    for invalid_input in invalid_inputs:
        result, input_str, pos = validator.validate(invalid_input, 0)
        assert result == QValidator.Invalid, f"Expected QValidator.Invalid, got {
            result
        } for input '{invalid_input}'"
        assert input_str == invalid_input
        assert pos == 0
