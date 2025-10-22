#!/usr/bin/env python3
"""
Test Interactive Brokers connection and basic functionality.

This script verifies:
- Connection to IB Gateway
- Account information retrieval
- Market data access
- Contract qualification

Usage:
    python scripts/test_ib_connection.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.brokers.ib_client import IBClient
from src.utils.config import get_config
from src.utils.logger import setup_logger


def main():
    """Run IB connection tests."""
    print("=" * 70)
    print("Interactive Brokers Connection Test")
    print("=" * 70)

    # Initialize logger
    config = get_config()
    setup_logger(
        log_dir=config.log_path,
        log_level="DEBUG",
        enable_console=True,
        enable_file=False,
    )

    print(f"\nConfiguration:")
    print(f"  Host: {config.ib_host}")
    print(f"  Port: {config.ib_port}")
    print(f"  Client ID: {config.ib_client_id}")
    print(f"  Account: {config.ib_account}")
    print(f"  Paper Trading: {config.paper_trading}")

    # Initialize IB client
    print("\n" + "=" * 70)
    print("Test 1: Connection")
    print("=" * 70)

    client = IBClient()

    print("\nAttempting to connect to IB Gateway...")
    if not client.connect():
        print("❌ Failed to connect to IB Gateway")
        print("\nTroubleshooting:")
        print("  1. Ensure IB Gateway is running")
        print("  2. Check that IB Gateway is configured for API access")
        print("  3. Verify host and port in .env file")
        print("  4. Check that API settings allow connections")
        return 1

    print("✓ Connected successfully!")

    # Test 2: Account Information
    print("\n" + "=" * 70)
    print("Test 2: Account Information")
    print("=" * 70)

    try:
        net_liq = client.get_net_liquidation()
        if net_liq:
            print(f"\n✓ Net Liquidation: ${net_liq:,.2f}")
        else:
            print("\n⚠ Could not retrieve net liquidation value")

        buying_power = client.get_buying_power()
        if buying_power:
            print(f"✓ Buying Power: ${buying_power:,.2f}")
        else:
            print("⚠ Could not retrieve buying power")

        # Check if account meets minimum balance
        if net_liq and net_liq < config.min_account_balance:
            print(f"\n⚠ Warning: Account balance (${net_liq:,.2f}) is below minimum "
                  f"required (${config.min_account_balance:,.2f})")
        elif net_liq:
            print(f"\n✓ Account balance meets minimum requirement")

    except Exception as e:
        print(f"\n❌ Error retrieving account information: {e}")

    # Test 3: Positions
    print("\n" + "=" * 70)
    print("Test 3: Current Positions")
    print("=" * 70)

    try:
        positions = client.get_positions()
        if positions:
            print(f"\n✓ Found {len(positions)} open position(s):")
            for pos in positions:
                print(f"  - {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost:.2f}")
        else:
            print("\n✓ No open positions (clean slate)")

    except Exception as e:
        print(f"\n❌ Error retrieving positions: {e}")

    # Test 4: Contract Qualification
    print("\n" + "=" * 70)
    print("Test 4: Contract Qualification (ASX Stocks)")
    print("=" * 70)

    test_symbols = ["BHP", "CBA", "RIO"]
    print(f"\nTesting contract qualification for: {', '.join(test_symbols)}")

    for symbol in test_symbols:
        try:
            contract = client.create_stock_contract(symbol)
            qualified = client.qualify_contract(contract)

            if qualified:
                print(f"  ✓ {symbol}: Qualified successfully")
            else:
                print(f"  ❌ {symbol}: Failed to qualify")

        except Exception as e:
            print(f"  ❌ {symbol}: Error - {e}")

    # Test 5: Market Data Access
    print("\n" + "=" * 70)
    print("Test 5: Market Data Access")
    print("=" * 70)

    test_symbol = "BHP"
    print(f"\nAttempting to fetch market data for {test_symbol}...")

    try:
        last_price = client.get_last_price(test_symbol)

        if last_price:
            print(f"  ✓ {test_symbol} Last Price: ${last_price:.3f}")
        else:
            print(f"  ⚠ Could not retrieve last price for {test_symbol}")
            print("  Note: Market may be closed or data subscription needed")

        # Try to get previous close
        prev_close = client.get_previous_close(test_symbol)
        if prev_close:
            print(f"  ✓ {test_symbol} Previous Close: ${prev_close:.3f}")
        else:
            print(f"  ⚠ Could not retrieve previous close for {test_symbol}")

    except Exception as e:
        print(f"  ❌ Error retrieving market data: {e}")
        print("  Note: You may need to subscribe to ASX market data in IB")

    # Test 6: Historical Data
    print("\n" + "=" * 70)
    print("Test 6: Historical Data")
    print("=" * 70)

    print(f"\nFetching 5-day historical data for {test_symbol}...")

    try:
        contract = client.create_stock_contract(test_symbol)
        bars = client.get_historical_data(contract, duration="5 D", bar_size="1 day")

        if bars and len(bars) > 0:
            print(f"  ✓ Retrieved {len(bars)} bars")
            print(f"\n  Recent prices:")
            for bar in bars[-3:]:  # Show last 3 days
                print(f"    {bar.date}: Close ${bar.close:.3f} (Vol: {bar.volume:,})")
        else:
            print(f"  ⚠ No historical data available")

    except Exception as e:
        print(f"  ❌ Error retrieving historical data: {e}")

    # Disconnect
    print("\n" + "=" * 70)
    print("Test 7: Disconnection")
    print("=" * 70)

    client.disconnect()
    print("\n✓ Disconnected successfully")

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    print("\n✓ All connection tests completed!")
    print("\nNext steps:")
    print("  1. Review the test results above")
    print("  2. If market data tests failed, ensure you have ASX data subscriptions")
    print("  3. Verify your .env configuration is correct")
    print("  4. You're ready to proceed with strategy implementation")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
