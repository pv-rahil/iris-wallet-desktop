""""
Mocked function for common repository.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_init(mocker):
    """Mock the init method of CommonOperationRepository."""
    def _mock_init(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.init',
            return_value=value,
        )
    return _mock_init


@pytest.fixture
def mock_unlock(mocker):
    """Mock the unlock method of CommonOperationRepository."""
    def _mock_unlock(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.unlock',
            return_value=value,
        )
    return _mock_unlock


@pytest.fixture
def mock_lock(mocker):
    """Mock the lock method of CommonOperationRepository."""
    def _mock_lock(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.lock',
            return_value=value,
        )
    return _mock_lock


@pytest.fixture
def mock_backup(mocker):
    """Mock the backup method of CommonOperationRepository."""
    def _mock_backup(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.backup',
            return_value=value,
        )
    return _mock_backup


@pytest.fixture
def mock_change_password(mocker):
    """Mock the change_password method of CommonOperationRepository."""
    def _mock_change_password(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.change_password',
            return_value=value,
        )
    return _mock_change_password


@pytest.fixture
def mock_restore(mocker):
    """Mock the restore method of CommonOperationRepository."""
    def _mock_restore(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.restore',
            return_value=value,
        )
    return _mock_restore


@pytest.fixture
def mock_send_onion_message(mocker):
    """Mock the send_onion_message method of CommonOperationRepository."""
    def _mock_send_onion_message(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.send_onion_message',
            return_value=value,
        )
    return _mock_send_onion_message


@pytest.fixture
def mock_shutdown(mocker):
    """Mock the shutdown method of CommonOperationRepository."""
    def _mock_shutdown(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.shutdown',
            return_value=value,
        )
    return _mock_shutdown


@pytest.fixture
def mock_sign_message(mocker):
    """Mock the sign_message method of CommonOperationRepository."""
    def _mock_sign_message(value):
        return mocker.patch(
            'src.data.repository.common_operations_repository.CommonOperationRepository.sign_message',
            return_value=value,
        )
    return _mock_sign_message
