"""
Database models and utilities for ASX Trading System.

This module defines the SQLAlchemy ORM models for:
- Trades
- Announcements
- Daily Performance
- System Logs
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Trade(Base):
    """Trade records with entry/exit details and P&L."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Symbol and Identification
    symbol = Column(String(20), nullable=False, index=True)
    ib_order_id = Column(Integer, nullable=True)
    ib_trade_id = Column(Integer, nullable=True)

    # Entry Details
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_value = Column(Float, nullable=False)

    # Exit Details
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_value = Column(Float, nullable=True)
    exit_reason = Column(
        String(50), nullable=True
    )  # stop_loss, eod_close, profit_target

    # P&L Metrics
    gross_pnl = Column(Float, nullable=True)
    commission = Column(Float, nullable=True, default=6.0)
    net_pnl = Column(Float, nullable=True)
    r_multiple = Column(Float, nullable=True)  # P&L / initial risk
    percent_return = Column(Float, nullable=True)

    # Strategy Details
    gap_percent = Column(Float, nullable=True)
    or_high = Column(Float, nullable=True)  # Opening range high
    or_low = Column(Float, nullable=True)  # Opening range low
    stop_price = Column(Float, nullable=True)
    catalyst_score = Column(Integer, nullable=True)
    catalyst_text = Column(Text, nullable=True)

    # Risk Metrics
    initial_risk_dollars = Column(Float, nullable=True)
    account_balance_at_entry = Column(Float, nullable=True)

    # Status
    is_open = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Trade {self.symbol} @ {self.entry_time} P&L: {self.net_pnl}>"


class Announcement(Base):
    """ASX announcements with catalyst scoring."""

    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Announcement Details
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(200), nullable=True)
    headline = Column(Text, nullable=False)
    url = Column(String(500), nullable=True)
    published_time = Column(DateTime, nullable=False, index=True)

    # Catalyst Scoring
    catalyst_score = Column(Integer, nullable=True)  # 1-10
    is_price_sensitive = Column(Boolean, default=False, index=True)
    is_positive = Column(Boolean, nullable=True)

    # Processing Status
    is_processed = Column(Boolean, default=False, index=True)
    added_to_watchlist = Column(Boolean, default=False)
    trade_executed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Announcement {self.symbol} Score: {self.catalyst_score}>"


class DailyPerformance(Base):
    """Daily trading performance metrics."""

    __tablename__ = "daily_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    trade_date = Column(DateTime, nullable=False, unique=True, index=True)

    # Trade Statistics
    num_trades = Column(Integer, default=0)
    num_winners = Column(Integer, default=0)
    num_losers = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)

    # P&L Metrics
    gross_pnl = Column(Float, default=0.0)
    total_commission = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)

    # Account Metrics
    starting_balance = Column(Float, nullable=True)
    ending_balance = Column(Float, nullable=True)
    daily_return_percent = Column(Float, nullable=True)

    # Risk Metrics
    total_risk_dollars = Column(Float, nullable=True)
    max_drawdown_intraday = Column(Float, nullable=True)
    avg_r_multiple = Column(Float, nullable=True)

    # Watchlist Stats
    num_announcements = Column(Integer, default=0)
    num_watchlist_symbols = Column(Integer, default=0)
    num_gaps_detected = Column(Integer, default=0)
    num_breakouts_detected = Column(Integer, default=0)

    # Kill Switch
    kill_switch_triggered = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DailyPerformance {self.trade_date} Net P&L: {self.net_pnl}>"


class SystemLog(Base):
    """System error and event logging."""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Log Details
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(50), nullable=True, index=True)  # ib_client, gap_detector, etc.
    message = Column(Text, nullable=False)

    # Error Details
    exception_type = Column(String(100), nullable=True)
    exception_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Context
    trade_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=True, index=True)
    order_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<SystemLog {self.level} @ {self.timestamp}: {self.message[:50]}>"


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str = "sqlite:///data/asx_trader.db"):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def reset_database(self):
        """Drop and recreate all tables (use with caution!)."""
        self.drop_tables()
        self.create_tables()


# Helper function for quick session access
def get_db_session(database_url: str = "sqlite:///data/asx_trader.db") -> Session:
    """
    Get a database session quickly.

    Args:
        database_url: SQLAlchemy database URL

    Returns:
        Database session
    """
    db = DatabaseManager(database_url)
    return db.get_session()
