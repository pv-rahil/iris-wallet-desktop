"""
End-to-End testing script.
"""
from __future__ import annotations

import pytest

from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import OFFLINE_CREATE_HARDWARE
from accessible_constant import OFFLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_CREATE_HARDWARE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_LOAD_HARDWARE
from accessible_constant import ONLINE_LOAD_ON_DEVICE
from accessible_constant import ONLINE_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add wallet variant option to pytest.
    """
    group = parser.getgroup('e2e')
    group.addoption(
        '--wallet-variant',
        action='store',
        help=(
            'Wallet mode key used by tests (e.g., online_create_on_device, '
            'online_create_hardware, offline_create_on_device, offline_create_hardware, '
            'online_load_on_device, offline_load_on_device, online_load_hardware, '
            'offline_load_hardware, online_watch_only).'
        ),
    )


@pytest.fixture(scope='session')
def wallet_variant_name(request) -> str:
    """
    Expose the CLI-provided wallet mode key to tests.
    """
    return request.config.getoption('--wallet-variant')


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip tests based on wallet mode via markers."""
    wallet_mode = item.config.getoption('--wallet-variant')

    # Skip tests marked with @pytest.mark.skip_for_hardware_wallet if running in hardware wallet mode
    if wallet_mode in [ONLINE_CREATE_HARDWARE, ONLINE_LOAD_HARDWARE] and any(
        True for _ in item.iter_markers('skip_for_hardware_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in hardware wallet mode.',
        )
    if wallet_mode in REQUIRE_USB_VARIANTS and any(
        True for _ in item.iter_markers('skip_for_offline_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in offline wallet mode.',
        )
    if wallet_mode in [ONLINE_CREATE_ON_DEVICE, ONLINE_LOAD_ON_DEVICE] and any(
        True for _ in item.iter_markers('skip_for_online_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in online wallet mode.',
        )
    if wallet_mode in [ONLINE_CREATE_HARDWARE, ONLINE_CREATE_ON_DEVICE, OFFLINE_CREATE_HARDWARE, OFFLINE_CREATE_ON_DEVICE] and any(
        True for _ in item.iter_markers('skip_for_create_wallet_variants')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in create wallet variant mode.',
        )
    if wallet_mode in LOAD_WALLET_VARIANT and any(
        True for _ in item.iter_markers('skip_for_load_wallet_variants')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in load wallet variant mode.',
        )
    if wallet_mode in [ONLINE_WATCH_ONLY] and any(
        True for _ in item.iter_markers('skip_for_watch_only')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in watch only mode.',
        )
