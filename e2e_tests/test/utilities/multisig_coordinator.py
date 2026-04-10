"""
Multisig setup coordinator for parallel wallet creation.
Handles synchronization between two applications during multisig wallet setup.
"""
from __future__ import annotations

import os
import threading

from e2e_tests.test.utilities.bridge_config import generate_biscuit_token
from e2e_tests.test.utilities.bridge_config import get_bridge_public_key
from e2e_tests.test.utilities.bridge_config import reset_bridge_config
from e2e_tests.test.utilities.bridge_config import start_regtest_services
from e2e_tests.test.utilities.bridge_config import stop_regtest_services
from e2e_tests.test.utilities.bridge_config import update_bridge_config


def _is_ci() -> bool:
    """Check if running in CI environment."""
    return os.environ.get('CI', '').lower() == 'true'


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
        # Load wallet credentials storage
        self._load_credentials: dict[str, dict] = {}
        self.reset()

    def reset(self):
        """Reset all synchronization state for a new multisig setup."""
        self._cosigner_strings.clear()
        self._colored_xpubs.clear()
        self._biscuit_tokens.clear()
        self._applications_registered.clear()
        self._threshold = 2
        self._bridge_updated = False
        self._load_credentials.clear()
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

    def get_all_other_cosigner_strings(self, application: str) -> list[tuple[str, str]]:
        """
        Get all cosigner strings from other applications.
        Used for watch-only wallets that need to import multiple cosigners.

        Args:
            application: Current application name

        Returns:
            List of tuples (app_name, cosigner_string) for all other applications
        """
        return [
            (app, string)
            for app, string in self._cosigner_strings.items()
            if app != application
        ]

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

    def store_load_credentials(
        self,
        application: str,
        mnemonic: str | None = None,
        password: str | None = None,
        xpub_vanilla: str | None = None,
        xpub_colored: str | None = None,
        fingerprint: str | None = None,
    ):
        """
        Store load wallet credentials for an application.

        Args:
            application: Application name.
            mnemonic: Mnemonic phrase (for software wallets).
            password: Wallet password.
            xpub_vanilla: Vanilla xpub (for hardware wallets).
            xpub_colored: Colored xpub (for hardware wallets).
            fingerprint: Master fingerprint (for hardware wallets).
        """
        self._load_credentials[application] = {
            'mnemonic': mnemonic,
            'password': password,
            'xpub_vanilla': xpub_vanilla,
            'xpub_colored': xpub_colored,
            'fingerprint': fingerprint,
        }

    def get_load_credentials(self, application: str) -> dict | None:
        """
        Get stored load wallet credentials for an application.

        Args:
            application: Application name.

        Returns:
            Dictionary with credentials or None if not stored.
        """
        return self._load_credentials.get(application)

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

            start_regtest_services()
            self._bridge_updated = True


def get_multisig_coordinator() -> MultisigSetupCoordinator:
    """Get the singleton multisig coordinator instance."""
    return MultisigSetupCoordinator()
