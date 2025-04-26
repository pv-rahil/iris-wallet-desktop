"""
This script reads environment variables for client configuration secrets and
writes them into a `config.py` file. The `config.py` file will contain a
dictionary named `client_config` with the provided secrets.

Steps:
1. Read environment variables for the client configuration secrets.
2. Format the secrets into a dictionary structure.
3. Write the formatted dictionary to a `config.py` file.
"""
from __future__ import annotations

import os


def get_env_var(key, default=None):
    """
    Returns the value of an environment variable, or a default value if the variable
    is not set or is an empty string.

    Args:
        key (str): The name of the environment variable.
        default (Any): The fallback value if the variable is not set or is empty.

    Returns:
        Any: The environment variable's value or the default.
    """
    value = os.getenv(key, default)
    # If the value is an empty string, return the default
    return value if value else default


# Read environment variables
client_id = get_env_var('CLIENT_ID')
project_id = get_env_var('PROJECT_ID')
auth_uri = get_env_var('AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
token_uri = get_env_var('TOKEN_URI', 'https://oauth2.googleapis.com/token')
auth_provider_cert_url = get_env_var(
    'AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs',
)
client_secret = get_env_var('CLIENT_SECRET')

# Create the content of config.py
config_content = f"""
client_config = {{
    'installed': {{
        'client_id': '{client_id}',
        'project_id': '{project_id}',
        'auth_uri': '{auth_uri}',
        'token_uri': '{token_uri}',
        'auth_provider_x509_cert_url': '{auth_provider_cert_url}',
        'client_secret': '{client_secret}',
    }},
}}
"""

# Write the content to config.py
with open('../../config.py', 'w', encoding='utf-8') as config_file:
    config_file.write(config_content)
