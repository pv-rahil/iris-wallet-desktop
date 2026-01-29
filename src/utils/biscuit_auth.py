"""
Helper module for Biscuit token generation for RGB functionalities.
"""
from __future__ import annotations

import os
import subprocess

from src.data.repository.setting_repository import SettingRepository
from src.utils.constant import MASTER_XPUB
from src.utils.logging import logger


def generate_and_store_token() -> str:
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

        # 2. Get Master XPUB
        master_xpub = SettingRepository.get_config_value(MASTER_XPUB, None)
        if not master_xpub:
            print('DEBUG: Master XPUB not found in settings.')
            logger.warning(
                'Master XPUB not found in settings. Cannot generate token.',
            )
            return None

        # 3. Locate private-key-file
        # Check current directory and parent directory (pv-gaurang)
        possible_paths = [
            os.path.abspath('private-key-file'),
            os.path.abspath(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.abspath(
                                        # ../../../.. from src/utils/biscuit_auth.py which is root/src/utils -> root
                                        __file__,
                                    ),
                                ),
                            ),
                        ),
                    ), 'private-key-file',
                ),
            ),
            os.path.abspath(
                os.path.join(
                    os.getcwd(), '..', 'private-key-file',
                ),
            ),
        ]

        private_key_path = None
        for path in possible_paths:
            if os.path.exists(path):
                private_key_path = path
                break

        if not private_key_path:
            print(f"DEBUG: private-key-file not found in {possible_paths}")
            logger.warning(
                'private-key-file not found in %s. Cannot generate token.',
                possible_paths,
            )
            return None

        # 4. Run biscuit CLI
        # Command: echo 'owner_xpub("XPUB");' | biscuit generate --private-key-file <path> -
        logger.info('Generating biscuit token for xpub: %s...', master_xpub)

        # Determine executable path - assuming 'biscuit' is in PATH
        binary = 'biscuit'

        # Prepare the datalog authority check/fact
        datalog = f'owner_xpub("{master_xpub}");'

        cmd = [
            binary,
            'generate',
            '--private-key-file', private_key_path,
            '-',
        ]

        # Use input=datalog to pipe string to stdin
        result = subprocess.run(
            cmd, input=datalog, capture_output=True, text=True, check=True,
        )
        token = result.stdout.strip()

        if token:
            # 5. Store token
            SettingRepository.set_bridge_token(token)
            logger.info('Successfully generated and stored biscuit token.')
            return token
        else:
            logger.error('Biscuit generation returned empty output.')
            return None

    except subprocess.CalledProcessError as e:
        logger.error('Failed to run biscuit command: %s', e.stderr)
        return None
    except Exception as e:
        logger.error('Error during biscuit token generation: %s', e)
        return None
