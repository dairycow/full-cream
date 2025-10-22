"""
Entry logic for ASX trading strategy.

This module combines all entry signals:
- Catalyst (price-sensitive announcement)
- Gap-up (3-15% at market open)
- Opening range breakout

Entry occurs when all conditions are met.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..signals.gap_detector import GapSignal
from ..signals.opening_range import OpeningRangeData, BreakoutSignal
from ..scrapers.catalyst_scorer import CatalystScore
from ..risk.position_sizer import PositionSize, PositionSizer
from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class EntrySignal:
    """Complete entry signal with all components."""

    symbol: str
    catalyst: CatalystScore
    gap: GapSignal
    or_data: OpeningRangeData
    breakout: BreakoutSignal
    position_size: PositionSize
    entry_price: float
    stop_price: float
    is_valid: bool
    rejection_reason: Optional[str] = None
    signal_time: datetime = None

    def __post_init__(self):
        """Set signal time if not provided."""
        if self.signal_time is None:
            self.signal_time = datetime.now()

    def __str__(self) -> str:
        """String representation."""
        if self.is_valid:
            return (
                f"ENTRY {self.symbol}: "
                f"Entry ${self.entry_price:.3f} | Stop ${self.stop_price:.3f} | "
                f"{self.position_size.shares} shares | "
                f"Catalyst [{self.catalyst.score}/10] | Gap {self.gap.gap_percent:.1f}%"
            )
        else:
            return f"REJECTED {self.symbol}: {self.rejection_reason}"


class EntryLogic:
    """Determines entry signals based on strategy criteria."""

    def __init__(self, position_sizer: Optional[PositionSizer] = None):
        """
        Initialize entry logic.

        Args:
            position_sizer: Position sizer instance (optional)
        """
        self.config = get_config()
        self.logger = get_logger().bind(component="entry_logic")
        self.position_sizer = position_sizer or PositionSizer()

    def validate_entry_conditions(
        self,
        symbol: str,
        catalyst: CatalystScore,
        gap: GapSignal,
        breakout: BreakoutSignal,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate all entry conditions are met.

        Args:
            symbol: Stock symbol
            catalyst: Catalyst score
            gap: Gap signal
            breakout: Breakout signal

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        # Check catalyst
        if not catalyst.is_positive or catalyst.score < self.config.get_setting("catalysts", "min_catalyst_score", default=5):
            return False, f"Catalyst score {catalyst.score} too low"

        # Check gap
        if not gap.is_gap_up:
            return False, "Not a gap up"

        if gap.gap_percent < self.config.min_gap_percent:
            return False, f"Gap {gap.gap_percent:.1f}% below minimum {self.config.min_gap_percent}%"

        if gap.gap_percent > self.config.max_gap_percent:
            return False, f"Gap {gap.gap_percent:.1f}% exceeds maximum {self.config.max_gap_percent}%"

        # Check breakout
        if not breakout.is_breakout:
            return False, "No OR breakout detected"

        # Check price range
        if breakout.breakout_price < self.config.min_stock_price:
            return False, f"Price ${breakout.breakout_price:.2f} below minimum ${self.config.min_stock_price:.2f}"

        if breakout.breakout_price > self.config.max_stock_price:
            return False, f"Price ${breakout.breakout_price:.2f} exceeds maximum ${self.config.max_stock_price:.2f}"

        # All conditions met
        return True, None

    def create_entry_signal(
        self,
        symbol: str,
        catalyst: CatalystScore,
        gap: GapSignal,
        or_data: OpeningRangeData,
        breakout: BreakoutSignal,
        account_balance: float,
    ) -> EntrySignal:
        """
        Create complete entry signal.

        Args:
            symbol: Stock symbol
            catalyst: Catalyst score
            gap: Gap signal
            or_data: Opening range data
            breakout: Breakout signal
            account_balance: Current account balance

        Returns:
            EntrySignal with all details
        """
        # Validate entry conditions
        is_valid, rejection_reason = self.validate_entry_conditions(
            symbol, catalyst, gap, breakout
        )

        if not is_valid:
            self.logger.debug(f"{symbol}: Entry rejected - {rejection_reason}")
            return EntrySignal(
                symbol=symbol,
                catalyst=catalyst,
                gap=gap,
                or_data=or_data,
                breakout=breakout,
                position_size=None,
                entry_price=breakout.breakout_price,
                stop_price=0,
                is_valid=False,
                rejection_reason=rejection_reason,
            )

        # Calculate entry and stop prices
        entry_price = breakout.breakout_price

        # Stop price calculation
        stop_buffer = self.config.get_setting("risk", "stop_loss_buffer_cents", default=0.01)
        stop_price = or_data.or_low - stop_buffer

        # Calculate position size
        position_size = self.position_sizer.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_price=stop_price,
            account_balance=account_balance,
        )

        # Validate position size
        if not self.position_sizer.validate_position_size(position_size):
            return EntrySignal(
                symbol=symbol,
                catalyst=catalyst,
                gap=gap,
                or_data=or_data,
                breakout=breakout,
                position_size=position_size,
                entry_price=entry_price,
                stop_price=stop_price,
                is_valid=False,
                rejection_reason=position_size.rejection_reason or "Invalid position size",
            )

        # Create valid entry signal
        signal = EntrySignal(
            symbol=symbol,
            catalyst=catalyst,
            gap=gap,
            or_data=or_data,
            breakout=breakout,
            position_size=position_size,
            entry_price=entry_price,
            stop_price=stop_price,
            is_valid=True,
        )

        self.logger.info(f"✓ {signal}")
        return signal

    def should_enter_trade(self, entry_signal: EntrySignal) -> bool:
        """
        Final check before entering trade.

        Args:
            entry_signal: Entry signal to validate

        Returns:
            True if should enter
        """
        if not entry_signal.is_valid:
            return False

        # Additional checks can be added here:
        # - Time of day filters
        # - Market conditions
        # - Existing positions check

        return True

    def __repr__(self) -> str:
        """String representation."""
        return f"<EntryLogic {self.position_sizer}>"
