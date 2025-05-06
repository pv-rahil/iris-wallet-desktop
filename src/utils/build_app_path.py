"""
Provides a globally accessible `app_paths` object that contains all
application-specific filesystem paths, such as logs, cache, config,
and temporary directories. Paths are constructed using the current
network environment and application constants.
"""
from __future__ import annotations

import os
import tempfile

from src.flavour import __network__
from src.model.common_operation_model import AppPathsModel
from src.utils.constant import APP_DIR
from src.utils.constant import APP_NAME
from src.utils.constant import CACHE_FOLDER_NAME
from src.utils.constant import LOG_FOLDER_NAME
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import NODE_DIR
from src.utils.handle_exception import handle_exceptions
from src.utils.local_store import local_store


def build_app_paths(base_path: str) -> AppPathsModel:
    """
    Constructs and returns an AppPathsModel instance containing all relevant
    filesystem paths used by the application.

    Args:
        base_path (str): The base directory for storing application data.

    Returns:
        AppPathsModel: A dataclass object containing structured path information
        for logs, cache, config, and backup/restore directories.
    """
    try:

        app_path = os.path.join(base_path, APP_DIR)
        node_path = os.path.join(base_path, NODE_DIR)

        # These are used only during backup and restore to create a temporary directory
        temp_dir = tempfile.gettempdir()
        app_name_with_network = f"{APP_NAME}_{__network__}"
        iriswallet_temp_folder_path = os.path.join(
            temp_dir, app_name_with_network,
        )

        return AppPathsModel(
            app_path=app_path,
            node_data_path=node_path,
            iriswallet_temp_folder_path=iriswallet_temp_folder_path,
            cache_path=os.path.join(app_path, CACHE_FOLDER_NAME),
            app_logs_path=os.path.join(app_path, LOG_FOLDER_NAME),
            node_logs_path=os.path.join(node_path, LOG_FOLDER_NAME),
            ldk_logs_path=os.path.join(node_path, '.ldk', 'logs', 'logs.txt'),
            pickle_file_path=os.path.join(app_path, 'token.pickle'),
            config_file_path=os.path.join(
                app_path, f"{APP_NAME}-{__network__}.ini",
            ),
            backup_folder_path=os.path.join(
                iriswallet_temp_folder_path, 'backup',
            ),
            restore_folder_path=os.path.join(
                iriswallet_temp_folder_path, 'restore',
            ),
            mnemonic_file_path=os.path.join(app_path, MNEMONIC_KEY),

        )
    except Exception as exc:
        handle_exceptions(exc)
        raise


# Expose app_paths globally
app_paths: AppPathsModel = build_app_paths(local_store.base_path)
