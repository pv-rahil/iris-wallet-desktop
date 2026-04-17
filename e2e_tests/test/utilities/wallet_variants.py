# pylint: disable=consider-using-with
"""Wallet variant utilities."""
from __future__ import annotations

import subprocess
import time
from typing import Tuple

from accessible_constant import NAME_TO_STEPS
from e2e_tests.test.utilities.dogtail_config import is_ci_environment
from e2e_tests.test.utilities.executable_shell_script import reset_regtest

Steps = Tuple[int, int, int, int, int]

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


def handle_hardware_wallet(app_name: str, reset: bool = False):
    """
    Handle hardware wallet setup and teardown.

    Args:
        app_name: Name of the hardware wallet app
        reset: Whether to reset the regtest environment
    """
    if reset:
        reset_regtest()

    elf_path = f"e2e_tests/ledger_app/{app_name}.elf"
    print(f"[HW_WALLET] Starting speculos with: {elf_path}")

    # Build speculos command
    speculos_cmd = ['speculos', '-m', 'nanosp', '--display', 'qt', elf_path]

    proc = subprocess.Popen(
        speculos_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for speculos to initialize
    time.sleep(3)

    # Check if speculos is still running
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        print(f"[HW_WALLET] Speculos FAILED to start!")
        print(f"[HW_WALLET] Exit code: {proc.returncode}")
        print(f"[HW_WALLET] stdout: {stdout.decode() if stdout else 'empty'}")
        print(f"[HW_WALLET] stderr: {stderr.decode() if stderr else 'empty'}")
        raise RuntimeError(f"Speculos failed to start: {stderr.decode() if stderr else 'unknown error'}")

    print(f"[HW_WALLET] Speculos started successfully with PID {proc.pid}")

    # List all windows to verify speculos window exists
    try:
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, check=False)
        print(f"[HW_WALLET] Current windows:\n{result.stdout}")
    except Exception as e:
        print(f"[HW_WALLET] Could not list windows: {e}")

    if not is_ci_environment():
        # Move Speculos window to background
        subprocess.run(
            [
                'wmctrl', '-r', 'Speculos',
                '-b', 'add,below',
            ], check=False,
        )

    return proc
