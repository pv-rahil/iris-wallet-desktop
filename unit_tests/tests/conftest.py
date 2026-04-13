# pylint: disable=too-few-public-methods
"""
Pytest fixture to ensure a QApplication instance is available for the test session.

This fixture is automatically used for the entire test session (`autouse=True`)
and ensures that a single instance of `QApplication` is created and shared
among all tests. If an instance of `QApplication` already exists, it will use
the existing one; otherwise, it creates a new instance.

The `scope="session"` parameter ensures that the `QApplication` instance is
created only once per test session, and is reused across all tests, which is
useful for tests that involve PySide6/Qt widgets.

Yields:
    QApplication: An instance of `QApplication` to be used in tests.
"""
from __future__ import annotations

import gc
import os
import tempfile
from unittest.mock import MagicMock

import keyring
import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from src.model.common_operation_model import AppPathsModel
from src.utils.constant import APP_DIR
from src.utils.constant import APP_NAME
from src.utils.constant import CACHE_FOLDER_NAME
from src.utils.constant import LOG_FOLDER_NAME
from src.utils.constant import MNEMONIC_KEY
from src.utils.constant import MULTISIG_COSIGNERS_FILE_NAME
from src.utils.constant import WALLET_DATA_FOLDER_NAME


@pytest.fixture(scope='session', autouse=True)
def qt_app():
    """Fixture to set up the QApplication instance for the test session."""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(autouse=True)
def mock_qthread_start(mocker):
    """
    Automatically mock QThread.start() to prevent actual thread creation.
    This prevents 'QThread: Destroyed while thread is still running' errors
    Tests that need actual threading should call thread.run() directly instead.
    """

    def mock_start_wrapper(self):
        """Mock start that calls run() synchronously instead of starting a thread."""
        # Call run() directly in the same thread instead of starting a new thread
        self.run()

    mocker.patch.object(QThread, 'start', mock_start_wrapper)


@pytest.fixture(autouse=True)
def mock_qthreadpool(mocker):
    """
    Automatically mock QThreadPool to prevent actual thread creation.
    This prevents Qt code execution inside mocks during parallel tests.
    """
    mock_pool = mocker.Mock()
    # Mock globalInstance to return our mock pool
    mocker.patch(
        'PySide6.QtCore.QThreadPool.globalInstance',
        return_value=mock_pool,
    )
    # Mock constructor to return our mock pool
    mocker.patch('PySide6.QtCore.QThreadPool', return_value=mock_pool)
    # Ensure start does nothing
    mock_pool.start.side_effect = lambda runnable: None


@pytest.fixture(autouse=True)
def mock_timer(mocker, request):
    """
    Prevent HeaderFrameViewModel from starting infinite thread loops via QTimer.
    Skip for header_frame_view_model_test.py so it can test the actual logic.
    Skip for repository tests that don't need this mock.
    """
    if 'header_frame_view_model_test.py' in str(request.fspath):
        return

    if 'repository_tests' in str(request.fspath):
        return

    if 'loading_screen_test.py' in str(request.fspath):
        return

    if 'custom_toast_test.py' in str(request.fspath):
        return

    # Mock QTimer.start() globally to prevent timers from running
    mocker.patch('PySide6.QtCore.QTimer.start', return_value=None)

    # Also mock the specific network check method
    mocker.patch(
        'src.viewmodels.header_frame_view_model.HeaderFrameViewModel.start_network_check',
    )


@pytest.fixture(autouse=True)
def gc_collect():
    """Force garbage collection after each test to prevent QObject accumulation."""
    yield
    gc.collect()


@pytest.fixture(autouse=True)
def mock_network_calls(mocker):
    """
    Mock socket.create_connection to prevent real network calls during tests.
    """
    mock_socket = mocker.MagicMock()
    mocker.patch('socket.create_connection', return_value=mock_socket)


@pytest.fixture(autouse=True)
def mock_toast_manager(mocker, request):
    """
    Mock ToastManager methods to isolate tests from UI dependencies.
    ToastManager requires a main window, which is unavailable in unit tests.
    Skipped for toast_test.py to allow direct ToastManager testing.
    """
    # Skip mocking for toast_test.py which specifically tests ToastManager
    if 'toast_test.py' in str(request.fspath):
        return

    mocker.patch('src.views.components.toast.ToastManager.error')
    mocker.patch('src.views.components.toast.ToastManager.success')
    mocker.patch('src.views.components.toast.ToastManager.info')
    mocker.patch('src.views.components.toast.ToastManager.warning')


# ---------------- Global Safety Fixtures -----------------


# Create a session-scoped temporary directory for isolation
_ISOLATION_DIR = tempfile.mkdtemp(prefix='iris_wallet_tests_')


@pytest.fixture(scope='session', autouse=True)
def _isolate_user_dirs():
    """Redirect user data/config/cache dirs to a temporary location for the entire test session."""
    # Set environment variables before any Qt/PySide6 path resolution
    os.environ['HOME'] = _ISOLATION_DIR
    os.environ['XDG_DATA_HOME'] = os.path.join(
        _ISOLATION_DIR, '.local', 'share',
    )
    os.environ['XDG_CONFIG_HOME'] = os.path.join(_ISOLATION_DIR, '.config')
    os.environ['XDG_CACHE_HOME'] = os.path.join(_ISOLATION_DIR, '.cache')
    os.environ['IRIS_WALLET_DATA_DIR'] = os.path.join(
        _ISOLATION_DIR, 'iris-wallet-vault',
    )
    yield
    # Cleanup happens at session end via atexit or finalizer


@pytest.fixture(autouse=True)
def _mock_app_paths(monkeypatch):
    """Mock app_paths and local_store to use isolated test directories."""

    app_path = os.path.join(_ISOLATION_DIR, APP_DIR)
    os.makedirs(app_path, exist_ok=True)

    mock_app_paths = AppPathsModel(
        app_path=app_path,
        iriswallet_temp_folder_path=os.path.join(
            _ISOLATION_DIR, 'temp', f'{APP_NAME}_regtest',
        ),
        cache_path=os.path.join(app_path, CACHE_FOLDER_NAME),
        app_logs_path=os.path.join(app_path, LOG_FOLDER_NAME),
        pickle_file_path=os.path.join(app_path, 'token.pickle'),
        config_file_path=os.path.join(app_path, f'{APP_NAME}-regtest.ini'),
        backup_folder_path=os.path.join(_ISOLATION_DIR, 'temp', 'backup'),
        restore_folder_path=os.path.join(_ISOLATION_DIR, 'temp', 'restore'),
        mnemonic_file_path=os.path.join(app_path, MNEMONIC_KEY),
        multisig_cosigners_file_path=os.path.join(
            app_path, MULTISIG_COSIGNERS_FILE_NAME,
        ),
        wallet_data_folder_path=os.path.join(
            app_path, WALLET_DATA_FOLDER_NAME,
        ),
        download_consignment_path=os.path.join(_ISOLATION_DIR, 'downloads'),
    )

    # Patch app_paths globally
    monkeypatch.setattr(
        'src.utils.build_app_path.app_paths',
        mock_app_paths, raising=False,
    )

    # Patch local_store.base_path
    monkeypatch.setattr(
        'src.utils.local_store.local_store.base_path', app_path, raising=False,
    )


@pytest.fixture(autouse=True)
def _mock_keyring(monkeypatch):
    """Ensure keyring operations are in-memory and never hit the system keychain."""

    _store: dict[tuple[str, str], str] = {}

    def _get_password(service_name: str, username: str) -> str | None:
        return _store.get((service_name, username))

    def _set_password(service_name: str, username: str, password: str) -> None:
        _store[(service_name, username)] = password

    def _delete_password(service_name: str, username: str) -> None:
        _store.pop((service_name, username), None)

    monkeypatch.setattr(keyring, 'get_password', _get_password, raising=False)
    monkeypatch.setattr(keyring, 'set_password', _set_password, raising=False)
    monkeypatch.setattr(
        keyring, 'delete_password',
        _delete_password, raising=False,
    )

    if hasattr(keyring, 'set_keyring'):
        class _InMemoryBackend:  # pragma: no cover
            priority = 1

            def get_password(self, service: str, username: str) -> str | None:
                """Get password from in-memory store."""
                return _get_password(service, username)

            def set_password(self, service: str, username: str, password: str) -> None:
                """Set password in in-memory store."""
                return _set_password(service, username, password)

            def delete_password(self, service: str, username: str) -> None:
                """Delete password from in-memory store."""
                return _delete_password(service, username)
        try:
            keyring.set_keyring(_InMemoryBackend())
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _mock_wallet_session(monkeypatch):
    """Provide a lightweight in-memory WalletDataService session so UI/services don't hit real session."""
    # Do not override WalletDataService session behavior for service tests that validate it
    current = os.environ.get('PYTEST_CURRENT_TEST', '')
    if '/service_tests/' in current:
        return
    drafts: list[dict] = []
    psbts: list[dict] = []

    class _Session:
        def get_btc_balance(self):
            """Get BTC balance."""
            v = MagicMock()
            v.vanilla = MagicMock(settled=0, spendable=0, future=0)
            return v

        def list_psbt(self, signed: bool):
            """List PSBTs."""
            return [p for p in psbts if bool(p.get('signed', False)) == bool(signed)]

        def add_psbt(self, psbt, purpose: str | None = None):
            """Add PSBT."""
            psbts.append({
                'psbt': getattr(psbt, 'psbt', psbt),
                'purpose': purpose, 'id': 'id1', 'signed': False,
            })

        def delete_psbt(self, psbt):
            """Delete PSBT."""
            psbts[:] = [p for p in psbts if p.get('psbt') != psbt]

        def upsert_draft_issue_asset(self, name: str, ticker: str, issued_amount: int):
            """Upsert draft issue asset."""
            for d in drafts:
                if d.get('ticker') == ticker:
                    d.update({'name': name, 'issued_amount': issued_amount})
                    break
            else:
                drafts.append({
                    'id': len(drafts) + 1, 'name': name,
                    'ticker': ticker, 'issued_amount': issued_amount,
                })

        def list_draft_issue_assets(self):
            """List draft issue assets."""
            return list(drafts)

        def delete_draft_issue_asset(self, draft_id):
            """Delete draft issue asset."""
            drafts[:] = [d for d in drafts if d.get('id') != draft_id]

    monkeypatch.setattr(
        'src.data.service.wallet_data_service.WalletDataService.get_session',
        _Session,
        raising=False,
    )


@pytest.fixture(autouse=True)
def _mock_cache_layer(monkeypatch):
    """Prevent real cache/DB writes by overriding cache session used in repositories."""
    class _FakeCache:  # pragma: no cover
        @staticmethod
        def get_cache_session():
            """Get cache session."""
            return MagicMock(invalidate_cache=MagicMock(), update_cache=MagicMock())

    monkeypatch.setattr(
        'src.data.repository.rgb_repository.Cache', _FakeCache, raising=False,
    )


@pytest.fixture(autouse=True)
def _mock_stylesheet_loader(monkeypatch):
    """Avoid disk I/O for stylesheet loading in UI tests by default (tests can override)."""
    monkeypatch.setattr(
        'src.utils.helpers.load_stylesheet',
        lambda *_a, **_k: '', raising=False,
    )
