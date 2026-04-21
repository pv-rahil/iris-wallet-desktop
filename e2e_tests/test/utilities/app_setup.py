# pylint: disable=too-many-instance-attributes, redefined-outer-name, consider-using-with
"""
This module provides a test environment for the Iris Wallet application.
It includes classes and fixtures for setting up and tearing down the test environment.
"""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import time

import keyring
import psutil
import pytest
from dogtail.tree import root

from accessible_constant import APP1_NAME
from accessible_constant import APP2_NAME
from accessible_constant import APP3_NAME
from accessible_constant import APP4_NAME
from accessible_constant import FAKEUSB_MOUNT_PATH
from accessible_constant import FIRST_APPLICATION
from accessible_constant import FIRST_APPLICATION_PATH
from accessible_constant import FIRST_SERVICE
from accessible_constant import FOURTH_APPLICATION
from accessible_constant import FOURTH_APPLICATION_PATH
from accessible_constant import FOURTH_SERVICE
from accessible_constant import LOAD_WALLET_VARIANT
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import SECOND_APPLICATION
from accessible_constant import SECOND_APPLICATION_PATH
from accessible_constant import SECOND_SERVICE
from accessible_constant import THIRD_APPLICATION
from accessible_constant import THIRD_APPLICATION_PATH
from accessible_constant import THIRD_SERVICE
from e2e_tests.test.features.main_features import MainFeatures
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.dogtail_config import refresh_atspi_for_new_app
from e2e_tests.test.utilities.dogtail_config import warm_up_atspi
from e2e_tests.test.utilities.fake_usb import setup_fake_usb
from e2e_tests.test.utilities.reset_app import delete_app_data
from e2e_tests.test.utilities.translation_utils import TranslationManager
from src.utils.constant import APP_NAME
from src.utils.constant import IS_NATIVE_AUTHENTICATION_ENABLED
from src.utils.constant import NATIVE_LOGIN_ENABLED
from src.utils.local_store import local_store
from src.version import __version__


class TestEnvironment:
    """
    A class representing the test environment for the iris wallet application.
    """

    def __init__(self, multi_instance=True, wallet_variant_name: str | None = None):
        """
        Initializes the test environment.

        Args:
            multi_instance (bool): If True, launches both applications. Otherwise, only launches one.
        """
        # Backward-compatible: bool -> 1 or 2, int -> exact number of instances
        if isinstance(multi_instance, bool):
            self.num_instances = 2 if multi_instance else 1
        elif isinstance(multi_instance, int):
            self.num_instances = max(1, min(4, multi_instance))
        else:
            self.num_instances = 2
        # Track originally requested count before we possibly bump due to variant
        self._requested_instances = self.num_instances
        # Initialize process attributes
        self.rgb_processes: list = []
        # Subprocess handles initialized here to satisfy linters
        self.first_process: subprocess.Popen | None = None
        self.second_process: subprocess.Popen | None = None
        self.third_process: subprocess.Popen | None = None
        self.fourth_process: subprocess.Popen | None = None

        self.first_application = None
        self.second_application = None
        self.third_application = None
        self.fourth_application = None

        self.first_page_features: MainFeatures | None = None
        self.second_page_features: MainFeatures | None = None
        self.third_page_features: MainFeatures | None = None
        self.fourth_page_features: MainFeatures | None = None

        self.first_page_objects: MainPageObjects | None = None
        self.second_page_objects: MainPageObjects | None = None
        self.third_page_objects: MainPageObjects | None = None
        self.fourth_page_objects: MainPageObjects | None = None

        self.first_page_operations: BaseOperations | None = None
        self.second_page_operations: BaseOperations | None = None
        self.third_page_operations: BaseOperations | None = None
        self.fourth_page_operations: BaseOperations | None = None

        # Determine whether to enable Fake USB environment based on variant
        self.wallet_variant_name = (wallet_variant_name or '').lower()
        # Force-enable second instance ONLY for load flows when single instance requested
        if self.wallet_variant_name in LOAD_WALLET_VARIANT and self.num_instances < 2:
            self.num_instances = 2
        # Lazy-create FakeUSB only when needed during launch
        self.fake_usb = None

        self.reset_app_data()
        self.remove_keyring_entries(service=FIRST_SERVICE, app_name=APP1_NAME)
        self.remove_keyring_entries(service=SECOND_SERVICE, app_name=APP2_NAME)
        if self.num_instances >= 3:
            self.remove_keyring_entries(
                service=THIRD_SERVICE, app_name=APP3_NAME,
            )
        if self.num_instances >= 4:
            self.remove_keyring_entries(
                service=FOURTH_SERVICE, app_name=APP4_NAME,
            )
        print('[TEST ENV] Warming up AT-SPI before launching applications...')
        warm_up_atspi(timeout=15)

        self.launch_applications()

    def reset_app_data(self, preserve_fake_usb: bool = False):
        """Resets the app data by deleting relevant directories.

        Args:
            preserve_fake_usb: If True, do not delete the fake USB mount directory.
        """
        actual_path = os.path.dirname(local_store.get_path())
        app1_data = actual_path.replace(APP_NAME, FIRST_APPLICATION_PATH)
        app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
        app3_data = actual_path.replace(APP_NAME, THIRD_APPLICATION_PATH)
        app4_data = actual_path.replace(APP_NAME, FOURTH_APPLICATION_PATH)

        delete_app_data(app1_data)
        if self.num_instances >= 2:
            delete_app_data(app2_data)
        if self.num_instances >= 3:
            delete_app_data(app3_data)
        if self.num_instances >= 4:
            delete_app_data(app4_data)

        # Only clean fake USB if not explicitly preserved (for backup/restore tests)
        if not preserve_fake_usb:
            shutil.rmtree(FAKEUSB_MOUNT_PATH, ignore_errors=True)

    def launch_applications(self):
        """Launches the required iris wallet applications and maximizes the windows."""
        env = os.environ.copy()
        env['QT_ACCESSIBILITY'] = '1'
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            usb_env, _ = setup_fake_usb()
            env.update(usb_env)

        self.first_process = subprocess.Popen(
            [f"""e2e_tests/applications/iris-wallet-vault_{
                APP1_NAME
            }-{__version__}-x86_64.AppImage"""],
            env=env,
            stderr=subprocess.PIPE,
        )
        self.wait_for_application(
            FIRST_APPLICATION, process=self.first_process,
        )

        # Maximize first application window
        subprocess.run(
            [
                'wmctrl', '-r', FIRST_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )
        print(f"[SETUP] Initializing {FIRST_APPLICATION}")
        # Use frame node for better element scoping when multiple apps are running
        self.first_application = self._find_application_frame(
            FIRST_APPLICATION,
        )
        print(f"""[SETUP] Successfully identified frame for
              {FIRST_APPLICATION}: {self.first_application}""")
        self.first_page_features = MainFeatures(self.first_application)
        self.first_page_objects = MainPageObjects(self.first_application)
        self.first_page_operations = BaseOperations(self.first_application)

        self.first_page_operations.register_current_environment(self)

        if self.num_instances >= 2:
            self.second_process = subprocess.Popen(
                [f"""e2e_tests/applications/iris-wallet-vault_{
                    APP2_NAME
                }-{__version__}-x86_64.AppImage"""],
                env=env,
                stderr=subprocess.PIPE,
            )
            self.wait_for_application(
                SECOND_APPLICATION, process=self.second_process,
            )

            # Maximize second application window
            subprocess.run(
                [
                    'wmctrl', '-r', SECOND_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            print(f"[SETUP] Initializing {SECOND_APPLICATION}")
            # Use frame node for better element scoping when multiple apps are running
            self.second_application = self._find_application_frame(
                SECOND_APPLICATION,
            )
            print(f"""[SETUP] Successfully identified frame for
                  {SECOND_APPLICATION}: {self.second_application}""")
            self.second_page_features = MainFeatures(self.second_application)
            self.second_page_objects = MainPageObjects(self.second_application)
            self.second_page_operations = BaseOperations(
                self.second_application,
            )

        if self.num_instances >= 3:
            # Wait for second app to be fully stable before launching third
            self._wait_for_app_stability(self.second_application)
            # Force AT-SPI tree refresh before launching third app
            refresh_atspi_for_new_app()
            self.third_process = subprocess.Popen(
                [f"""e2e_tests/applications/iris-wallet-vault_{
                    APP3_NAME
                }-{__version__}-x86_64.AppImage"""],
                env=env,
                stderr=subprocess.PIPE,
            )
            self.wait_for_application(
                THIRD_APPLICATION, process=self.third_process,
            )

            subprocess.run(
                [
                    'wmctrl', '-r', THIRD_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            print(f"[SETUP] Initializing {THIRD_APPLICATION}")
            # Use frame node for better element scoping when multiple apps are running
            self.third_application = self._find_application_frame(
                THIRD_APPLICATION,
            )
            print(f"""[SETUP] Successfully identified frame for
                  {THIRD_APPLICATION}: {self.third_application}""")
            self.third_page_features = MainFeatures(self.third_application)
            self.third_page_objects = MainPageObjects(self.third_application)
            self.third_page_operations = BaseOperations(
                self.third_application,
            )

        if self.num_instances >= 4:
            # Wait for third app to be fully stable before launching fourth
            self._wait_for_app_stability(self.third_application)
            # Force AT-SPI tree refresh before launching fourth app
            refresh_atspi_for_new_app()
            self.fourth_process = subprocess.Popen(
                [f"""e2e_tests/applications/iris-wallet-vault_{
                    APP4_NAME
                }-{__version__}-x86_64.AppImage"""],
                env=env,
                stderr=subprocess.PIPE,
            )
            self.wait_for_application(
                FOURTH_APPLICATION, process=self.fourth_process,
            )

            subprocess.run(
                [
                    'wmctrl', '-r', FOURTH_APPLICATION, '-b',
                    'add,maximized_vert,maximized_horz',
                ],
                check=True,
            )
            print(f"[SETUP] Initializing {FOURTH_APPLICATION}")
            # Use frame node for better element scoping when multiple apps are running
            self.fourth_application = self._find_application_frame(
                FOURTH_APPLICATION,
            )
            print(f"""[SETUP] Successfully identified frame for
                  {FOURTH_APPLICATION}: {self.fourth_application}""")
            self.fourth_page_features = MainFeatures(self.fourth_application)
            self.fourth_page_objects = MainPageObjects(self.fourth_application)
            self.fourth_page_operations = BaseOperations(
                self.fourth_application,
            )

    def _wait_for_app_stability(self, app_frame, timeout: int = 10):
        """Wait for app to be fully stable by checking for UI element."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if app_frame and app_frame.child(roleName='radio button', requireResult=False):
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def _find_application_node(self, app_name):
        """Helper to find the stable application node for a given app name."""
        print(f"[DEBUG] Searching for parent application of: {app_name}")

        # Method 1: Search through all applications to find one containing the target frame
        try:
            for app in root.applications():
                if 'iris' in app.name.lower():
                    # Check if this app has the frame we're looking for
                    for child in app.children:
                        if child.roleName == 'frame' and child.name == app_name:
                            print(f"""[DEBUG] Found parent application '
                                  {app.name}' for frame '{app_name}'""")
                            return app
        except Exception:
            pass

        # Method 2: Fallback - find the frame and get its parent
        try:
            frame = root.child(roleName='frame', name=app_name)
            if frame:
                parent = frame.parent
                if parent and parent.roleName == 'application':
                    return parent
                return frame  # Return frame as last resort if parent is not app
        except Exception:
            pass

        # This is dogtail's standard way to get application root by hint
        return root.application(app_name)

    def _find_application_frame(self, app_name):
        """
        Helper to find the frame node for a given app name.
        This is used for single-sig to ensure element searches are scoped to the correct frame.
        Returns frame node instead of application node for better element scoping.
        """
        # Extract app identifier from frame name
        match = re.search(r'(test_app_\d+|app_\d+)$', app_name)
        target_app_identifier = match.group(1) if match else None

        # Search through all applications to find the correct frame
        try:
            apps = [a for a in root.applications() if 'iris' in a.name.lower()]

            # Sort apps to prioritize the target app
            if target_app_identifier:
                apps = sorted(
                    apps, key=lambda a: 0 if target_app_identifier in a.name else 1,
                )

            for app in apps:
                # Check if this app matches the target identifier
                if target_app_identifier and target_app_identifier not in app.name:
                    continue

                # Find the frame within this application
                for child in app.children:
                    if child.roleName == 'frame' and child.name == app_name:
                        print(f"""[DEBUG] Found frame '
                              {app_name}' under app '{app.name}'""")
                        return child
        except Exception:
            pass

        # Fallback - find frame directly from root
        try:
            frame = root.child(roleName='frame', name=app_name)
            if frame:
                return frame
        except Exception:
            pass

        print(f"[WARN] No frame found for '{app_name}'")
        return None

    def _find_showing_frame(self, app_name, retry_count=3, retry_delay=1.0):
        """Helper to find a showing frame for a given app name.
        """
        def timeout_handler(signum, frame):
            raise TimeoutError('AT-SPI call timed out')
        match = re.search(r'(test_app_\d+|app_\d+)$', app_name)
        target_app_identifier = match.group(1) if match else None

        for attempt in range(retry_count):
            try:
                # Set timeout for AT-SPI calls
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout per attempt

                # Try to find visible frame under visible application nodes first
                apps = [
                    a for a in root.applications(
                    ) if 'iris' in a.name.lower()
                ]
                print(f"""[FIND_FRAME] Attempt
                      {attempt+1}/{retry_count}, found {len(apps)} iris apps, target: {target_app_identifier}""")
                signal.alarm(0)  # Cancel alarm after successful call

            except TimeoutError:
                print('[FIND_FRAME] AT-SPI timeout getting applications')
                signal.alarm(0)
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                continue
            except Exception as e:
                signal.alarm(0)
                print(f"[FIND_FRAME] Exception: {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                continue

            # Sort apps to prioritize the target app
            if target_app_identifier:
                # Sort so that apps matching target_app_identifier come first
                apps = sorted(
                    apps, key=lambda a: 0 if target_app_identifier in a.name else 1,
                )

            for app in apps:
                if app.showing:
                    # Check if this app matches the target identifier
                    if target_app_identifier and target_app_identifier not in app.name:
                        print(f"""[FIND_FRAME] Skipping app '
                              {app.name}' (doesn't match target '{target_app_identifier}')""")
                        continue

                    try:
                        frame = app.child(roleName='frame', name=app_name)
                        if frame and frame.showing:
                            print(f"""[FIND_FRAME] Found showing frame '
                                  {app_name}' under app '{app.name}'""")
                            return frame
                    except Exception as e:
                        print(f"""[FIND_FRAME] No frame '
                              {app_name}' under app '{app.name}': {e}""")
                        continue

            # Wait before retry
            if attempt < retry_count - 1:
                print(f"""[FIND_FRAME] Frame not showing, waiting
                      {retry_delay}s...""")
                time.sleep(retry_delay)

        # Fallback to direct search
        print(f"[FIND_FRAME] Using fallback direct search for '{app_name}'")
        return root.child(roleName='frame', name=app_name)

    def wait_for_application(self, name, timeout=60, process=None):
        """Wait for the application and its main frame to be visible.
        """
        def timeout_handler(signum, frame):
            raise TimeoutError('AT-SPI call timed out')

        print(f"[SETUP] Waiting for visibility of {name} (timeout {timeout}s)")
        start_time = time.time()
        poll_interval = 0.5
        last_refresh_time = 0

        while time.time() - start_time < timeout:
            # Early failure detection: check if process died
            if process and process.poll() is not None:
                exit_code = process.poll()
                # Try to capture any stderr output for debugging
                stderr_output = ''
                if hasattr(process, 'stderr') and process.stderr:
                    try:
                        stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
                    except Exception:
                        pass
                error_msg = f"Application '{
                    name
                }' process exited unexpectedly with code {exit_code}"
                if stderr_output:
                    # Last 500 chars
                    error_msg += f"\nStderr: {stderr_output[-500:]}"
                raise RuntimeError(error_msg)

            # Force AT-SPI tree refresh every 2 seconds to detect new apps
            # This is critical for CI where AT-SPI caching causes stale data
            current_time = time.time()
            if current_time - last_refresh_time > 2.0:
                try:
                    _ = root.children  # Force refresh
                    last_refresh_time = current_time
                except Exception:
                    pass

            try:
                # Set timeout for AT-SPI calls
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout per iteration

                try:
                    # Use our helper to see if an application node with a frame exists
                    app = self._find_application_node(name)
                    if app:
                        # Also check if it has a showing frame
                        frame = app.child(roleName='frame', name=name)
                        if frame and frame.showing:
                            signal.alarm(0)  # Cancel alarm
                            print(f"[SETUP] {name} is showing and ready.")
                            return True
                except TimeoutError:
                    print(f"[SETUP] AT-SPI timeout while searching for {name}")
                finally:
                    signal.alarm(0)  # Ensure alarm is cancelled

            except Exception as e:
                signal.alarm(0)
                print(f"[SETUP] Exception while searching for {name}: {e}")
            time.sleep(poll_interval)
        raise TimeoutError(
            f"""Application '{name}' failed to start or show frame within {
                timeout
            } seconds""",
        )

    def get_child_pids(self, parent_pid):
        """Returns a list of child process PIDs for a given parent process."""
        try:
            parent = psutil.Process(parent_pid)
            return [child.pid for child in parent.children(recursive=True)]
        except psutil.NoSuchProcess:
            return []

    def terminate_process(self, process):
        """Gracefully terminates a process and its children."""
        if not process:
            return

        pid = process.pid
        if not pid:
            return

        # Get all child processes
        child_pids = self.get_child_pids(pid)

        os.kill(pid, signal.SIGKILL)  # Force shutdown
        for child_pid in child_pids:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already terminated

    def terminate(self):
        """Cleans up the test environment by shutting down applications"""
        self.terminate_process(self.first_process)
        if self.num_instances >= 2:
            self.terminate_process(self.second_process)
        if self.num_instances >= 3:
            self.terminate_process(self.third_process)
        if self.num_instances >= 4:
            self.terminate_process(self.fourth_process)

        if self.fake_usb:
            self.fake_usb.cleanup()

    def restart(self, reset_data=True):
        """Restarts the application by terminating, optionally resetting data, and relaunching."""
        self.terminate()

        if reset_data:
            self.reset_app_data()

        self.launch_applications()

    def restart_single_instance(self, reset_data: bool = True, preserve_fake_usb: bool = False):
        """Restart only the first application instance and ensure environment runs single-instance.
        This is useful for flows where we initially needed multiple instances (e.g. load/on-device),
        but subsequent tests should continue with a single app instance only.
        """
        # Terminate any running processes (first/second/third if present)
        self.terminate()

        # Force the environment to single-instance going forward
        self.num_instances = 1

        # Optionally clear app data (first app only is strictly necessary here)
        if reset_data:
            self.reset_app_data(preserve_fake_usb=preserve_fake_usb)

        # Relaunch only the first application
        self.launch_applications()

    def reset_first_instance(self, reset_data: bool = True, skip_warmup: bool = False):
        """Reset and relaunch only the first application instance."""
        # Kill only the first process
        self.terminate_process(self.first_process)
        self.first_process = None

        # Optionally clear only the first app's data
        if reset_data:
            actual_path = os.path.dirname(local_store.get_path())
            app1_data = actual_path.replace(APP_NAME, FIRST_APPLICATION_PATH)
            delete_app_data(app1_data)

        # Recreate Fake USB environment if required by variant
        # Always include QT_ACCESSIBILITY for AT-SPI to work properly
        env = os.environ.copy()
        env['QT_ACCESSIBILITY'] = '1'
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            usb_env, _ = setup_fake_usb()
            env.update(usb_env)

        # Relaunch first application and reinitialize its page abstractions
        self.first_process = subprocess.Popen(
            [f"""e2e_tests/applications/iris-wallet-vault_{
                APP1_NAME
            }-{__version__}-x86_64.AppImage"""],
            env=env,
        )
        self.wait_for_application(
            FIRST_APPLICATION, process=self.first_process,
        )

        subprocess.run(
            [
                'wmctrl', '-r', FIRST_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )

        # Use the same helper as launch_applications for consistent node finding
        self.first_application = self._find_showing_frame(FIRST_APPLICATION)
        print(f"[RESET] first_application node: {self.first_application}")
        print(f"""[RESET] first_application.showing:
              {getattr(self.first_application, 'showing', 'N/A')}""")

        # Ensure the frame is actually showing before proceeding
        if not getattr(self.first_application, 'showing', False):
            print('[RESET] Warning: frame not showing, waiting...')
            time.sleep(2.0)
            self.first_application = self._find_showing_frame(
                FIRST_APPLICATION,
            )

        self.first_page_features = MainFeatures(self.first_application)
        self.first_page_objects = MainPageObjects(self.first_application)
        self.first_page_operations = BaseOperations(self.first_application)
        print(f"[RESET] Page objects reinitialized for {FIRST_APPLICATION}")

        # Force AT-SPI tree refresh to clear stale element caches
        # Skip if part of batch reset (will be done once at the end)
        if not skip_warmup:
            warm_up_atspi(timeout=10)
            time.sleep(1.0)
            print('[RESET] AT-SPI tree refreshed')

    def reset_second_instance(self, reset_data: bool = True, skip_warmup: bool = False):
        """Reset and relaunch only the second application instance."""
        # If only one instance is active, nothing to do
        if self.num_instances < 2:
            return

        # Kill only the second process
        self.terminate_process(self.second_process)
        self.second_process = None

        # Optionally clear only the second app's data
        if reset_data:
            actual_path = os.path.dirname(local_store.get_path())
            app2_data = actual_path.replace(APP_NAME, SECOND_APPLICATION_PATH)
            delete_app_data(app2_data)

        # Recreate Fake USB environment if required by variant
        # Always include QT_ACCESSIBILITY for AT-SPI to work properly
        env = os.environ.copy()
        env['QT_ACCESSIBILITY'] = '1'
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            usb_env, _ = setup_fake_usb()
            env.update(usb_env)

        # Relaunch second application and reinitialize its page abstractions
        self.second_process = subprocess.Popen(
            [f"""e2e_tests/applications/iris-wallet-vault_{
                APP2_NAME
            }-{__version__}-x86_64.AppImage"""],
            env=env,
        )
        self.wait_for_application(
            SECOND_APPLICATION, process=self.second_process,
        )

        subprocess.run(
            [
                'wmctrl', '-r', SECOND_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )
        print(f"[RESET] Initializing {SECOND_APPLICATION}")
        self.second_application = self._find_showing_frame(SECOND_APPLICATION)
        print(f"""[RESET] Successfully identified frame for
              {SECOND_APPLICATION}: {self.second_application}""")
        self.second_page_features = MainFeatures(self.second_application)
        self.second_page_objects = MainPageObjects(self.second_application)
        self.second_page_operations = BaseOperations(self.second_application)
        print(f"[RESET] Page objects reinitialized for {SECOND_APPLICATION}")

        # Force AT-SPI tree refresh with longer delay to ensure elements are visible
        # Skip if part of batch reset (will be done once at the end)
        if not skip_warmup:
            warm_up_atspi(timeout=10)
            # Additional wait for UI and AT-SPI bus to stabilize
            time.sleep(2.0)
            print('[RESET] AT-SPI tree refreshed')

    def reset_third_instance(self, reset_data: bool = True, skip_warmup: bool = False):
        """Reset and relaunch only the third application instance."""
        # If less than 3 instances are active, nothing to do
        if self.num_instances < 3:
            return

        # Kill only the third process
        self.terminate_process(self.third_process)
        self.third_process = None

        # Optionally clear only the third app's data
        if reset_data:
            actual_path = os.path.dirname(local_store.get_path())
            app3_data = actual_path.replace(APP_NAME, THIRD_APPLICATION_PATH)
            delete_app_data(app3_data)

        # Recreate Fake USB environment if required by variant
        # Always include QT_ACCESSIBILITY for AT-SPI to work properly
        env = os.environ.copy()
        env['QT_ACCESSIBILITY'] = '1'
        if self.wallet_variant_name in REQUIRE_USB_VARIANTS:
            usb_env, _ = setup_fake_usb()
            env.update(usb_env)

        # Relaunch third application and reinitialize its page abstractions
        self.third_process = subprocess.Popen(
            [f"""e2e_tests/applications/iris-wallet-vault_{
                APP3_NAME
            }-{__version__}-x86_64.AppImage"""],
            env=env,
        )
        self.wait_for_application(
            THIRD_APPLICATION, process=self.third_process,
        )

        subprocess.run(
            [
                'wmctrl', '-r', THIRD_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )
        print(f"[RESET] Initializing {THIRD_APPLICATION}")
        self.third_application = self._find_showing_frame(THIRD_APPLICATION)
        print(f"""[RESET] Successfully identified frame for
              {THIRD_APPLICATION}: {self.third_application}""")
        self.third_page_features = MainFeatures(self.third_application)
        self.third_page_objects = MainPageObjects(self.third_application)
        self.third_page_operations = BaseOperations(self.third_application)
        print(f"[RESET] Page objects reinitialized for {THIRD_APPLICATION}")

        # Force AT-SPI tree refresh
        # Skip if part of batch reset (will be done once at the end)
        if not skip_warmup:
            warm_up_atspi(timeout=10)
            time.sleep(1.0)
            print('[RESET] AT-SPI tree refreshed')

    def reset_fourth_instance(self, reset_data: bool = False, skip_warmup: bool = False):
        """Reset and relaunch only the fourth application instance."""
        # If only less than 4 instances are active, nothing to do
        if self.num_instances < 4:
            return

        # Kill only the fourth process
        self.terminate_process(self.fourth_process)
        self.fourth_process = None

        # Optionally clear only the fourth app's data
        if reset_data:
            actual_path = os.path.dirname(local_store.get_path())
            app4_data = actual_path.replace(APP_NAME, FOURTH_APPLICATION_PATH)
            delete_app_data(app4_data)

        # Always include QT_ACCESSIBILITY for AT-SPI to work properly
        env = os.environ.copy()
        env['QT_ACCESSIBILITY'] = '1'

        # Relaunch fourth application and reinitialize its page abstractions
        self.fourth_process = subprocess.Popen(
            [f'e2e_tests/applications/iris-wallet-vault_{
                APP4_NAME
            }-{__version__}-x86_64.AppImage'],
            env=env,
        )
        self.wait_for_application(
            FOURTH_APPLICATION, process=self.fourth_process,
        )

        subprocess.run(
            [
                'wmctrl', '-r', FOURTH_APPLICATION, '-b',
                'add,maximized_vert,maximized_horz',
            ],
            check=True,
        )
        print(f"[RESET] Initializing {FOURTH_APPLICATION}")
        self.fourth_application = self._find_showing_frame(FOURTH_APPLICATION)
        print(f"""[RESET] Successfully identified frame for
              {FOURTH_APPLICATION}: {self.fourth_application}""")
        self.fourth_page_features = MainFeatures(self.fourth_application)
        self.fourth_page_objects = MainPageObjects(self.fourth_application)
        self.fourth_page_operations = BaseOperations(self.fourth_application)
        print(f"[RESET] Page objects reinitialized for {FOURTH_APPLICATION}")

        # Force AT-SPI tree refresh
        # Skip if part of batch reset (will be done once at the end)
        if not skip_warmup:
            warm_up_atspi(timeout=10)
            time.sleep(1.0)
            print('[RESET] AT-SPI tree refreshed')

    def reset_offline_multisig_instances(self, reset_data: bool = False):
        """Reset first, second, third, and fourth application instances for offline multisig tests."""
        # Reset all instances with skip_warmup=True to avoid redundant AT-SPI calls
        # Each reset adds 2s delay between kills to prevent AT-SPI bus overload
        self.reset_first_instance(reset_data=reset_data, skip_warmup=True)
        time.sleep(2.0)  # Delay between resets to prevent AT-SPI bus overload
        self.reset_second_instance(reset_data=reset_data, skip_warmup=True)
        time.sleep(2.0)
        self.reset_third_instance(reset_data=reset_data, skip_warmup=True)
        time.sleep(2.0)
        self.reset_fourth_instance(reset_data=reset_data, skip_warmup=True)

        # Final AT-SPI tree refresh to clear any stale references (done once for all)
        warm_up_atspi(timeout=10)
        print('[RESET] All offline multisig instances reset and stable')

    def remove_keyring_entries(self, service, app_name):
        """Removes keyring entries for a given service and application name."""
        keys = [
            NATIVE_LOGIN_ENABLED,
            IS_NATIVE_AUTHENTICATION_ENABLED,
        ]

        for key in keys:
            try:
                keyring.delete_password(service, f"{key}_{app_name}")
                print(f"Removed {key}{app_name} from keyring.")
            except keyring.errors.PasswordDeleteError:
                print(f"No entry found for {key}_{app_name}.")


@pytest.fixture(scope='module')
def test_environment(request, wallet_variant_name: str):
    """
    A fixture that sets up and tears down the test environment.

    Use `request.param` to determine if multi-instance should be enabled.
    """
    multi_instance = getattr(request, 'param', True)
    env = TestEnvironment(
        multi_instance=multi_instance,
        wallet_variant_name=wallet_variant_name,
    )
    # Register the environment so features can trigger environment-level resets
    base_operation = BaseOperations()
    base_operation.register_current_environment(env)
    yield env
    env.terminate()


@pytest.fixture
def wallets_and_operations(test_environment: TestEnvironment):
    """
    A fixture that provides dynamic access to the TestEnvironment handles.
    """

    class _HandlesProxy:
        """
        A proxy class that provides dynamic access to the TestEnvironment handles.
        """

        def __init__(self, env: TestEnvironment):
            self._env = env

        # Features
        @property
        def first_page_features(self):
            """
            Returns the first page features.
            """
            return self._env.first_page_features

        @property
        def second_page_features(self):
            """
            Returns the second page features.
            """
            return self._env.second_page_features if self._env.num_instances >= 2 else None

        @property
        def third_page_features(self):
            """
            Returns the third page features.
            """
            return self._env.third_page_features if self._env.num_instances >= 3 else None

        @property
        def fourth_page_features(self):
            """
            Returns the fourth page features.
            """
            return self._env.fourth_page_features if self._env.num_instances >= 4 else None

        # Objects
        @property
        def first_page_objects(self):
            """
            Returns the first page objects.
            """
            return self._env.first_page_objects

        @property
        def second_page_objects(self):
            """
            Returns the second page objects.
            """
            return self._env.second_page_objects if self._env.num_instances >= 2 else None

        @property
        def third_page_objects(self):
            """
            Returns the third page objects.
            """
            return self._env.third_page_objects if self._env.num_instances >= 3 else None

        @property
        def fourth_page_objects(self):
            """
            Returns the fourth page objects.
            """
            return self._env.fourth_page_objects if self._env.num_instances >= 4 else None

        # Operations
        @property
        def first_page_operations(self):
            """
            Returns the first page operations.
            """
            return self._env.first_page_operations

        @property
        def second_page_operations(self):
            """
            Returns the second page operations.
            """
            return self._env.second_page_operations if self._env.num_instances >= 2 else None

        @property
        def third_page_operations(self):
            """
            Returns the third page operations.
            """
            return self._env.third_page_operations if self._env.num_instances >= 3 else None

        @property
        def fourth_page_operations(self):
            """
            Returns the fourth page operations.
            """
            return self._env.fourth_page_operations if self._env.num_instances >= 4 else None

    return _HandlesProxy(test_environment)


@pytest.fixture(scope='session', autouse=True)
def load_qm_translation():
    """Load the .qm translation file once per test session."""
    TranslationManager.load_translation()
