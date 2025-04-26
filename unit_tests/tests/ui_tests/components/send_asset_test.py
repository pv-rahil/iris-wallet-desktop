"""Unit test for Send asset component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.send_asset import SendAssetWidget


@pytest.fixture
def send_asset_widget(qtbot):
    """Fixture to create and provide SendAssetWidget for testing."""
    _app = QApplication.instance() or QApplication([])

    # Create a mock for MainViewModel
    view_model = MagicMock(spec=MainViewModel)

    # Add a mock for estimate_fee_view_model with required signals
    estimate_fee_view_model = MagicMock()
    estimate_fee_view_model.fee_estimation_success = MagicMock()
    estimate_fee_view_model.fee_estimation_error = MagicMock()
    estimate_fee_view_model.get_fee_rate = MagicMock()
    view_model.estimate_fee_view_model = estimate_fee_view_model

    # Create the widget
    widget = SendAssetWidget(view_model=view_model, address='test_address')
    qtbot.addWidget(widget)
    return widget


def test_initial_ui_state(send_asset_widget):
    """Test the initial state of the SendAssetWidget UI."""
    assert send_asset_widget.asset_address_value.text() == ''
    assert send_asset_widget.asset_address_value.placeholderText() == 'test_address'
    assert send_asset_widget.asset_amount_value.text() == ''
    assert send_asset_widget.asset_amount_validation.isHidden()
    assert send_asset_widget.spendable_balance_validation.isHidden()
    assert send_asset_widget.estimate_fee_error_label.isHidden()


def test_retranslate_ui(send_asset_widget):
    """Test the retranslate_ui method sets the correct text."""
    send_asset_widget.retranslate_ui()
    assert send_asset_widget.asset_title.text() == 'send'
    assert send_asset_widget.balance_value.text() == 'total_balance'
    assert send_asset_widget.pay_to_label.text() == 'pay_to'
    assert send_asset_widget.fee_rate_label.text() == 'fee_rate'
    assert send_asset_widget.txn_label.text() == 'transaction_fees'


def test_enable_fee_rate_line_edit(send_asset_widget, qtbot):
    """Test the enable_fee_rate_line_edit method."""
    send_asset_widget.enable_fee_rate_line_edit()
    assert not send_asset_widget.fee_rate_value.isReadOnly()


def test_disable_fee_rate_line_edit(send_asset_widget):
    """Test the disable_fee_rate_line_edit method."""
    send_asset_widget.disable_fee_rate_line_edit('fast_checkBox')
    assert send_asset_widget.fee_rate_value.isReadOnly()
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate.assert_called_once_with(
        'fast_checkBox',
    )


def test_validate_amount_signal(send_asset_widget, qtbot):
    """Test that the validate_amount signal is connected."""
    with qtbot.waitSignal(send_asset_widget.asset_amount_value.textChanged):
        send_asset_widget.asset_amount_value.setText('100')


def test_show_fee_estimation_error(send_asset_widget):
    """Test fee estimation error handling."""
    send_asset_widget.show_fee_estimation_error()
    assert not send_asset_widget.estimate_fee_error_label.isHidden()
    expected_title = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'estimation_error', None,
    )
    assert send_asset_widget.estimate_fee_error_label.text() == expected_title


def test_set_fee_rate(send_asset_widget):
    """Test setting the fee rate."""
    send_asset_widget.set_fee_rate(25)
    assert float(send_asset_widget.fee_rate_value.text()) == 25


def test_validate_amount_valid(send_asset_widget, qtbot):
    """Test the validate_amount method with a valid pay amount."""
    # Set the spendable balance to a known value
    send_asset_widget.asset_balance_label_spendable.setText('1000')

    # Set a valid pay amount (less than or equal to spendable amount)
    send_asset_widget.asset_amount_value.setText('500')

    # Call the validation method
    send_asset_widget.validate_amount()

    # Check if the validation passed (error message should be hidden)
    assert send_asset_widget.asset_amount_validation.isHidden()
    assert send_asset_widget.send_btn.isEnabled()


def test_validate_amount_invalid(send_asset_widget, qtbot):
    """Test the validate_amount method with an invalid pay amount (greater than spendable)."""
    # Set the spendable balance to a known value
    send_asset_widget.asset_balance_label_spendable.setText('1000')

    # Set an invalid pay amount (greater than spendable amount)
    send_asset_widget.asset_amount_value.setText('1500')

    # Call the validation method
    send_asset_widget.validate_amount()

    # Check if the error message is shown (validation failed)
    assert not send_asset_widget.asset_amount_validation.isHidden()
    assert not send_asset_widget.send_btn.isEnabled()


def test_validate_amount_edge_case(send_asset_widget, qtbot):
    """Test edge case where pay amount equals the spendable balance."""
    # Set the spendable balance to a known value
    send_asset_widget.asset_balance_label_spendable.setText('1000')

    # Set the pay amount equal to the spendable amount
    send_asset_widget.asset_amount_value.setText('1000')

    # Call the validation method
    send_asset_widget.validate_amount()

    # Check if the validation passed (error message should be hidden)
    assert send_asset_widget.asset_amount_validation.isHidden()
    assert send_asset_widget.send_btn.isEnabled()


def test_fee_estimation_signals(send_asset_widget, qtbot):
    """Test that fee estimation signals are connected and triggered."""
    with qtbot.waitSignal(send_asset_widget.asset_amount_value.textChanged):
        send_asset_widget.asset_amount_value.setText('150')
    with qtbot.waitSignal(send_asset_widget.asset_address_value.textChanged):
        send_asset_widget.asset_address_value.setText('new_address')


def test_get_transaction_fee_rate_slow(send_asset_widget):
    """Test get_transaction_fee_rate with 'slow' transaction fee speed."""
    # Mock the view model's estimate_fee_view_model
    send_asset_widget._view_model = MagicMock()
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate = MagicMock()

    # Simulate selecting the 'slow' checkbox
    send_asset_widget.slow_checkbox.setChecked(True)

    # Call the method to test
    send_asset_widget.get_transaction_fee_rate('slow_checkBox')

    # Assert that the get_fee_rate method was called with the correct argument
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate.assert_called_with(
        'slow_checkBox',
    )


def test_get_transaction_fee_rate_medium(send_asset_widget):
    """Test get_transaction_fee_rate with 'medium' transaction fee speed."""
    # Mock the view model's estimate_fee_view_model
    send_asset_widget._view_model = MagicMock()
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate = MagicMock()

    # Simulate selecting the 'medium' checkbox
    send_asset_widget.medium_checkbox.setChecked(True)

    # Call the method to test
    send_asset_widget.get_transaction_fee_rate('medium_checkBox')

    # Assert that the get_fee_rate method was called with the correct argument
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate.assert_called_with(
        'medium_checkBox',
    )


def test_get_transaction_fee_rate_fast(send_asset_widget, qtbot):
    """Test get_transaction_fee_rate with 'fast' transaction fee speed."""
    # Mock the view model's estimate_fee_view_model
    send_asset_widget._view_model = MagicMock()
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate = MagicMock()

    # Ensure the 'fast' checkbox is initialized and select it
    send_asset_widget.fast_checkbox.setChecked(True)

    # Trigger the UI update and the method call
    qtbot.mouseClick(send_asset_widget.fast_checkbox, Qt.LeftButton)

    # Call the method to test
    send_asset_widget.get_transaction_fee_rate('fast_checkBox')

    # Assert that the get_fee_rate method was called with the correct argument
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate.assert_called_with(
        'fast_checkBox',
    )


def test_get_transaction_fee_rate_no_checkbox_selected(send_asset_widget):
    """Test get_transaction_fee_rate with no transaction fee speed selected."""
    # Mock the view model's estimate_fee_view_model
    send_asset_widget._view_model = MagicMock()
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate = MagicMock()

    # Call the method with no checkbox selected
    send_asset_widget.get_transaction_fee_rate('slow')

    # Assert that the get_fee_rate method was not called, as no checkbox was selected
    send_asset_widget._view_model.estimate_fee_view_model.get_fee_rate.assert_not_called()
