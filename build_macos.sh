#!/bin/bash

# Getting the app name and version from version.py and constant.py.
APP_NAME=$(grep 'APP_NAME' ./src/utils/constant.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
VERSION=$(grep '__version__' ./src/version.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
BITCOIN_NETWORK=$(grep '__network__' ./src/flavour.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
ARCH=$(uname -m)


# Check if APP_NAME and VERSION are non-empty
if [ -z "${APP_NAME}" ]; then
    echo "APP_NAME is empty. Please check the extraction command."
    exit 1
fi

if [ -z "${VERSION}" ]; then
    echo "VERSION is empty. Please check the extraction command."
    exit 1
fi

# Get the current directory
CURRENT_DIR="$(pwd)"
DIST_PATH="$CURRENT_DIR/dist"
APP_BUNDLE="${DIST_PATH}/${APP_NAME}.app"

# Build the .app with PyInstaller
echo "Building .app with PyInstaller..."
poetry run pyinstaller iris_wallet_desktop.spec

# List the contents of the dist directory to see what was created
echo "Contents of dist directory:"
ls -l "${DIST_PATH}"

# Check if the app bundle was created successfully
if [ -d "${APP_BUNDLE}" ]; then
    echo "App bundle created successfully."
    echo "Creating DMG file..."

    # Create the DMG and capture the output directory
    npx create-dmg --dmg-title="${APP_NAME}-${VERSION}" "${APP_BUNDLE}"

    # Locate the newly created DMG file in the current directory
    DMG_FILE=$(ls -1t *.dmg | head -n 1)

    if [ -f "${DMG_FILE}" ]; then
        echo "DMG file created: ${DMG_FILE}"

        # Rename the DMG file
        NEW_DMG_NAME="${APP_NAME}-${VERSION}-${BITCOIN_NETWORK}-${ARCH}.dmg"
        mv "${DMG_FILE}" "${NEW_DMG_NAME}"
        echo "DMG file renamed to: ${NEW_DMG_NAME}"
    else
        echo "Failed to locate the DMG file."
    fi

    echo "Removing app bundle..."
    rm -rf "${DIST_PATH}"

else
    echo "Failed to create app bundle. Expected path not found: ${APP_BUNDLE}"
fi
