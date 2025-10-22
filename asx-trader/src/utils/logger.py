"""
Logging configuration for ASX Trading System.

This module sets up structured logging using loguru with:
- Console output with color coding
- File output with rotation
- Separate logs for trades and errors
- Integration with database logging
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


class TradingLogger:
    """Centralized logging configuration for the trading system."""

    def __init__(
        self,
        log_dir: str = "data/logs",
        log_level: str = "INFO",
        rotation: str = "100 MB",
        retention: str = "30 days",
        enable_console: bool = True,
        enable_file: bool = True,
    ):
        """
        Initialize the trading logger.

        Args:
            log_dir: Directory to store log files
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            rotation: When to rotate log files (e.g., "100 MB", "1 day")
            retention: How long to keep old logs
            enable_console: Whether to log to console
            enable_file: Whether to log to files
        """
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.rotation = rotation
        self.retention = retention
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Remove default logger
        logger.remove()

        # Set up loggers
        self._setup_console_logger()
        if self.enable_file:
            self._setup_file_loggers()

    def _setup_console_logger(self):
        """Set up console logging with color coding."""
        if not self.enable_console:
            return

        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level=self.log_level,
            colorize=True,
        )

    def _setup_file_loggers(self):
        """Set up file logging with rotation."""
        # Main log file
        logger.add(
            self.log_dir / "trading_system.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.log_level,
            rotation=self.rotation,
            retention=self.retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

        # Error log file (WARNING and above only)
        logger.add(
            self.log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level="WARNING",
            rotation=self.rotation,
            retention=self.retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

        # Trade log file (for trade-specific events)
        logger.add(
            self.log_dir / "trades.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            rotation="1 day",
            retention=self.retention,
            compression="zip",
            filter=lambda record: "trade" in record["extra"].get("component", "").lower(),
        )

    @staticmethod
    def get_logger():
        """Get the configured logger instance."""
        return logger

    def log_trade_entry(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_price: float,
        catalyst_score: Optional[int] = None,
    ):
        """
        Log a trade entry with structured data.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            entry_price: Entry price
            stop_price: Stop loss price
            catalyst_score: Catalyst score (1-10)
        """
        risk_dollars = quantity * abs(entry_price - stop_price)
        logger.bind(component="trade").info(
            f"ENTRY | {symbol} | Qty: {quantity} | "
            f"Entry: ${entry_price:.3f} | Stop: ${stop_price:.3f} | "
            f"Risk: ${risk_dollars:.2f} | Catalyst: {catalyst_score or 'N/A'}"
        )

    def log_trade_exit(
        self,
        symbol: str,
        quantity: int,
        exit_price: float,
        pnl: float,
        exit_reason: str,
    ):
        """
        Log a trade exit with P&L.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            exit_price: Exit price
            pnl: Net profit/loss
            exit_reason: Reason for exit (stop_loss, eod_close, etc.)
        """
        pnl_symbol = "+" if pnl >= 0 else ""
        logger.bind(component="trade").info(
            f"EXIT  | {symbol} | Qty: {quantity} | "
            f"Exit: ${exit_price:.3f} | P&L: {pnl_symbol}${pnl:.2f} | "
            f"Reason: {exit_reason}"
        )

    def log_system_event(self, component: str, message: str, level: str = "INFO"):
        """
        Log a system event.

        Args:
            component: Component name (e.g., 'ib_client', 'gap_detector')
            message: Event message
            level: Log level
        """
        log_func = getattr(logger.bind(component=component), level.lower())
        log_func(message)

    def log_error(self, component: str, message: str, exception: Optional[Exception] = None):
        """
        Log an error with optional exception details.

        Args:
            component: Component name
            message: Error message
            exception: Exception object (if applicable)
        """
        if exception:
            logger.bind(component=component).exception(f"{message}: {exception}")
        else:
            logger.bind(component=component).error(message)

    def log_kill_switch_triggered(self, daily_loss: float, threshold_percent: float):
        """
        Log kill switch activation.

        Args:
            daily_loss: Current daily loss
            threshold_percent: Loss threshold that triggered kill switch
        """
        logger.bind(component="kill_switch").critical(
            f"KILL SWITCH TRIGGERED! Daily loss: ${daily_loss:.2f} "
            f"exceeds {threshold_percent}% threshold"
        )


# Global logger instance
_trading_logger: Optional[TradingLogger] = None


def setup_logger(
    log_dir: str = "data/logs",
    log_level: str = "INFO",
    rotation: str = "100 MB",
    retention: str = "30 days",
    enable_console: bool = True,
    enable_file: bool = True,
) -> TradingLogger:
    """
    Set up the global trading logger.

    Args:
        log_dir: Directory to store log files
        log_level: Minimum log level
        rotation: When to rotate log files
        retention: How long to keep old logs
        enable_console: Whether to log to console
        enable_file: Whether to log to files

    Returns:
        Configured TradingLogger instance
    """
    global _trading_logger
    _trading_logger = TradingLogger(
        log_dir=log_dir,
        log_level=log_level,
        rotation=rotation,
        retention=retention,
        enable_console=enable_console,
        enable_file=enable_file,
    )
    return _trading_logger


def get_logger() -> logger:
    """
    Get the global logger instance.

    Returns:
        loguru.logger instance
    """
    if _trading_logger is None:
        setup_logger()
    return logger


# Convenience function for quick logging
def log_info(message: str, component: str = "system"):
    """Quick info log."""
    get_logger().bind(component=component).info(message)


def log_warning(message: str, component: str = "system"):
    """Quick warning log."""
    get_logger().bind(component=component).warning(message)


def log_error(message: str, component: str = "system", exception: Optional[Exception] = None):
    """Quick error log."""
    if exception:
        get_logger().bind(component=component).exception(f"{message}: {exception}")
    else:
        get_logger().bind(component=component).error(message)


def log_debug(message: str, component: str = "system"):
    """Quick debug log."""
    get_logger().bind(component=component).debug(message)
