"""Request class for making HTTP requests with common methods like GET, POST, PUT, and DELETE."""
from __future__ import annotations

from typing import Any

import requests  # type: ignore

from src.utils.constant import BACKED_URL_LIGHTNING_NETWORK
from src.utils.constant import LIGHTNING_URL_KEY
from src.utils.constant import REQUEST_TIMEOUT
from src.utils.local_store import local_store
from src.utils.logging import logger


class Request:
    """
    This class provides utility methods to handle HTTP requests to a base URL, which is loaded from
    local storage or uses a default backup URL. It also handles merging custom headers with default
    headers, and logs the response time for each request.

    Key Features:
        - Load base URL from local storage or fallback to a default Lightning Network URL.
        - Merge additional headers with default 'Content-Type: application/json' header.
        - Send GET, POST, PUT, and DELETE requests.
        - Log the time taken for each request along with the endpoint being accessed.

    Methods:
        - load_base_url(): Load the base URL for network requests.
        - get(): Perform a GET request.
        - post(): Perform a POST request with optional JSON body and file upload support.
        - put(): Perform a PUT request with optional JSON body.
        - delete(): Perform a DELETE request.
    """
    @staticmethod
    def load_base_url() -> str:
        """This function solves the delay of getting the URL from the local store."""
        base_url = local_store.get_value(
            LIGHTNING_URL_KEY, value_type=str,
        ) or BACKED_URL_LIGHTNING_NETWORK
        return base_url

    @staticmethod
    def _merge_headers(extra_headers: dict[str, str] | None) -> dict[str, str]:
        """Merge default headers with provided headers. This method is private."""
        headers = {'Content-Type': 'application/json'}  # Default header
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @staticmethod
    def get(
        endpoint: str,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        """Send a GET request to the specified endpoint."""
        headers = Request._merge_headers(headers)
        params = params if params is not None else {}
        url = f'{Request.load_base_url()}{endpoint}'

        # Log request initiation
        logger.info('Starting GET request to %s', url)

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
            json=body,
        )

        # Log the endpoint and response time
        logger.info(
            'GET request to %s took %.3f seconds',
            response.url, response.elapsed.total_seconds(),
        )

        return response

    @staticmethod
    def post(
        endpoint: str,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] | None = None,
        files: Any | None = None,
    ) -> requests.Response:
        """Send a POST request to the specified endpoint with a JSON body."""
        headers = Request._merge_headers(headers)
        params = params if params is not None else {}
        url = f'{Request.load_base_url()}{endpoint}'

        # Log request initiation
        logger.info('Starting POST request to %s', url)

        if files is not None:
            response = requests.post(url, files=files, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.post(
                url,
                json=body,
                headers=headers,
                params=params,
                timeout=timeout,
            )

        # Log the endpoint and response time
        logger.info(
            'POST request to %s took %.3f seconds',
            response.url, response.elapsed.total_seconds(),
        )

        return response

    @staticmethod
    def put(
        endpoint: str,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        """Send a PUT request to the specified endpoint with a JSON body."""
        headers = Request._merge_headers(headers)
        params = params if params is not None else {}
        url = f'{Request.load_base_url()}{endpoint}'

        # Log request initiation
        logger.info('Starting PUT request to %s', url)

        response = requests.put(
            url,
            json=body,
            headers=headers,
            params=params,
            timeout=timeout,
        )

        # Log the endpoint and response time
        logger.info(
            'PUT request to %s took %.3f seconds',
            response.url, response.elapsed.total_seconds(),
        )

        return response

    @staticmethod
    def delete(
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        """Send a DELETE request to the specified endpoint."""
        headers = Request._merge_headers(headers)
        params = params if params is not None else {}
        url = f'{Request.load_base_url()}{endpoint}'

        # Log request initiation
        logger.info('Starting DELETE request to %s', url)

        response = requests.delete(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
        )

        # Log the endpoint and response time
        logger.info(
            'DELETE request to %s took %.3f seconds',
            response.url, response.elapsed.total_seconds(),
        )

        return response
