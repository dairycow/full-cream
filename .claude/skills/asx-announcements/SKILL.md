---
name: asx-announcements
description: Fetch and parse price-sensitive announcements from the Australian Securities Exchange (ASX). Use this skill when users request today's ASX announcements, price-sensitive announcements, ASX market updates, or ticker-specific announcement headers.
---

# ASX Announcements

## Overview

Fetch today's price-sensitive announcements from the Australian Securities Exchange (ASX), extracting ticker symbols and announcement headers in a consolidated JSON format.

## When to Use This Skill

Use this skill when the user requests:
- Today's ASX announcements
- Price-sensitive announcements from ASX
- Latest ASX market updates
- Announcement headers for specific tickers
- Market-sensitive information from the ASX

## Fetching Announcements

To fetch today's ASX price-sensitive announcements, execute the `scripts/fetch_announcements.py` script:

```bash
python3 scripts/fetch_announcements.py
```

The script will:
1. Fetch HTML from the ASX public API endpoint (`https://www.asx.com.au/asx/v2/statistics/todayAnns.do`)
2. Parse the HTML to extract only price-sensitive announcements (marked with "pricesens")
3. Extract ticker symbols and announcement headers from each row
4. Handle HTML entities (&amp;, &lt;, &gt;, &quot;)
5. Consolidate multiple announcements for the same ticker using " • " as a separator
6. Truncate consolidated headers to 100 characters if necessary
7. Output JSON to stdout

### Output Format

The script outputs a JSON array with the following structure:

```json
[
  {
    "ticker": "ABC",
    "header": "Trading Halt",
    "price_sensitive": true
  },
  {
    "ticker": "XYZ",
    "header": "Quarterly Results • Capital Raising",
    "price_sensitive": true
  }
]
```

### Processing the Output

After executing the script:
1. Parse the JSON output
2. Present the results to the user in a readable format (e.g., table or list)
3. If the user asks about specific tickers, filter the results accordingly
4. If the user needs more details, guide them to the ASX website for full announcement text

### Error Handling

The script handles common errors:
- Network failures when fetching ASX data
- Missing or malformed HTML in the response
- Empty result sets (e.g., outside market hours or on non-trading days)

Progress messages are sent to stderr, while the JSON output goes to stdout, making it easy to capture the data separately.

## Important Notes

- Only price-sensitive announcements are included (non-price-sensitive announcements are filtered out)
- Multiple announcements for the same ticker are consolidated into a single entry
- Headers longer than 100 characters are truncated with "..."
- The ASX API endpoint requires no authentication and is publicly accessible
- Results reflect announcements made on the current trading day
- For testing with previous business day data, the script contains a commented alternative URL

## Resources

### scripts/fetch_announcements.py

Executable Python script that fetches and parses ASX announcements. Can be run directly without loading into context. The script is self-contained and uses only Python standard library modules (no external dependencies required).
