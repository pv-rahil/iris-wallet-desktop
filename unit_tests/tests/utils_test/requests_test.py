# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for the Request class."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from src.utils.constant import BACKED_URL_LIGHTNING_NETWORK
from src.utils.constant import REQUEST_TIMEOUT
from src.utils.request import Request


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock(spec=requests.Response)
    # Create a mock elapsed time object
    elapsed = MagicMock(spec=timedelta)
    elapsed.total_seconds.return_value = 0.1
    response.elapsed = elapsed
    response.url = 'http://test.com/endpoint'
    return response


@pytest.fixture(autouse=True)
def mock_requests():
    """Mock all requests methods."""
    with patch('src.utils.request.requests') as mock_req:
        mock_req.Response = MagicMock(spec=requests.Response)
        yield mock_req


def test_load_base_url_with_local_store():
    """Test loading base URL from local store."""
    test_url = 'http://test.url'
    with patch('src.utils.request.local_store.get_value', return_value=test_url):
        url = Request.load_base_url()
        assert url == test_url


def test_load_base_url_fallback():
    """Test loading base URL fallback when local store returns None."""
    with patch('src.utils.request.local_store.get_value', return_value=None):
        url = Request.load_base_url()
        assert url == BACKED_URL_LIGHTNING_NETWORK


def test_merge_headers_with_extra():
    """Test merging headers with extra headers."""
    extra_headers = {'Authorization': 'Bearer token'}
    headers = Request._merge_headers(extra_headers)
    assert headers == {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token',
    }


def test_merge_headers_without_extra():
    """Test merging headers without extra headers."""
    headers = Request._merge_headers(None)
    assert headers == {'Content-Type': 'application/json'}


@patch('src.utils.request.logger')
def test_get_request(mock_logger, mock_requests, mock_response):
    """Test GET request functionality."""
    mock_requests.get.return_value = mock_response

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        # Test with various parameters
        response = Request.get(
            endpoint='/test',
            body={'key': 'value'},
            headers={'Authorization': 'Bearer token'},
            params={'param': 'value'},
            timeout=30,
        )

        # Verify the request was made correctly
        mock_requests.get.assert_called_once_with(
            'http://127.0.0.1:3001/test',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token',
            },
            params={'param': 'value'},
            timeout=30,
            json={'key': 'value'},
        )

        # Verify logging
        mock_logger.info.assert_has_calls([
            call('Starting GET request to %s', 'http://127.0.0.1:3001/test'),
            call(
                'GET request to %s took %.3f seconds', mock_response.url,
                mock_response.elapsed.total_seconds(),
            ),
        ])

        assert response == mock_response


@patch('src.utils.request.logger')
def test_post_request(mock_logger, mock_requests, mock_response):
    """Test POST request functionality."""
    mock_requests.post.return_value = mock_response

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        # Test with JSON body
        response = Request.post(
            endpoint='/test',
            body={'key': 'value'},
            headers={'Authorization': 'Bearer token'},
            params={'param': 'value'},
            timeout=30,
        )

        # Verify the request was made correctly
        mock_requests.post.assert_called_once_with(
            'http://127.0.0.1:3001/test',
            json={'key': 'value'},
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token',
            },
            params={'param': 'value'},
            timeout=30,
        )

        # Verify logging
        mock_logger.info.assert_has_calls([
            call('Starting POST request to %s', 'http://127.0.0.1:3001/test'),
            call(
                'POST request to %s took %.3f seconds',
                mock_response.url, mock_response.elapsed.total_seconds(),
            ),
        ])

        assert response == mock_response


@patch('src.utils.request.logger')
def test_post_request_with_files(mock_logger, mock_requests, mock_response):
    """Test POST request with file upload."""
    mock_requests.post.return_value = mock_response
    test_files = {'file': ('test.txt', 'test content')}

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        response = Request.post(
            endpoint='/upload',
            files=test_files,
        )

        # Verify the request was made correctly
        mock_requests.post.assert_called_once_with(
            'http://127.0.0.1:3001/upload',
            files=test_files,
            timeout=REQUEST_TIMEOUT,
        )

        assert response == mock_response


@patch('src.utils.request.logger')
def test_put_request(mock_logger, mock_requests, mock_response):
    """Test PUT request functionality."""
    mock_requests.put.return_value = mock_response

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        response = Request.put(
            endpoint='/test',
            body={'key': 'value'},
            headers={'Authorization': 'Bearer token'},
            params={'param': 'value'},
            timeout=30,
        )

        # Verify the request was made correctly
        mock_requests.put.assert_called_once_with(
            'http://127.0.0.1:3001/test',
            json={'key': 'value'},
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token',
            },
            params={'param': 'value'},
            timeout=30,
        )

        # Verify logging
        mock_logger.info.assert_has_calls([
            call('Starting PUT request to %s', 'http://127.0.0.1:3001/test'),
            call(
                'PUT request to %s took %.3f seconds', mock_response.url,
                mock_response.elapsed.total_seconds(),
            ),
        ])

        assert response == mock_response


@patch('src.utils.request.logger')
def test_delete_request(mock_logger, mock_requests, mock_response):
    """Test DELETE request functionality."""
    mock_requests.delete.return_value = mock_response

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        response = Request.delete(
            endpoint='/test',
            headers={'Authorization': 'Bearer token'},
            params={'param': 'value'},
            timeout=30,
        )

        # Verify the request was made correctly
        mock_requests.delete.assert_called_once_with(
            'http://127.0.0.1:3001/test',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token',
            },
            params={'param': 'value'},
            timeout=30,
        )

        # Verify logging
        mock_logger.info.assert_has_calls([
            call(
                'Starting DELETE request to %s',
                'http://127.0.0.1:3001/test',
            ),
            call(
                'DELETE request to %s took %.3f seconds',
                mock_response.url, mock_response.elapsed.total_seconds(),
            ),
        ])

        assert response == mock_response


def test_request_with_default_params(mock_requests, mock_response):
    """Test requests with default parameters."""
    mock_requests.get.return_value = mock_response

    # Mock the base URL to ensure consistent testing
    with patch('src.utils.request.Request.load_base_url', return_value='http://127.0.0.1:3001'):
        Request.get('/test')

        # Verify defaults were used
        mock_requests.get.assert_called_once_with(
            'http://127.0.0.1:3001/test',
            headers={'Content-Type': 'application/json'},
            params={},
            timeout=None,
            json=None,
        )
