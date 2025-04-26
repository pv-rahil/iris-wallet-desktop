"""Unit tests for issue asset helper"""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations


def assert_success_page_called(widget, asset_name):
    """Helper function to assert the success page was called with correct parameters."""
    widget._view_model.page_navigation.show_success_page.assert_called_once()

    params = widget._view_model.page_navigation.show_success_page.call_args[0][0]
    assert params.header == 'Issue new ticker'
    assert params.title == 'You’re all set!'
    assert params.description == f"Asset '{
        asset_name
    }' has been issued successfully."
    assert params.button_text == 'Home'
