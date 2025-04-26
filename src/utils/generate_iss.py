"""
This script extracts the application version from the version.py file
and generates a temporary Inno Setup script (updated_iriswallet.iss) with the dynamically
set version information. This ensures that the installer always uses the
correct application version defined in version.py.

Steps:
1. Read the version information from version.py.
2. Read the base Inno Setup script template (windows_iriswallet.iss).
3. Replace the AppVersion placeholder with the actual version.
4. Write the modified content to a temporary Inno Setup script (updated_iriswallet.iss).
"""
from __future__ import annotations

import re

# Read the version from version.py
with open('../version.py', encoding='utf-8') as f:  # Adjust the path as necessary
    content = f.read()

version_match = re.search(r"__version__ = '(.*)'", content)
if version_match:
    version = version_match.group(1)
else:
    raise ValueError('Version not found in version.py')

# Read the base Inno Setup script template
with open('../../windows_iriswallet.iss', encoding='utf-8') as f:  # Adjust the path as necessary
    iss_template = f.read()

# Replace the AppVersion placeholder with the actual version
iss_content = iss_template.replace('{#AppVersion}', version)
# Write the modified content to a temporary Inno Setup script
with open('../../updated_iriswallet.iss', 'w', encoding='utf-8') as f:
    f.write(iss_content)
