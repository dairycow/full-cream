#!/bin/bash

# TradingView Scan - Australian stocks up >5% from open
# Outputs tickers to JSON for jq parsing

OUTPUT_FILE="${1:-tv_momentum.json}"

# TradingView API payload for 5% momentum scan
PAYLOAD='{
  "markets": ["australia"],
  "symbols": {"query": {"types": []}, "tickers": []},
  "options": {"lang": "en"},
  "columns": ["name", "close", "change_from_open"],
  "sort": {"sortBy": "change_from_open", "sortOrder": "desc"},
  "range": [0, 100],
  "filter": [{"left": "change_from_open", "operation": "greater", "right": 5}]
}'

# Make API request and extract tickers with percentages
curl -s -X POST "https://scanner.tradingview.com/australia/scan" \
  -H "content-type: application/json" \
  -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "origin: https://www.tradingview.com" \
  -H "referer: https://www.tradingview.com/" \
  -H "accept: text/plain, */*; q=0.01" \
  -H "sec-fetch-site: same-site" \
  -H "sec-fetch-mode: cors" \
  -H "sec-fetch-dest: empty" \
  -d "$PAYLOAD" | \
jq '[.data[] | {ticker: .s, percentage: (.d[2] | tonumber | . * 100 | round / 100)}]' > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo "TradingView momentum tickers saved to $OUTPUT_FILE"
  echo "Count: $(jq 'length' "$OUTPUT_FILE")"
else
  echo "Error: Failed to fetch or parse TradingView data" >&2
  exit 1
fi
