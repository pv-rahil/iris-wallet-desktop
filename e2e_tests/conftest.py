# pylint: disable=redefined-outer-name
"""
Custom pytest configuration for wallet mode testing
"""
from __future__ import annotations

import subprocess

import allure
import pytest

from accessible_constant import DEFAULT_WALLET_MODES
from src.model.enums.enums_model import WalletType


def pytest_addoption(parser):
    """
    Add custom command-line options for pytest to select wallet mode.

    :param parser: pytest parser object
    """
    parser.addoption(
        '--wallet-mode',
        action='store',
        choices=DEFAULT_WALLET_MODES,
        help="Set wallet mode to 'embedded' or 'remote'. If not provided, tests run for both modes.",
    )


def pytest_generate_tests(metafunc):
    """
    Dynamically run tests for both wallet modes if --wallet-mode is not provided.

    :param metafunc: pytest metafunction object
    """
    if 'wallet_mode' in metafunc.fixturenames:
        wallet_mode = metafunc.config.getoption('wallet_mode')
        if wallet_mode:
            # Run for the specified mode
            metafunc.parametrize('wallet_mode', [wallet_mode])
        else:
            # Run for both modes
            metafunc.parametrize('wallet_mode', DEFAULT_WALLET_MODES)


@pytest.fixture(scope='session')
def wallet_mode(request):
    """
    Fixture to provide the selected wallet mode.

    :param request: Pytest request object
    :return: selected wallet mode
    """
    return request.param


def pytest_runtest_setup(item):
    """Skip tests based on wallet mode."""
    wallet_mode = item.config.getoption('--wallet-mode')

    # Skip tests marked with @pytest.mark.skip_for_embedded if running in embedded mode
    if wallet_mode == WalletType.EMBEDDED_TYPE_WALLET.value and any(mark.name == 'skip_for_embedded' for mark in item.own_markers):
        pytest.skip(
            'Skipping test because it is not applicable in embedded mode.',
        )

    # Skip tests marked with @pytest.mark.skip_for_remote if running in remote mode
    if wallet_mode == WalletType.REMOTE_TYPE_WALLET.value and any(mark.name == 'skip_for_remote' for mark in item.own_markers):
        pytest.skip(
            'Skipping test because it is not applicable in remote mode.',
        )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """
    Capture screenshot on test failure and attach to Allure report.
    """
    outcome = yield
    report = outcome.get_result()

    # Only capture screenshot on test failure during the call phase
    if report.when == 'call' and report.failed:
        try:
            # Capture screenshot using scrot (X11 screenshot tool)
            screenshot_path = f'/tmp/screenshot_{item.name}.png'
            subprocess.run(
                ['scrot', screenshot_path],
                check=True,
                capture_output=True,
            )

            # Attach screenshot to Allure report
            with open(screenshot_path, 'rb') as screenshot_file:
                allure.attach(
                    screenshot_file.read(),
                    name=f'Screenshot on failure: {item.name}',
                    attachment_type=allure.attachment_type.PNG,
                )
        except Exception as e:
            print(f'Failed to capture screenshot: {e}')
