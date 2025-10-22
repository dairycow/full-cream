"""
Exit logic for ASX trading strategy.

This module handles exit conditions:
- Stop loss hit
- End-of-day close
- (Future) Trailing stop after profit target
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class ExitSignal:
    """Exit signal with reason and price."""

    symbol: str
    exit_price: float
    exit_reason: str  # stop_loss, eod_close, trailing_stop, profit_target
    should_exit: bool
    exit_time: datetime = None

    def __post_init__(self):
        """Set exit time if not provided."""
        if self.exit_time is None:
            self.exit_time = datetime.now()

    def __str__(self) -> str:
        """String representation."""
        if self.should_exit:
            return (
                f"EXIT {self.symbol}: ${self.exit_price:.3f} | "
                f"Reason: {self.exit_reason} | "
                f"Time: {self.exit_time.strftime('%H:%M:%S')}"
            )
        else:
            return f"HOLD {self.symbol}: No exit signal"


class ExitLogic:
    """Determines exit signals based on strategy criteria."""

    def __init__(self):
        """Initialize exit logic."""
        self.config = get_config()
        self.logger = get_logger().bind(component="exit_logic")

        # Get EOD close time from config
        eod_time_str = self.config.eod_close_time
        hour, minute = map(int, eod_time_str.split(":"))
        self.eod_close_time = time(hour=hour, minute=minute)

        self.logger.info(f"Exit logic: EOD close at {self.eod_close_time}")

    def check_stop_loss(
        self,
        symbol: str,
        current_price: float,
        stop_price: float,
    ) -> ExitSignal:
        """
        Check if stop loss has been hit.

        Args:
            symbol: Stock symbol
            current_price: Current price
            stop_price: Stop loss price

        Returns:
            ExitSignal
        """
        should_exit = current_price <= stop_price

        if should_exit:
            self.logger.warning(
                f"{symbol}: STOP LOSS HIT! Current ${current_price:.3f} <= "
                f"Stop ${stop_price:.3f}"
            )

        return ExitSignal(
            symbol=symbol,
            exit_price=stop_price if should_exit else current_price,
            exit_reason="stop_loss",
            should_exit=should_exit,
        )

    def check_eod_close(
        self,
        symbol: str,
        current_price: float,
        current_time: Optional[datetime] = None,
    ) -> ExitSignal:
        """
        Check if it's time for end-of-day close.

        Args:
            symbol: Stock symbol
            current_price: Current price
            current_time: Current time (default: now)

        Returns:
            ExitSignal
        """
        if current_time is None:
            current_time = datetime.now()

        should_exit = current_time.time() >= self.eod_close_time

        if should_exit:
            self.logger.info(
                f"{symbol}: EOD close time reached ({self.eod_close_time}), "
                f"closing at ${current_price:.3f}"
            )

        return ExitSignal(
            symbol=symbol,
            exit_price=current_price,
            exit_reason="eod_close",
            should_exit=should_exit,
            exit_time=current_time,
        )

    def check_trailing_stop(
        self,
        symbol: str,
        current_price: float,
        entry_price: float,
        stop_price: float,
        highest_price_since_entry: float,
    ) -> tuple[ExitSignal, float]:
        """
        Check trailing stop (future enhancement).

        Args:
            symbol: Stock symbol
            current_price: Current price
            entry_price: Entry price
            stop_price: Current stop price
            highest_price_since_entry: Highest price since entry

        Returns:
            Tuple of (ExitSignal, new_stop_price)
        """
        # Check if trailing stop is enabled
        trailing_enabled = self.config.get_setting("exit", "trailing_stop_enabled", default=False)

        if not trailing_enabled:
            return (
                ExitSignal(
                    symbol=symbol,
                    exit_price=current_price,
                    exit_reason="trailing_stop",
                    should_exit=False,
                ),
                stop_price,
            )

        # Get trailing stop parameters
        trigger_r = self.config.get_setting("exit", "trailing_stop_trigger_r", default=2.0)
        distance_percent = self.config.get_setting(
            "exit", "trailing_stop_distance_percent", default=5.0
        )

        # Calculate R (initial risk)
        initial_risk = entry_price - stop_price
        trigger_price = entry_price + (initial_risk * trigger_r)

        # Check if we've reached trigger price
        if highest_price_since_entry < trigger_price:
            # Not triggered yet
            return (
                ExitSignal(
                    symbol=symbol,
                    exit_price=current_price,
                    exit_reason="trailing_stop",
                    should_exit=False,
                ),
                stop_price,
            )

        # Calculate trailing stop price
        trailing_stop = highest_price_since_entry * (1 - distance_percent / 100)

        # Use the higher of original stop or trailing stop
        new_stop_price = max(stop_price, trailing_stop)

        # Check if trailing stop hit
        should_exit = current_price <= new_stop_price

        if should_exit:
            self.logger.info(
                f"{symbol}: TRAILING STOP HIT! Current ${current_price:.3f} <= "
                f"Trailing Stop ${new_stop_price:.3f}"
            )

        return (
            ExitSignal(
                symbol=symbol,
                exit_price=new_stop_price if should_exit else current_price,
                exit_reason="trailing_stop",
                should_exit=should_exit,
            ),
            new_stop_price,
        )

    def get_exit_signal(
        self,
        symbol: str,
        current_price: float,
        stop_price: float,
        entry_price: Optional[float] = None,
        highest_price: Optional[float] = None,
        current_time: Optional[datetime] = None,
    ) -> ExitSignal:
        """
        Get exit signal by checking all exit conditions.

        Args:
            symbol: Stock symbol
            current_price: Current price
            stop_price: Stop loss price
            entry_price: Entry price (for trailing stop)
            highest_price: Highest price since entry (for trailing stop)
            current_time: Current time (default: now)

        Returns:
            ExitSignal (first triggered condition wins)
        """
        # Priority order:
        # 1. Stop loss (highest priority)
        # 2. EOD close
        # 3. Trailing stop (future)

        # Check stop loss
        stop_signal = self.check_stop_loss(symbol, current_price, stop_price)
        if stop_signal.should_exit:
            return stop_signal

        # Check EOD close
        eod_signal = self.check_eod_close(symbol, current_price, current_time)
        if eod_signal.should_exit:
            return eod_signal

        # Check trailing stop (if enabled and have required data)
        if entry_price is not None and highest_price is not None:
            trailing_signal, new_stop = self.check_trailing_stop(
                symbol, current_price, entry_price, stop_price, highest_price
            )
            if trailing_signal.should_exit:
                return trailing_signal

        # No exit signal
        return ExitSignal(
            symbol=symbol,
            exit_price=current_price,
            exit_reason="none",
            should_exit=False,
            exit_time=current_time or datetime.now(),
        )

    def should_exit_trade(self, exit_signal: ExitSignal) -> bool:
        """
        Final check before exiting trade.

        Args:
            exit_signal: Exit signal to validate

        Returns:
            True if should exit
        """
        if exit_signal.should_exit:
            self.logger.info(f"✓ Exit confirmed: {exit_signal}")
            return True

        return False

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExitLogic eod_close={self.eod_close_time}>"
