from __future__ import annotations

import subprocess
from e2e_tests.test.utilities.executable_shell_script import reset_regtest

NAME_TO_STEPS: dict[str, tuple[int, int, int, int]] = {
    # Online
    'online_watch_only': (1, 2, 0, 0),
    'online_create_on_device': (1, 1, 1, 1),
    'online_create_hardware': (1, 1, 1, 2),
    'online_load_on_device': (1, 1, 2, 1),
    'online_load_hardware': (1, 1, 2, 2),
    # Offline
    'offline_create_on_device': (2, 1, 1, 0),
    'offline_create_hardware': (2, 1, 2, 0),
    'offline_load_on_device': (2, 2, 1, 0),
    'offline_load_hardware': (2, 2, 2, 0),
}


# Precompute a lenient lookup table allowing both exact names and slug forms.
_LOOKUP: dict[str, tuple[int, int, int, int]] = {}
for canon, steps in NAME_TO_STEPS.items():
    _LOOKUP[canon.lower()] = steps

# Reverse lookup from steps to canonical name
_STEPS_TO_NAME: dict[tuple[int, int, int, int], str] = {
    v: k for k, v in NAME_TO_STEPS.items()}


def resolve_steps(variant_name: str) -> tuple[int, int, int, int]:
    if not variant_name:
        raise ValueError('wallet variant name must be provided')
    key_exact = variant_name.strip().lower()
    if key_exact in _LOOKUP:
        return _LOOKUP[key_exact]
    expected = ', '.join(sorted(NAME_TO_STEPS.keys()))
    raise ValueError(
        f"Unknown wallet variant '{
            variant_name}'. Expected one of: {expected}",
    )


def list_variants() -> None:
    """List all available wallet variants in a CLI-friendly format.

    Prints a header followed by each variant name on its own line, sorted
    alphabetically. Intended for use by list-style commands.
    """
    print('Available wallet variants:\n')
    for name in sorted(NAME_TO_STEPS.keys()):
        print(f"- {name}")


def map_to_load_variant(variant_name: str) -> str:
    """Map the given variant to its corresponding 'load' variant for restore flows.

    Rules:
    - If step3 (create/load) is 1 (create), switch it to 2 (load) and keep other steps
      identical.
    - If step3 is already 2 (load), leave it unchanged.
    - If step3 is 0 (not applicable), return the original variant unchanged.
    """
    s1, s2, s3, s4 = resolve_steps(variant_name)
    if s3 == 0:
        # e.g., online_watch_only has no create/load step
        return variant_name.strip().lower()
    target_steps = (s1, 2, s3, s4)
    mapped = _STEPS_TO_NAME.get(target_steps)
    if not mapped:
        raise ValueError(
            f"No matching 'load' variant found for steps {
                target_steps}. Known: {sorted(NAME_TO_STEPS.keys())}",
        )
    return mapped


def handle_hardware_wallet(app_name: str , reset: bool = False):
    """
    Handle the hardware wallet.
    """
    if reset:
        reset_regtest()
    speculos_process = subprocess.Popen(
        ['speculos', '-m', 'nanosp', f"e2e_tests/ledger_app/{app_name}.elf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    return speculos_process
