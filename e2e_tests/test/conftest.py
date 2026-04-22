# pylint: disable=unused-argument
"""
End-to-End testing script.
"""
from __future__ import annotations

import os
import time
from collections import OrderedDict

import pytest

from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import MULTISIG_VARIANTS
from accessible_constant import OFFLINE_CREATE_HARDWARE
from accessible_constant import OFFLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_CREATE_HARDWARE
from accessible_constant import ONLINE_CREATE_ON_DEVICE
from accessible_constant import ONLINE_LOAD_HARDWARE
from accessible_constant import ONLINE_LOAD_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_HARDWARE
from accessible_constant import ONLINE_MULTISIG_LOAD_HARDWARE
from accessible_constant import ONLINE_MULTISIG_LOAD_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_ON_DEVICE
from accessible_constant import ONLINE_MULTISIG_WATCH_ONLY
from accessible_constant import ONLINE_WATCH_ONLY
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import SINGLE_SIG_VARIANTS
from e2e_tests.test.utilities.atspi_helpers import refresh_atspi_tree

# Timing constants
CI_STABILIZATION_DELAY = 2.0
LOCAL_STABILIZATION_DELAY = 0.5


def _is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv('CI', '').lower() in ('true', '1', 'yes')


def _reset_operations_state(test_environment):
    """
    Reset state in all BaseOperations instances.
    Clears debounce tracking, circuit breakers, and window switch flags.
    """
    try:
        if hasattr(test_environment, 'first_page_operations'):
            test_environment.first_page_operations.reset_state()

        if hasattr(test_environment, 'num_instances') and test_environment.num_instances >= 2 and hasattr(test_environment, 'second_page_operations'):
            test_environment.second_page_operations.reset_state()
        if hasattr(test_environment, 'num_instances') and test_environment.num_instances >= 3 and hasattr(test_environment, 'third_page_operations'):
            test_environment.third_page_operations.reset_state()
    except Exception:
        pass


def _stabilize_ui(delay_seconds):
    """
    Add stabilization delay for UI and AT-SPI to settle.
    Longer delays in CI to account for slower accessibility tree synchronization.
    """
    time.sleep(delay_seconds)


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
            'offline_load_hardware, online_watch_only, online_multisig_on_device, '
            'online_multisig_hardware, online_multisig_watch_only, '
            'offline_multisig_on_device, offline_multisig_hardware, '
            'online_multisig_load_on_device, online_multisig_load_hardware, '
            'offline_multisig_load_on_device, offline_multisig_load_hardware).'
        ),
    )


@pytest.fixture(scope='session')
def wallet_variant_name(request) -> str:
    """
    Expose the CLI-provided wallet mode key to tests.
    """
    return request.config.getoption('--wallet-variant')


def pytest_collection_modifyitems(config, items):
    """
    Shard test collection for parallel CI execution.

    When SHARD_ID and TOTAL_SHARDS env vars are set, splits tests across shards.
    Groups tests by file to keep dependent tests together.
    """
    shard_id = int(os.getenv('SHARD_ID', '1'))
    total_shards = int(os.getenv('TOTAL_SHARDS', '1'))

    if total_shards <= 1:
        return

    # Group tests by their source file
    file_groups = OrderedDict()
    for item in items:
        # Get the file path from the test item
        file_path = item.location[0] if item.location else str(item.fspath)
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(item)

    # Get list of files and distribute them across shards
    files = list(file_groups.keys())
    selected_files = [
        f for i, f in enumerate(files)
        if i % total_shards == (shard_id - 1)
    ]

    # Collect all tests from selected files
    selected = []
    for f in selected_files:
        selected.extend(file_groups[f])

    print(f"""[SHARD] {len(selected)} tests from {len(selected_files)} files
          selected for shard {shard_id}/{total_shards}""")
    items[:] = selected


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip tests based on wallet mode via markers."""
    wallet_mode = item.config.getoption('--wallet-variant')

    # Skip tests marked with @pytest.mark.skip_for_hardware_wallet if running in hardware wallet mode
    if wallet_mode in [
        ONLINE_CREATE_HARDWARE, ONLINE_LOAD_HARDWARE, ONLINE_MULTISIG_HARDWARE,
        ONLINE_MULTISIG_LOAD_HARDWARE,
    ] and any(
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
    if wallet_mode in [ONLINE_CREATE_ON_DEVICE, ONLINE_LOAD_ON_DEVICE, ONLINE_MULTISIG_ON_DEVICE, ONLINE_MULTISIG_LOAD_ON_DEVICE] and any(
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
    if wallet_mode in [ONLINE_WATCH_ONLY, ONLINE_MULTISIG_WATCH_ONLY] and any(
        True for _ in item.iter_markers('skip_for_watch_only')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in watch only mode.',
        )
    if wallet_mode in MULTISIG_VARIANTS and any(
        True for _ in item.iter_markers('skip_for_multisig')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in multisig wallet mode.',
        )
    if wallet_mode in SINGLE_SIG_VARIANTS and any(
        True for _ in item.iter_markers('skip_for_single_sig')
    ):
        pytest.skip(
            'Skipping test because it is not applicable in single-sig wallet mode.',
        )


@pytest.fixture(autouse=True)
def cleanup_between_tests(request):
    """
    Automatic cleanup fixture that runs between each test function.

    This fixture ensures clean state when using module-scoped test_environment
    by:
    - Refreshing AT-SPI tree BEFORE each test to clear stale caches
    - Yielding before the test runs
    - Performing cleanup after the test completes
    - Refreshing AT-SPI tree to clear stale caches
    - Resetting all BaseOperations state
    - Adding stabilization delays in CI
    - Full AT-SPI reset for all tests
    """
    test_name = request.node.name
    print(f'\n[Starting] Test started: {test_name}')

    # Before test: refresh AT-SPI tree to clear stale element caches
    # This is critical when tests run sequentially with shared app instances
    try:
        refresh_atspi_tree()
        delay = CI_STABILIZATION_DELAY if _is_ci_environment() else LOCAL_STABILIZATION_DELAY
        _stabilize_ui(delay)
    except Exception as e:
        print(f'[SETUP] Warning: Pre-test refresh encountered an error: {e}')

    yield

    # After test: perform cleanup
    print(f'\n[CLEANUP] Test completed: {test_name}')

    try:
        # Full AT-SPI reset for all tests
        print('[CLEANUP] Running full AT-SPI reset')
        refresh_atspi_tree()

        # Get the test_environment fixture if it exists
        if 'test_environment' in request.fixturenames:
            test_env = request.getfixturevalue('test_environment')
            # Reset state in BaseOperations instances
            _reset_operations_state(test_env)

        # Stabilization delay (longer in CI)
        delay = CI_STABILIZATION_DELAY if _is_ci_environment() else LOCAL_STABILIZATION_DELAY
        _stabilize_ui(delay)

        print('[CLEANUP] Complete')
    except Exception as e:
        # Don't fail tests if cleanup has issues
        print(f'[CLEANUP] Warning: Cleanup encountered an error: {e}')
