#!/bin/bash
# Generate Allure and coverage reports for GitHub Pages (with history)

set -euo pipefail

# Use GitHub run id (fallback if not set)
RUN_ID="${RUN_ID:-local}"
SITE_DIR="site"
RUN_DIR="$SITE_DIR/runs/$RUN_ID"
LATEST_DIR="$SITE_DIR/latest"

mkdir -p "$RUN_DIR" "$LATEST_DIR"

# Generate embedded report
if [ -d "allure-results-embedded" ] && [ "$(ls -A allure-results-embedded 2>/dev/null)" ]; then
  allure generate allure-results-embedded --clean -o "$RUN_DIR/embedded"
  allure generate allure-results-embedded --clean -o "$LATEST_DIR/embedded"
else
  mkdir -p "$RUN_DIR/embedded" "$LATEST_DIR/embedded"
  echo "<h1>No embedded test results available</h1>" > "$RUN_DIR/embedded/index.html"
  cp "$RUN_DIR/embedded/index.html" "$LATEST_DIR/embedded/index.html"
fi

# Generate remote report
if [ -d "allure-results-remote" ] && [ "$(ls -A allure-results-remote 2>/dev/null)" ]; then
  allure generate allure-results-remote --clean -o "$RUN_DIR/remote"
  allure generate allure-results-remote --clean -o "$LATEST_DIR/remote"
else
  mkdir -p "$RUN_DIR/remote" "$LATEST_DIR/remote"
  echo "<h1>No remote test results available</h1>" > "$RUN_DIR/remote/index.html"
  cp "$RUN_DIR/remote/index.html" "$LATEST_DIR/remote/index.html"
fi

# Copy coverage report
if [ -d "coverage-report" ] && [ "$(ls -A coverage-report 2>/dev/null)" ]; then
  cp -r coverage-report "$RUN_DIR/coverage"
  rm -rf "$LATEST_DIR/coverage"
  cp -r coverage-report "$LATEST_DIR/coverage"
else
  mkdir -p "$RUN_DIR/coverage" "$LATEST_DIR/coverage"
  echo "<h1>No coverage report available</h1>" > "$RUN_DIR/coverage/index.html"
  cp "$RUN_DIR/coverage/index.html" "$LATEST_DIR/coverage/index.html"
fi

# Create index page with links to all reports
cp .github/pages/allure-index.html "$SITE_DIR/index.html"

# Create runs index page
RUN_INDEX="$RUN_DIR/index.html"

{
  echo "<!DOCTYPE html>"
  echo "<html><head><meta charset='utf-8'><title>Run $RUN_ID</title></head><body>"
  echo "<h1>Test Run $RUN_ID</h1>"
  echo "<ul>"
  echo "<li><a href='./embedded/'>Embedded Mode</a></li>"
  echo "<li><a href='./remote/'>Remote Mode</a></li>"
  echo "<li><a href='./coverage/'>Coverage Report</a></li>"
  echo "</ul>"
  echo "<p><a href='../'>← Back to all runs</a></p>"
  echo "<p><a href='../../'>← Back to main page</a></p>"
  echo "</body></html>"
} > "$RUN_INDEX"

echo "✅ Reports generated successfully"
