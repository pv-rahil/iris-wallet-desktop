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


def serve_allure_result():
    """Serves the Allure report for a specific results directory."""
    try:
        with subprocess.Popen(['allure', 'serve', 'allure-results']) as process:
            process.wait()
    except KeyboardInterrupt:
        print('\nTerminating Allure server...')
        process.send_signal(signal.SIGINT)
        process.wait()


def single_test():
    """Runs a single test with optional force build."""
    if len(sys.argv) < 2:
        print('Usage: single-test <test-file> [force-build]')
        sys.exit(1)

    test_file = sys.argv[1]
    force_build = False

    # Parse optional arguments
    for arg in sys.argv[2:]:
        if arg.lower() == 'force-build':
            force_build = True
        else:
            print(f"Error: Unrecognized argument '{arg}'")
            sys.exit(1)

    if force_build:
        print('Forcing application build before running tests...')
        run_e2e(['--force-build'])

    run_e2e([test_file])


def e2e_test():
    """Runs all E2E tests with '--all' and optional force build."""
    if 'all' not in sys.argv:
        print("Error: The 'all' argument is required for e2e tests.")
        sys.exit(1)

    extra_args = ['--all']
    force_build = False

    # Parse optional arguments
    for arg in sys.argv[1:]:
        if arg.lower() == 'force-build':
            force_build = True
        elif arg.lower() != 'all':
            print(f"Error: Unrecognized argument '{arg}'")
            sys.exit(1)

    if force_build:
        print('Forcing application build before running tests...')
        run_e2e(['--force-build'])

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
