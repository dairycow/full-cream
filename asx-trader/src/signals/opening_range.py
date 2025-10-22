"""
Opening Range tracker for ASX stocks.

This module tracks the opening range (OR) - the high and low prices during
the first N minutes of trading (typically 15 minutes for ASX: 10:00-10:15 AM).

The OR high and low are used for:
- Entry: Breakout above OR high
- Stop loss: Below OR low
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional, List

from ..brokers.ib_client import IBClient
from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class OpeningRangeData:
    """Opening range data for a symbol."""

    symbol: str
    or_high: float
    or_low: float
    or_start_time: datetime
    or_end_time: datetime
    or_duration_minutes: int
    range_dollars: float
    range_percent: float
    volume: Optional[int] = None
    num_bars: int = 0

    def __str__(self) -> str:
        """String representation."""
        return (
            f"OR {self.symbol}: High ${self.or_high:.3f} | Low ${self.or_low:.3f} | "
            f"Range ${self.range_dollars:.3f} ({self.range_percent:.2f}%)"
        )


@dataclass
class BreakoutSignal:
    """Opening range breakout signal."""

    symbol: str
    or_data: OpeningRangeData
    breakout_price: float
    breakout_time: datetime
    distance_above_or: float
    distance_percent: float
    is_breakout: bool

    def __str__(self) -> str:
        """String representation."""
        if self.is_breakout:
            return (
                f"BREAKOUT {self.symbol}: ${self.breakout_price:.3f} "
                f"(+${self.distance_above_or:.3f} above OR high)"
            )
        return f"NO BREAKOUT {self.symbol}: ${self.breakout_price:.3f}"


class OpeningRangeTracker:
    """Tracks opening range for stocks."""

    def __init__(self, ib_client: Optional[IBClient] = None, duration_minutes: Optional[int] = None):
        """
        Initialize opening range tracker.

        Args:
            ib_client: IB client instance (optional)
            duration_minutes: OR duration in minutes (default from config)
        """
        self.config = get_config()
        self.logger = get_logger().bind(component="opening_range")
        self.ib_client = ib_client
        self._owns_client = False

        if self.ib_client is None:
            self.ib_client = IBClient()
            self._owns_client = True

        # Get OR duration from config or use provided value
        or_minutes_config = self.config.get_setting("trading_hours", "opening_range_minutes", default=15)
        self.duration_minutes = duration_minutes or or_minutes_config

        self.logger.info(f"Opening Range duration: {self.duration_minutes} minutes")

    def calculate_opening_range(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[OpeningRangeData]:
        """
        Calculate opening range for a symbol.

        Args:
            symbol: Stock symbol
            start_time: OR start time (default: market open from config)
            end_time: OR end time (default: start + duration_minutes)

        Returns:
            OpeningRangeData or None if failed
        """
        try:
            # Default to market open time if not provided
            if start_time is None:
                # Use today's market open time
                market_open_str = self.config.get_setting("trading_hours", "market_open", default="10:00")
                hour, minute = map(int, market_open_str.split(":"))
                start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

            if end_time is None:
                end_time = start_time + timedelta(minutes=self.duration_minutes)

            # Get historical bars for the OR period
            contract = self.ib_client.create_stock_contract(symbol)

            # Request 1-minute bars for the OR period
            # We'll get slightly more data to ensure we cover the full range
            bars = self.ib_client.get_historical_data(
                contract,
                duration=f"{self.duration_minutes + 5} min",
                bar_size="1 min",
                what_to_show="TRADES",
                use_rth=True,
            )

            if not bars or len(bars) == 0:
                self.logger.warning(f"No bars available for {symbol}")
                return None

            # Filter bars within OR time window
            or_bars = [bar for bar in bars if start_time <= bar.date <= end_time]

            if not or_bars:
                self.logger.warning(f"No bars found in OR window for {symbol}")
                return None

            # Calculate OR high and low
            or_high = max(bar.high for bar in or_bars)
            or_low = min(bar.low for bar in or_bars)
            total_volume = sum(bar.volume for bar in or_bars)

            # Calculate range metrics
            range_dollars = or_high - or_low
            range_percent = (range_dollars / or_low) * 100 if or_low > 0 else 0

            or_data = OpeningRangeData(
                symbol=symbol,
                or_high=or_high,
                or_low=or_low,
                or_start_time=start_time,
                or_end_time=end_time,
                or_duration_minutes=self.duration_minutes,
                range_dollars=range_dollars,
                range_percent=range_percent,
                volume=total_volume,
                num_bars=len(or_bars),
            )

            self.logger.debug(str(or_data))
            return or_data

        except Exception as e:
            self.logger.error(f"Error calculating opening range for {symbol}: {e}", exception=e)
            return None

    def detect_breakout(
        self,
        symbol: str,
        current_price: float,
        or_data: OpeningRangeData,
        breakout_buffer: Optional[float] = None,
    ) -> BreakoutSignal:
        """
        Detect if current price has broken above OR high.

        Args:
            symbol: Stock symbol
            current_price: Current price to check
            or_data: Opening range data
            breakout_buffer: Additional buffer above OR high (in dollars)

        Returns:
            BreakoutSignal
        """
        # Get breakout buffer from config if not provided
        if breakout_buffer is None:
            breakout_ticks = self.config.get_setting("entry", "breakout_confirmation_ticks", default=2)
            # Assume 1 tick = 1 cent for ASX stocks
            breakout_buffer = breakout_ticks * 0.01

        breakout_threshold = or_data.or_high + breakout_buffer
        distance_above_or = current_price - or_data.or_high
        distance_percent = (distance_above_or / or_data.or_high) * 100 if or_data.or_high > 0 else 0

        is_breakout = current_price >= breakout_threshold

        signal = BreakoutSignal(
            symbol=symbol,
            or_data=or_data,
            breakout_price=current_price,
            breakout_time=datetime.now(),
            distance_above_or=distance_above_or,
            distance_percent=distance_percent,
            is_breakout=is_breakout,
        )

        if is_breakout:
            self.logger.info(str(signal))
        else:
            self.logger.debug(
                f"{symbol}: ${current_price:.3f} below breakout threshold "
                f"${breakout_threshold:.3f}"
            )

        return signal

    def is_valid_breakout(self, signal: BreakoutSignal) -> bool:
        """
        Validate breakout signal meets all criteria.

        Args:
            signal: Breakout signal to validate

        Returns:
            True if valid for entry
        """
        if not signal.is_breakout:
            return False

        # Additional validation can be added here:
        # - Volume surge check
        # - Time-of-day filters
        # - Maximum distance above OR (to avoid chasing)

        self.logger.info(f"✓ Valid breakout: {signal}")
        return True

    def monitor_breakouts(
        self,
        symbols: List[str],
        or_data_map: dict[str, OpeningRangeData],
    ) -> List[BreakoutSignal]:
        """
        Monitor multiple symbols for OR breakouts.

        Args:
            symbols: List of symbols to monitor
            or_data_map: Dictionary mapping symbols to their OR data

        Returns:
            List of breakout signals
        """
        breakouts = []

        for symbol in symbols:
            if symbol not in or_data_map:
                self.logger.warning(f"No OR data for {symbol}, skipping")
                continue

            # Get current price
            current_price = self.ib_client.get_last_price(symbol)
            if current_price is None:
                self.logger.warning(f"Could not get current price for {symbol}")
                continue

            # Detect breakout
            or_data = or_data_map[symbol]
            signal = self.detect_breakout(symbol, current_price, or_data)

            if signal.is_breakout:
                breakouts.append(signal)

        self.logger.info(f"Detected {len(breakouts)} breakouts from {len(symbols)} symbols")
        return breakouts

    def calculate_stop_price(
        self,
        or_data: OpeningRangeData,
        buffer_cents: Optional[float] = None,
    ) -> float:
        """
        Calculate stop loss price based on OR low.

        Args:
            or_data: Opening range data
            buffer_cents: Buffer below OR low in cents (default from config)

        Returns:
            Stop price
        """
        if buffer_cents is None:
            buffer_cents = self.config.get_setting("risk", "stop_loss_buffer_cents", default=0.01)

        stop_price = or_data.or_low - buffer_cents

        self.logger.debug(
            f"{or_data.symbol}: Stop price ${stop_price:.3f} "
            f"(OR low ${or_data.or_low:.3f} - ${buffer_cents:.2f})"
        )

        return stop_price

    def __enter__(self):
        """Context manager entry."""
        if self._owns_client and not self.ib_client.is_connected:
            self.ib_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._owns_client:
            self.ib_client.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        return f"<OpeningRangeTracker duration={self.duration_minutes}min>"
