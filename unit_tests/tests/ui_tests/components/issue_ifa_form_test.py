"""Unit tests for issue_ifa_form."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

import pytest

from src.views.components.issue_ifa_form import IssueIFAForm


@pytest.fixture
def ifa_form(qtbot):
    """Fixture for IssueIFAForm."""
    form = IssueIFAForm()
    qtbot.addWidget(form)
    return form


def test_ifa_form_initialization(ifa_form):
    """Test IssueIFAForm initializes correctly."""
    # Assert
    assert ifa_form.ticker_input is not None
    assert ifa_form.name_input is not None
    assert ifa_form.total_supply_input is not None
    assert ifa_form.issue_amount_input is not None
    assert ifa_form.fee_rate_input is not None
    assert ifa_form.error_label.isHidden()


def test_ifa_form_show_error(ifa_form):
    """Test show_error displays error message."""
    # Execute
    ifa_form.show_error('Test error message')

    # Assert
    assert not ifa_form.error_label.isHidden()
    assert ifa_form.error_label.text() == 'Test error message'


def test_ifa_form_hide_error(ifa_form):
    """Test hide_error hides error message."""
    # Setup
    ifa_form.show_error('Test error')

    # Execute
    ifa_form.hide_error()

    # Assert
    assert ifa_form.error_label.isHidden()


def test_ifa_form_clear_error(ifa_form):
    """Test clear_error clears and hides error message."""
    # Setup
    ifa_form.show_error('Test error')

    # Execute
    ifa_form.clear_error()

    # Assert
    assert ifa_form.error_label.text() == ''
    assert ifa_form.error_label.isHidden()


def test_ifa_form_configure_secondary_issuance(ifa_form):
    """Test configure_secondary_issuance sets up form correctly."""
    # Execute
    ifa_form.configure_secondary_issuance('Test Asset', 'asset_id_123')

    # Assert
    assert ifa_form.name_input.text() == 'Test Asset'
    assert ifa_form.ticker_input.text() == 'asset_id_123'
    assert ifa_form.ticker_input.isReadOnly()
    assert ifa_form.name_input.isReadOnly()
    assert ifa_form.total_supply_title_widget.isHidden()
    assert ifa_form.total_supply_input.isHidden()


def test_ifa_form_configure_primary_issuance(ifa_form):
    """Test configure_primary_issuance resets form correctly."""
    # Setup
    ifa_form.ticker_input.setText('TEST')
    ifa_form.name_input.setText('Test Asset')
    ifa_form.issue_amount_input.setText('100')

    # Execute
    ifa_form.configure_primary_issuance()

    # Assert
    assert ifa_form.ticker_input.text() == ''
    assert ifa_form.name_input.text() == ''
    assert ifa_form.issue_amount_input.text() == ''
    assert ifa_form.fee_rate_label.isHidden()
    assert ifa_form.fee_rate_input.isHidden()


def test_ifa_form_get_ticker(ifa_form):
    """Test get_ticker returns uppercase ticker."""
    # Setup
    ifa_form.ticker_input.setText('test')

    # Execute
    result = ifa_form.get_ticker()

    # Assert
    assert result == 'TEST'


def test_ifa_form_get_name(ifa_form):
    """Test get_name returns name text."""
    # Setup
    ifa_form.name_input.setText('Test Asset Name')

    # Execute
    result = ifa_form.get_name()

    # Assert
    assert result == 'Test Asset Name'


def test_ifa_form_get_total_supply(ifa_form):
    """Test get_total_supply returns total supply text."""
    # Setup
    ifa_form.total_supply_input.setText('1000000')

    # Execute
    result = ifa_form.get_total_supply()

    # Assert
    assert result == '1000000'


def test_ifa_form_get_issue_amount(ifa_form):
    """Test get_issue_amount returns issue amount text."""
    # Setup
    ifa_form.issue_amount_input.setText('500')

    # Execute
    result = ifa_form.get_issue_amount()

    # Assert
    assert result == '500'


def test_ifa_form_get_fee_rate(ifa_form):
    """Test get_fee_rate returns fee rate text."""
    # Setup
    ifa_form.fee_rate_input.setText('5')

    # Execute
    result = ifa_form.get_fee_rate()

    # Assert
    assert result == '5'


def test_ifa_form_default_fee_rate(qtbot):
    """Test IssueIFAForm with custom default fee rate."""
    # Execute
    form = IssueIFAForm(default_fee_rate=10)
    qtbot.addWidget(form)

    # Assert
    assert form.fee_rate_input.text() == '10'
