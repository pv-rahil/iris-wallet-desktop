#!/usr/bin/env bash

set -e  # Exit on error
set -o pipefail  # Exit if any command in a pipeline fails
set -u  # Treat unset variables as errors

export QT_LOGGING_RULES="qt.accessibility.atspi*=false"

# Define paths
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
E2E_DIR="$ROOT_DIR/e2e_tests"
TESTS_DIR="$E2E_DIR/test/spec"
APPLICATIONS_DIR="$E2E_DIR/applications"
VERSION=$(grep '__version__' ./src/version.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
APP1_NAME=$(grep '^APP1_NAME' accessible_constant.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
APP2_NAME=$(grep '^APP2_NAME' accessible_constant.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)
APP3_NAME=$(grep '^APP3_NAME' accessible_constant.py | awk -F'=' '{print $2}' | tr -d ' "' | xargs)

# Paths for the built applications
FIRST_WALLET_NAME="iris-wallet-vault_${APP1_NAME}-${VERSION}-x86_64.AppImage"
SECOND_WALLET_NAME="iris-wallet-vault_${APP2_NAME}-${VERSION}-x86_64.AppImage"
THIRD_WALLET_NAME="iris-wallet-vault_${APP3_NAME}-${VERSION}-x86_64.AppImage"

APP1_PATH="$APPLICATIONS_DIR/$FIRST_WALLET_NAME"
APP2_PATH="$APPLICATIONS_DIR/$SECOND_WALLET_NAME"
APP3_PATH="$APPLICATIONS_DIR/$THIRD_WALLET_NAME"

# Paths for constants file
CONSTANT_FILE="./src/utils/constant.py"
BACKUP_FILE="./src/utils/constant_backup.py"

# Command-line arguments
TEST_FILE=""
RUN_ALL=false
FORCE_BUILD=false
# Collect extra pytest args (e.g., --wallet-variant <name>)
PYTEST_EXTRA_ARGS=()
WALLET_VARIANT_SPECIFIED=false
SPECIFIED_WALLET_VARIANT=""
SERVE_ALLURE=false
GENERATE_ALLURE=false

# Default wallet variants (as documented in e2e test help)
# These will be used when no --wallet-variant is explicitly provided.
DEFAULT_WALLET_VARIANTS=(
  "online_create_on_device"
  "online_create_hardware"
  "offline_create_on_device"
  "offline_create_hardware"
  "online_load_on_device"
  "offline_load_on_device"
  "online_load_hardware"
  "offline_load_hardware"
  "online_watch_only"
)

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force-build)
            FORCE_BUILD=true
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --serve-allure)
            SERVE_ALLURE=true
            shift
            ;;
        --generate-allure)
            GENERATE_ALLURE=true
            shift
            ;;
        --wallet-variant)
            # forward to pytest with its value
            shift
            if [[ $# -eq 0 ]]; then
                echo "Error: --wallet-variant requires a value";
                exit 1
            fi
            PYTEST_EXTRA_ARGS+=("--wallet-variant" "$1")
            WALLET_VARIANT_SPECIFIED=true
            SPECIFIED_WALLET_VARIANT="$1"
            shift
            ;;
        --*)
            # Forward any other unknown long options to pytest as-is
            PYTEST_EXTRA_ARGS+=("$1")
            shift
            ;;
        *)
            # First bare arg is treated as TEST_FILE; subsequent bare args
            # are forwarded to pytest (to avoid overriding TEST_FILE when
            # option values are passed positionally)
            if [[ -z "$TEST_FILE" ]]; then
                TEST_FILE=$1
            else
                PYTEST_EXTRA_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

# Ensure constants are restored if the script exits unexpectedly
trap restore_constants EXIT

# Function to temporarily modify constants before build
modify_constants() {
    echo "Modifying constants for testing..."
    [[ ! -f "$BACKUP_FILE" ]] && cp "$CONSTANT_FILE" "$BACKUP_FILE"

    sed -i -E "
        s|INDEXER_URL_REGTEST = 'electrum.rgbtools.org:50041'|INDEXER_URL_REGTEST = '127.0.0.1:50001'|;
        s|PROXY_ENDPOINT_REGTEST = 'rpcs://proxy.iriswallet.com/0.2/json-rpc'|PROXY_ENDPOINT_REGTEST = 'rpc://127.0.0.1:3000/json-rpc'|;
    " "$CONSTANT_FILE"

    echo "Constants modified."
}

# Function to restore original constants after build
restore_constants() {
    if [[ -f "$BACKUP_FILE" ]]; then
        echo "Restoring original constants..."
        mv -f "$BACKUP_FILE" "$CONSTANT_FILE"
        echo "Original constants restored."
    fi
}

# Function to move an application after it is built
move_application() {
    local app_name=$1
    local app_path="$ROOT_DIR/$app_name"

    echo "Moving $app_name to $APPLICATIONS_DIR..."
    mkdir -p "$APPLICATIONS_DIR"

    if [[ -f "$app_path" ]]; then
        mv -f "$app_path" "$APPLICATIONS_DIR/"
        echo "$app_name moved successfully."
    else
        echo "Error: $app_name not found at $app_path"
        exit 1
    fi
}

# Function to build applications if they are missing
build_applications() {
    echo "Building applications..."

    cd "$ROOT_DIR" || exit 1

    # Modify constants before build
    modify_constants

    echo "Building first wallet..."
    build-iris-wallet --network regtest --distribution appimage --app-name "${APP1_NAME}" &
    wait $!
    move_application "$FIRST_WALLET_NAME"

    echo "Building second wallet..."
    build-iris-wallet --network regtest --distribution appimage --app-name "${APP2_NAME}" &
    wait $!
    move_application "$SECOND_WALLET_NAME"

    echo "Building third wallet..."
    build-iris-wallet --network regtest --distribution appimage --app-name "${APP3_NAME}" &
    wait $!
    move_application "$THIRD_WALLET_NAME"

    echo "Build process completed."
}

ensure_applications_exist() {
    if [[ "$FORCE_BUILD" == true ]]; then
        echo "--force-build flag detected. Rebuilding applications..."
        build_applications
        exit 0
    fi

    if [[ ! -f "$APP1_PATH" || ! -f "$APP2_PATH" || ! -f "$APP3_PATH" ]]; then
        echo "One or more applications are missing. Initiating build..."
        build_applications
    else
        echo "All applications are available. Proceeding with tests."
    fi
}

run_e2e_tests() {
    local results_root_dir="allure-results"
    local reports_root_dir="allure-reports"

    echo "Running E2E tests"

    # Clean previous aggregated results and recreate root
    rm -rf "$results_root_dir"
    mkdir -p "$results_root_dir"
    # Prepare reports directory when generating
    if [[ "$GENERATE_ALLURE" == true ]]; then
        rm -rf "$reports_root_dir"
        mkdir -p "$reports_root_dir"
    fi

    # Determine base target (all tests or a single file)
    local base_target=""
    if [[ "$RUN_ALL" == true ]]; then
        echo "Running full test suite..."
        base_target="$TESTS_DIR/"
    elif [[ -n "$TEST_FILE" ]]; then
        echo "Running single test file: $TEST_FILE"
        base_target="$TESTS_DIR/$TEST_FILE"
    else
        echo "No test file provided. Use --all to run all tests."
        exit 1
    fi

    # If a wallet variant was provided, run once. Otherwise iterate through defaults.
    if [[ "$WALLET_VARIANT_SPECIFIED" == true ]]; then
        echo "Running tests with explicitly provided wallet variant: ${SPECIFIED_WALLET_VARIANT}"
        local results_dir="$results_root_dir/${SPECIFIED_WALLET_VARIANT:-specified}"
        mkdir -p "$results_dir"
        if ! pytest -s "$base_target" --alluredir="$results_dir" ${PYTEST_EXTRA_ARGS[@]:+"${PYTEST_EXTRA_ARGS[@]}"}; then
            echo "E2E tests failed!"
            exit 1
        fi

        # Optionally generate and/or serve the report for this variant
        if [[ "$GENERATE_ALLURE" == true ]]; then
            local report_out="$reports_root_dir/${SPECIFIED_WALLET_VARIANT:-specified}"
            mkdir -p "$report_out"
            echo "Generating Allure report: $report_out"
            allure generate -c "$results_dir" -o "$report_out"
            echo "Report generated at: $report_out (open index.html or run: allure open \"$report_out\")"
        fi
        if [[ "$SERVE_ALLURE" == true ]]; then
            echo "Serving Allure report for variant: ${SPECIFIED_WALLET_VARIANT}"
            allure serve "$results_dir"
        fi
    else
        echo "No --wallet-variant provided. Running for all default variants: ${DEFAULT_WALLET_VARIANTS[*]}"
        local failures=()
        for variant in "${DEFAULT_WALLET_VARIANTS[@]}"; do
            echo "\n===== Running with wallet variant: $variant ====="
            # Build args by appending the variant
            local results_dir="$results_root_dir/$variant"
            # ensure per-variant directory exists and is clean for fresh run
            rm -rf "$results_dir" && mkdir -p "$results_dir"
            if ! pytest -s "$base_target" --wallet-variant "$variant" --alluredir="$results_dir" ${PYTEST_EXTRA_ARGS[@]:+"${PYTEST_EXTRA_ARGS[@]}"}; then
                failures+=("$variant")
                echo "---- Failed for variant: $variant ----"
            else
                echo "---- Passed for variant: $variant ----"
            fi

            # Optionally generate report per variant
            if [[ "$GENERATE_ALLURE" == true ]]; then
                local report_out="$reports_root_dir/$variant"
                mkdir -p "$report_out"
                echo "Generating Allure report: $report_out"
                allure generate -c "$results_dir" -o "$report_out"
                echo "Report generated at: $report_out (open index.html or run: allure open \"$report_out\")"
            fi

            # Optionally serve report sequentially per variant
            if [[ "$SERVE_ALLURE" == true ]]; then
                echo "Serving Allure report for variant: $variant"
                allure serve "$results_dir"
            fi
        done

        if [[ ${#failures[@]} -gt 0 ]]; then
            echo "\nOne or more variants failed: ${failures[*]}"
            exit 1
        fi
    fi
}

ensure_applications_exist

run_e2e_tests

echo "Setup and tests completed successfully!"
