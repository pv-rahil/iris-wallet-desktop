# pylint: disable=consider-using-with
"""Wallet variant utilities."""
from __future__ import annotations

import socket
import subprocess
import time
from typing import Tuple

import requests

from accessible_constant import NAME_TO_STEPS
from e2e_tests.test.utilities.dogtail_config import is_ci_environment
from e2e_tests.test.utilities.executable_shell_script import reset_regtest

Steps = Tuple[int, int, int, int, int]

SPECULOS_API_HOST = '127.0.0.1'
SPECULOS_API_PORT = 5000
SPECULOS_APDU_PORT = 9999

# Lookup tables
name_to_steps: dict[str, Steps] = {
    name.lower(): steps for name, steps in NAME_TO_STEPS.items()
}
steps_to_name: dict[Steps, str] = {
    steps: name for name, steps in NAME_TO_STEPS.items()
}


def resolve_steps(variant_name: str) -> Steps:
    """Convert a variant name into its configuration tuple."""
    if not variant_name:
        raise ValueError('Variant name must be provided')

    key = variant_name.strip().lower()
    if key in name_to_steps:
        return name_to_steps[key]

    expected = ', '.join(sorted(NAME_TO_STEPS.keys()))
    raise ValueError(f"""Unknown wallet variant
    '{variant_name}'
                     . Expected one of: {expected}""")


def list_variants() -> None:
    """Print all available wallet variants."""
    print('Available wallet variants:\n')
    for name in sorted(NAME_TO_STEPS.keys()):
        print(f"- {name}")


def map_to_load_variant(variant_name: str) -> str:
    """Map a variant to its corresponding 'load' variant for restore flows."""
    s1, s2, s3, s4, s5 = resolve_steps(variant_name)

    # For watch-only variants (s3 == 2 and s4 == 0), return as-is
    if s3 == 2 and s4 == 0:
        return variant_name.strip().lower()

    # Map entry_type (s4) from create (1) to load (2)
    target = (s1, s2, s3, 2, s5)
    mapped = steps_to_name.get(target)

    if not mapped:
        expected = ', '.join(sorted(NAME_TO_STEPS.keys()))
        raise ValueError(
            f"No matching 'load' variant found for steps {
                target
            }. Known: {expected}",
        )
    return mapped


def map_load_to_create(variant_name: str) -> str:
    """Map a 'load' variant name to its corresponding 'create' variant name.

    Strategy:
    - Convert variant to steps using resolve_steps.
    - Map entry_type (s4) from load (2) to create (1).
    - Look up the variant name from the adjusted steps.
    """
    s1, s2, s3, _, s5 = resolve_steps(variant_name)

    # Map entry_type (s4) to create (1)
    target = (s1, s2, s3, 1, s5)

    mapped = steps_to_name.get(target)
    if not mapped:
        expected = ', '.join(sorted(NAME_TO_STEPS.keys()))
        raise ValueError(
            f"No matching 'create' variant found for steps {
                target
            }. Known: {expected}",
        )
    return mapped


def _wait_for_speculos_ready(timeout: float = 10.0) -> bool:
    """
    Wait for speculos emulator to be fully ready.

    Checks both the REST API and APDU port to ensure the emulator
    can receive commands before returning.

    Args:
        timeout: Maximum time to wait in seconds.

    Returns:
        True if emulator is ready, False if timeout reached.
    """
    start_time = time.time()
    api_url = f'http://{SPECULOS_API_HOST}:{SPECULOS_API_PORT}'

    while time.time() - start_time < timeout:
        # Check APDU port is listening
        try:
            with socket.create_connection(
                (SPECULOS_API_HOST, SPECULOS_APDU_PORT), timeout=1.0,
            ):
                apdu_ready = True
        except (OSError, ConnectionRefusedError):
            apdu_ready = False

        # Check REST API is responding
        try:
            response = requests.get(f'{api_url}/', timeout=1.0)
            api_ready = response.status_code == 200
        except Exception:
            api_ready = False

        if apdu_ready and api_ready:
            return True

        time.sleep(0.5)

    return False


def handle_hardware_wallet(app_name: str, reset: bool = False):
    """
    Handle hardware wallet setup and teardown.

    Args:
        app_name: Name of the hardware wallet app
        reset: Whether to reset the regtest environment
    """
    if reset and not is_ci_environment():
        reset_regtest()

    proc = subprocess.Popen(
        ['speculos', '-m', 'nanosp', f"e2e_tests/ledger_app/{app_name}.elf"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for emulator to be fully ready to receive APDU commands
    if not _wait_for_speculos_ready(timeout=10.0):
        proc.terminate()
        raise RuntimeError('Speculos emulator failed to start within timeout')

    if not is_ci_environment():
        # Move Speculos window to background
        subprocess.run(
            [
                'wmctrl', '-r', 'Speculos',
                '-b', 'add,below',
            ], check=False,
        )

    return proc
