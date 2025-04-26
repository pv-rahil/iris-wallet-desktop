"""Mocked function of helpers of main asset page"""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_get_offline_asset_ticker(mocker):
    """Mocked get offline asset ticker function"""
    def _mock_get_offline_asset_ticker(value):
        return mocker.patch(
            'src.data.service.helpers.main_asset_page_helper.get_offline_asset_ticker',
            return_value=value,
        )

    return _mock_get_offline_asset_ticker


@pytest.fixture
def mock_get_asset_name(mocker):
    """Mocked get asset name function"""
    def _mock_get_asset_name(value):
        return mocker.patch(
            'src.data.service.helpers.main_asset_page_helper.get_asset_name',
            return_value=value,
        )

    return _mock_get_asset_name


@pytest.fixture
def mock_convert_digest_to_hex(mocker):
    """Mocked get asset name function"""
    def _mock_convert_digest_to_hex(value):
        return mocker.patch(
            'src.data.service.helpers.main_asset_page_helper.convert_digest_to_hex',
            return_value=value,
        )

    return _mock_convert_digest_to_hex
