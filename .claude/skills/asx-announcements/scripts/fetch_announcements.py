#!/usr/bin/env python3
"""
ASX Announcements Fetcher
Extracts price sensitive announcements with headers from ASX.
"""

import json
import re
import sys
from urllib.request import urlopen
from urllib.error import URLError
from collections import defaultdict


def fetch_asx_html(url):
    """Fetch HTML content from ASX endpoint."""
    try:
        with urlopen(url) as response:
            return response.read().decode('utf-8')
    except URLError as e:
        print(f"Error: Failed to fetch ASX data: {e}", file=sys.stderr)
        sys.exit(1)


def parse_price_sensitive_announcements(html):
    """
    Parse HTML to extract price-sensitive announcements.
    Returns list of dicts with ticker, header, and price_sensitive fields.
    """
    announcements = []

    # Split HTML into table rows
    rows = re.split(r'<tr[\s>]', html)

    for row in rows:
        if '</tr>' not in row or 'pricesens' not in row:
            continue

        # Extract ticker from first <td>
        ticker_match = re.search(r'<td>([^<]+)</td>', row)
        if not ticker_match:
            continue
        ticker = ticker_match.group(1).strip()

        # Extract announcement header from <a> tag text before <br>
        header_match = re.search(r'<a[^>]*>\s*([^<]+)\s*<br>', row)
        if not header_match:
            continue
        header = header_match.group(1).strip()

        # Decode HTML entities
        header = header.replace('&amp;', '&')
        header = header.replace('&lt;', '<')
        header = header.replace('&gt;', '>')
        header = header.replace('&quot;', '"')

        if ticker and header:
            announcements.append({
                'ticker': ticker,
                'header': header,
                'price_sensitive': True
            })

    return announcements


def consolidate_announcements(announcements):
    """
    Consolidate multiple announcements for the same ticker.
    Joins headers with ' • ' separator and truncates to 100 chars.
    """
    ticker_groups = defaultdict(list)

    for ann in announcements:
        ticker_groups[ann['ticker']].append(ann['header'])

    consolidated = []
    for ticker, headers in ticker_groups.items():
        # Remove duplicates while preserving order
        unique_headers = []
        seen = set()
        for h in headers:
            if h not in seen:
                unique_headers.append(h)
                seen.add(h)

        # Join headers
        combined_header = ' • '.join(unique_headers)

        # Truncate if needed
        if len(combined_header) > 100:
            combined_header = combined_header[:97] + '...'

        consolidated.append({
            'ticker': ticker,
            'header': combined_header,
            'price_sensitive': True
        })

    return consolidated


def main():
    """Main execution function."""
    # ASX endpoint for today's announcements
    asx_url = "https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
    # For debugging/testing with previous business day:
    # asx_url = "https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do"

    print("Fetching ASX announcement data...", file=sys.stderr)
    html = fetch_asx_html(asx_url)

    print("Parsing price sensitive announcements...", file=sys.stderr)
    announcements = parse_price_sensitive_announcements(html)

    print(f"Raw announcements found: {len(announcements)}", file=sys.stderr)

    print("Consolidating duplicate tickers...", file=sys.stderr)
    consolidated = consolidate_announcements(announcements)

    print(f"Consolidated announcements: {len(consolidated)}", file=sys.stderr)

    # Output JSON to stdout
    print(json.dumps(consolidated, indent=2))


if __name__ == '__main__':
    main()
