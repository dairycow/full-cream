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
INTERSECTION_FILE="intersection.json"
ALERTED_FILE="alerted_today.json"

# Cleanup function
cleanup() {
  echo "Cleaning up temporary files..."
  rm -f "$MOMENTUM_FILE" "$INTERSECTION_FILE"
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

# Initialize or clean up daily tracking file
TODAY=$(date +%Y%m%d)
if [ ! -f "$ALERTED_FILE" ] || [ "$(jq -r '.date // empty' "$ALERTED_FILE" 2>/dev/null)" != "$TODAY" ]; then
  echo "Initializing daily alert tracking for $TODAY"
  echo "{\"date\": \"$TODAY\", \"tickers\": []}" > "$ALERTED_FILE"
fi

echo "Normalizing ticker formats..."
# Remove ASX: prefix from momentum tickers to match price sensitive format
jq 'map(sub("ASX:"; ""))' "$MOMENTUM_RAW_FILE" > "$MOMENTUM_FILE"
echo "Normalized momentum tickers: $(jq 'length' "$MOMENTUM_FILE")"

echo "Finding ticker intersections..."
# Create intersection using jq
jq -n \
  --argjson momentum "$(cat "$MOMENTUM_FILE")" \
  --argjson sensitive "$(cat "$SENSITIVE_FILE")" \
  '$momentum - ($momentum - $sensitive)' > "$INTERSECTION_FILE"

TICKER_COUNT=$(jq 'length' "$INTERSECTION_FILE")
echo "Found $TICKER_COUNT intersecting tickers"

# Find NEW intersections (not already alerted today)
NEW_INTERSECTIONS=$(jq -n \
  --argjson current "$(cat "$INTERSECTION_FILE")" \
  --argjson alerted "$(jq '.tickers' "$ALERTED_FILE")" \
  '$current - $alerted')

NEW_COUNT=$(echo "$NEW_INTERSECTIONS" | jq 'length')
echo "Found $NEW_COUNT new intersecting tickers (not yet alerted today)"

if [ "$NEW_COUNT" -gt 0 ]; then
  echo ""
  echo "NEW ALERT: Found $NEW_COUNT new tickers with both 5%+ momentum AND price sensitive announcements!"
  echo ""
  echo "NEW MOMENTUM + PRICE SENSITIVE TICKERS:"
  echo "$NEW_INTERSECTIONS" | jq -r '.[]' | while read ticker; do
    echo "  - $ticker"
  done
  echo ""
  echo "Raw JSON: $NEW_INTERSECTIONS"
  echo ""
  echo "These tickers have both:"
  echo "  - Gained 5%+ from market open today"
  echo "  - Released price sensitive announcements"
  echo ""
  
  # Update alerted list with new tickers
  jq --argjson new "$NEW_INTERSECTIONS" '.tickers += $new | .tickers |= unique' "$ALERTED_FILE" > tmp_alerted && mv tmp_alerted "$ALERTED_FILE"
  echo "Updated daily alert tracking with $NEW_COUNT new tickers"
  echo ""
  echo "Scan completed successfully - NEW intersecting tickers found and alerted"
elif [ "$TICKER_COUNT" -gt 0 ]; then
  echo "Found $TICKER_COUNT intersecting tickers, but all were already alerted today"
  echo "Previously alerted: $(jq -c '.tickers' "$ALERTED_FILE")"
  echo "Current intersections: $(jq -c '.' "$INTERSECTION_FILE")"
  echo "Scan completed successfully - no new alerts needed"
else
  echo "No intersecting tickers found today"
  echo "Momentum tickers: $(jq -c '.' "$MOMENTUM_FILE")"
  echo "Price sensitive tickers: $(jq -c '.' "$SENSITIVE_FILE")"
  echo "Scan completed successfully - no intersections"
fi

exit 0