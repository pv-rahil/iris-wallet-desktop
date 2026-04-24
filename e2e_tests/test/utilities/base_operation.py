# pylint: disable=too-many-arguments,too-many-instance-attributes
"""
This module provides a class for performing base operations on a graphical user interface (GUI) application.
"""
from __future__ import annotations

import os
import re
import time

import pyperclip
from dogtail.rawinput import keyCombo
from dogtail.rawinput import press
from dogtail.rawinput import pressKey
from dogtail.rawinput import release
from dogtail.rawinput import typeText
from dogtail.tree import root
from dotenv import load_dotenv
from Xlib import display
from Xlib import X
from Xlib.error import BadWindow

from accessible_constant import TOASTER_DESCRIPTION
from e2e_tests.test.utilities.atspi_mixin import AtspiMixin
from e2e_tests.test.utilities.dogtail_config import get_default_timeout
from e2e_tests.test.utilities.dogtail_config import is_ci_environment

load_dotenv()
NATIVE_AUTHENTICATION_PASSWORD = os.getenv('NATIVE_AUTHENTICATION_PASSWORD')
_CURRENT_ENV = None


class BaseOperations(AtspiMixin):
    """
    A class for performing base operations on a GUI application.

    Attributes:
        application (Node): The root node of the GUI application.
    """

    def __init__(self, application=None):
        """
        Initializes the BaseOperations class.

        Args:
            application (Node, optional): The root node of the GUI application. Defaults to None.
        """
        self.application = application
        # Store application name for recovery when node becomes stale
        self._application_name = None
        if application and hasattr(application, 'name'):
            self._application_name = application.name

        # Circuit breaker pattern for element searches
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5 if is_ci_environment() else 4
        self._circuit_broken = False
        self._last_click_times = {}
        self._just_switched_window = False

        # Define the elements like buttons and text fields as lambdas
        self.refresh_button = lambda: self.perform_action_on_element(
            role_name='push button',
            name='refresh_button',
        )
        self.close_button = lambda: self.perform_action_on_element(
            role_name='push button',
            name='close_button',
        )
        self.copy_button = lambda: self.perform_action_on_element(
            role_name='push button',
            name='Copy address',
        )

    def click_close_button(self):
        """
        Clicks on the cancel button.

        Returns:
            None
        """
        button = self.close_button()
        if self.do_is_displayed(button):
            self.do_click(button)

    def click_refresh_button(self):
        """
        Clicks on the refresh button.

        Returns:
            None
        """
        button = self.refresh_button()
        if self.do_is_displayed(button):
            self.do_click(button)

    def _execute_click(self, element):
        """
        Execute the actual click on an element.
        Handles different click strategies based on environment and element type.
        """
        element.grabFocus()
        time.sleep(0.5)

        if not is_ci_environment():
            is_copy_button = any(
                kw in (element.name or '').lower() for kw in [
                    'copy', 'indexer_url_copy_button', 'rgb_proxy_url_copy_button',
                ]
            )
            if is_copy_button:
                pos = element.position
                center_x = int(pos[0] + element.size[0]//2)
                center_y = int(pos[1] + element.size[1]//2)
                press(center_x, center_y)
                time.sleep(0.2)
                release(center_x, center_y)
                time.sleep(1.0)
                return

        if is_ci_environment() and element.roleName in ('push button', 'button'):
            if element.name not in ['Next', 'Try another way', 'Continue']:
                element.queryAction().doAction(0)
                time.sleep(0.5)
                return

        element.click()

    def do_click(self, element, max_retries=2):
        """
        Clicks on the specified element with debouncing to prevent rapid repeated clicks.
        """
        if not element:
            print('[CLICK ERROR] Element is None')
            return

        element_name = getattr(element, 'name', 'unknown')
        element_role = getattr(element, 'roleName', None)

        for attempt in range(max_retries + 1):
            try:
                if is_ci_environment():
                    if not self._wait_for_element_stable(element, timeout=2.0):
                        raise RuntimeError('Element not stable within timeout')

                self._ensure_valid_application()
                self._execute_click(element)
                return

            except Exception as e:
                error_str = str(e).lower()
                if any(err in error_str for err in ['no such object path', 'atspi_error', 'not stable', 'stale', 'object not found']):
                    if attempt < max_retries:
                        print(f"""[CLICK RETRY] Stale element '
                              {element_name}', refreshing AT-SPI tree (attempt {attempt + 1}/{max_retries})""")
                        self._refresh_atspi_tree()
                        time.sleep(1.0)
                        if element_name and element_role and self.application:
                            try:
                                self._ensure_valid_application()
                                element = self.application.child(
                                    roleName=element_role, name=element_name,
                                )
                            except Exception:
                                pass
                        continue
                print(f"[CLICK ERROR] Failed to click '{element_name}': {e}")
                return

    def do_set_value(self, element, value: str):
        """
        Sets the value of the specified element.
        """
        if not element or not value:
            return
        try:
            if self.do_is_displayed(element):
                element.typeText(value)
        except Exception:
            pass

    def do_set_text(self, element, value: str):
        """
        Sets the value of the specified element.
        """
        if not element or not value:
            return
        try:
            if self.do_is_displayed(element):
                element.text = value
        except Exception:
            pass

    def do_get_text(self, element) -> str:
        """
        Gets the text of the specified element.
        """
        if not element:
            return ''
        try:
            if self.do_is_displayed(element):
                return element.name if element.name else ''
        except Exception:
            pass
        return ''

    def do_get_value(self, element) -> str:
        """
        Gets the value (text content) of the specified element.
        """
        if not element:
            return ''
        try:
            if self.do_is_displayed(element):
                return element.text if element.text is not None else ''
        except Exception:
            pass
        return ''

    def do_is_displayed(
        self,
        element,
        timeout: int | None = None,
        interval: float = 2.0,
    ) -> bool:
        """
        Check if the UI element is displayed within a given timeout.

        Args:
            element: The UI element to check (must support grabFocus & showing attributes).
            timeout (int): Maximum time to wait, in seconds. If None, uses CI-aware default.
            interval (float): How often to retry, in seconds.

        Returns:
            bool: True if element is visible within timeout, False otherwise.
        """
        if timeout is None:
            timeout = get_default_timeout(15)

        if not element:
            print('[ELEMENT NOT FOUND] Element is None or empty')
            return False

        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                time.sleep(0.2)
                element.grabFocus()
                if element.showing:
                    return True
            except Exception:
                pass

            time.sleep(interval)

        # Log when element not found after timeout
        try:
            element_info = f"role={element.roleName}, name={
                element.name
            }" if hasattr(element, 'roleName') else str(element)
            print(f"""[ELEMENT NOT FOUND] Timeout after
                  {timeout}s waiting for: {element_info}""")
        except Exception:
            print(f'[ELEMENT NOT FOUND] Timeout after {timeout}s')

        return False

    def do_is_enabled(self, element) -> bool:
        """
        Checks if the specified element is enabled.

        Args:
            element (Node): The element to check.

        Returns:
            bool: True if the element is enabled, False otherwise.
        """
        if not element:
            return False
        try:
            return element.enabled
        except Exception:
            return False

    def click_copy_button(self):
        """
        Clicks on the copy address button.

        Returns:
            None
        """
        button = self.copy_button()
        if self.do_is_displayed(button):
            self.do_click(button)

    def do_get_copied_address(self, timeout=5.0) -> str:
        """
        Gets the copied address, waiting for the clipboard to be updated if necessary.

        Args:
            timeout (float): Maximum time to wait for the clipboard to become non-empty.

        Returns:
            str: The copied address, or an empty string if timeout is reached.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                text = pyperclip.paste()
                if text and text.strip():
                    return text
            except Exception:
                pass
            time.sleep(0.5)
        return ''

    def activate_window_by_name(self, window_name, max_retries=3):
        """
        Activates the window with the given name.

        Args:
            window_name (str): The name of the window to activate.
            max_retries (int): Maximum number of retries if window list is stale.

        Returns:
            None
        """
        for attempt in range(max_retries):
            d = display.Display()
            root_screen = d.screen().root
            root_screen.change_attributes(event_mask=X.SubstructureNotifyMask)

            # Sync with X server to ensure fresh window list
            d.sync()

            # Get window list
            try:
                raw_data = root_screen.get_full_property(
                    d.intern_atom(
                        '_NET_CLIENT_LIST',
                    ),
                    X.AnyPropertyType,
                ).value
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                print(
                    f"Window '{
                        window_name
                    }' not found (failed to get window list)",
                )
                return

            for window_id in raw_data:
                try:
                    window = d.create_resource_object('window', window_id)
                    window_name_property = window.get_wm_name()

                    if window_name_property and re.search(window_name, window_name_property):
                        window.set_input_focus(X.RevertToParent, X.CurrentTime)
                        window.raise_window()
                        d.sync()
                        print(f"Activated window: {window_name}")
                        return
                except BadWindow:
                    # Window was destroyed between getting the list and accessing it
                    continue

            # Window not found in this attempt, retry if we have attempts left
            if attempt < max_retries - 1:
                # Longer delay in CI for window manager to update
                time.sleep(1.0 if is_ci_environment() else 0.5)

        print(f"Window '{window_name}' not found after {max_retries} attempts")

    def do_focus_on_application(self, application, verify_ready=True):
        """
        Focuses on the given application and waits for AT-SPI to synchronize.

        Args:
            application (str or Node): The name of the application to focus on, or a frame node.
            verify_ready (bool): If True, wait for AT-SPI tree to be ready.

        Returns:
            None
        """
        # Handle both string application names and frame node objects
        app_name = application
        if hasattr(application, 'name'):
            # It's a node object, extract the name
            app_name = application.name

        self.activate_window_by_name(app_name)

        if verify_ready:
            # Give AT-SPI time to synchronize after window switch
            # CI environments need more time due to slower accessibility tree updates
            sync_delay = 3.0 if is_ci_environment() else 0.5
            time.sleep(sync_delay)

            # Verify the application is actually ready
            self._verify_application_ready(
                timeout=3.0 if is_ci_environment() else 2.0,
            )

            # Flag that we just switched windows for enhanced retry on next search
            self._just_switched_window = True

    def _ensure_application_node(self):
        """
        Ensures self.application is a valid, showing node.
        If it's not showing, attempts to find a showing one with the same name and role.
        Also forces refresh of children to ensure AT-SPI tree is populated.
        Uses stored _application_name as fallback when node attributes are inaccessible.
        """
        if self.application and hasattr(self.application, 'showing') and self.application.showing:
            # Force refresh of children by accessing them
            try:
                _ = list(self.application.children)
            except Exception:
                pass
            # Update stored name if not set
            if not self._application_name and hasattr(self.application, 'name'):
                self._application_name = self.application.name
            return

        # Node is dead or hidden. Try to find a showing one with same name and role.
        # First try to get name/role from the stale node
        name = None
        role = 'frame'  # Default role for application windows

        if self.application:
            try:
                if hasattr(self.application, 'name'):
                    name = self.application.name
                if hasattr(self.application, 'roleName'):
                    role = self.application.roleName
            except Exception:
                # Node is completely dead, attributes inaccessible
                pass

        # Fallback to stored application name
        if not name and self._application_name:
            name = self._application_name

        if name:
            try:
                # Search from root for a showing node with same identity
                new_node = root.child(
                    roleName=role, name=name, showingOnly=True,
                )
                if new_node:
                    self.application = new_node
                    self._application_name = name  # Update stored name
                    # Force refresh of children
                    _ = list(self.application.children)
                    print(f"""
                          [RECOVERY] Switched to showing
                          {role} node for '{name}'""")
            except Exception as e:
                print(f"""[RECOVERY] Failed to find showing node for
                      {name}: {e}""")

    def _find_elements_by_criteria(self, role_name, name=None, description=None, application_node=None, refresh_on_empty=True):
        """
        Find elements matching the given criteria.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element.
            description (str, optional): The description of the element.
            application_node (Node, optional): The node to search within. Defaults to self.application.
            refresh_on_empty (bool): Whether to refresh AT-SPI tree if no elements found. Default True.

        Returns:
            list: List of matching elements.
        """
        self._ensure_application_node()
        search_root = application_node if application_node else self.application

        def _search():
            if name and search_root:
                return list(
                    search_root.findChildren(
                        lambda n: n.roleName == role_name and n.name == name,
                    ),
                )
            if description and search_root:
                return list(
                    search_root.findChildren(
                        lambda n: n.roleName == role_name
                        and n.description == description,
                    ),
                )
            return []

        elements = _search()

        # If no elements found and refresh is enabled, try refreshing AT-SPI tree once
        if not elements and refresh_on_empty:
            identifier = name if name else description
            print(
                f"[AT-SPI] No elements found for {role_name}/{
                    identifier
                }, refreshing tree...",
            )
            self._refresh_atspi_tree()
            time.sleep(0.5)  # Give tree time to update after refresh
            # Re-ensure application node after refresh
            self._ensure_application_node()
            search_root = application_node if application_node else self.application
            elements = _search()
            if elements:
                print(f"[AT-SPI] Found {
                    len(elements)
                } element(s) after refresh")

        return elements

    def _is_element_ready(self, element):
        """
        Check if the element is ready for interaction (showing and sensitive).

        Args:
            element: The element to check.

        Returns:
            bool: True if element is ready, False otherwise.
        """
        if not element:
            return False
        try:
            return element.showing and (
                not hasattr(element, 'sensitive') or element.sensitive
            )
        except Exception:
            return False

    def _wait_for_element_stable(self, element, timeout=1.5):
        """
        Wait for element to become stable (not changing state).
        This prevents race conditions where elements are found but still updating.

        Args:
            element: The element to check
            timeout: How long to wait for stability (default 1.5s local, 5.0s in CI)

        Returns:
            bool: True if stable, False if timeout

        Raises:
            RuntimeError: If element appears to be stale (AT-SPI object invalid)
        """
        # Increase timeout in CI for slower environments
        if is_ci_environment():
            timeout = max(timeout, 5.0)

        start_time = time.time()
        last_state = None
        stable_checks = 0
        required_stable_checks = 3 if is_ci_environment() else 2
        consecutive_errors = 0

        while time.time() - start_time < timeout:
            try:
                try:
                    sens = element.sensitive
                except AttributeError:
                    sens = True
                current_state = (
                    element.showing,
                    sens,
                    element.name,
                )

                # Reset error counter on success
                consecutive_errors = 0

                if current_state == last_state:
                    stable_checks += 1
                    if stable_checks >= required_stable_checks:
                        return True
                else:
                    stable_checks = 0

                last_state = current_state
                time.sleep(0.2)

            except Exception as e:
                consecutive_errors += 1
                # If we get multiple consecutive errors, element is likely stale
                if consecutive_errors >= 3:
                    raise RuntimeError(f'Stale element detected: {e}') from e
                time.sleep(0.2)

        return False

    def _get_first_ready_element(self, elements):
        """
        Get the first element from a list that is showing and sensitive.

        Args:
            elements (list): List of elements to check.
            role_name (str): The role of the element.
            name (str): The name of the element.

        Returns:
            Node or None: The first ready element, or None if none found.
        """
        if not elements:
            return None
        for element in elements:
            try:
                if element.showing and element.sensitive:
                    element.grabFocus()
                    return element
            except Exception:
                continue
        return None

    def _validate_and_return_element(self, element):
        """
        Validate element is stable and ready before returning it.

        Args:
            element: The element to validate

        Returns:
            element if valid, None if should retry
        """
        # In CI, verify element is stable before returning
        if is_ci_environment():
            if not self._wait_for_element_stable(element, timeout=2.0):
                return None

        # Verify element is still valid (stale element detection)
        try:
            _ = element.name
            _ = element.showing
            self._reset_circuit_breaker()
            return element
        except Exception:
            return None

    def _handle_circuit_breaker_check(self, role_name, identifier):
        """
        Check and handle circuit breaker state.

        Args:
            role_name: The role of the element being searched
            identifier: Name or description of the element

        Raises:
            RuntimeError: If circuit breaker triggers and recovery fails
        """
        if not self._should_break_circuit():
            return

        # Attempt AT-SPI recovery before failing
        if self._refresh_atspi_tree():
            self._reset_circuit_breaker()
        else:
            error_msg = f"Circuit breaker triggered for {
                role_name
            } '{identifier}'"
            raise RuntimeError(error_msg)

    def _handle_window_switch_delay(self):
        """Apply delay after window switch for AT-SPI synchronization."""
        try:
            switched = self._just_switched_window
        except AttributeError:
            switched = False

        if switched:
            initial_delay = 1.5 if is_ci_environment() else 0.3
            time.sleep(initial_delay)
            self._just_switched_window = False

    def _should_exit_retry_loop(self, attempt, max_retries, role_name, identifier):
        """
        Check if we should exit the retry loop based on max_retries.

        Args:
            attempt: Current attempt number
            max_retries: Maximum retries allowed
            role_name: Role of the element
            identifier: Name or description

        Returns:
            bool: True if should exit, False if should continue
        """
        if max_retries and attempt >= max_retries:
            print(
                f"""[MAX RETRIES] Reached max retries ({max_retries})
                for {role_name} '{identifier}'""",
            )
            return True
        return False

    def perform_action_on_element(
        self,
        role_name,
        name=None,
        description=None,
        timeout=None,
        max_retries=None,
        application_node=None,
    ):
        """
        Retrieves the specified element with the given role and name or description, with exponential backoff retries.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element. Defaults to None.
            description (str, optional): The description of the element. Defaults to None.
            timeout (int, optional): The maximum time to wait for the element in seconds. If None, uses CI-aware default.
            max_retries (int, optional): Maximum number of retry attempts. If None, uses timeout-based approach.
            application_node (Node, optional): The node to search within. Defaults to self.application.

        Returns:
            Node: The retrieved element, or False if no matching element is found within the timeout.

        Raises:
            RuntimeError: If circuit breaker is triggered after consecutive failures.
        """
        identifier = name if name else description

        # Check circuit breaker and attempt recovery if needed
        self._handle_circuit_breaker_check(role_name, identifier)

        # Apply delay if we just switched windows
        self._handle_window_switch_delay()

        if timeout is None:
            timeout = get_default_timeout(10)  # 10s local, 15s CI

        start_time = time.time()
        # Faster retries locally, slower in CI
        current_interval = 1.5 if is_ci_environment() else 0.5
        max_interval = 4.0 if is_ci_environment() else 2.0
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                elements = self._find_elements_by_criteria(
                    role_name, name, description, application_node,
                )

                if elements:
                    element = elements[-1]
                    if self._is_element_ready(element):
                        validated_element = self._validate_and_return_element(
                            element,
                        )
                        if validated_element:
                            return validated_element
                        time.sleep(0.3)
                        continue

            except Exception as e:
                print(
                    f"""[RETRY {attempt}] Finding {
                        role_name
                    } '{identifier}': {e}""",
                )

            # Check if we should exit early (max_retries)
            if self._should_exit_retry_loop(attempt, max_retries, role_name, identifier):
                break

            # Exponential backoff
            time.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_interval)

        # Circuit breaker logic for quick failures
        elapsed_time = time.time() - start_time
        if elapsed_time < 2.0:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0

        print(f"""[WARN] Element not found after
              {timeout}s and {attempt} attempts: role={role_name}, name/desc={identifier}""")

        return False

    def get_first_element(
        self,
        role_name,
        name=None,
        description=None,
        timeout=None,
        retry_interval=0.3,
    ):
        """
        Retrieves the first element with the given role and name or description, with exponential backoff retries.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element. Defaults to None.
            description (str, optional): The description of the element. Defaults to None.
            timeout (int, optional): The maximum time to wait for the element in seconds. If None, uses CI-aware default.
            retry_interval (float): The initial time to wait between retries in seconds. Defaults to 0.3.

        Returns:
            Node: The retrieved element, or False if no matching element is found within the timeout.
        """
        if timeout is None:
            timeout = get_default_timeout(30)

        start_time = time.time()
        current_interval = 1.0 if is_ci_environment() else retry_interval
        max_interval = 4.0 if is_ci_environment() else 2.0

        while time.time() - start_time < timeout:
            try:
                elements = self._find_elements_by_criteria(
                    role_name, name, description,
                )

                if elements:
                    element = self._get_first_ready_element(elements)
                    if element:
                        return element

            except Exception as e:
                # Log the exception with more details for debugging
                identifier = name if name else description
                print(f"[RETRY] Finding first {role_name} '{identifier}': {e}")

            # Exponential backoff: increase interval for next retry
            time.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_interval)

        return False

    def do_clear_text(self, element):
        """
        Clears the text of the specified element
        """

        if self.do_is_displayed(element):

            for _ in range(len(element.text)):
                pressKey('backspace')

    def get_text(self, element) -> str:
        """gets the text of the specified element from its description"""
        if self.do_is_displayed(element):
            return element.text
        return ''

    def wait_for_toaster_message(
        self,
        toaster_name=TOASTER_DESCRIPTION,
        timeout=None,
        interval=0.5,
    ):
        """
        Waits until a toaster message appears on the screen.

        Args:
            toaster_name (str): The accessible name of the toaster message.
            timeout (int, optional): Maximum time to wait (in seconds). If None, uses CI-aware default.
            interval (float): Time interval between checks. Default is 0.5 seconds.

        Raises:
            TimeoutError: If the toaster message does not appear within the timeout.
        """
        if timeout is None:
            timeout = get_default_timeout(150)

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                toaster = self.perform_action_on_element(
                    role_name='label',
                    description=toaster_name,
                    timeout=5,
                )
                if toaster:
                    return
            except Exception:
                pass

            time.sleep(interval)

        raise TimeoutError(
            f"""Toaster message '{toaster_name}' did not appear within {
                timeout
            } seconds.""",
        )

    def do_get_child_count(self, element):
        """gets the number of children of the specified element"""
        if self.do_is_displayed(element):

            return element.children

        return None

    def enter_native_password(self):
        """Enter the password when the native auth dialog is show"""
        typeText(NATIVE_AUTHENTICATION_PASSWORD)
        if not os.getenv('CI'):
            keyCombo('enter')

    def reset_state(self):
        """
        Reset all internal state tracking to ensure clean state between tests.
        This is crucial when using module-scoped fixtures where the same
        BaseOperations instance is reused across multiple test functions.

        Resets:
        - Click debounce tracking
        - Circuit breaker failure counters
        - Window switch flags
        """
        self._last_click_times = {}
        self._consecutive_failures = 0
        self._circuit_broken = False
        self._just_switched_window = False

    def register_current_environment(self, env) -> None:
        """Register the active TestEnvironment for cross-feature access."""
        global _CURRENT_ENV
        _CURRENT_ENV = env

    def get_current_environment(self):
        """Retrieve the active TestEnvironment if registered."""
        return _CURRENT_ENV

    def wait_for_toggle_state(self, toggle_element_getter, expected_checked, timeout=5):
        """
        Wait for a toggle button to reach the expected checked state.

        Args:
            toggle_element_getter: Function that returns the toggle element
            expected_checked: Expected boolean state (True or False)
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if state matched, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                element = toggle_element_getter()
                if element:
                    try:
                        current_state = element.checked
                    except AttributeError:
                        current_state = None
                    if current_state == expected_checked:
                        return True
                element.click()
                time.sleep(0.3)
            except Exception:
                time.sleep(0.3)

        return False
