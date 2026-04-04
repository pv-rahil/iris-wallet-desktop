"""
Helper module for Biscuit token generation for RGB functionalities.
"""
from __future__ import annotations

import os
import subprocess

from src.data.repository.setting_repository import SettingRepository
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.logging import logger


def _find_private_key_file() -> str | None:
    """Locate private-key-file in possible paths."""
    possible_paths = [
        os.path.abspath('private-key-file'),
        os.path.abspath(
            os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.abspath(__file__),
                            ),
                        ),
                    ),
                ), 'private-key-file',
            ),
        ),
        os.path.abspath(
            os.path.join(os.getcwd(), '..', 'private-key-file'),
        ),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def _generate_token_with_cli(account_xpub_colored: str, private_key_path: str) -> str | None:
    """Generate biscuit token using CLI."""
    logger.info(
        'Generating biscuit token for xpub: %s...',
        account_xpub_colored,
    )

    binary = 'biscuit'
    datalog = f'role("cosigner"); xpub("{account_xpub_colored}");'

    cmd = [binary, 'generate', '--private-key-file', private_key_path, '-']

    try:
        result = subprocess.run(
            cmd, input=datalog, capture_output=True, text=True, check=True,
        )
        token = result.stdout.strip()

        if token:
            SettingRepository.set_bridge_token(token)
            logger.info('Successfully generated and stored biscuit token.')
            return token
        logger.error('Biscuit generation returned empty output.')
        return None
    except subprocess.CalledProcessError as e:
        logger.error('Failed to run biscuit command: %s', e.stderr)
        return None


def generate_and_store_token() -> str | None:
    """
    Checks if a bridge token exists. If not, attempts to generate one using
    the local private-key-file and the wallet's Master XPUB.
    """
    try:
        # 1. Check if token already exists
        existing_token = SettingRepository.get_bridge_token()
        if existing_token:
            print('DEBUG: Bridge token already exists in settings.')
            logger.info('Bridge token already exists in settings.')
            return existing_token

        # 2. Get Colored Account XPUB
        account_xpub_colored = SettingRepository.get_config_value(
            ACCOUNT_XPUB_COLORED, None,
        )
        if not account_xpub_colored:
            print('DEBUG: Colored Account XPUB not found in settings.')
            logger.warning(
                'Colored Account XPUB not found in settings. Cannot generate token.',
            )
            return None

        # 3. Locate private-key-file
        private_key_path = _find_private_key_file()
        if not private_key_path:
            print('DEBUG: private-key-file not found in searched paths')
            logger.warning(
                'private-key-file not found. Cannot generate token.',
            )
            return None

        # 4. Generate and return token
        return _generate_token_with_cli(account_xpub_colored, private_key_path)

    except Exception as e:
        logger.error('Error during biscuit token generation: %s', e)
        return None
