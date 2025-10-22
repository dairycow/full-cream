"""
Position sizing calculator for risk management.

This module calculates position sizes based on:
- Risk per trade (% of capital)
- Entry and stop prices
- Account balance
- Maximum position size constraints
"""

from dataclasses import dataclass
from typing import Optional

from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class PositionSize:
    """Position sizing calculation result."""

    symbol: str
    entry_price: float
    stop_price: float
    account_balance: float
    risk_amount_dollars: float
    risk_per_share: float
    shares: int
    position_value: float
    position_percent: float
    is_valid: bool
    rejection_reason: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        if self.is_valid:
            return (
                f"Position {self.symbol}: {self.shares} shares @ ${self.entry_price:.3f} | "
                f"Value: ${self.position_value:,.2f} ({self.position_percent:.1f}% of capital) | "
                f"Risk: ${self.risk_amount_dollars:.2f}"
            )
        else:
            return f"REJECTED {self.symbol}: {self.rejection_reason}"


class PositionSizer:
    """Calculates position sizes based on risk parameters."""

    def __init__(self):
        """Initialize position sizer."""
        self.config = get_config()
        self.logger = get_logger().bind(component="position_sizer")

        self.risk_per_trade_percent = self.config.risk_per_trade_percent
        self.max_position_size_percent = self.config.max_position_size_percent

        self.logger.info(
            f"Position sizer: {self.risk_per_trade_percent}% risk per trade, "
            f"{self.max_position_size_percent}% max position size"
        )

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_price: float,
        account_balance: float,
    ) -> PositionSize:
        """
        Calculate position size based on risk.

        Args:
            symbol: Stock symbol
            entry_price: Planned entry price
            stop_price: Stop loss price
            account_balance: Current account balance

        Returns:
            PositionSize with calculation details
        """
        # Validate inputs
        if entry_price <= 0:
            return PositionSize(
                symbol=symbol,
                entry_price=entry_price,
                stop_price=stop_price,
                account_balance=account_balance,
                risk_amount_dollars=0,
                risk_per_share=0,
                shares=0,
                position_value=0,
                position_percent=0,
                is_valid=False,
                rejection_reason="Invalid entry price",
            )

        if stop_price >= entry_price:
            return PositionSize(
                symbol=symbol,
                entry_price=entry_price,
                stop_price=stop_price,
                account_balance=account_balance,
                risk_amount_dollars=0,
                risk_per_share=0,
                shares=0,
                position_value=0,
                position_percent=0,
                is_valid=False,
                rejection_reason=f"Stop price ${stop_price:.3f} must be below entry ${entry_price:.3f}",
            )

        # Calculate risk per share
        risk_per_share = entry_price - stop_price

        # Calculate risk amount in dollars (% of account)
        risk_amount_dollars = account_balance * (self.risk_per_trade_percent / 100)

        # Calculate number of shares
        shares = int(risk_amount_dollars / risk_per_share)

        if shares <= 0:
            return PositionSize(
                symbol=symbol,
                entry_price=entry_price,
                stop_price=stop_price,
                account_balance=account_balance,
                risk_amount_dollars=risk_amount_dollars,
                risk_per_share=risk_per_share,
                shares=0,
                position_value=0,
                position_percent=0,
                is_valid=False,
                rejection_reason=f"Risk per share ${risk_per_share:.3f} too large for account",
            )

        # Calculate position value
        position_value = shares * entry_price
        position_percent = (position_value / account_balance) * 100

        # Check maximum position size constraint
        max_position_value = account_balance * (self.max_position_size_percent / 100)

        if position_value > max_position_value:
            # Reduce shares to meet max position size
            shares_adjusted = int(max_position_value / entry_price)
            position_value_adjusted = shares_adjusted * entry_price
            position_percent_adjusted = (position_value_adjusted / account_balance) * 100
            risk_amount_adjusted = shares_adjusted * risk_per_share

            self.logger.debug(
                f"{symbol}: Position size reduced from {shares} to {shares_adjusted} shares "
                f"to meet max position size constraint"
            )

            result = PositionSize(
                symbol=symbol,
                entry_price=entry_price,
                stop_price=stop_price,
                account_balance=account_balance,
                risk_amount_dollars=risk_amount_adjusted,
                risk_per_share=risk_per_share,
                shares=shares_adjusted,
                position_value=position_value_adjusted,
                position_percent=position_percent_adjusted,
                is_valid=True,
            )
        else:
            result = PositionSize(
                symbol=symbol,
                entry_price=entry_price,
                stop_price=stop_price,
                account_balance=account_balance,
                risk_amount_dollars=risk_amount_dollars,
                risk_per_share=risk_per_share,
                shares=shares,
                position_value=position_value,
                position_percent=position_percent,
                is_valid=True,
            )

        self.logger.debug(str(result))
        return result

    def validate_position_size(self, position: PositionSize) -> bool:
        """
        Validate that position meets all constraints.

        Args:
            position: Position size to validate

        Returns:
            True if valid
        """
        if not position.is_valid:
            self.logger.warning(str(position))
            return False

        # Check minimum account balance
        if position.account_balance < self.config.min_account_balance:
            self.logger.warning(
                f"{position.symbol}: Account balance ${position.account_balance:,.2f} "
                f"below minimum ${self.config.min_account_balance:,.2f}"
            )
            return False

        # Additional validation checks can be added here
        self.logger.info(f"✓ Valid position size: {position}")
        return True

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PositionSizer risk={self.risk_per_trade_percent}% "
            f"max={self.max_position_size_percent}%>"
        )
