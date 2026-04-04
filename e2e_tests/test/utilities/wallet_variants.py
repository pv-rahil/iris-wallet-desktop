"""Wallet variant utilities."""
from __future__ import annotations

import subprocess
from typing import Tuple

from accessible_constant import NAME_TO_STEPS
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


def handle_hardware_wallet(app_name: str, reset: bool = False) -> subprocess.Popen:
    """Launch the Speculos emulator for a given hardware wallet app."""
    if reset:
        reset_regtest()

    return subprocess.Popen(
        ['speculos', '-m', 'nanosp', f"e2e_tests/ledger_app/{app_name}.elf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
