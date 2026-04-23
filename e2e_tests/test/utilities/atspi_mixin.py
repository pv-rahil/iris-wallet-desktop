# pylint: disable=too-few-public-methods
"""
AT-SPI and application management mixin for BaseOperations.
"""
from __future__ import annotations

import time

from dogtail.tree import root


class AtspiMixin:
    """
    Mixin providing AT-SPI tree management and application validation methods.
    """

    def _ensure_valid_application(self):
        """
        Ensure self.application is valid and accessible.
        Refreshes the application reference if it appears stale.
        """
        if not self.application:
            return

        try:
            # Quick check - access a property to verify the reference is valid
            _ = self.application.name
        except Exception:
            # Application reference is stale, try to refresh
            if hasattr(self, '_application_name') and self._application_name:
                try:
                    # Find the application by name (root is imported at module level)
                    for app in root.applications():
                        if self._application_name in app.name:
                            self.application = app
                            return
                except Exception:
                    pass

    def _verify_application_ready(self, timeout=3.0):
        """
        Verify that the application's AT-SPI tree is accessible and stable.

        Args:
            timeout (float): Maximum time to wait for readiness

        Returns:
            bool: True if ready, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if self.application and hasattr(self.application, 'children'):
                    children_count = len(self.application.children)
                    if children_count > 0:
                        return True
            except Exception:
                pass

            time.sleep(0.2)

        return False

    def _should_break_circuit(self):
        """
        Check if circuit breaker should trigger.

        Returns:
            bool: True if circuit should break, False otherwise.
        """
        return self._consecutive_failures >= self._max_consecutive_failures

    def _reset_circuit_breaker(self):
        """Reset the circuit breaker counter after a successful element find."""
        self._consecutive_failures = 0
        self._circuit_broken = False

    def _refresh_atspi_tree(self):
        """
        Force AT-SPI to refresh its tree cache.
        Use this when experiencing stale element issues or corrupted tree state.

        Returns:
            bool: True if refresh successful, False otherwise
        """
        try:
            _ = root.children
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def _safe_find_dialog(self, role_name, name):
        """
        Safely find a dialog element, returning None if not found.
        This prevents SearchError when the dialog doesn't exist yet.
        """
        try:
            return self.application.parent.findChild(
                lambda x: x.roleName == role_name and x.name == name,
                retry=False, requireResult=False,
            )
        except Exception:
            return None
