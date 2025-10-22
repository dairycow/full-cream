"""
Gap detection for ASX stocks.

This module detects gap-ups (and gap-downs) at market open by comparing
the opening price to the previous day's closing price.

A gap-up occurs when: (open_price - prev_close) / prev_close * 100 > threshold
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..brokers.ib_client import IBClient
from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class GapSignal:
    """Gap detection signal."""

    symbol: str
    prev_close: float
    open_price: float
    gap_percent: float
    gap_dollars: float
    detected_at: datetime
    is_gap_up: bool
    is_gap_down: bool
    volume: Optional[int] = None

    def __str__(self) -> str:
        """String representation."""
        direction = "UP" if self.is_gap_up else "DOWN" if self.is_gap_down else "FLAT"
        return (
            f"Gap {direction}: {self.symbol} | "
            f"Prev Close: ${self.prev_close:.3f} → Open: ${self.open_price:.3f} | "
            f"Gap: {self.gap_percent:+.2f}% (${self.gap_dollars:+.3f})"
        )


class GapDetector:
    """Detects price gaps at market open."""

    def __init__(self, ib_client: Optional[IBClient] = None):
        """
        Initialize gap detector.

        Args:
            ib_client: IB client instance (optional, will create if not provided)
        """
        self.config = get_config()
        self.logger = get_logger().bind(component="gap_detector")
        self.ib_client = ib_client
        self._owns_client = False

        if self.ib_client is None:
            self.ib_client = IBClient()
            self._owns_client = True

    def calculate_gap(
        self,
        symbol: str,
        open_price: float,
        prev_close: float,
    ) -> GapSignal:
        """
        Calculate gap percentage and dollars.

        Args:
            symbol: Stock symbol
            open_price: Opening price
            prev_close: Previous day's closing price

        Returns:
            GapSignal with calculated metrics
        """
        gap_dollars = open_price - prev_close
        gap_percent = (gap_dollars / prev_close) * 100

        is_gap_up = gap_percent > 0
        is_gap_down = gap_percent < 0

        signal = GapSignal(
            symbol=symbol,
            prev_close=prev_close,
            open_price=open_price,
            gap_percent=gap_percent,
            gap_dollars=gap_dollars,
            detected_at=datetime.now(),
            is_gap_up=is_gap_up,
            is_gap_down=is_gap_down,
        )

        self.logger.debug(str(signal))
        return signal

    def detect_gap(self, symbol: str, open_price: Optional[float] = None) -> Optional[GapSignal]:
        """
        Detect gap for a symbol at market open.

        Args:
            symbol: Stock symbol
            open_price: Opening price (if None, will fetch from IB)

        Returns:
            GapSignal if detected, None if error
        """
        try:
            # Get previous close
            prev_close = self.ib_client.get_previous_close(symbol)
            if prev_close is None:
                self.logger.warning(f"Could not get previous close for {symbol}")
                return None

            # Get open price if not provided
            if open_price is None:
                # Get current/opening price
                current_price = self.ib_client.get_last_price(symbol)
                if current_price is None:
                    self.logger.warning(f"Could not get current price for {symbol}")
                    return None
                open_price = current_price

            # Calculate gap
            signal = self.calculate_gap(symbol, open_price, prev_close)

            return signal

        except Exception as e:
            self.logger.error(f"Error detecting gap for {symbol}: {e}", exception=e)
            return None

    def is_valid_gap_up(self, signal: GapSignal) -> bool:
        """
        Check if gap-up meets entry criteria.

        Args:
            signal: Gap signal to validate

        Returns:
            True if valid for trading
        """
        if not signal.is_gap_up:
            self.logger.debug(f"{signal.symbol}: Not a gap up")
            return False

        # Check minimum gap
        if signal.gap_percent < self.config.min_gap_percent:
            self.logger.debug(
                f"{signal.symbol}: Gap {signal.gap_percent:.2f}% below minimum "
                f"{self.config.min_gap_percent}%"
            )
            return False

        # Check maximum gap (avoid excessive gaps)
        if signal.gap_percent > self.config.max_gap_percent:
            self.logger.debug(
                f"{signal.symbol}: Gap {signal.gap_percent:.2f}% exceeds maximum "
                f"{self.config.max_gap_percent}%"
            )
            return False

        # Check price range
        if signal.open_price < self.config.min_stock_price:
            self.logger.debug(
                f"{signal.symbol}: Price ${signal.open_price:.2f} below minimum "
                f"${self.config.min_stock_price:.2f}"
            )
            return False

        if signal.open_price > self.config.max_stock_price:
            self.logger.debug(
                f"{signal.symbol}: Price ${signal.open_price:.2f} exceeds maximum "
                f"${self.config.max_stock_price:.2f}"
            )
            return False

        self.logger.info(f"✓ Valid gap-up detected: {signal}")
        return True

    def scan_for_gaps(self, symbols: list[str]) -> list[GapSignal]:
        """
        Scan multiple symbols for gaps.

        Args:
            symbols: List of symbols to scan

        Returns:
            List of detected gap signals
        """
        gaps = []

        self.logger.info(f"Scanning {len(symbols)} symbols for gaps...")

        for symbol in symbols:
            signal = self.detect_gap(symbol)
            if signal:
                gaps.append(signal)

        self.logger.info(f"Found {len(gaps)} gaps")
        return gaps

    def get_valid_gap_ups(self, symbols: list[str]) -> list[GapSignal]:
        """
        Get valid gap-up signals that meet entry criteria.

        Args:
            symbols: List of symbols to scan

        Returns:
            List of valid gap-up signals
        """
        all_gaps = self.scan_for_gaps(symbols)
        valid_gaps = [gap for gap in all_gaps if self.is_valid_gap_up(gap)]

        self.logger.info(
            f"Found {len(valid_gaps)} valid gap-ups out of {len(all_gaps)} total gaps"
        )

        return valid_gaps

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
        return (
            f"<GapDetector min={self.config.min_gap_percent}% "
            f"max={self.config.max_gap_percent}%>"
        )
