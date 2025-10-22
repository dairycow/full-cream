"""
Configuration loader for ASX Trading System.

This module loads configuration from:
- .env file (environment variables)
- config/settings.yaml (trading parameters)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for the trading system."""

    def __init__(self, env_file: Optional[str] = None, settings_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            env_file: Path to .env file (default: .env in project root)
            settings_file: Path to settings.yaml (default: config/settings.yaml)
        """
        # Determine project root (parent of src directory)
        self.project_root = Path(__file__).parent.parent.parent

        # Load environment variables
        if env_file is None:
            env_file = self.project_root / ".env"
        load_dotenv(env_file)

        # Load settings from YAML
        if settings_file is None:
            settings_file = self.project_root / "config" / "settings.yaml"

        with open(settings_file, "r") as f:
            self.settings: Dict[str, Any] = yaml.safe_load(f)

    def get_env(self, key: str, default: Any = None) -> str:
        """
        Get environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Boolean value
        """
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_env_int(self, key: str, default: int = 0) -> int:
        """
        Get integer environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Integer value
        """
        try:
            return int(os.getenv(key, default))
        except ValueError:
            return default

    def get_env_float(self, key: str, default: float = 0.0) -> float:
        """
        Get float environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Float value
        """
        try:
            return float(os.getenv(key, default))
        except ValueError:
            return default

    def get_setting(self, *keys: str, default: Any = None) -> Any:
        """
        Get setting from YAML config using dot notation.

        Args:
            *keys: Keys to navigate (e.g., 'risk', 'max_daily_loss_percent')
            default: Default value if not found

        Returns:
            Setting value or default

        Example:
            config.get_setting('risk', 'max_daily_loss_percent')
            config.get_setting('entry', 'min_gap_percent')
        """
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    # === BROKER CONFIGURATION ===

    @property
    def ib_host(self) -> str:
        """IB Gateway host."""
        return self.get_env("IB_HOST", "127.0.0.1")

    @property
    def ib_port(self) -> int:
        """IB Gateway port."""
        return self.get_env_int("IB_PORT", 4002)

    @property
    def ib_client_id(self) -> int:
        """IB client ID."""
        return self.get_env_int("IB_CLIENT_ID", 1)

    @property
    def ib_account(self) -> str:
        """IB account ID."""
        account = self.get_env("IB_ACCOUNT", "")
        if not account or account == "YOUR_ACCOUNT_ID_HERE":
            raise ValueError(
                "IB_ACCOUNT not configured! Please set your IB account ID in .env file"
            )
        return account

    @property
    def connection_timeout(self) -> int:
        """Connection timeout in seconds."""
        return self.get_setting("broker", "connection_timeout", default=30)

    @property
    def retry_attempts(self) -> int:
        """Number of connection retry attempts."""
        return self.get_setting("broker", "retry_attempts", default=3)

    @property
    def retry_delay(self) -> int:
        """Delay between retry attempts in seconds."""
        return self.get_setting("broker", "retry_delay", default=5)

    # === RISK MANAGEMENT ===

    @property
    def risk_per_trade_percent(self) -> float:
        """Risk per trade as percentage of capital."""
        return self.get_setting("risk", "risk_per_trade_percent", default=2.0)

    @property
    def max_position_size_percent(self) -> float:
        """Maximum position size as percentage of capital."""
        return self.get_setting("risk", "max_position_size_percent", default=10.0)

    @property
    def max_concurrent_positions(self) -> int:
        """Maximum number of concurrent positions."""
        return self.get_setting("risk", "max_concurrent_positions", default=3)

    @property
    def max_daily_loss_percent(self) -> float:
        """Maximum daily loss percentage (kill switch threshold)."""
        return self.get_setting("risk", "max_daily_loss_percent", default=5.0)

    @property
    def min_account_balance(self) -> float:
        """Minimum account balance required to trade."""
        return self.get_setting("risk", "min_account_balance", default=10000.0)

    # === ENTRY CRITERIA ===

    @property
    def min_gap_percent(self) -> float:
        """Minimum gap percentage for entry."""
        return self.get_setting("entry", "min_gap_percent", default=3.0)

    @property
    def max_gap_percent(self) -> float:
        """Maximum gap percentage for entry."""
        return self.get_setting("entry", "max_gap_percent", default=15.0)

    @property
    def min_stock_price(self) -> float:
        """Minimum stock price."""
        return self.get_setting("entry", "min_stock_price", default=0.50)

    @property
    def max_stock_price(self) -> float:
        """Maximum stock price."""
        return self.get_setting("entry", "max_stock_price", default=50.00)

    # === EXIT CRITERIA ===

    @property
    def eod_close_time(self) -> str:
        """End-of-day close time."""
        return self.get_setting("exit", "eod_close_time", default="15:50")

    @property
    def use_hard_stop(self) -> bool:
        """Whether to use hard stop orders."""
        return self.get_setting("exit", "use_hard_stop", default=True)

    # === DATABASE ===

    @property
    def database_path(self) -> str:
        """Database file path."""
        db_path = self.get_env("DATABASE_PATH", self.get_setting("database", "path", default="data/asx_trader.db"))
        # Make path absolute relative to project root
        if not os.path.isabs(db_path):
            db_path = str(self.project_root / db_path)
        return db_path

    @property
    def database_url(self) -> str:
        """SQLAlchemy database URL."""
        return f"sqlite:///{self.database_path}"

    # === LOGGING ===

    @property
    def log_level(self) -> str:
        """Logging level."""
        return self.get_env("LOG_LEVEL", self.get_setting("logging", "level", default="INFO"))

    @property
    def log_path(self) -> str:
        """Log directory path."""
        log_path = self.get_env("LOG_PATH", "data/logs")
        # Make path absolute relative to project root
        if not os.path.isabs(log_path):
            log_path = str(self.project_root / log_path)
        return log_path

    @property
    def log_rotation(self) -> str:
        """Log rotation setting."""
        return self.get_env("LOG_ROTATION", self.get_setting("logging", "rotation", default="100 MB"))

    @property
    def log_retention(self) -> str:
        """Log retention setting."""
        return self.get_env("LOG_RETENTION", self.get_setting("logging", "retention", default="30 days"))

    # === PAPER TRADING ===

    @property
    def paper_trading(self) -> bool:
        """Whether paper trading is enabled."""
        return self.get_env_bool("PAPER_TRADING", self.get_setting("paper_trading", "enabled", default=True))

    def __repr__(self) -> str:
        """String representation."""
        return f"<Config IB:{self.ib_host}:{self.ib_port} Account:{self.ib_account}>"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from files.

    Returns:
        Fresh Config instance
    """
    global _config
    _config = Config()
    return _config
