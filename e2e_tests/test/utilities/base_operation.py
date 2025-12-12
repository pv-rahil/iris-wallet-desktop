# pylint: disable=unused-import,too-many-arguments,too-many-statements,too-many-branches,too-many-lines
"""
This module provides a class for performing base operations on a graphical user interface (GUI) application.
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime

import pyperclip
from dogtail.rawinput import keyCombo
from dogtail.rawinput import pressKey
from dogtail.rawinput import typeText
from dogtail.tree import root
from dotenv import load_dotenv
from Xlib import display
from Xlib import X

from accessible_constant import OPTION_1_FRAME
from accessible_constant import OPTION_2_FRAME
from accessible_constant import RECEIVE_BITCOIN_BUTTON
from accessible_constant import SEND_ASSET_BUTTON
from accessible_constant import SEND_BITCOIN_BUTTON
from accessible_constant import TOASTER_DESCRIPTION
from e2e_tests.test.utilities.dogtail_config import get_default_timeout
from e2e_tests.test.utilities.dogtail_config import is_ci_environment

load_dotenv()
NATIVE_AUTHENTICATION_PASSWORD = os.getenv('NATIVE_AUTHENTICATION_PASSWORD')


class BaseOperations:
    """
    A class for performing base operations on a GUI application.

    Attributes:
        application (Node): The root node of the GUI application.
    """

    def __init__(self, application):
        """
        Initializes the BaseOperations class.

        Args:
            application (Node): The root node of the GUI application.
        """
        self.application = application

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

    def do_click(self, element, debounce_ms=800, skip_display_check=False):
        """
        Clicks on the specified element with debouncing to prevent rapid repeated clicks.

        Args:
            element (Node): The element to click on.
            debounce_ms (int): Minimum milliseconds between clicks on same element. Default 800ms (increased for CI stability).
            skip_display_check (bool): If True, skip the display check (use when element is known to be visible).

        Returns:
            None
        """
        # Validate element exists and has required attributes
        if not element:
            print('[CLICK ERROR] Element is None')
            return

        if not hasattr(element, 'name') or not hasattr(element, 'roleName'):
            print('[CLICK ERROR] Element missing required attributes (name/roleName)')
            return

        # Only check if displayed when not skipping
        if not skip_display_check:
            if not self.do_is_displayed(element):
                print(
                    f"[CLICK] Element '{
                        element.name
                    }' not displayed, skipping click",
                )
                return

        # Track last click time per element to prevent double-clicks
        if not hasattr(self, '_last_click_times'):
            self._last_click_times = {}

        # Use stable identifier (name + role) instead of object id
        # Object ID changes when AT-SPI refreshes elements
        element_name = element.name
        element_role = element.roleName
        element_key = f"{element_role}:{element_name}"

        # Special handling for toaster elements - use longer debounce
        if element_name == TOASTER_DESCRIPTION or 'toaster' in element_name.lower():
            debounce_ms = max(debounce_ms, 1000)  # Minimum 1s for toasters

        current_time = time.time() * 1000  # Convert to milliseconds

        # Check if we need to debounce
        if element_key in self._last_click_times:
            time_since_last_click = current_time - \
                self._last_click_times[element_key]
            if time_since_last_click < debounce_ms:
                print(
                    f"[DEBOUNCE] Prevented double-click on '{element_name}' "
                    f"({element_role}) - only {time_since_last_click:.0f}ms since last click "
                    f"(minimum: {debounce_ms}ms)",
                )
                return

        # Perform the click
        try:
            # Validate element is still valid before clicking
            if not hasattr(element, 'showing'):
                print(
                    f"[CLICK ERROR] Element '{
                        element_name
                    }' became stale before click",
                )
                return

            # In CI, verify element is stable before clicking
            # This prevents clicks on elements that are still animating/updating
            if is_ci_environment() and not skip_display_check:
                if not self._wait_for_element_stable(element, timeout=2.0):
                    print(
                        f"[CLICK WARN] Element '{element_name}' not stable, "
                        f"proceeding with click anyway (may fail)",
                    )

            if element_role not in ['push button', 'button', 'panel'] and \
                    element_name not in [SEND_BITCOIN_BUTTON, SEND_ASSET_BUTTON, RECEIVE_BITCOIN_BUTTON, OPTION_1_FRAME, OPTION_2_FRAME]:
                element.grabFocus()
            time.sleep(0.1)
            element.click()
            self._last_click_times[element_key] = current_time

            # Add post-click wait for panel elements in CI to allow event propagation
            # This compensates for signal/slot timing issues without modifying app code
            if element_role == 'panel' and element_name in [OPTION_1_FRAME, OPTION_2_FRAME]:
                post_click_delay = 0.8 if is_ci_environment() else 0.3
                print(
                    f"[PANEL CLICK] Waiting {
                        post_click_delay
                    }s for event propagation on '{element_name}'...",
                )
                time.sleep(post_click_delay)

            print(
                f"[CLICK] Successfully clicked '{
                    element_name
                }' ({element_role})",
            )
        except Exception as e:
            print(f"[CLICK ERROR] Failed to click '{element_name}': {e}")

    def do_set_value(self, element, value: str):
        """
        Sets the value of the specified element.

        Args:
            element (Node): The element to set the value for.
            value (str): The value to set.

        Returns:
            None
        """
        if self.do_is_displayed(element) and value:
            element.typeText(value)

    def do_set_text(self, element, value: str):
        """
        Sets the value of the specified element.

        Args:
            element (Node): The element to set the value for.
            value (str): The value to set.

        Returns:
            None
        """
        if self.do_is_displayed(element) and value:
            element.text = value

    def do_get_text(self, element) -> str:
        """
        Gets the text of the specified element.

        Args:
            element (Node): The element to get the text from.

        Returns:
            str: The text of the element.
        """
        if self.do_is_displayed(element):
            return element.name

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
            timeout = get_default_timeout(30)

        if not element:
            print('[WARN] do_is_displayed: element is None.')
            return False

        if not hasattr(element, 'grabFocus') or not hasattr(element, 'showing'):
            print('[ERROR] do_is_displayed: element does not have required attributes.')
            return False

        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                time.sleep(0.3)
                element.grabFocus()
                if element.showing:  # check visibility
                    return True
            except Exception as e:
                print(f"[INFO] Retrying... element not ready yet: {e}")

            time.sleep(interval)

        # Print detailed element information on timeout
        try:
            element_info = (
                f"role='{element.roleName}', "
                f"name='{element.name}', "
                f"description='{element.description}'"
            )
        except Exception:
            element_info = '<unable to read element details>'

        print(
            f"""[TIMEOUT] Element was not visible after
        {timeout} seconds. Element: [{element_info}]""",
        )
        return False

    def do_is_enabled(self, element) -> bool:
        """
        Checks if the specified element is enabled.

        Args:
            element (Node): The element to check.

        Returns:
            bool: True if the element is enabled, False otherwise.
        """
        return element.enabled

    def click_copy_button(self):
        """
        Clicks on the copy address button.

        Returns:
            None
        """
        button = self.copy_button()
        if self.do_is_displayed(button):
            self.do_click(button)

    def do_get_copied_address(self) -> str:
        """
        Gets the copied address.

        Returns:
            str: The copied address.
        """
        return pyperclip.paste()

    def activate_window_by_name(self, window_name):
        """
        Activates the window with the given name.

        Args:
            window_name (str): The name of the window to activate.

        Returns:
            None
        """
        d = display.Display()
        root_screen = d.screen().root
        root_screen.change_attributes(event_mask=X.SubstructureNotifyMask)

        # Get window list
        raw_data = root_screen.get_full_property(
            d.intern_atom(
                '_NET_CLIENT_LIST',
            ),
            X.AnyPropertyType,
        ).value
        for window_id in raw_data:
            window = d.create_resource_object('window', window_id)
            window_name_property = window.get_wm_name()

            if window_name_property and re.search(window_name, window_name_property):
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                window.raise_window()
                d.sync()
                print(f"Activated window: {window_name}")
                return

        print(f"Window '{window_name}' not found")

    def do_focus_on_application(self, application, verify_ready=True):
        """
        Focuses on the given application and waits for AT-SPI to synchronize.

        Args:
            application (str): The name of the application to focus on.
            verify_ready (bool): If True, wait for AT-SPI tree to be ready.

        Returns:
            None
        """
        self.activate_window_by_name(application)

        if verify_ready:
            # Give AT-SPI time to synchronize after window switch
            # CI environments need more time due to slower accessibility tree updates
            sync_delay = 3.0 if is_ci_environment() else 1.0
            print(
                f"[FOCUS] Waiting {
                    sync_delay
                }s for AT-SPI to sync after focus change...",
            )
            time.sleep(sync_delay)

            # Verify the application is actually ready by checking if we can access its tree
            self._verify_application_ready(timeout=5.0)

            # Flag that we just switched windows for enhanced retry on next search
            self._just_switched_window = True

    def _find_elements_by_criteria(self, role_name, name=None, description=None):
        """
        Find elements matching the given criteria.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element.
            description (str, optional): The description of the element.

        Returns:
            list: List of matching elements.
        """
        if name and self.application:
            return list(
                self.application.findChildren(
                    lambda n: n.roleName == role_name and n.name == name,
                ),
            )
        if description and self.application:
            return list(
                self.application.findChildren(
                    lambda n: n.roleName == role_name
                    and n.description == description,
                ),
            )
        return []

    def _is_element_ready(self, element):
        """
        Check if the element is ready for interaction (showing and sensitive).

        Args:
            element: The element to check.

        Returns:
            bool: True if element is ready, False otherwise.
        """
        return element.showing and (
            not hasattr(element, 'sensitive') or element.sensitive
        )

    def _wait_for_element_stable(self, element, timeout=3.0):
        """
        Wait for element to become stable (not changing state).
        This prevents race conditions where elements are found but still updating.

        Args:
            element: The element to check
            timeout: How long to wait for stability (default 3.0s, increased to 5.0s in CI)

        Returns:
            bool: True if stable, False if timeout
        """
        # Increase timeout in CI for slower environments
        if is_ci_environment():
            timeout = max(timeout, 5.0)

        start_time = time.time()
        last_state = None
        stable_checks = 0
        # Must be stable for 3 consecutive checks (increased from 2)
        required_stable_checks = 3

        while time.time() - start_time < timeout:
            try:
                # Capture current element state (showing, sensitive, name)
                current_state = (
                    element.showing,
                    getattr(element, 'sensitive', True),
                    element.name,
                )

                if current_state == last_state:
                    stable_checks += 1
                    if stable_checks >= required_stable_checks:
                        print(
                            f"[STABILITY] Element '{
                                element.name
                            }' stable after "
                            f"{stable_checks} checks",
                        )
                        return True
                else:
                    # State changed, reset counter
                    stable_checks = 0
                    print(
                        f"[STABILITY] Element '{element.name}' state changed, "
                        f"waiting for stability...",
                    )

                last_state = current_state
                time.sleep(0.3)  # Check every 300ms

            except Exception as e:
                print(f"[STABILITY] Element became invalid during check: {e}")
                return False

        print(
            f"[STABILITY] Element '{element.name}' did not stabilize within "
            f"{timeout}s",
        )
        return False

    def _should_grab_focus(self, role_name, name):
        """
        Determine if grabFocus should be called on the element.

        Args:
            role_name (str): The role of the element.
            name (str): The name of the element.

        Returns:
            bool: True if grabFocus should be called, False otherwise.
        """
        excluded_roles = ['push button', 'button', 'panel']
        excluded_names = [
            SEND_BITCOIN_BUTTON,
            SEND_ASSET_BUTTON,
            RECEIVE_BITCOIN_BUTTON,
            OPTION_1_FRAME,
            OPTION_2_FRAME,
        ]
        return role_name not in excluded_roles and name not in excluded_names

    def _get_first_ready_element(self, elements, role_name, name):
        """
        Get the first element from a list that is showing and sensitive.

        Args:
            elements (list): List of elements to check.
            role_name (str): The role of the element.
            name (str): The name of the element.

        Returns:
            Node or None: The first ready element, or None if none found.
        """
        for element in elements:
            if element.showing and element.sensitive:
                if self._should_grab_focus(role_name, name):
                    element.grabFocus()
                return element
        return None

    def _validate_and_return_element(
        self,
        element,
        role_name,
        name,
        identifier,
        timeout,
        attempt,
    ):
        """
        Validate element is stable and ready before returning it.

        Args:
            element: The element to validate
            role_name: Role of the element
            name: Name of the element
            identifier: Name or description identifier
            timeout: Timeout value for logging
            attempt: Current attempt number

        Returns:
            element if valid, None if should retry
        """
        # In CI, verify element is stable before returning
        if is_ci_environment():
            if not self._wait_for_element_stable(element, timeout=2.0):
                print(
                    f"[STABILITY WARN] Element '{
                        element.name
                    }' not stable, "
                    f"continuing search...",
                )
                return None  # Signal to continue retry loop

        # Verify element is still valid (stale element detection)
        try:
            # Access element properties to ensure it's not stale
            _ = element.name
            _ = element.showing

            # Grab focus if needed
            if self._should_grab_focus(role_name, name):
                element.grabFocus()
                time.sleep(0.2)  # Allow focus to settle

            self._log_search_attempt(
                role_name,
                identifier,
                timeout,
                'SUCCESS',
                attempt,
            )
            self._reset_circuit_breaker()  # Reset on success
            return element

        except Exception as e:
            print(
                f"[STALE ELEMENT] Element became invalid before return: {
                    e
                }",
            )
            return None  # Signal to continue retry loop

    def perform_action_on_element(
        self,
        role_name,
        name=None,
        description=None,
        timeout=None,
        max_retries=None,
    ):
        """
        Retrieves the specified element with the given role and name or description, with exponential backoff retries.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element. Defaults to None.
            description (str, optional): The description of the element. Defaults to None.
            timeout (int, optional): The maximum time to wait for the element in seconds. If None, uses CI-aware default (20s).
            max_retries (int, optional): Maximum number of retry attempts. If None, uses timeout-based approach.

        Returns:
            Node: The retrieved element, or False if no matching element is found within the timeout.

        Raises:
            RuntimeError: If circuit breaker is triggered after consecutive failures.
        """
        # Check circuit breaker
        if self._should_break_circuit():
            identifier = name if name else description

            # Attempt AT-SPI recovery before failing
            print('[CIRCUIT BREAKER] Attempting AT-SPI recovery before failing...')
            if self._refresh_atspi_tree():
                print(
                    '[CIRCUIT BREAKER] Recovery successful, resetting counter and retrying',
                )
                self._reset_circuit_breaker()
                # Don't fail, continue with the search
            else:
                # Recovery failed, fail the search
                error_msg = (
                    f"[CIRCUIT BREAKER] Stopping search for {
                        role_name
                    } '{identifier}' "
                    f"after {
                        self._consecutive_failures
                    } consecutive failures and failed recovery"
                )
                print(error_msg)
                raise RuntimeError(error_msg)

        # If we just switched windows, use enhanced retry strategy
        if getattr(self, '_just_switched_window', False):
            identifier = name if name else description
            print(
                f"[POST-FOCUS] First search after window switch for {
                    role_name
                } '{identifier}' - using enhanced retry",
            )
            initial_delay = 1.5 if is_ci_environment() else 0.8
            time.sleep(initial_delay)
            self._just_switched_window = False

        if timeout is None:
            timeout = get_default_timeout(20)

        start_time = time.time()
        # Optimize retry intervals for CI
        current_interval = 1.5
        max_interval = 4.0
        attempt = 0

        identifier = name if name else description
        self._log_search_attempt(role_name, identifier, timeout, 'START')

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                # Try to find elements by name or description
                elements = self._find_elements_by_criteria(
                    role_name, name, description,
                )

                if elements:
                    element = elements[-1]
                    if self._is_element_ready(element):
                        # Validate and return element (handles stability + stale detection)
                        validated_element = self._validate_and_return_element(
                            element,
                            role_name,
                            name,
                            identifier,
                            timeout,
                            attempt,
                        )
                        if validated_element:
                            return validated_element
                        # If None returned, continue retry loop
                        time.sleep(0.5)
                        continue

            except Exception as e:
                # Log the exception with more details for debugging
                print(
                    f"""[RETRY {attempt}] Finding {role_name} '{identifier}': {e}
                      """,
                )

            # Check if we should exit early (max_retries)
            if max_retries and attempt >= max_retries:
                print(
                    f"""[MAX RETRIES] Reached max retries (
                      {max_retries}) for {role_name} '{identifier}'
                      """,
                )
                break

            # Exponential backoff: increase interval for next retry
            time.sleep(current_interval)
            current_interval = min(current_interval * 1.5, max_interval)

        # Element not found - log failure
        self._log_search_attempt(
            role_name,
            identifier,
            timeout,
            'FAILURE',
            attempt,
        )
        self._dump_tree_on_failure(role_name, identifier)

        # Circuit breaker logic: only trigger on QUICK consecutive failures
        # (indicating AT-SPI tree is broken), not on normal element-not-found
        elapsed_time = time.time() - start_time

        # If search took the full timeout, it's a normal "element not found" - don't count it
        # If search failed quickly (< 2 seconds), AT-SPI tree might be broken - count it
        if elapsed_time < 2.0:
            self._consecutive_failures += 1
            print(
                f"""[CIRCUIT BREAKER] Quick failure detected ({elapsed_time:.1f}s) -
                consecutive quick failures: {self._consecutive_failures}/{self._max_consecutive_failures}""",
            )
        else:
            # Normal timeout - element genuinely not found, reset counter
            if self._consecutive_failures > 0:
                print(
                    f"""[CIRCUIT BREAKER] Normal timeout - resetting counter from {
                        self._consecutive_failures
                    }""",
                )
            self._consecutive_failures = 0

        print(
            f"""[WARN] Element not found after {
                timeout
            }s and {attempt} attempts""",
        )

        return False

    def get_first_element(
        self,
        role_name,
        name=None,
        description=None,
        timeout=None,
        retry_interval=0.5,
    ):
        """
        Retrieves the first element with the given role and name or description, with exponential backoff retries.

        Args:
            role_name (str): The role of the element.
            name (str, optional): The name of the element. Defaults to None.
            description (str, optional): The description of the element. Defaults to None.
            timeout (int, optional): The maximum time to wait for the element in seconds. If None, uses CI-aware default.
            retry_interval (float): The initial time to wait between retries in seconds. Defaults to 0.5.

        Returns:
            Node: The retrieved element, or False if no matching element is found within the timeout.
        """
        if timeout is None:
            timeout = get_default_timeout(30)

        start_time = time.time()
        current_interval = retry_interval
        max_interval = 4.0  # Cap exponential backoff at 4 seconds

        while time.time() - start_time < timeout:
            try:
                # Try to find elements by name or description
                elements = self._find_elements_by_criteria(
                    role_name, name, description,
                )

                if elements:
                    element = self._get_first_ready_element(
                        elements, role_name, name,
                    )
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
            timeout (int, optional): Maximum time to wait (in seconds). If None, uses CI-aware default (150s base, increased for reliability).
            interval (float): Time interval between checks. Default is 0.5 seconds.

        Raises:
            TimeoutError: If the toaster message does not appear within the timeout.
        """
        if timeout is None:
            # Increased from 120s to 150s for better reliability with slow operations
            timeout = get_default_timeout(150)

        start_time = time.time()
        retry_count = 0

        while time.time() - start_time < timeout:
            retry_count += 1
            try:
                toaster = self.perform_action_on_element(
                    role_name='label',
                    description=toaster_name,
                    timeout=10,  # Shorter timeout per attempt
                )
                if toaster:
                    print(
                        f"[TOASTER] Found toaster message after {
                            retry_count
                        } attempts",
                    )
                    return  # Exit function when toaster appears
            except Exception as _:
                # Log every 10th attempt to avoid spam
                if retry_count % 10 == 0:
                    print(
                        f"[TOASTER] Still waiting for toaster (attempt {
                            retry_count
                        })...",
                    )

            time.sleep(interval)  # Wait and retry

        raise TimeoutError(
            f"""Toaster message '{toaster_name}
                ' did not appear within {timeout} seconds after {retry_count} attempts.""",
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
        print('[STATE RESET] BaseOperations state cleared for next test')

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
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                # Refresh element on each check to avoid stale references
                element = toggle_element_getter()
                if element:
                    current_state = getattr(element, 'checked', None)
                    print(
                        f"[TOGGLE STATE] Attempt {attempt}: current={
                            current_state
                        }, expected={expected_checked}",
                    )
                    if current_state == expected_checked:
                        print(
                            f"[TOGGLE STATE] Verified checked={
                                expected_checked
                            } after {attempt} attempts",
                        )
                        return True
                else:
                    print(
                        f"[TOGGLE STATE] Attempt {attempt}: Element not found",
                    )
                time.sleep(0.5)  # Check every 500ms
            except Exception as e:
                print(f"[TOGGLE STATE] Attempt {attempt} error: {e}")
                time.sleep(0.5)

        print(
            f"[TOGGLE STATE] Timeout after {
                attempt
            } attempts waiting for checked={expected_checked}",
        )
        return False

    def _verify_application_ready(self, timeout=5.0):
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
                # Try to access the application tree to verify it's ready
                if self.application and hasattr(self.application, 'children'):
                    # Successfully accessed the tree
                    children_count = len(self.application.children)
                    if children_count > 0:
                        print(
                            f"[FOCUS] Application ready - AT-SPI tree accessible ({
                                children_count
                            } children)",
                        )
                        return True
            except Exception as e:
                print(f"[FOCUS] Waiting for AT-SPI tree readiness: {e}")

            time.sleep(0.3)

        print(
            f"[FOCUS] Warning: Application readiness could not be verified within {
                timeout
            }s",
        )
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
        if self._consecutive_failures > 0:
            print(
                f"""[CIRCUIT BREAKER] Reset after
            {self._consecutive_failures} failures""",
            )
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
            # Access root to force tree refresh
            _ = root.children
            time.sleep(0.5)
            print('[AT-SPI] Tree refreshed successfully')
            return True
        except Exception as e:
            print(f"[AT-SPI] Failed to refresh tree: {e}")
            return False

    def _log_search_attempt(self, role_name, identifier, timeout, status, attempt=0):
        """
        Log element search attempts with structured information.

        Args:
            role_name (str): The role of the element being searched.
            identifier (str): The name or description of the element.
            timeout (int): The timeout value for the search.
            status (str): Status of the search (START, SUCCESS, FAILURE).
            attempt (int): Current attempt number.
        """
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        if status == 'START':
            print(
                f"""[{timestamp}] [SEARCH START] {role_name} '
            {identifier}' (timeout: {timeout}s)""",
            )
        elif status == 'SUCCESS':
            print(
                f"""[{timestamp}] [SEARCH SUCCESS] {role_name} '
            {identifier}' (attempt: {attempt})""",
            )
        elif status == 'FAILURE':
            print(
                f"""[{timestamp}] [SEARCH FAILURE] {role_name} '
            {identifier}' (attempts: {attempt}, timeout: {timeout}s)""",
            )

    def _get_visible_elements(self):
        """Get all visible elements from the application tree."""
        all_elements = list(self.application.findChildren(lambda n: True))
        visible_elements = []
        for elem in all_elements:
            try:
                if elem.showing:
                    visible_elements.append(elem)
            except Exception:
                continue
        return visible_elements

    def _group_elements_by_role(self, elements):
        """Group elements by their role name."""
        elements_by_role = {}
        for elem in elements:
            role = elem.roleName
            if role not in elements_by_role:
                elements_by_role[role] = []
            elements_by_role[role].append(elem)
        return elements_by_role

    def _print_element_details(self, idx, elem):
        """Print details of a single element."""
        try:
            name = elem.name if elem.name else '<empty>'
            description = elem.description if elem.description else '<empty>'

            # Show name and description on same line if both are short
            if len(name) < 40 and len(description) < 40:
                print(f"{idx}. name: '{name}' | description: '{description}'")
            else:
                print(f"{idx}. name: '{name}'")
                if description != '<empty>':
                    print(f"       description: '{description}'")
        except Exception:
            print(f"    {idx}. [Error reading element]")

    def _print_matching_role_elements(self, role_name, elements_by_role):
        """Print elements with the same role as the one being searched for."""
        if role_name in elements_by_role:
            print(
                f"""▶ Elements with role '
            {role_name}' (what you're looking for):""",
            )
            print(
                f""" Found {
                    len(elements_by_role[role_name])
                } visible element(s)\n""",
            )
            for idx, elem in enumerate(elements_by_role[role_name], 1):
                try:
                    name = elem.name if elem.name else '<empty>'
                    description = elem.description if elem.description else '<empty>'
                    print(f"  {idx}. name: '{name}'")
                    print(f"     description: '{description}'")
                    print()
                except Exception as e:
                    print(f"  {idx}. [Error reading element: {e}]\n")
            print(f"{'─'*80}\n")
        else:
            print(f"▶ No visible elements found with role '{role_name}'\n")
            print(f"{'─'*80}\n")

    def _print_other_role_elements(self, role_name, elements_by_role):
        """Print all other visible elements grouped by role."""
        print('▶ All other visible elements on this page:\n')
        for role in sorted(elements_by_role.keys()):
            if role == role_name:
                continue  # Already shown above

            elements = elements_by_role[role]
            print(f"  [{role}] ({len(elements)} element(s))")

            # Show up to 5 elements per role to keep output manageable
            for idx, elem in enumerate(elements[:5], 1):
                self._print_element_details(idx, elem)

            if len(elements) > 5:
                print(f"    ... and {len(elements) - 5} more")
            print()

    def _dump_tree_on_failure(self, role_name, identifier):
        """
        Dump AT-SPI tree information when element search fails.
        Shows only visible elements on the current page for easier debugging.

        Args:
            role_name (str): The role of the element that was not found.
            identifier (str): The name or description of the element.
        """
        try:
            # Get current page/window info
            try:
                app_name = (
                    self.application.name
                    if hasattr(
                        self.application,
                        'name',
                    )
                    else '<unknown>'
                )
                window_name = (
                    self.application.child(
                        roleName='frame',
                    ).name
                    if self.application.child(roleName='frame')
                    else '<unknown>'
                )
            except Exception:
                app_name = '<unknown>'
                window_name = '<unknown>'

            print(f"\n{'='*80}")
            print('❌ ELEMENT NOT FOUND ❌')
            print(f"{'='*80}")
            print(f"  Role:        {role_name}")
            print(f"  Name/Desc:   {identifier}")
            print(f"  Current App: {app_name}")
            print(f"  Window:      {window_name}")
            print(f"{'='*80}")

            # Only dump tree in CI or when explicitly enabled
            if not (
                is_ci_environment()
                or os.getenv('DUMP_ATSPI_TREE', '').lower() == 'true'
            ):
                print('[INFO] Set DUMP_ATSPI_TREE=true to see available elements')
                return

            try:
                visible_elements = self._get_visible_elements()

                if not visible_elements:
                    print(
                        '\n[WARNING] No visible elements found on current page!',
                    )
                    print(
                        "This might indicate the page hasn't loaded or AT-SPI tree is not ready.\n",
                    )
                    return

                print(
                    f"\n📋 VISIBLE ELEMENTS ON CURRENT PAGE: {
                        len(visible_elements)
                    } total",
                )
                print(f"{'─'*80}\n")

                elements_by_role = self._group_elements_by_role(
                    visible_elements,
                )
                self._print_matching_role_elements(role_name, elements_by_role)
                self._print_other_role_elements(role_name, elements_by_role)

                print(f"{'='*80}\n")

            except Exception as e:
                print(f"[ERROR] Failed to dump element tree: {e}\n")

        except Exception as e:
            print(f"[ERROR] Critical error in _dump_tree_on_failure: {e}")
