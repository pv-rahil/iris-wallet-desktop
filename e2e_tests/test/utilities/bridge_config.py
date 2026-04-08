"""
Utility to update the multisig bridge config.toml file.
Updates cosigner xpubs dynamically based on wallet setup.
Generates biscuit tokens for bridge authentication.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
import tomllib

from e2e_tests.test.utilities.dogtail_config import is_ci_environment


BRIDGE_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'bridge',
    'config.toml',
)

PRIVATE_KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    'private-key-file',
)


def _get_prefixed_private_key() -> str | None:
    """
    Read the private-key-file and ensure it has the correct prefix for biscuit-cli 0.6.0.
    """
    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"ERROR: private-key-file not found at {PRIVATE_KEY_PATH}")
        return None

    with open(PRIVATE_KEY_PATH, encoding='utf-8') as f:
        content = f.read().strip()
        if not content.startswith('ed25519-private/'):
            # If it's just hex, add the prefix back
            return f"ed25519-private/{content}"
        return content


def read_bridge_config() -> dict:
    """
    Read the current bridge config.toml file.

    Returns:
        dict: The config contents.
    """
    if not os.path.exists(BRIDGE_CONFIG_PATH):
        return {}

    with open(BRIDGE_CONFIG_PATH, 'rb') as f:
        return tomllib.load(f)


def update_bridge_config(
    cosigner_xpubs: list[str] | None = None,
    threshold_colored: int | None = None,
    threshold_vanilla: int | None = None,
    root_public_key: str | None = None,
) -> None:
    """
    Update the bridge config.toml file with new values.

    Args:
        cosigner_xpubs: List of cosigner xpubs (colored xpubs).
        threshold_colored: Threshold for colored coins.
        threshold_vanilla: Threshold for vanilla coins.
        root_public_key: Root public key for the multisig.
    """
    config_lines = []

    if cosigner_xpubs is not None:
        xpubs_str = ',\n    '.join(f'"{xpub}"' for xpub in cosigner_xpubs)
        config_lines.append(f'cosigner_xpubs = [\n    {xpubs_str},\n]')

    if threshold_colored is not None:
        config_lines.append(f'threshold_colored = {threshold_colored}')

    if threshold_vanilla is not None:
        config_lines.append(f'threshold_vanilla = {threshold_vanilla}')

    if root_public_key is not None:
        config_lines.append(f'root_public_key = "{root_public_key}"')

    config_lines.append('rgb_lib_version = "0.3"')

    with open(BRIDGE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(config_lines) + '\n')


def reset_bridge_config() -> None:
    """
    Reset the bridge config to default placeholder values.
    Creates the bridge directory and config.toml file if they don't exist.
    """
    # Ensure the bridge directory exists
    bridge_dir = os.path.dirname(BRIDGE_CONFIG_PATH)
    if not os.path.exists(bridge_dir):
        os.makedirs(bridge_dir, exist_ok=True)
        print(f"Created bridge directory at {bridge_dir}")

    default_config = """cosigner_xpubs = [
    "PLACEHOLDER_XPUB_1",
    "PLACEHOLDER_XPUB_2",
]
threshold_colored = 2
threshold_vanilla = 2
root_public_key = "PLACEHOLDER_ROOT_KEY"
rgb_lib_version = "0.3"
"""
    with open(BRIDGE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.write(default_config)


def generate_biscuit_token(colored_xpub: str) -> str | None:
    """
    Generate a biscuit token for a cosigner's colored xpub.

    Args:
        colored_xpub: The cosigner's colored account xpub.

    Returns:
        The generated biscuit token, or None if generation failed.
    """
    key = _get_prefixed_private_key()
    if not key:
        return None

    datalog = f'role("cosigner"); xpub("{colored_xpub}");'

    try:
        cmd = ['biscuit', 'generate', '--private-key', key, '-']
        result = subprocess.run(
            cmd,
            input=datalog,
            capture_output=True,
            text=True,
            check=True,
        )
        token = result.stdout.strip()
        if not token:
            print('ERROR: Biscuit CLI returned empty token output')
            return None
        return token
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to run biscuit CLI: {e.stderr}')
        return None
    except FileNotFoundError:
        print('ERROR: biscuit CLI not found. Please install it.')
        return None
    except Exception as e:
        print(f'ERROR: Token generation exception: {e}')
        return None


def get_bridge_public_key() -> str | None:
    """
    Get the bridge's public key from the private-key-file.

    Returns:
        The public key, or None if extraction failed.
    """
    key = _get_prefixed_private_key()
    if not key:
        return None

    try:
        cmd = [
            'biscuit', 'keypair', '--from-private-key',
            key, '--only-public-key',
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        pubkey_output = result.stdout.strip()
        # Strip 'ed25519/' prefix if present
        if '/' in pubkey_output:
            return pubkey_output.split('/')[-1]
        return pubkey_output
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to get public key: {e.stderr}')
        return None
    except FileNotFoundError:
        print('ERROR: biscuit CLI not found. Please install it.')
        return None


def clean_bridge() -> bool:
    """
    Stop and clean bridge data/config. Does NOT start the bridge.
    Caller must update config and start bridge separately.
    Use this before updating bridge config for load wallet flow.

    Returns:
        True if successful, False otherwise.
    """
    try:
        e2e_tests_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..'),
        )
        bridge_data_dir = os.path.join(e2e_tests_dir, 'bridge')

        print('Stopping rgb-multisig-bridge container...')
        subprocess.run(
            ['docker', 'compose', 'stop', 'rgb-multisig-bridge'],
            cwd=e2e_tests_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Clean bridge data (rgb_multisig_bridge_db, files, logs)
        for subdir in ['rgb_multisig_bridge_db', 'files', 'logs']:
            subdir_path = os.path.join(bridge_data_dir, subdir)
            if os.path.exists(subdir_path):
                print(f'Cleaning bridge data: {subdir_path}')
                shutil.rmtree(subdir_path, ignore_errors=True)

        # Clear bridge config.toml to avoid 'cannot change cosigner' error
        config_path = os.path.join(bridge_data_dir, 'config.toml')
        if os.path.exists(config_path):
            print(f'Cleaning bridge config: {config_path}')
            os.remove(config_path)

        return True
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to clean bridge: {e.stderr}')
        return False
    except Exception as e:
        print(f'ERROR: Unexpected error: {e}')
        return False


def start_bridge_service() -> bool:
    """
    Start only the rgb-multisig-bridge container.
    Should be called after clean_bridge and update_bridge_config.

    Returns:
        True if start successful, False otherwise.
    """
    try:
        e2e_tests_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..'),
        )
        # Start the bridge container
        subprocess.run(
            ['docker', 'compose', 'up', '-d', 'rgb-multisig-bridge'],
            cwd=e2e_tests_dir,
            capture_output=True,
            text=True,

        )

        # Wait for the bridge to be reachable
        print('Waiting for bridge to be ready...')
        for _ in range(30):
            try:
                subprocess.run(
                    [
                        'curl', '-fsS',
                        'http://127.0.0.1:8141/info',
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print('Bridge service started successfully')
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                time.sleep(1)

        print('ERROR: Bridge did not become reachable')
        return False
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to start bridge: {e.stderr}')
        return False
    except Exception as e:
        print(f'ERROR: Unexpected error: {e}')
        return False


def restart_bridge_service() -> bool:
    """
    Restart the rgb-multisig-bridge container to reload config.toml.
    Should be called after updating config.toml with cosigner xpubs.

    Returns:
        True if restart successful, False otherwise.
    """
    try:
        e2e_tests_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..'),
        )
        # Restart the bridge container
        subprocess.run(
            ['docker', 'compose', 'restart', 'rgb-multisig-bridge'],
            cwd=e2e_tests_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Wait for the bridge to be reachable (helps CI and slower machines)
        for _ in range(30):
            try:
                subprocess.run(
                    [
                        'curl', '-fsS',
                        'http://127.0.0.1:8141/info',
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print('Bridge service restarted successfully')
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                time.sleep(1)

        # Diagnostics (best-effort)
        try:
            ps_out = subprocess.run(
                ['docker', 'compose', 'ps'],
                cwd=e2e_tests_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            print(ps_out.stdout)
            logs_out = subprocess.run(
                [
                    'docker', 'compose', 'logs', '--tail',
                    '200', 'rgb-multisig-bridge',
                ],
                cwd=e2e_tests_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            print(logs_out.stdout)
            if logs_out.stderr:
                print(logs_out.stderr)
        except Exception:
            pass

        print(
            'ERROR: Bridge service did not become reachable on http://127.0.0.1:8141/info',
        )
        return False
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to restart bridge service: {e.stderr}')
        return False
    except FileNotFoundError:
        print('ERROR: docker command not found')
        return False


def start_regtest_services() -> bool:
    """
    Start all regtest services using regtest.sh script.
    This starts bitcoind, electrs, proxy, and rgb-multisig-bridge.

    Returns:
        True if start successful, False otherwise.
    """
    try:
        regtest_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'regtest.sh',
        )
        subprocess.run(
            [regtest_path, 'start'],
            capture_output=True,
            text=True,
            check=True,
        )
        if is_ci_environment():
            print('Waiting for bridge to be ready...')
            for _ in range(60):
                try:
                    subprocess.run(
                        [
                            'curl', '-fsS',
                            'http://127.0.0.1:8141/info',
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print('Bridge service started successfully')
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    time.sleep(1)
        print('Regtest services started successfully')
        return True
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to start regtest services: {e.stderr}')
        return False
    except FileNotFoundError:
        print('ERROR: regtest.sh not found')
        return False


def stop_regtest_services() -> bool:
    """
    Stop all regtest services using regtest.sh script.

    Returns:
        True if stop successful, False otherwise.
    """
    try:
        regtest_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'regtest.sh',
        )
        subprocess.run(
            [regtest_path, 'stop'],
            capture_output=True,
            text=True,
            check=True,
        )
        print('Regtest services stopped successfully')
        return True
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Failed to stop regtest services: {e.stderr}')
        return False
    except FileNotFoundError:
        print('ERROR: regtest.sh not found')
        return False
