# ASX Catalyst Trading System

An automated paper trading system for ASX stocks that detects price-sensitive announcements, identifies gap-ups at market open, and executes opening range breakout trades via Interactive Brokers.

## Status

🚧 **Under Development** - Phase 3: Core Trading Logic Complete

## Quick Start

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Interactive Brokers Paper Trading Account
- Digital Ocean droplet (or similar VPS) in Sydney/Singapore region

### Installation

1. **Clone the repository**
   ```bash
   cd asx-trader
   ```

2. **Create virtual environment with uv**
   ```bash
   uv venv --python 3.13
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env and fill in your IB account details
   ```

5. **Initialize database**
   ```bash
   uv run python scripts/init_database.py
   ```

6. **Test IB connection** (requires IB Gateway running)
   ```bash
   uv run python scripts/test_ib_connection.py
   ```

## Configuration

### Environment Variables (.env)

Copy `.env.template` to `.env` and fill in:

- `IB_ACCOUNT`: Your IB paper trading account ID (e.g., DU123456)
- `IB_HOST`: IB Gateway host (default: 127.0.0.1)
- `IB_PORT`: IB Gateway port (default: 4002 for paper trading)
- Other trading parameters as needed

### Trading Parameters (config/settings.yaml)

Adjust trading parameters in `config/settings.yaml`:

- **Risk Management**: Position sizing, stop losses, kill switch thresholds
- **Entry Criteria**: Gap percentages, volume requirements, breakout confirmation
- **Exit Criteria**: Stop loss types, end-of-day close timing
- **Catalyst Scoring**: Keywords for scoring announcements

## Project Structure

```
asx-trader/
├── config/              # Configuration files
│   └── settings.yaml    # Trading parameters
├── data/                # SQLite database and logs (gitignored)
│   ├── asx_trader.db
│   └── logs/
├── scripts/             # Utility and deployment scripts
│   └── init_database.py
├── src/                 # Source code
│   ├── brokers/         # IB client implementation
│   ├── scrapers/        # Announcements integration
│   ├── signals/         # Gap detection, opening range
│   ├── strategy/        # Entry/exit logic
│   ├── execution/       # Order management
│   ├── risk/            # Position sizing, kill switch
│   └── utils/           # Database, logging
└── tests/               # Unit tests
```

## Development Status

### ✅ Completed
- [x] Project structure
- [x] Dependencies configuration
- [x] Database schema (SQLAlchemy models)
- [x] Logging setup (loguru)
- [x] Configuration templates
- [x] Configuration loader (YAML + .env)
- [x] Interactive Brokers client
  - [x] Connection management with auto-reconnect
  - [x] Contract creation for ASX stocks
  - [x] Market data requests (real-time & historical)
  - [x] Order execution (market & stop orders)
  - [x] Account management (positions, balances)
  - [x] Connection test script
- [x] Core Trading Signals
  - [x] Gap detector (3-15% gap-up detection)
  - [x] Opening range tracker (first 15 minutes)
  - [x] Catalyst scorer (announcement keyword scoring)
  - [x] Breakout detection (OR high breakout)
- [x] Risk Management
  - [x] Position sizer (2% risk per trade)
  - [x] Risk-based position sizing
  - [x] Maximum position constraints
- [x] Strategy Logic
  - [x] Entry logic (catalyst + gap + OR breakout)
  - [x] Exit logic (stop loss, EOD close, trailing stop)
  - [x] Complete signal validation

### 🚧 In Progress
- [ ] Trade execution engine
- [ ] Position tracking and monitoring
- [ ] Main trading loop

### 📋 Upcoming
- [ ] Kill switch implementation
- [ ] Deployment scripts
- [ ] Testing and validation
- [ ] Performance analytics

## Trading Strategy

### Overview
1. **Pre-market (7:00 AM)**: Scrape ASX price-sensitive announcements
2. **Market Open (10:00 AM)**: Detect gap-ups (3-15%)
3. **Opening Range (10:00-10:15 AM)**: Track first 15-minute range
4. **Breakout Monitoring (10:15 AM-3:45 PM)**: Watch for OR high breakouts
5. **Position Management**: Monitor stops continuously
6. **End of Day (3:50 PM)**: Close all positions

### Entry Criteria
- Price-sensitive announcement with high catalyst score (>5)
- Gap up 3-15% at market open
- Opening range breakout above OR high
- Volume confirmation (>1.5x average)

### Exit Criteria
- Stop loss at opening range low (or lower)
- End-of-day close at 3:50 PM AEST
- (Future) Trailing stop after 2R profit

### Risk Management
- Risk 2% of capital per trade
- Maximum 10% of capital per position
- Maximum 3 concurrent positions
- Kill switch at -5% daily loss

## Database Schema

### Tables

1. **trades**: Trade records with entry/exit details and P&L
2. **announcements**: ASX announcements with catalyst scores
3. **daily_performance**: Daily trading metrics
4. **system_logs**: Error tracking and system events

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_gap_detector.py
```

## Deployment

**Coming Soon** - Deployment scripts for Digital Ocean droplet

## Documentation

- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Detailed implementation roadmap
- [Phase 1 PRD](../phase1-prd.md) - Product requirements document

## License

MIT License - See [LICENSE](../LICENSE) file

## Disclaimer

This is a **paper trading system** for educational and testing purposes only. Always thoroughly test any trading system before considering real money trading. Past performance does not guarantee future results.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Current Phase**: Core Trading Logic (Week 3)
**Next Milestone**: Trade Execution Engine & Main Loop (Week 4)
