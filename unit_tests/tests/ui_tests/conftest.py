# pylint: disable=missing-function-docstring
"""
Shared fixtures for UI tests.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_wallet_session(mocker):
    """
    Fixture to mock WalletDataService.get_session with empty PSBT list.

    Returns:
        MagicMock: The mocked session object.
    """
    svc = MagicMock()
    svc.list_psbt.return_value = []
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session',
        return_value=svc,
    )
    return svc
