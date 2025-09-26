"""
End-to-End testing script.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys

E2E_SCRIPT = './run_e2e_tests.sh'
SPEC_DIR = os.path.join(os.path.dirname(__file__), 'test', 'spec')


def run_e2e(extra_args=None):
    """Runs the e2e.sh script with optional arguments."""
    cmd = ['bash', E2E_SCRIPT]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True)


def serve_allure_result(variant: str | None = None):
    """
    Serve Allure report(s).

    How to use via CLI (pyproject `allure-result`):
    - `allure-result`                    -> auto-detect and serve each variant under allure-results/
    - `allure-result online_create_on_device` -> serve allure-results/online_create_on_device
    - `allure-result list`               -> list available variant result folders

    Behavior:
    - If `variant` is provided (or a positional arg is passed) and `allure-results/<variant>` exists, serve that directory.
    - Else, if subdirectories exist under `allure-results/`, serve each sequentially.
    - Else, fall back to serving the root `allure-results/` directory.
    """
    base_dir = 'allure-results'
    try:
        # Accept variant from positional CLI arg when invoked as console script
        if variant is None and len(sys.argv) > 1:
            candidate = sys.argv[1].strip()
            if candidate:
                if candidate.lower() in {'list', '--list', '-l'}:
                    if not os.path.isdir(base_dir):
                        print('No allure-results directory found.')
                        return
                    print('Available allure result variants:')
                    for name in sorted(os.listdir(base_dir)):
                        if os.path.isdir(os.path.join(base_dir, name)):
                            print(f"- {name}")
                    return
                variant = candidate

        # If a specific variant is requested, try to serve that
        if variant:
            target = os.path.join(base_dir, variant)
            if os.path.isdir(target):
                with subprocess.Popen(['allure', 'serve', target]) as process:
                    process.wait()
                return

        # Auto-detect per-variant subdirectories
        if os.path.isdir(base_dir):
            subdirs = [
                os.path.join(base_dir, name)
                for name in sorted(os.listdir(base_dir))
                if os.path.isdir(os.path.join(base_dir, name))
            ]

            if subdirs:
                for path in subdirs:
                    print(f"Serving Allure results: {path}")
                    with subprocess.Popen(['allure', 'serve', path]) as process:
                        process.wait()
                return

        # Fallback: serve the root directory (legacy behavior)
        with subprocess.Popen(['allure', 'serve', base_dir]) as process:
            process.wait()
    except KeyboardInterrupt:
        print('\nTerminating Allure server...')
        process.send_signal(signal.SIGINT)
        process.wait()


def single_test():
    """Runs a single test with optional force build."""
    if len(sys.argv) < 2:
        print(
            'Usage: single-test <test-file> [force-build] [--wallet-variant <mode-name-or-slug>]',
        )
        sys.exit(1)

    test_file = sys.argv[1]
    force_build = False
    wallet_variant = None

    # Parse optional arguments
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        arg = args[i]
        if isinstance(arg, str) and arg.lower() == 'force-build':
            force_build = True
            i += 1
            continue
        if arg == '--wallet-variant':
            if i + 1 >= len(args):
                print('Error: --wallet-variant requires a value')
                sys.exit(1)
            wallet_variant = args[i + 1]
            i += 2
            continue
        print(f"Error: Unrecognized argument '{arg}'")
        sys.exit(1)

    if force_build:
        print('Forcing application build before running tests...')
        run_e2e(['--force-build'])

    forward = [test_file]
    if wallet_variant:
        forward.extend(['--wallet-variant', wallet_variant])
    run_e2e(forward)


def e2e_test():
    """Runs all E2E tests with '--all' and optional force build."""
    if 'all' not in sys.argv:
        print("Error: The 'all' argument is required for e2e tests.")
        sys.exit(1)

    extra_args = ['--all']
    force_build = False
    wallet_variant = None

    # Parse optional arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if isinstance(arg, str) and arg.lower() == 'all':
            i += 1
            continue
        if isinstance(arg, str) and arg.lower() == 'force-build':
            force_build = True
            i += 1
            continue
        if arg == '--wallet-variant':
            if i + 1 >= len(args):
                print('Error: --wallet-variant requires a value')
                sys.exit(1)
            wallet_variant = args[i + 1]
            i += 2
            continue
        print(f"Error: Unrecognized argument '{arg}'")
        sys.exit(1)

    if force_build:
        print('Forcing application build before running tests...')
        run_e2e(['--force-build'])

    if wallet_variant:
        extra_args.extend(['--wallet-variant', wallet_variant])
    run_e2e(extra_args)


def run_regtest(extra_args=None):
    """Runs the regtest script with optional arguments."""
    cmd = [
        'bash', '-c',
        'COMPOSE_FILE=compose.yaml ./e2e_tests/regtest.sh start',
    ]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True)


def list_tests():
    """Lists all test files in the spec directory."""
    if not os.path.isdir(SPEC_DIR):
        print(f"Spec directory '{SPEC_DIR}' does not exist.")
        sys.exit(1)

    print('Available test specs:\n')
    for filename in sorted(os.listdir(SPEC_DIR)):
        if filename.endswith('.py'):
            print(f"- {filename}")
