"""Unit test for TermConditionWidget."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument, protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QScrollBar

from src.utils.constant import PRIVACY_POLICY_URL
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_term_condition import TermConditionWidget


@pytest.fixture
def term_condition_widget(qtbot):
    """Fixture to create and return an instance of TermConditionWidget."""
    mock_navigation = MagicMock()

    # Create the view model without mocking it initially
    view_model = MainViewModel(mock_navigation)

    # Create and set up the terms view model mock
    mock_terms_view_model = MagicMock()
    mock_terms_view_model.on_accept_click = MagicMock()
    mock_terms_view_model.on_decline_click = MagicMock()

    # Set the mock terms view model
    view_model.terms_view_model = mock_terms_view_model

    widget = TermConditionWidget(view_model)
    qtbot.addWidget(widget)
    return widget


def test_init(term_condition_widget: TermConditionWidget):
    """Test the initialization of TermConditionWidget."""
    # Test initial state
    assert term_condition_widget.accept_btn.isEnabled() is False
    assert term_condition_widget.tnc_text_desc.isReadOnly() is True
    assert term_condition_widget.tnc_text_desc.openExternalLinks() is True


def test_retranslate_ui(term_condition_widget: TermConditionWidget):
    """Test the retranslation of UI elements in TermConditionWidget."""
    term_condition_widget.retranslate_ui()

    # Test text translations
    assert term_condition_widget.tnc_label_text.text() == 'terms_and_conditions'
    assert term_condition_widget.wallet_logo_tnc.logo_text.text() == 'iris_wallet'
    assert term_condition_widget.decline_btn.text() == 'decline'
    assert term_condition_widget.accept_btn.text() == 'accept'


def test_setup_ui_connection(term_condition_widget: TermConditionWidget, qtbot):
    """Test UI connections are properly set up."""
    # The buttons should be properly connected from widget initialization

    # Enable accept button since it's disabled by default
    term_condition_widget.accept_btn.setEnabled(True)

    # Trigger button clicks
    qtbot.mouseClick(
        term_condition_widget.accept_btn,
        Qt.MouseButton.LeftButton,
    )
    qtbot.mouseClick(
        term_condition_widget.decline_btn,
        Qt.MouseButton.LeftButton,
    )

    # Verify view model methods were called
    term_condition_widget._view_model.terms_view_model.on_accept_click.assert_called_once()
    term_condition_widget._view_model.terms_view_model.on_decline_click.assert_called_once()


def test_check_scroll_completion(term_condition_widget: TermConditionWidget, qtbot):
    """Test the scroll completion behavior."""
    # Create mock scrollbar
    mock_scrollbar = MagicMock(spec=QScrollBar)
    mock_scrollbar.value.return_value = 100
    mock_scrollbar.maximum.return_value = 100

    # Replace the actual scrollbar with mock
    with patch.object(term_condition_widget.tnc_text_desc, 'verticalScrollBar', return_value=mock_scrollbar):
        # Trigger scroll completion
        term_condition_widget.check_scroll_completion()

        # Verify accept button is enabled
        assert term_condition_widget.accept_btn.isEnabled() is True

    # Test when not scrolled to bottom
    mock_scrollbar.value.return_value = 50
    with patch.object(term_condition_widget.tnc_text_desc, 'verticalScrollBar', return_value=mock_scrollbar):
        # Reset accept button state
        term_condition_widget.accept_btn.setEnabled(False)

        # Trigger scroll check
        term_condition_widget.check_scroll_completion()

        # Verify accept button remains disabled
        assert term_condition_widget.accept_btn.isEnabled() is False


def test_load_terms_conditions(term_condition_widget: TermConditionWidget):
    """Test loading and formatting of terms and conditions text."""
    # Mock the translations
    with patch.object(QCoreApplication, 'translate') as mock_translate:
        # Set up mock returns for different translation calls
        def translate_side_effect(context, text, *args):
            translations = {
                'privacy_policy_tnc': 'Privacy Policy',
                'terms_and_conditions_content': 'Sample terms content with {0}',
            }
            return translations.get(text, text)

        mock_translate.side_effect = translate_side_effect

        # Call the method
        term_condition_widget.load_terms_conditions()

        # Verify privacy policy link is properly formatted
        content = term_condition_widget.tnc_text_desc.toHtml()

        # Check for essential elements
        assert PRIVACY_POLICY_URL in content  # Privacy policy URL
        assert 'color:#01a781' in content     # Link color
        assert 'Privacy Policy' in content     # Link text
        assert 'text-decoration: underline' in content  # Link underline
        assert 'Sample terms content' in content  # Terms content

        # Verify word wrap mode
        assert term_condition_widget.tnc_text_desc.wordWrapMode(
        ) == QTextOption.WrapAtWordBoundaryOrAnywhere


@pytest.mark.parametrize(
    'scroll_value,maximum,expected_enabled',
    [
        (100, 100, True),   # Scrolled to bottom
        (50, 100, False),   # Halfway scrolled
        (0, 100, False),    # Top of scroll
        (0, 0, True),       # No scroll needed
    ],
)
def test_scroll_scenarios(term_condition_widget: TermConditionWidget, scroll_value, maximum, expected_enabled):
    """Test various scroll scenarios and their effect on the accept button."""
    mock_scrollbar = MagicMock(spec=QScrollBar)
    mock_scrollbar.value.return_value = scroll_value
    mock_scrollbar.maximum.return_value = maximum

    with patch.object(term_condition_widget.tnc_text_desc, 'verticalScrollBar', return_value=mock_scrollbar):
        term_condition_widget.accept_btn.setEnabled(False)
        term_condition_widget.check_scroll_completion()
        assert term_condition_widget.accept_btn.isEnabled() is expected_enabled
