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
jq '.[]' my_momentum.json  # List all tickers
jq 'length' my_momentum.json  # Count
```

### `asx_ps_scrape.sh`
Scrapes ASX website for stocks with price-sensitive announcements.

**Usage:**
```bash
./asx_ps_scrape.sh [output_file]
```

**Default output:** `asx_price_sensitive.json`

**Example:**
```bash
./asx_ps_scrape.sh my_announcements.json
jq '.[]' my_announcements.json  # List all tickers
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

Both scripts output clean JSON arrays:
```json
["BHP", "CBA", "WBC"]
```

Perfect for further processing with `jq` or integration with other tools.
