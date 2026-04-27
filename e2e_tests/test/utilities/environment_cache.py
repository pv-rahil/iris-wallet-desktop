# pylint: disable=too-many-instance-attributes
"""
Environment cache helper to prevent duplicate application launches.
"""
from __future__ import annotations

from typing import Any

from e2e_tests.test.features.main_features import MainFeatures
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations

# Module-level cache to track running environments
# Key: (num_instances, wallet_variant_name), Value: TestEnvironment instance
_ENVIRONMENT_CACHE: dict[tuple[int, str], Any] = {}


class EnvironmentCache:
    """Helper class to manage environment caching without circular imports."""

    @staticmethod
    def get_or_create(
        multi_instance: bool | int,
        wallet_variant_name: str,
    ) -> tuple[Any | None, tuple[int, str], bool]:
        """
        Get existing cached environment or return None to indicate creation needed.

        Returns: (env, cache_key, is_reused) - env is None if creation needed.
        """
        # Calculate the number of instances needed
        if isinstance(multi_instance, bool):
            num_instances = 2 if multi_instance else 1
        elif isinstance(multi_instance, int):
            num_instances = max(1, min(4, multi_instance))
        else:
            num_instances = 2

        cache_key = (num_instances, wallet_variant_name)

        # Check if we already have a running environment with this exact config
        if cache_key in _ENVIRONMENT_CACHE:
            existing_env = _ENVIRONMENT_CACHE[cache_key]
            if existing_env.first_process and existing_env.first_process.poll() is None:
                print(f"""[SETUP] Reusing existing environment with
                      {num_instances} instances""")
                return existing_env, cache_key, True
            del _ENVIRONMENT_CACHE[cache_key]

        # Check if there's an environment with MORE instances that we can use
        for (cached_num, cached_variant), cached_env in list(
            _ENVIRONMENT_CACHE.items(),
        ):
            if cached_variant == wallet_variant_name and cached_num >= num_instances:
                if cached_env.first_process and cached_env.first_process.poll() is None:
                    print(f"""[SETUP] Reusing existing environment with
                          {cached_num} instances""")
                    return cached_env, cache_key, True
                del _ENVIRONMENT_CACHE[(cached_num, cached_variant)]

        return None, cache_key, False

    @staticmethod
    def cache(cache_key: tuple[int, str], env: Any) -> None:
        """Store environment in cache."""
        _ENVIRONMENT_CACHE[cache_key] = env

    @staticmethod
    def remove(cache_key: tuple[int, str]) -> None:
        """Remove environment from cache."""
        if cache_key in _ENVIRONMENT_CACHE:
            del _ENVIRONMENT_CACHE[cache_key]

    @staticmethod
    def exists(cache_key: tuple[int, str]) -> bool:
        """Check if cache key exists."""
        return cache_key in _ENVIRONMENT_CACHE


class HandlesProxy:
    """A proxy class that provides dynamic access to the TestEnvironment handles."""

    def __init__(self, env: Any) -> None:
        self._env = env

    # Features
    @property
    def first_page_features(self) -> MainFeatures:
        """Returns the first page features."""
        return self._env.first_page_features

    @property
    def second_page_features(self) -> MainFeatures | None:
        """Returns the second page features."""
        return self._env.second_page_features if self._env.num_instances >= 2 else None

    @property
    def third_page_features(self) -> MainFeatures | None:
        """Returns the third page features."""
        return self._env.third_page_features if self._env.num_instances >= 3 else None

    @property
    def fourth_page_features(self) -> MainFeatures | None:
        """Returns the fourth page features."""
        return self._env.fourth_page_features if self._env.num_instances >= 4 else None

    # Objects
    @property
    def first_page_objects(self) -> MainPageObjects:
        """Returns the first page objects."""
        return self._env.first_page_objects

    @property
    def second_page_objects(self) -> MainPageObjects | None:
        """Returns the second page objects."""
        return self._env.second_page_objects if self._env.num_instances >= 2 else None

    @property
    def third_page_objects(self) -> MainPageObjects | None:
        """Returns the third page objects."""
        return self._env.third_page_objects if self._env.num_instances >= 3 else None

    @property
    def fourth_page_objects(self) -> MainPageObjects | None:
        """Returns the fourth page objects."""
        return self._env.fourth_page_objects if self._env.num_instances >= 4 else None

    # Operations
    @property
    def first_page_operations(self) -> BaseOperations:
        """Returns the first page operations."""
        return self._env.first_page_operations

    @property
    def second_page_operations(self) -> BaseOperations | None:
        """Returns the second page operations."""
        return self._env.second_page_operations if self._env.num_instances >= 2 else None

    @property
    def third_page_operations(self) -> BaseOperations | None:
        """Returns the third page operations."""
        return self._env.third_page_operations if self._env.num_instances >= 3 else None

    @property
    def fourth_page_operations(self) -> BaseOperations | None:
        """Returns the fourth page operations."""
        return self._env.fourth_page_operations if self._env.num_instances >= 4 else None
