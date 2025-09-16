from __future__ import annotations

import pytest


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("e2e")
    group.addoption(
        "--wallet-variant",
        action="store",
        default="online_create_on_device",
        help=(
            "Wallet mode key used by tests (e.g., online_watch_only, online_create_on_device, "
            "online_create_hardware, online_load_on_device, online_load_hardware, "
            "offline_create_on_device, offline_create_hardware, offline_load_on_device, offline_load_hardware)."
        ),
    )


@pytest.fixture(scope='session')
def wallet_variant_name(request) -> str:
    """
    Expose the CLI-provided wallet mode key to tests.
    """
    return request.config.getoption('--wallet-variant')
