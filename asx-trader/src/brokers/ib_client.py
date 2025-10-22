"""
Interactive Brokers client for ASX Trading System.

This module provides a wrapper around ib_insync for:
- Connection management with auto-reconnect
- Contract creation for ASX stocks
- Market data requests
- Historical data fetching
- Order execution
- Account information
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ib_insync import IB, Stock, Order, Trade, MarketOrder, StopOrder, Contract, BarDataList
from ib_insync.objects import Position, PortfolioItem

from ..utils.config import get_config
from ..utils.logger import get_logger


class IBClient:
    """Interactive Brokers client wrapper."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
    ):
        """
        Initialize IB client.

        Args:
            host: IB Gateway host (default from config)
            port: IB Gateway port (default from config)
            client_id: Client ID (default from config)
        """
        self.config = get_config()
        self.logger = get_logger().bind(component="ib_client")

        self.host = host or self.config.ib_host
        self.port = port or self.config.ib_port
        self.client_id = client_id or self.config.ib_client_id

        self.ib = IB()
        self.is_connected = False
        self._reconnect_attempts = 0

        # Event handlers
        self.ib.disconnectedEvent += self._on_disconnect
        self.ib.errorEvent += self._on_error

    def connect(self, timeout: Optional[int] = None) -> bool:
        """
        Connect to IB Gateway.

        Args:
            timeout: Connection timeout in seconds (default from config)

        Returns:
            True if connected successfully, False otherwise
        """
        if self.is_connected:
            self.logger.info("Already connected to IB Gateway")
            return True

        timeout = timeout or self.config.connection_timeout

        try:
            self.logger.info(f"Connecting to IB Gateway at {self.host}:{self.port}...")
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=timeout,
                readonly=False,
            )
            self.is_connected = True
            self._reconnect_attempts = 0
            self.logger.info("✓ Connected to IB Gateway successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to IB Gateway: {e}", exception=e)
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from IB Gateway."""
        if self.is_connected:
            self.logger.info("Disconnecting from IB Gateway...")
            self.ib.disconnect()
            self.is_connected = False
            self.logger.info("✓ Disconnected from IB Gateway")

    def _on_disconnect(self):
        """Handle disconnection event."""
        self.is_connected = False
        self.logger.warning("Disconnected from IB Gateway")

    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract: Contract):
        """
        Handle error events.

        Args:
            reqId: Request ID
            errorCode: Error code
            errorString: Error message
            contract: Associated contract (if any)
        """
        # Error codes:
        # 502: Couldn't connect to TWS
        # 1100: Connectivity lost
        # 2104/2106: Market data farm connection (informational)
        # 2158: Sec-def data farm connection (informational)

        if errorCode in (2104, 2106, 2158):
            # Informational messages, log as debug
            self.logger.debug(f"IB Info [{errorCode}]: {errorString}")
        elif errorCode in (502, 1100):
            # Connection errors
            self.logger.error(f"IB Connection Error [{errorCode}]: {errorString}")
            self.is_connected = False
        else:
            # Other errors
            symbol = contract.symbol if contract else "N/A"
            self.logger.warning(f"IB Error [{errorCode}] {symbol}: {errorString}")

    def reconnect(self, max_attempts: Optional[int] = None, delay: Optional[int] = None) -> bool:
        """
        Attempt to reconnect to IB Gateway.

        Args:
            max_attempts: Maximum reconnection attempts (default from config)
            delay: Delay between attempts in seconds (default from config)

        Returns:
            True if reconnected successfully, False otherwise
        """
        max_attempts = max_attempts or self.config.retry_attempts
        delay = delay or self.config.retry_delay

        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Reconnection attempt {attempt}/{max_attempts}...")

            if self.connect():
                self.logger.info("✓ Reconnected successfully")
                return True

            if attempt < max_attempts:
                self.logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)

        self.logger.error(f"Failed to reconnect after {max_attempts} attempts")
        return False

    # === CONTRACT CREATION ===

    def create_stock_contract(self, symbol: str, exchange: str = "ASX", currency: str = "AUD") -> Stock:
        """
        Create a stock contract for ASX.

        Args:
            symbol: Stock symbol (e.g., 'BHP')
            exchange: Exchange (default: 'ASX')
            currency: Currency (default: 'AUD')

        Returns:
            Stock contract
        """
        contract = Stock(symbol=symbol, exchange=exchange, currency=currency)
        self.logger.debug(f"Created contract for {symbol} on {exchange}")
        return contract

    def qualify_contract(self, contract: Contract) -> Optional[Contract]:
        """
        Qualify a contract with IB.

        Args:
            contract: Contract to qualify

        Returns:
            Qualified contract or None if failed
        """
        try:
            qualified = self.ib.qualifyContracts(contract)
            if qualified:
                self.logger.debug(f"✓ Qualified contract: {contract.symbol}")
                return qualified[0]
            else:
                self.logger.warning(f"Failed to qualify contract: {contract.symbol}")
                return None
        except Exception as e:
            self.logger.error(f"Error qualifying contract {contract.symbol}: {e}", exception=e)
            return None

    # === MARKET DATA ===

    def get_market_data(self, contract: Contract, snapshot: bool = False) -> Optional[Any]:
        """
        Request market data for a contract.

        Args:
            contract: Contract to get data for
            snapshot: If True, request snapshot only (default: streaming)

        Returns:
            Ticker object with market data
        """
        try:
            # Qualify contract first
            qualified = self.qualify_contract(contract)
            if not qualified:
                return None

            ticker = self.ib.reqMktData(qualified, snapshot=snapshot)
            self.ib.sleep(1)  # Wait for data to populate

            self.logger.debug(f"Market data for {contract.symbol}: Last={ticker.last} Bid={ticker.bid} Ask={ticker.ask}")
            return ticker

        except Exception as e:
            self.logger.error(f"Error getting market data for {contract.symbol}: {e}", exception=e)
            return None

    def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Get last traded price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Last price or None if unavailable
        """
        contract = self.create_stock_contract(symbol)
        ticker = self.get_market_data(contract, snapshot=True)

        if ticker and ticker.last:
            return ticker.last
        elif ticker and ticker.close:
            # If last is not available, use previous close
            self.logger.debug(f"Last price not available for {symbol}, using close: {ticker.close}")
            return ticker.close
        else:
            self.logger.warning(f"No price data available for {symbol}")
            return None

    def get_historical_data(
        self,
        contract: Contract,
        duration: str = "1 D",
        bar_size: str = "1 min",
        what_to_show: str = "TRADES",
        use_rth: bool = True,
    ) -> Optional[BarDataList]:
        """
        Get historical bar data.

        Args:
            contract: Contract to get data for
            duration: How far back to fetch (e.g., '1 D', '1 W', '1 M')
            bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            use_rth: Use regular trading hours only

        Returns:
            List of bar data or None if failed
        """
        try:
            # Qualify contract first
            qualified = self.qualify_contract(contract)
            if not qualified:
                return None

            bars = self.ib.reqHistoricalData(
                qualified,
                endDateTime="",  # Current time
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1,  # Return as datetime objects
            )

            self.logger.debug(f"Retrieved {len(bars)} bars for {contract.symbol}")
            return bars

        except Exception as e:
            self.logger.error(f"Error getting historical data for {contract.symbol}: {e}", exception=e)
            return None

    def get_previous_close(self, symbol: str) -> Optional[float]:
        """
        Get previous day's closing price.

        Args:
            symbol: Stock symbol

        Returns:
            Previous close price or None if unavailable
        """
        contract = self.create_stock_contract(symbol)
        bars = self.get_historical_data(contract, duration="2 D", bar_size="1 day")

        if bars and len(bars) >= 1:
            # Get the most recent complete day
            prev_close = bars[-1].close
            self.logger.debug(f"Previous close for {symbol}: ${prev_close:.3f}")
            return prev_close
        else:
            self.logger.warning(f"No historical data available for {symbol}")
            return None

    # === ORDER EXECUTION ===

    def place_market_order(
        self,
        contract: Contract,
        quantity: int,
        action: str = "BUY",
    ) -> Optional[Trade]:
        """
        Place a market order.

        Args:
            contract: Contract to trade
            quantity: Number of shares
            action: 'BUY' or 'SELL'

        Returns:
            Trade object or None if failed
        """
        try:
            # Qualify contract
            qualified = self.qualify_contract(contract)
            if not qualified:
                return None

            order = MarketOrder(action=action, totalQuantity=quantity)

            trade = self.ib.placeOrder(qualified, order)
            self.logger.info(f"Placed {action} market order: {quantity} x {contract.symbol}")

            # Wait for order to be submitted
            self.ib.sleep(1)

            return trade

        except Exception as e:
            self.logger.error(f"Error placing market order for {contract.symbol}: {e}", exception=e)
            return None

    def place_stop_order(
        self,
        contract: Contract,
        quantity: int,
        stop_price: float,
        action: str = "SELL",
    ) -> Optional[Trade]:
        """
        Place a stop loss order.

        Args:
            contract: Contract to trade
            quantity: Number of shares
            stop_price: Stop trigger price
            action: 'BUY' or 'SELL' (usually 'SELL' for stop loss)

        Returns:
            Trade object or None if failed
        """
        try:
            # Qualify contract
            qualified = self.qualify_contract(contract)
            if not qualified:
                return None

            order = StopOrder(
                action=action,
                totalQuantity=quantity,
                stopPrice=stop_price,
            )

            trade = self.ib.placeOrder(qualified, order)
            self.logger.info(
                f"Placed {action} stop order: {quantity} x {contract.symbol} @ ${stop_price:.3f}"
            )

            # Wait for order to be submitted
            self.ib.sleep(1)

            return trade

        except Exception as e:
            self.logger.error(f"Error placing stop order for {contract.symbol}: {e}", exception=e)
            return None

    def cancel_order(self, order: Order) -> bool:
        """
        Cancel an order.

        Args:
            order: Order to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            self.ib.cancelOrder(order)
            self.logger.info(f"Cancelled order: {order.orderId}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order {order.orderId}: {e}", exception=e)
            return False

    def get_open_orders(self) -> List[Trade]:
        """
        Get all open orders.

        Returns:
            List of open trades
        """
        try:
            trades = self.ib.openTrades()
            self.logger.debug(f"Retrieved {len(trades)} open orders")
            return trades
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}", exception=e)
            return []

    # === ACCOUNT MANAGEMENT ===

    def get_account_value(self, tag: str = "NetLiquidation") -> Optional[float]:
        """
        Get account value.

        Args:
            tag: Account value tag (e.g., 'NetLiquidation', 'TotalCashValue', 'BuyingPower')

        Returns:
            Account value or None if unavailable
        """
        try:
            account_values = self.ib.accountValues()
            for av in account_values:
                if av.tag == tag:
                    value = float(av.value)
                    self.logger.debug(f"Account {tag}: ${value:,.2f}")
                    return value

            self.logger.warning(f"Account value tag '{tag}' not found")
            return None

        except Exception as e:
            self.logger.error(f"Error getting account value: {e}", exception=e)
            return None

    def get_buying_power(self) -> Optional[float]:
        """
        Get available buying power.

        Returns:
            Buying power or None if unavailable
        """
        return self.get_account_value("BuyingPower")

    def get_net_liquidation(self) -> Optional[float]:
        """
        Get net liquidation value (total account value).

        Returns:
            Net liquidation value or None if unavailable
        """
        return self.get_account_value("NetLiquidation")

    def get_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of positions
        """
        try:
            positions = self.ib.positions()
            self.logger.debug(f"Retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}", exception=e)
            return []

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Position or None if not found
        """
        positions = self.get_positions()
        for pos in positions:
            if pos.contract.symbol == symbol:
                return pos
        return None

    def get_portfolio(self) -> List[PortfolioItem]:
        """
        Get portfolio items.

        Returns:
            List of portfolio items
        """
        try:
            portfolio = self.ib.portfolio()
            self.logger.debug(f"Retrieved {len(portfolio)} portfolio items")
            return portfolio
        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}", exception=e)
            return []

    # === UTILITY METHODS ===

    def wait_for_fill(self, trade: Trade, timeout: int = 60) -> bool:
        """
        Wait for an order to be filled.

        Args:
            trade: Trade to monitor
            timeout: Timeout in seconds

        Returns:
            True if filled, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.ib.sleep(1)
            if trade.orderStatus.status == "Filled":
                self.logger.info(f"Order filled: {trade.contract.symbol}")
                return True
            elif trade.orderStatus.status in ("Cancelled", "ApiCancelled"):
                self.logger.warning(f"Order cancelled: {trade.contract.symbol}")
                return False

        self.logger.warning(f"Order fill timeout for {trade.contract.symbol}")
        return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        status = "Connected" if self.is_connected else "Disconnected"
        return f"<IBClient {self.host}:{self.port} {status}>"
