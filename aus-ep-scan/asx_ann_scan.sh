#!/bin/bash

# ASX Announcements Scanner
# Extracts price sensitive announcements with headers from ASX
# Uses only tools available in GitHub Actions runners by default

OUTPUT_FILE="${1:-asx_announcements.json}"
ASX_URL="https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
# For debugging use:
# ASX_URL="https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do"

# Create temporary files
TEMP_AWK_FILE=$(mktemp)
TEMP_HTML_FILE=$(mktemp)

# Cleanup function
cleanup_temp() {
  rm -f "$TEMP_AWK_FILE" "$TEMP_HTML_FILE"
}
trap cleanup_temp EXIT

# Fetch HTML
echo "Fetching ASX announcement data..."
curl -s "$ASX_URL" > "$TEMP_HTML_FILE"

if [ ! -s "$TEMP_HTML_FILE" ]; then
  echo "Error: Failed to fetch ASX data" >&2
  exit 1
fi

echo "Parsing price sensitive announcements..."

# Extract price sensitive announcements
awk '
  /<tr class=""/ { row = ""; in_row = 1 }
  in_row { row = row $0 "\n" }
  /<\/tr>/ && in_row { 
    if (row ~ /pricesens/) {
      # Extract ticker from first <td>
      ticker = ""
      if (match(row, /<td>([^<]+)<\/td>/)) {
        ticker = substr(row, RSTART + 4, RLENGTH - 9)
        gsub(/^[ \t\n\r]+|[ \t\n\r]+$/, "", ticker)
      }
      
      # Extract announcement header from the <a> tag text
      header = ""
      if (match(row, /<a[^>]*>[ \t\n\r]*([^<]+)[ \t\n\r]*<br>/)) {
        header = substr(row, RSTART, RLENGTH)
        # Extract text between > and <br>
        if (match(header, />[ \t\n\r]*([^<]+)[ \t\n\r]*<br>/)) {
          header = substr(header, RSTART + 1, RLENGTH - 5)
          gsub(/^[ \t\n\r]+|[ \t\n\r]+$/, "", header)
          gsub(/&amp;/, "\\&", header)
          gsub(/&lt;/, "<", header)
          gsub(/&gt;/, ">", header)
          gsub(/&quot;/, "\"", header)
        }
      }
      
      # Output JSON object if both ticker and header found
      if (ticker != "" && header != "") {
        # Escape quotes in header for JSON
        gsub(/"/, "\\\"", header)
        printf "{\"ticker\":\"%s\",\"header\":\"%s\",\"price_sensitive\":true}\n", ticker, header
      }
    }
    in_row = 0
  }
' < "$TEMP_HTML_FILE" > "$TEMP_AWK_FILE"

echo "Raw announcements found: $(wc -l < "$TEMP_AWK_FILE")"

# Consolidate duplicates with jq
echo "Consolidating duplicate tickers..."
jq -s '
  group_by(.ticker) | 
  map({
    ticker: .[0].ticker,
    header: (
      map(.header) | 
      join(" | ") | 
      if length > 100 then .[0:97] + "..." else . end
    ),
    price_sensitive: true
  })
' < "$TEMP_AWK_FILE" > "$OUTPUT_FILE"

if [ $? -eq 0 ] && [ -s "$OUTPUT_FILE" ]; then
  echo "ASX price sensitive announcements saved to $OUTPUT_FILE"
  echo "Count: $(jq 'length' "$OUTPUT_FILE")"
else
  echo "Error: Failed to process ASX data" >&2
  exit 1
fi
