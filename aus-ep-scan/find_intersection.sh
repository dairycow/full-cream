#!/bin/bash

# Find intersection between TradingView momentum and ASX price sensitive tickers
# Usage: ./find_intersection.sh <momentum_file> <sensitive_file>

set -e  # Exit on any error

# Check arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <momentum_file> <sensitive_file>" >&2
  exit 1
fi

MOMENTUM_RAW_FILE="$1"
SENSITIVE_FILE="$2"
MOMENTUM_FILE="momentum_normalized.json"
SENSITIVE_TICKERS_ONLY="sensitive_tickers_only.json"
INTERSECTION_FILE="intersection.json"

# Cleanup function
cleanup() {
  echo "Cleaning up temporary files..."
  rm -f "$MOMENTUM_FILE" "$SENSITIVE_TICKERS_ONLY" "$INTERSECTION_FILE"
  echo "Cleanup complete"
}

# Set trap to cleanup on exit (success or failure)
trap cleanup EXIT

# Validate input files exist
if [ ! -f "$MOMENTUM_RAW_FILE" ]; then
  echo "Error: Momentum file '$MOMENTUM_RAW_FILE' not found" >&2
  exit 1
fi

if [ ! -f "$SENSITIVE_FILE" ]; then
  echo "Error: Sensitive file '$SENSITIVE_FILE' not found" >&2
  exit 1
fi

echo "Normalizing ticker formats..."
# Remove ASX: prefix from momentum tickers to match price sensitive format
jq 'map(sub("ASX:"; ""))' "$MOMENTUM_RAW_FILE" > "$MOMENTUM_FILE"
echo "Normalized momentum tickers: $(jq 'length' "$MOMENTUM_FILE")"

# Extract ticker arrays for intersection logic
jq 'map(.ticker)' "$SENSITIVE_FILE" > "$SENSITIVE_TICKERS_ONLY"
echo "Extracted announcement tickers: $(jq 'length' "$SENSITIVE_TICKERS_ONLY")"

echo "Finding ticker intersections..."
# Create intersection using jq (compare ticker arrays)
jq -n \
  --argjson momentum "$(cat "$MOMENTUM_FILE")" \
  --argjson sensitive "$(cat "$SENSITIVE_TICKERS_ONLY")" \
  '$momentum - ($momentum - $sensitive)' > "$INTERSECTION_FILE"

INTERSECTION_COUNT=$(jq 'length' "$INTERSECTION_FILE")
echo "Found $INTERSECTION_COUNT intersecting tickers"

# Read intersections for processing
INTERSECTIONS=$(cat "$INTERSECTION_FILE")

# Write GitHub workflow summary
write_github_summary() {
  if [ -n "$GITHUB_STEP_SUMMARY" ]; then
    echo "## Australian Equity Price Scan Results" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
    echo "**Scan Date:** $(date '+%Y-%m-%d %H:%M:%S UTC')" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
    
    if [ "$INTERSECTION_COUNT" -gt 0 ]; then
      echo "### Current Alerts: $INTERSECTION_COUNT Tickers" >> "$GITHUB_STEP_SUMMARY"
      echo "" >> "$GITHUB_STEP_SUMMARY"
      echo "The following tickers have both **5%+ momentum** and **price sensitive announcements**:" >> "$GITHUB_STEP_SUMMARY"
      echo "" >> "$GITHUB_STEP_SUMMARY"
      echo "| Ticker | Announcement | Chart |" >> "$GITHUB_STEP_SUMMARY"
      echo "|--------|--------------|-------|" >> "$GITHUB_STEP_SUMMARY"
      echo "$INTERSECTIONS" | jq -r '.[]' | while read ticker; do
        # Get announcement header for this ticker
        HEADER=$(jq -r --arg t "$ticker" '.[] | select(.ticker == $t) | .header' "$SENSITIVE_FILE")
        echo "| $ticker | $HEADER | [View Chart](https://www.tradingview.com/chart/?symbol=ASX%3A$ticker) |" >> "$GITHUB_STEP_SUMMARY"
      done
      echo "" >> "$GITHUB_STEP_SUMMARY"
    else
      echo "### No Alerts" >> "$GITHUB_STEP_SUMMARY"
      echo "" >> "$GITHUB_STEP_SUMMARY"
      echo "No intersecting tickers found." >> "$GITHUB_STEP_SUMMARY"
      echo "" >> "$GITHUB_STEP_SUMMARY"
    fi
    
    echo "### Summary Statistics" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
    echo "- **Momentum tickers:** $(jq 'length' "$MOMENTUM_FILE")" >> "$GITHUB_STEP_SUMMARY"
    echo "- **Price sensitive tickers:** $(jq 'length' "$SENSITIVE_TICKERS_ONLY")" >> "$GITHUB_STEP_SUMMARY"
    echo "- **Current intersections:** $INTERSECTION_COUNT" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
  fi
}

if [ "$INTERSECTION_COUNT" -gt 0 ]; then
  echo ""
  echo "ALERT: Found $INTERSECTION_COUNT tickers with both 5%+ momentum AND price sensitive announcements!"
  echo ""
  echo "INTERSECTING TICKERS:"
  echo "$INTERSECTIONS" | jq -r '.[]' | while read ticker; do
    echo "  - $ticker"
  done
  echo ""
  echo "Raw JSON: $INTERSECTIONS"
  echo ""
  echo "These tickers have both:"
  echo "  - Gained 5%+ from market open today"
  echo "  - Released price sensitive announcements"
  echo ""
  echo "Scan completed successfully - intersecting tickers found"
else
  echo "No intersecting tickers found"
  echo "Momentum tickers: $(jq -c '.' "$MOMENTUM_FILE")"
  echo "Price sensitive tickers: $(jq -c '.' "$SENSITIVE_TICKERS_ONLY")"
  echo "Scan completed successfully - no intersections"
fi

# Write the GitHub workflow summary
write_github_summary

exit 0