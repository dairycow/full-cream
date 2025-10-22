#!/usr/bin/env python3
"""
Initialize the ASX Trading System database.

This script creates all necessary tables in the database.
Run this once before starting the trading system.

Usage:
    python scripts/init_database.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.database import DatabaseManager


def main():
    """Initialize the database."""
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Create logs directory
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Database path
    db_path = data_dir / "asx_trader.db"
    database_url = f"sqlite:///{db_path}"

    print(f"Initializing database at: {db_path}")

    # Initialize database manager
    db_manager = DatabaseManager(database_url)

    # Check if database exists
    if db_path.exists():
        response = input(
            "Database already exists. Do you want to reset it? This will DELETE all data! (yes/no): "
        )
        if response.lower() == "yes":
            print("Resetting database...")
            db_manager.reset_database()
            print("✓ Database reset successfully!")
        else:
            print("Creating missing tables only...")
            db_manager.create_tables()
            print("✓ Database tables created/verified!")
    else:
        print("Creating new database...")
        db_manager.create_tables()
        print("✓ Database created successfully!")

    # Verify tables were created
    from sqlalchemy import inspect

    inspector = inspect(db_manager.engine)
    tables = inspector.get_table_names()

    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table}")

    print("\n✓ Database initialization complete!")
    print(f"\nDatabase location: {db_path}")
    print("\nYou can now:")
    print("  1. Copy .env.template to .env and fill in your IB credentials")
    print("  2. Run the trading system: python scripts/live_trader.py")


if __name__ == "__main__":
    main()
