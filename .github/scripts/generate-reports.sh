#!/bin/bash
# Generate Allure and coverage reports for GitHub Pages

set -euo pipefail

mkdir -p site

# Define all wallet variants (18 total)
SINGLE_SIG_VARIANTS=(
    "online_watch_only"
    "online_create_on_device"
    "online_create_hardware"
    "online_load_on_device"
    "online_load_hardware"
    "offline_create_on_device"
    "offline_create_hardware"
    "offline_load_on_device"
    "offline_load_hardware"
)

MULTISIG_VARIANTS=(
    "online_multisig_watch_only"
    "online_multisig_on_device"
    "online_multisig_hardware"
    "online_multisig_load_on_device"
    "online_multisig_load_hardware"
    "offline_multisig_on_device"
    "offline_multisig_hardware"
    "offline_multisig_load_on_device"
    "offline_multisig_load_hardware"
)

# Function to generate report for a single variant
generate_variant_report() {
    local variant=$1
    local output_dir="site/$variant"
    local merged_results="allure-results-merged-$variant"

    mkdir -p "$output_dir"
    mkdir -p "$merged_results"

    # Merge all test file results for this variant
    for result_dir in allure-results-*-${variant}; do
        if [ -d "$result_dir" ]; then
            cp -r "$result_dir"/* "$merged_results/" 2>/dev/null || true
        fi
    done

    # Generate Allure report if results exist
    if [ -d "$merged_results" ] && [ "$(ls -A $merged_results 2>/dev/null)" ]; then
        allure generate "$merged_results" --clean -o "$output_dir"
        echo "✅ Generated report for $variant"
    else
        echo "<h1>No test results available for $variant</h1>" > "$output_dir/index.html"
        echo "⚠️ No results for $variant"
    fi

    # Cleanup merged results
    rm -rf "$merged_results"
}

# Generate reports for Single-Sig variants
echo "Generating reports for Single-Signature variants (9)..."
for variant in "${SINGLE_SIG_VARIANTS[@]}"; do
    generate_variant_report "$variant"
done

# Generate reports for Multisig variants
echo "Generating reports for Multisig variants (9)..."
for variant in "${MULTISIG_VARIANTS[@]}"; do
    generate_variant_report "$variant"
done

# Copy coverage report
if [ -d "coverage-report" ] && [ "$(ls -A coverage-report 2>/dev/null)" ]; then
  cp -r coverage-report site/coverage
else
  mkdir -p site/coverage
  echo "<h1>No coverage report available</h1>" > site/coverage/index.html
fi

# Create index page with links to all reports
cp .github/pages/allure-index.html site/index.html

echo "✅ All reports generated successfully (18 variants + coverage)"
