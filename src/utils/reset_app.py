"""Module to clean up the iriswallet directory by deleting all its contents. Use with caution as this will permanently remove all wallet data."""
from __future__ import annotations

import argparse
import os
import shutil
import sys

from src.utils.build_app_path import app_paths
from src.utils.constant import APP_NAME
from src.utils.local_store import local_store
from src.utils.logging import logger


def get_app_directory(app_name_suffix: str | None):
    """
    Determines the correct app data directory based on the provided app name suffix.

    Args:
        app_name_suffix (str | None): The app name suffix, if provided.

    Returns:
        str: The directory path of the app data.
    """
    base_dir = os.path.dirname(local_store.get_path())

    if app_name_suffix:
        base_dir = os.path.join(
            os.path.dirname(
                base_dir,
            ), f"{APP_NAME}_{app_name_suffix}",
        )

    return base_dir  # Default path if no app name is provided


def delete_app_data(directory_path: str, network=None):
    """
    Delete all files and directories in the specified directory.
    If a network is specified, only delete the network-specific configuration file, cache directory.

    Args:
        directory_path (str): The path to the directory from which files and directories will be deleted.
        network (str, optional): The network type ('testnet', 'regtest', or 'mainnet'). If None, deletes everything.

    Raises:
        Exception: If an error occurs during the deletion process.
    """
    try:
        # Check if the directory exists
        if not os.path.exists(directory_path):
            print(f'Directory does not exist: {directory_path}')
            return

        if network and network not in ('testnet', 'regtest', 'mainnet'):
            print(
                "Invalid network type. Choose either 'testnet', 'regtest', or 'mainnet'.",
            )
            return

        # Remove specific or all files and directories
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)

            if network:

                config_file_path = app_paths.config_file_path
                cache_directory_path = app_paths.cache_path

                # Delete only network-specific files and directories
                paths_to_delete = [
                    config_file_path,
                    cache_directory_path,
                ]

                for path in paths_to_delete:
                    if path and os.path.exists(path):
                        delete_path(path)

            else:
                # Delete everything
                delete_path(item_path)
    except Exception as e:
        logger.error('An error occurred while deleting files: %s', e)


def delete_path(path):
    """Helper function to delete a file or directory."""
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        logger.info('Deleted file: %s', path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
        logger.info('Deleted directory: %s', path)


def main():
    """
    Main function to clean up the iriswallet directory.

    It retrieves the path to the iriswallet directory and then deletes all its contents.

    Note:
        This method is intended for development and testing purposes only. Use with caution as it will
        permanently delete data in the specified directory.
    """
    parser = argparse.ArgumentParser(
        description='Reset app data for Iris Wallet.',
    )
    parser.add_argument(
        '--app-name',
        required=False,
        help='Specify the app name if multiple instances were created.',
    )
    args = parser.parse_args()
    # Path to the iriswallet directory
    iriswallet_path = get_app_directory(args.app_name)
    print(f'Directory to clean: {iriswallet_path}')

    # Prompt user for confirmation
    confirm = input(
        'Warning: This will permanently delete all data in the iriswallet directory. Proceed? (y/n): ',
    ).strip().lower()

    if confirm != 'y':
        print('Operation cancelled. No data was deleted.')
        sys.exit(1)

    try:
        # Delete all files and directories in the iriswallet path
        delete_app_data(iriswallet_path)

        print('Cleanup complete.')
    except Exception as e:
        print(f'An error occurred: {e}')


if __name__ == '__main__':
    main()
