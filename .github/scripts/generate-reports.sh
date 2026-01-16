#!/bin/bash
# Generate Allure and coverage reports for GitHub Pages (with history)

set -euo pipefail

SITE_DIR="site"

mkdir -p "$SITE_DIR"

# Generate embedded report
if [ -d "allure-results-embedded" ] && [ "$(ls -A allure-results-embedded 2>/dev/null)" ]; then
  allure generate allure-results-embedded --clean -o "$SITE_DIR/embedded"
else
  mkdir -p "$SITE_DIR/embedded"
  echo "<h1>No embedded test results available</h1>" > "$SITE_DIR/embedded/index.html"
fi

# Generate remote report
if [ -d "allure-results-remote" ] && [ "$(ls -A allure-results-remote 2>/dev/null)" ]; then
  allure generate allure-results-remote --clean -o "$SITE_DIR/remote"
else
  mkdir -p "$SITE_DIR/remote"
  echo "<h1>No remote test results available</h1>" > "$SITE_DIR/remote/index.html"
fi

# Copy coverage report
if [ -d "coverage-report" ] && [ "$(ls -A coverage-report 2>/dev/null)" ]; then
  cp -r coverage-report "$SITE_DIR/coverage"
else
  mkdir -p "$SITE_DIR/coverage"
  echo "<h1>No coverage report available</h1>" > "$SITE_DIR/coverage/index.html"
fi

# Create index page with links to all reports
cp .github/pages/allure-index.html "$SITE_DIR/index.html"

echo "✅ Reports generated successfully"
