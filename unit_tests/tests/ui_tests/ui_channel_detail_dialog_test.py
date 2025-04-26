"""Unit test for ChannelDetailDialogBox UI."""
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QDialog

from src.views.ui_channel_detail_dialog import ChannelDetailDialogBox


@pytest.fixture
def channel_detail_dialog_page_navigation():
    """Fixture to create a mocked page navigation object."""
    return MagicMock()


@pytest.fixture
def channel_detail_dialog_param():
    """Fixture to create a mocked parameter object."""
    mock_param = MagicMock()
    mock_param.pub_key = 'mock_pub_key'
    mock_param.bitcoin_local_balance = 5000000  # 5,000,000 msat
    mock_param.bitcoin_remote_balance = 3000000  # 3,000,000 msat
    mock_param.channel_id = 'mock_channel_id'
    return mock_param


@pytest.fixture
def channel_detail_dialog(qtbot, channel_detail_dialog_page_navigation, channel_detail_dialog_param):
    """Fixture to create a ChannelDetailDialogBox instance."""
    dialog = ChannelDetailDialogBox(
        channel_detail_dialog_page_navigation, channel_detail_dialog_param,
    )
    qtbot.addWidget(dialog)
    return dialog


def test_initial_state(channel_detail_dialog):
    """Test the initial state of the ChannelDetailDialogBox."""
    assert isinstance(channel_detail_dialog, QDialog)
    assert channel_detail_dialog.pub_key == 'mock_pub_key'
    assert channel_detail_dialog.bitcoin_local_balance == 5000000
    assert channel_detail_dialog.bitcoin_remote_balance == 3000000


def test_retranslate_ui(channel_detail_dialog):
    """Test the retranslate_ui method."""
    channel_detail_dialog.retranslate_ui()
    assert channel_detail_dialog.channel_detail_title_label.text() == 'channel_details'
    assert channel_detail_dialog.btc_local_balance_label.text() == 'bitcoin_local_balance'
    assert channel_detail_dialog.btc_remote_balance_label.text() == 'bitcoin_remote_balance'
    assert channel_detail_dialog.pub_key_label.text() == 'peer_pubkey'
    assert channel_detail_dialog.close_channel_button.text() == 'close_channel'


def test_close_channel(channel_detail_dialog):
    """Test the close_channel method."""
    with patch('src.views.ui_channel_detail_dialog.CloseChannelDialog') as mock_close_channel_dialog:
        mock_dialog_instance = mock_close_channel_dialog.return_value
        mock_dialog_instance.exec = MagicMock()

        channel_detail_dialog.close_channel()

        mock_close_channel_dialog.assert_called_once_with(
            page_navigate=channel_detail_dialog._view_model.page_navigation,
            pub_key=channel_detail_dialog.pub_key,
            channel_id=channel_detail_dialog.channel_id,
            parent=channel_detail_dialog.parent_widget,
        )
        mock_dialog_instance.exec.assert_called_once()
