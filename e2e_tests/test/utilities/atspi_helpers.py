# pylint: disable=too-many-arguments, too-few-public-methods, unused-argument, too-many-branches, too-many-statements
"""
AT-SPI helper functions for e2e tests.
"""
from __future__ import annotations

import gc
import subprocess
import time

from dogtail.tree import root


def _restart_atspi():
    """Restart AT-SPI registry daemon to clear all caches."""
    try:
        # Kill the AT-SPI registry daemon
        subprocess.run(
            ['pkill', '-f', 'at-spi2-registryd'],
            capture_output=True,
            timeout=5,
            check=False,
        )
        time.sleep(1)
        # It should auto-restart via D-Bus activation, but we can also trigger it
        subprocess.run(
            [
                'busctl', '--user', 'call', 'org.a11y.Bus',
                '/org/a11y/bus', 'org.a11y.Bus', 'GetAddress',
            ],
            capture_output=True,
            timeout=5,
            check=False,
        )
        time.sleep(2)  # Wait for AT-SPI to fully restart
    except Exception:
        pass


def _aggressive_cleanup():
    """Aggressive cleanup to prevent AT-SPI exhaustion in long tests."""
    # Refresh AT-SPI tree
    try:
        _ = root.children
    except Exception:
        pass
    # Force garbage collection
    gc.collect()
    # Small delay to let UI settle
    time.sleep(0.5)


def _full_atspi_reset():
    """Full AT-SPI reset - restart service and clear all caches. Use sparingly."""
    _aggressive_cleanup()
    _restart_atspi()
    _aggressive_cleanup()
