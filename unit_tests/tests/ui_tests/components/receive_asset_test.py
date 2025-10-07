"""Unit test for Receive asset component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument, too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QImage

from src.model.common_operation_model import ReceiveAssetModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.receive_asset import ReceiveAssetWidget


@pytest.fixture
def receive_asset_widget(qtbot):
    """Fixture to create and return an instance of ReceiveAssetWidget."""
    view_model = MagicMock(spec=MainViewModel)
    params = ReceiveAssetModel(
        page_name='mock_page_name',
        address_info='mock_address_info',
        psbt=None,
        is_signed=None,
        close_button_navigation=None,
    )
    widget = ReceiveAssetWidget(view_model, params)
    qtbot.addWidget(widget)
    return widget


def test_retranslate_ui(receive_asset_widget: ReceiveAssetWidget):
    """Test the retranslation of UI elements in ReceiveAssetWidget."""
    receive_asset_widget.retranslate_ui()

    assert receive_asset_widget.address_label.text() == 'address'
    assert receive_asset_widget.asset_title.text() == 'receive'
    # additional init/retranslate assertions
    assert receive_asset_widget.wallet_address_description_text.text() == 'mock_address_info'
    assert receive_asset_widget.receive_asset_close_button.text() == ''
    assert receive_asset_widget.label.text() == ''


def test_update_qr_and_address(receive_asset_widget: ReceiveAssetWidget):
    """Test the update qr and address of UI ReceiveAssetWidget."""
    mock_address = 'mock_address'
    receive_asset_widget.update_qr_and_address(mock_address)

    assert receive_asset_widget.receiver_address.text() == mock_address


def _make_psbt_widget(page_name: str, is_signed: bool | None = False) -> tuple[ReceiveAssetWidget, MagicMock]:
    """Create a `ReceiveAssetWidget` configured with PSBT context and return it with its view model."""
    view_model = MagicMock(spec=MainViewModel)
    # attach page_navigation with expected methods
    view_model.page_navigation = MagicMock()
    params = ReceiveAssetModel(
        page_name=page_name,
        address_info='mock_info_key',
        psbt='psbt_payload',
        is_signed=is_signed,
        close_button_navigation=MagicMock(name='close_nav'),
    )
    return ReceiveAssetWidget(view_model, params), view_model


def test_retranslate_ui_with_psbt_unsigned_sets_labels(qtbot):
    """When PSBT is unsigned, retranslate_ui sets 'unsigned_transaction' and 'psbt' labels."""
    widget, _ = _make_psbt_widget(page_name='send_bitcoin', is_signed=False)
    qtbot.addWidget(widget)
    # when psbt and unsigned
    widget.retranslate_ui()
    assert widget.asset_title.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'unsigned_transaction', None,
    )
    assert widget.address_label.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt', None,
    )


def test_retranslate_ui_with_psbt_signed_sets_labels(qtbot):
    """When PSBT is signed, retranslate_ui sets 'signed_transaction' label."""
    widget, _ = _make_psbt_widget(page_name='send_bitcoin', is_signed=True)
    qtbot.addWidget(widget)
    widget.retranslate_ui()
    assert widget.asset_title.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'signed_transaction', None,
    )


def test_close_button_routing_send_bitcoin_calls_bitcoin_page(qtbot):
    """Close button should route to bitcoin page when page_name is 'send_bitcoin'."""
    widget, vm = _make_psbt_widget(page_name='send_bitcoin')
    qtbot.addWidget(widget)
    # Ensure clicking triggers expected navigation
    widget.receive_asset_close_button.click()
    vm.page_navigation.bitcoin_page.assert_called_once()


def test_close_button_routing_nia_calls_fungibles_page(qtbot):
    """Close button should route to fungibles page for NIA page."""
    widget, vm = _make_psbt_widget(page_name='NIA page')
    qtbot.addWidget(widget)
    widget.receive_asset_close_button.click()
    vm.page_navigation.fungibles_asset_page.assert_called_once()


def test_close_button_routing_receive_cfa_calls_provided_navigation(qtbot):
    """Close button should call provided navigation for 'Receive CFA page'."""
    widget, _ = _make_psbt_widget(page_name='Receive CFA page')
    qtbot.addWidget(widget)
    widget.receive_asset_close_button.click()
    # close_button_navigation is a MagicMock provided via params
    widget.close_button_navigation.assert_called_once()


def test_close_button_routing_else_calls_collectibles_page(qtbot):
    """Close button should route to collectibles page for other page names."""
    widget, vm = _make_psbt_widget(page_name='some-other')
    qtbot.addWidget(widget)
    widget.receive_asset_close_button.click()
    vm.page_navigation.collectibles_asset_page.assert_called_once()


def test_update_qr_and_address_psbt_with_match_prefixes_text(qtbot, monkeypatch):
    """When a matching PSBT is found, prefix the label with 'psbt:<purpose>:' text."""
    widget, _ = _make_psbt_widget(page_name='send_bitcoin')
    qtbot.addWidget(widget)

    # Patch QR generator to avoid heavy work
    def fake_qr(_):
        return QImage(10, 10, QImage.Format_RGB32)

    monkeypatch.setattr(
        'src.views.components.receive_asset.set_qr_code', fake_qr,
    )

    # Mock wallet service returning a match with a purpose
    class FakeService:
        """Fake service class."""

        def list_psbt(self, signed: bool):
            """List PSBT."""
            if signed:
                return [{'psbt': 'abc', 'purpose': 'spend'}]
            return [{'psbt': 'psbt_payload', 'purpose': 'receive'}]

    monkeypatch.setattr(
        'src.data.service.wallet_data_service.WalletDataService.get_session',
        staticmethod(FakeService),
    )

    widget.update_qr_and_address('psbt_payload')
    assert widget.receiver_address.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt:receive:psbt_payload', None,
    )


def test_update_qr_and_address_psbt_no_service_uses_raw_text(qtbot, monkeypatch):
    """If no wallet service is available, keep raw PSBT text in label."""
    widget, _ = _make_psbt_widget(page_name='send_bitcoin')
    qtbot.addWidget(widget)

    monkeypatch.setattr(
        'src.data.service.wallet_data_service.WalletDataService.get_session',
        staticmethod(lambda: None),
    )
    monkeypatch.setattr(
        'src.views.components.receive_asset.set_qr_code',
        lambda _: QImage(10, 10, QImage.Format_RGB32),
    )

    widget.update_qr_and_address('raw_psbt')
    assert widget.receiver_address.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'raw_psbt', None,
    )


def test_update_qr_and_address_psbt_with_no_match_keeps_raw(qtbot, monkeypatch):
    """If no matching PSBT exists, keep the raw text unchanged."""
    widget, _ = _make_psbt_widget(page_name='send_bitcoin')
    qtbot.addWidget(widget)

    # No matching psbt in either list
    class FakeService:
        """Fake service class."""

        def list_psbt(self, signed: bool):
            """List PSBT."""
            return [{'psbt': 'other', 'purpose': 'spend'}]

    monkeypatch.setattr(
        'src.data.service.wallet_data_service.WalletDataService.get_session',
        staticmethod(FakeService),
    )
    monkeypatch.setattr(
        'src.views.components.receive_asset.set_qr_code',
        lambda _: QImage(10, 10, QImage.Format_RGB32),
    )

    widget.update_qr_and_address('psbt_payload')
    # Should remain unchanged
    assert widget.receiver_address.text() == QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_payload', None,
    )
