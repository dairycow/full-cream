#!/bin/bash

# ASX Price Sensitive Announcements Scraper
# Uses only tools available in GitHub Actions runners by default

OUTPUT_FILE="${1:-asx_price_sensitive.json}"
# ASX_URL="https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
ASX_URL="https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do"

# Fetch HTML and extract price sensitive tickers
# Strategy: Find table rows containing pricesens img, then extract first cell content
curl -s "$ASX_URL" | \
awk '
  /<tr/ { row = ""; in_row = 1 }
  in_row { row = row $0 "\n" }
  /<\/tr>/ { 
    if (row ~ /pricesens/) {
      # Extract first <td> content from this row
      if (match(row, /<td[^>]*>([^<]+)<\/td>/)) {
        ticker = substr(row, RSTART, RLENGTH)
        gsub(/<[^>]*>/, "", ticker)
        gsub(/^[ \t\n\r]+|[ \t\n\r]+$/, "", ticker)
        if (ticker != "") print ticker
      }
    }
    in_row = 0
  }
' | \
jq -R -s 'split("\n") | map(select(length > 0))' > "$OUTPUT_FILE"

if [ $? -eq 0 ] && [ -s "$OUTPUT_FILE" ]; then
  echo "ASX price sensitive tickers saved to $OUTPUT_FILE"
  echo "Count: $(jq 'length' "$OUTPUT_FILE")"
else
  echo "Error: Failed to fetch or parse ASX data" >&2
  exit 1
fi