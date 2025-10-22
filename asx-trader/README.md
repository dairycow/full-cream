# ASX Catalyst Trading System

An automated paper trading system for ASX stocks that detects price-sensitive announcements, identifies gap-ups at market open, and executes opening range breakout trades via Interactive Brokers.

## Status

🚧 **Under Development** - Phase 1: Foundation Setup Complete

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Interactive Brokers Paper Trading Account
- Digital Ocean droplet (or similar VPS) in Sydney/Singapore region

### Installation

1. **Clone the repository**
   ```bash
   cd asx-trader
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env and fill in your IB account details
   ```

5. **Initialize database**
   ```bash
   python scripts/init_database.py
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

### 🚧 In Progress
- [ ] Interactive Brokers client
- [ ] Gap detection
- [ ] Opening range tracking
- [ ] Entry/exit logic

### 📋 Upcoming
- [ ] Risk management
- [ ] Trade execution engine
- [ ] Deployment scripts
- [ ] Testing and validation

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

**Current Phase**: Foundation Setup (Week 1)
**Next Milestone**: Interactive Brokers Integration (Week 1-2)
