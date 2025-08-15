# Australian Equity Price Scan

A minimal alert system for Australian equity markets that identifies stocks with both momentum and price-sensitive news.

## Overview

This module combines two data sources to find trading opportunities:
- **TradingView API**: Stocks with intraday momentum
- **ASX Announcements**: Stocks with price-sensitive announcements

When stocks appear in both lists, it suggests market-moving events worth investigating.

## Scripts

### `tv_scan.sh`
Scans TradingView for Australian stocks up >5% from market open.

**Usage:**
```bash
./tv_scan.sh [output_file]
```

**Default output:** `tv_momentum.json`

**Example:**
```bash
./tv_scan.sh my_momentum.json
jq '.[] | .ticker' my_momentum.json  # List all tickers
jq '.[] | "\(.ticker): +\(.percentage)%"' my_momentum.json  # List with percentages
jq 'length' my_momentum.json  # Count
```

### `asx_ann_scan.sh`
Scans ASX announcements for price-sensitive announcements with headers.

**Usage:**
```bash
./asx_ann_scan.sh [output_file]
```

**Default output:** `asx_announcements.json`

**Example:**
```bash
./asx_ann_scan.sh my_announcements.json
jq '.[] | .ticker' my_announcements.json  # List all tickers
jq '.[] | "\(.ticker): \(.header)"' my_announcements.json  # List with headers
```

## Data Sources

- **TradingView Scanner API**: `https://scanner.tradingview.com/australia/scan`
- **ASX Announcements**: `https://www.asx.com.au/asx/v2/statistics/todayAnns.do`

## Dependencies

Uses only standard tools available in GitHub Actions:
- `curl` - HTTP requests
- `jq` - JSON processing
- `awk` - HTML parsing

## Automation

The GitHub Actions workflow (`../.github/workflows/aus-ep-scan.yml`) runs this scan automatically.

## Output Format

**TradingView Scanner (`tv_scan.sh`):**
```json
[
  {"ticker": "ASX:BHP", "percentage": 12.5},
  {"ticker": "ASX:CBA", "percentage": 8.2},
  {"ticker": "ASX:WBC", "percentage": 6.7}
]
```

**ASX Announcements (`asx_ann_scan.sh`):**
```json
[
  {
    "ticker": "BHP",
    "header": "Quarterly Production Report",
    "price_sensitive": true
  },
  {
    "ticker": "CBA", 
    "header": "Full Year Results - Record Profit",
    "price_sensitive": true
  }
]
```

Perfect for further processing with `jq` or integration with other tools. Announcement headers are truncated to 100 characters maximum.

## GitHub Workflow Summary

The automated workflow generates a summary table with enhanced information:

| Ticker | % Up | Announcement | Chart |
|--------|------|--------------|-------|
| DBO | +26.32% | Drilling to Commence - Phoenix Copper Project | [View Chart] |
| GTE | +15.38% | Gravity Survey Defines Potential Core of VHMS Cu-Au System | [View Chart] |

This provides immediate visibility into both momentum strength and announcement context.
