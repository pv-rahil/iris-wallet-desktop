"""
Dogtail configuration module for optimizing AT-SPI performance in CI environments.

This module configures dogtail's search behavior, timeouts, and retry logic to handle
slow AT-SPI responses, especially in CI environments where accessibility services
may be slower to respond.
"""
from __future__ import annotations

import os
import time

from dogtail import config
from dogtail.tree import root


def is_ci_environment():
    """
    Detect if running in a CI environment.

    Returns:
        bool: True if running in CI, False otherwise.
    """
    return os.getenv('CI', '').lower() in ('true', '1', 'yes')


def configure_dogtail():
    """
    Configure dogtail with optimized settings for CI environments.

    This function sets up dogtail's configuration to handle slow AT-SPI responses
    by adjusting search timeouts, retry intervals, and action delays.
    """
    # Detect environment
    in_ci = is_ci_environment()

    # Get timeout from environment or use defaults
    search_timeout = int(
        os.getenv('DOGTAIL_SEARCH_TIMEOUT', '90' if in_ci else '60'),
    )
    search_backoff = float(
        os.getenv('DOGTAIL_SEARCH_BACKOFF', '1.5' if in_ci else '1.0'),
    )

    # Configure search behavior
    # searchBackoffDuration: Time to wait between search attempts (in seconds)
    config.config.searchBackoffDuration = search_backoff

    # searchCutoffCount: Maximum number of search attempts before giving up
    # In CI, we want more attempts with longer backoff
    config.config.searchCutoffCount = 60 if in_ci else 40

    # defaultDelay: Delay before performing actions (in seconds)
    # Slightly longer in CI to ensure UI is ready
    config.config.defaultDelay = 1.5 if in_ci else 0.3

    # actionDelay: Delay after performing actions (in seconds)
    # Longer in CI to allow UI to update
    config.config.actionDelay = 1.5 if in_ci else 0.5

    # typingDelay: Delay between keystrokes when typing
    config.config.typingDelay = 0.1 if in_ci else 0.05

    # # Enable debug logging in CI for troubleshooting
    # if in_ci:
    #     config.config.logDebugToFile = False  # Avoid excessive log files
    #     config.config.logDebugToStdOut = True  # Enable stdout logging for CI visibility
    #     print('[DOGTAIL CONFIG] Debug logging enabled for CI')
    # else:
    #     config.config.logDebugToStdOut = False  # Keep local logs clean

    print(f"[DOGTAIL CONFIG] Environment: {'CI' if in_ci else 'Local'}")
    print(f"[DOGTAIL CONFIG] Search timeout: {search_timeout}s")
    print(f"[DOGTAIL CONFIG] Search backoff: {search_backoff}s")
    print(
        f"[DOGTAIL CONFIG] Search cutoff count: "
        f"{config.config.searchCutoffCount}",
    )

    print(f"[DOGTAIL CONFIG] Default delay: {config.config.defaultDelay}s")
    print(f"[DOGTAIL CONFIG] Action delay: {config.config.actionDelay}s")


def warm_up_atspi(timeout=10):
    """
    Warm up the AT-SPI accessibility tree by pre-loading it.

    This function attempts to access the accessibility tree early to ensure
    AT-SPI is fully initialized before tests begin. This can prevent initial
    timeouts when the first element search happens.

    Args:
        timeout (int): Maximum time to wait for AT-SPI warmup (in seconds).
    """
    print('[DOGTAIL CONFIG] Warming up AT-SPI accessibility tree...')
    start_time = time.time()

    attempts = 0
    max_attempts = 5

    while time.time() - start_time < timeout and attempts < max_attempts:
        try:
            # Try to access the root accessibility node
            # This forces AT-SPI to initialize and cache the tree
            _ = root.children
            print(
                f"""[DOGTAIL CONFIG] AT-SPI warmup successful (attempt {
                    attempts + 1
                })""",
            )

            # Give AT-SPI a moment to fully stabilize
            time.sleep(2)
            return True

        except Exception as e:
            attempts += 1
            print(
                f"""[DOGTAIL CONFIG] AT-SPI warmup attempt {
                    attempts
                } failed: {e}""",
            )
            time.sleep(1)

    if attempts >= max_attempts:
        print(
            f"""[DOGTAIL CONFIG] AT-SPI warmup completed after {
                attempts
            } attempts""",
        )

    return True


def get_ci_timeout_multiplier():
    """
    Get the timeout multiplier for CI environments.

    Returns:
        float: Multiplier to apply to timeouts (1.5x in CI, 1.0x locally).
    """
    return 1.5 if is_ci_environment() else 1.0


def get_default_timeout(base_timeout=30):
    """
    Get the default timeout adjusted for the current environment.

    Args:
        base_timeout (int): Base timeout in seconds.

    Returns:
        int: Adjusted timeout for the current environment.
    """
    multiplier = get_ci_timeout_multiplier()
    return int(base_timeout * multiplier)


def get_toaster_timeout():
    """
    Get the timeout for toaster element searches.
    Toasters are short-lived (6s display time), so we need shorter timeouts.

    Returns:
        int: Timeout in seconds (10s in CI, 8s locally).
    """
    return 10 if is_ci_environment() else 8


def get_toaster_poll_interval():
    """
    Get the polling interval for toaster element searches.
    Aggressive polling is needed to catch short-lived toasters.

    Returns:
        float: Poll interval in seconds (0.1s for aggressive polling).
    """
    return 0.1


def get_max_consecutive_failures():
    """
    Get the maximum number of consecutive element search failures
    before circuit breaker triggers.

    Returns:
        int: Max failures (3 in CI, 2 locally).
    """
    return 3 if is_ci_environment() else 2


def get_element_search_timeout():
    """
    Get the default timeout for element searches.
    Reduced from 30s to 20s for faster failure detection.

    Returns:
        int: Timeout in seconds (30s in CI, 20s locally).
    """
    return get_default_timeout(20)


# Initialize dogtail configuration when module is imported
# configure_dogtail()
