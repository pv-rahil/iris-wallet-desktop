"""
Multisig setup coordinator for parallel wallet creation.
Handles synchronization between two applications during multisig wallet setup.
"""
from __future__ import annotations

import os
import threading

from e2e_tests.test.utilities.bridge_config import generate_biscuit_token
from e2e_tests.test.utilities.bridge_config import get_bridge_public_key
from e2e_tests.test.utilities.bridge_config import restart_bridge_service
from e2e_tests.test.utilities.bridge_config import reset_bridge_config
from e2e_tests.test.utilities.bridge_config import stop_regtest_services
from e2e_tests.test.utilities.bridge_config import update_bridge_config


class MultisigSetupCoordinator:
    """
    Coordinates multisig wallet setup between two parallel applications.
    Ensures both wallets reach synchronization points together before proceeding.
    """

    _instance: MultisigSetupCoordinator | None = None
    _lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> MultisigSetupCoordinator:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cosigner_strings: dict[str, str] = {}
        self._colored_xpubs: dict[str, str] = {}
        self._biscuit_tokens: dict[str, str] = {}
        self._applications_registered: set[str] = set()
        self._registration_lock = threading.Lock()
        self._threshold: int = 2
        self._bridge_updated: bool = False
        self.reset()

    def reset(self):
        """Reset all synchronization state for a new multisig setup."""
        self._cosigner_strings.clear()
        self._colored_xpubs.clear()
        self._biscuit_tokens.clear()
        self._applications_registered.clear()
        self._threshold = 2
        self._bridge_updated = False
        if str(os.environ.get('CI', '')).lower() != 'true':
            stop_regtest_services()
        reset_bridge_config()

    def set_threshold(self, threshold: int):
        """Set the threshold for the multisig setup."""
        self._threshold = threshold

    def get_threshold(self) -> int:
        """Get the threshold for the multisig setup."""
        return self._threshold

    def is_bridge_updated(self) -> bool:
        """Check if the bridge configuration has been updated."""
        return self._bridge_updated

    def register_application(self, application: str) -> int:
        """
        Register an application for multisig setup.

        Args:
            application: Application name (FIRST_APPLICATION or SECOND_APPLICATION)

        Returns:
            int: The index of the registered application (0 or 1)
        """
        with self._registration_lock:
            if application not in self._applications_registered:
                self._applications_registered.add(application)
            return len(self._applications_registered) - 1

    def store_cosigner_string(self, application: str, cosigner_string: str):
        """
        Store a cosigner string for an application.

        Args:
            application: Application name
            cosigner_string: The cosigner string to store
        """
        self._cosigner_strings[application] = cosigner_string

    def store_colored_xpub(self, application: str, colored_xpub: str):
        """
        Store a colored xpub for an application and generate its biscuit token.

        Args:
            application: Application name
            colored_xpub: The colored xpub to store
        """
        self._colored_xpubs[application] = colored_xpub
        token = generate_biscuit_token(colored_xpub)
        if token:
            self._biscuit_tokens[application] = token

    def get_other_cosigner_string(self, application: str) -> str | None:
        """
        Get the cosigner string from the other application.

        Args:
            application: Current application name

        Returns:
            The other application's cosigner string, or None if not available
        """
        for app, string in self._cosigner_strings.items():
            if app != application:
                return string
        return None

    def get_other_colored_xpub(self, application: str) -> str | None:
        """
        Get the colored xpub from the other application.

        Args:
            application: Current application name

        Returns:
            The other application's colored xpub, or None if not available
        """
        for app, xpub in self._colored_xpubs.items():
            if app != application:
                return xpub
        return None

    def get_biscuit_token(self, application: str) -> str | None:
        """
        Get the biscuit token for an application.

        Args:
            application: Application name

        Returns:
            The biscuit token, or None if not generated.
        """
        return self._biscuit_tokens.get(application)

    def is_coordinator_active(self) -> bool:
        """Check if coordinator has active registrations."""
        return len(self._applications_registered) >= 2

    def get_colored_xpubs(self) -> dict[str, str]:
        """
        Get all stored colored xpubs.

        Returns:
            Dictionary mapping application names to their colored xpubs.
        """
        return self._colored_xpubs.copy()

    def update_bridge_config(self, threshold: int = 2):
        """
        Update the bridge config.toml with collected xpubs and root public key.
        Then start regtest services to load the config.

        Args:
            threshold: The threshold for the multisig (default 2).
        """
        xpubs = list(self._colored_xpubs.values())
        root_public_key = get_bridge_public_key()
        print(f"""[SYNC] Updating bridge config with xpubs:
              {xpubs} and root public key: {root_public_key}""")
        if len(xpubs) >= 2:
            update_bridge_config(
                cosigner_xpubs=xpubs,
                threshold_colored=threshold,
                threshold_vanilla=threshold,
                root_public_key=root_public_key,
            )
            restart_bridge_service()
            self._bridge_updated = True


def get_multisig_coordinator() -> MultisigSetupCoordinator:
    """Get the singleton multisig coordinator instance."""
    return MultisigSetupCoordinator()
