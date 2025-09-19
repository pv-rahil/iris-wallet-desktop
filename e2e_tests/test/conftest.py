from __future__ import annotations

import pytest


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('e2e')
    group.addoption(
        '--wallet-variant',
        action='store',
        default='online_create_on_device',
        help=(
            'Wallet mode key used by tests (e.g., online_watch_only, online_create_on_device, '
            'online_create_hardware, online_load_on_device, online_load_hardware, '
            'offline_create_on_device, offline_create_hardware, offline_load_on_device, offline_load_hardware).'
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
    if wallet_mode == 'online_create_hardware' and any(
        True for _ in item.iter_markers('skip_for_hardware_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in hardware wallet mode.')
    if wallet_mode in ['offline_create_hardware' ,'offline_create_on_device'] and any(
        True for _ in item.iter_markers('skip_for_offline_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in offline wallet mode.')
    if wallet_mode == 'online_create_on_device' and any(
        True for _ in item.iter_markers('skip_for_online_wallet')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in online wallet mode.')