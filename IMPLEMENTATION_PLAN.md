# ASX Catalyst Trading System - Implementation Plan

This document breaks down the Phase 1 PRD into actionable steps for implementation.

---

## Overview

We're building an automated paper trading system that:
1. Detects ASX stocks with price-sensitive announcements
2. Identifies gap-ups at market open
3. Executes opening range breakout trades via Interactive Brokers
4. Manages positions with automated stops and exits

**Target:** 4-6 weeks to complete paper trading MVP

---

## Pre-Implementation: User Setup Tasks

These tasks require **YOUR** action before we can proceed with development:

### Week 0: Account & Infrastructure Setup

#### 1. Interactive Brokers Account (Required First)
- [x] Go to https://www.interactivebrokers.com
- [x] Create a **Paper Trading Account** (free, no deposit required)
- [x] Complete application and wait for approval (~10 minutes)
- [x] Set up 2FA authentication
- [x] **Save your account details:**
  - Paper Trading Account ID (format: DU123456)
  - Username
  - Password

#### 2. Enable IB API Access
- [ ] Log into IB Account Management: https://gdcdyn.interactivebrokers.com/sso/Login
- [ ] Navigate to: Settings → API → Settings
- [ ] Enable these settings:
  - ☑ Enable ActiveX and Socket Clients
  - ☑ Create API message log file
  - ☑ Include market data in API log file
  - ☐ **UNCHECK** "Read-Only API" (we need write access)
- [ ] Set "Master API client ID" to: **1**
- [ ] Click OK and Continue

#### 3. Enable ASX Market Data
- [ ] In Account Management: Market Data → Subscriptions
- [ ] Click "Australian Securities Exchange"
- [ ] Select:
  - ☑ ASX Real-Time + Delayed (free for paper trading)
  - ☑ ASX Depth
- [ ] Accept agreements and submit

#### 4. Digital Ocean Droplet Setup
- [ ] Create Digital Ocean account (if needed)
- [ ] Create a new Droplet:
  - **OS:** Ubuntu 24.04 LTS
  - **Plan:** Basic ($12/month, 2GB RAM, 2 vCPU)
  - **Region:** Singapore or Sydney (closest to ASX)
  - **SSH:** Add your SSH key
- [ ] Save droplet IP address
- [ ] Test SSH connection: `ssh root@your-droplet-ip`

#### 5. Provide Credentials to Developer
Create a `.env` file locally with these values (DO NOT commit to public repo):

```bash
# Interactive Brokers
IB_HOST=127.0.0.1
IB_PORT=4002
IB_CLIENT_ID=1
IB_ACCOUNT=DU123456  # Replace with your actual account ID

# Trading Parameters
PAPER_TRADING=true
MAX_POSITION_SIZE_PERCENT=10
MAX_DAILY_LOSS_PERCENT=5
MIN_GAP_PERCENT=3.0
```

**Note:** You'll need to manually install IB Gateway on your droplet later (requires GUI login first time).

---

## Development Implementation: Developer Tasks

### Phase 1: Project Foundation (Week 1)

#### Step 1.1: Repository Structure Setup
- [x] Create MIT License
- [ ] Create project directory structure:
  ```
  /asx-trader/
  ├── config/          # Configuration files
  ├── data/            # SQLite database, logs
  ├── scripts/         # Utility and deployment scripts
  ├── src/
  │   ├── brokers/     # IB client implementation
  │   ├── scrapers/    # Announcements integration
  │   ├── signals/     # Gap detection, opening range
  │   ├── strategy/    # Entry/exit logic
  │   ├── execution/   # Order management
  │   ├── risk/        # Position sizing, kill switch
  │   └── utils/       # Database, logging
  └── tests/           # Unit tests
  ```

#### Step 1.2: Dependencies & Environment
- [ ] Create `requirements.txt` with core dependencies:
  - `ib_insync` - IB API wrapper
  - `pandas`, `numpy` - Data processing
  - `sqlalchemy` - Database ORM
  - `loguru` - Logging
  - `python-dotenv` - Environment variables
  - `pyyaml` - Config files
  - `schedule` - Task scheduling
- [ ] Create `.gitignore` (exclude `.env`, `data/`, `logs/`, `*.db`)
- [ ] Create `config/settings.yaml` with trading parameters
- [ ] Set up virtual environment instructions in README

#### Step 1.3: Database Schema
- [ ] Create `scripts/init_database.py`
- [ ] Implement tables:
  - `trades` - Trade records with entry/exit/P&L
  - `announcements` - ASX announcements with catalyst scores
  - `daily_performance` - Daily metrics
  - `system_logs` - Error tracking
- [ ] Create database utility class (`src/utils/database.py`)

#### Step 1.4: Logging System
- [ ] Create `src/utils/logger.py` with loguru setup
- [ ] Configure console and file logging
- [ ] Set up log rotation (100MB, 30 days retention)

---

### Phase 2: Interactive Brokers Integration (Week 1-2)

#### Step 2.1: IB Client Core
- [ ] Implement `src/brokers/ib_client.py`:
  - Connection management
  - Contract creation for ASX stocks
  - Market data requests
  - Historical data fetching
- [ ] Add error handling and reconnection logic

#### Step 2.2: Order Execution
- [ ] Implement order methods in IB client:
  - `place_market_order()` - Entry orders
  - `place_stop_order()` - Stop losses
  - `cancel_order()` - Order cancellation
- [ ] Add order status tracking

#### Step 2.3: Account Management
- [ ] Implement account info methods:
  - `get_account_value()` - Net liquidation
  - `get_buying_power()` - Available cash
  - `get_positions()` - Current holdings
  - `get_open_orders()` - Pending orders

#### Step 2.4: Testing
- [ ] Create `scripts/test_ib_connection.py`
- [ ] Test connection to paper trading account
- [ ] Test market data retrieval (BHP, CBA)
- [ ] Test historical data fetching
- [ ] Verify account info retrieval

---

### Phase 3: Core Trading Logic (Week 2-3)

#### Step 3.1: Announcements Integration
- [ ] Move existing `asx-announcements` skill into `src/scrapers/`
- [ ] Create `src/scrapers/catalyst_scorer.py`:
  - Keyword-based scoring (acquisition, takeover, etc.)
  - Score announcements 1-10
  - Filter out negative catalysts
- [ ] Create morning watchlist generation script

#### Step 3.2: Gap Detection
- [ ] Implement `src/signals/gap_detector.py`:
  - Compare open price to previous close
  - Calculate gap percentage
  - Filter by min/max gap thresholds (3-15%)
  - Verify volume requirements
- [ ] Unit tests for gap calculations

#### Step 3.3: Opening Range Tracker
- [ ] Implement `src/signals/opening_range.py`:
  - Track first 15 minutes (10:00-10:15 AM AEST)
  - Calculate OR high and OR low
  - Detect breakouts above OR high
  - Volume confirmation on breakout
- [ ] Unit tests for OR logic

#### Step 3.4: Entry Logic
- [ ] Implement `src/strategy/entry_logic.py`:
  - Combine announcements + gap + OR breakout
  - Entry conditions validation
  - Entry price determination
  - Stop price calculation (OR low or LOD)

#### Step 3.5: Exit Logic
- [ ] Implement `src/strategy/exit_logic.py`:
  - Stop loss monitoring
  - EOD close (3:50 PM AEST)
  - Optional: Trailing stop (2R profit)
  - Exit reason tracking

---

### Phase 4: Risk & Position Management (Week 3)

#### Step 4.1: Position Sizer
- [ ] Implement `src/risk/position_sizer.py`:
  - Risk-based position sizing (2% risk per trade)
  - Max position size constraint (10% of capital)
  - Calculate shares based on entry/stop prices
- [ ] Unit tests for position calculations

#### Step 4.2: Kill Switch
- [ ] Implement `src/risk/kill_switch.py`:
  - Track daily P&L
  - Trigger at -5% daily loss
  - Halt all new trades
  - Close existing positions
- [ ] Emergency stop testing

#### Step 4.3: Risk Manager
- [ ] Implement `src/risk/risk_manager.py`:
  - Max concurrent positions (3)
  - Pre-trade risk checks
  - Portfolio-level constraints
  - Trading hours validation

---

### Phase 5: Execution Engine (Week 3-4)

#### Step 5.1: Order Manager
- [ ] Implement `src/execution/order_manager.py`:
  - Queue management for orders
  - Order retry logic
  - Fill verification
  - Error handling for rejected orders

#### Step 5.2: Position Tracker
- [ ] Implement `src/execution/position_tracker.py`:
  - Track open positions
  - Monitor stop prices
  - Update positions from IB
  - Calculate unrealized P&L

#### Step 5.3: Trade Logger
- [ ] Implement trade recording to database:
  - Entry details (time, price, quantity)
  - Exit details (time, price, reason)
  - Calculate P&L and R-multiples
  - Store catalyst text and gap %

---

### Phase 6: Main Trading Loop (Week 4)

#### Step 6.1: Live Trader Script
- [ ] Create `scripts/live_trader.py`:
  - **7:00 AM:** Scrape announcements, generate watchlist
  - **10:00 AM:** Detect gaps at market open
  - **10:00-10:15 AM:** Track opening range
  - **10:15 AM-3:45 PM:** Monitor for OR breakouts, execute entries
  - **Continuous:** Monitor stops on open positions
  - **3:50 PM:** Close all positions (EOD)
  - **4:00 PM:** Shutdown and cleanup

#### Step 6.2: State Management
- [ ] Implement state machine for trading day:
  - PRE_MARKET → MARKET_OPEN → OPENING_RANGE → BREAKOUT_MONITORING → EOD_CLOSE → SHUTDOWN
- [ ] Persist state to database for recovery

#### Step 6.3: Error Handling
- [ ] Implement comprehensive error handling:
  - IB connection failures → retry with backoff
  - Market data delays → skip that bar
  - Order rejections → log and alert
  - Database errors → fallback to file logging
- [ ] Graceful shutdown on critical errors

---

### Phase 7: Monitoring & Reporting (Week 4-5)

#### Step 7.1: Health Check Script
- [ ] Create `scripts/daily_health_check.py`:
  - Verify IB connection
  - Check account balance
  - List open positions
  - Count errors in logs
  - Database integrity check

#### Step 7.2: Daily Report Generator
- [ ] Create `scripts/generate_daily_report.py`:
  - Summary statistics (wins, losses, P&L)
  - Trade details table
  - Best/worst trades
  - Win rate and R-multiples
  - Save to `daily_performance` table

#### Step 7.3: Performance Analytics
- [ ] Create `scripts/analyze_performance.py`:
  - Weekly/monthly aggregations
  - Equity curve plotting
  - Drawdown analysis
  - Catalyst scoring effectiveness

---

### Phase 8: Deployment Setup (Week 5)

#### Step 8.1: Server Setup Scripts
- [ ] Create `scripts/setup_server.sh`:
  - System updates
  - Install dependencies (Python, Java, xvfb, supervisor)
  - Create trader user
  - Directory structure

#### Step 8.2: IB Gateway Installation
- [ ] Create `scripts/setup_ib_gateway.sh`:
  - Download IB Gateway installer
  - Headless installation
  - Configuration file setup
- [ ] Create `scripts/start_ib_gateway.sh`:
  - Start virtual display (Xvfb)
  - Launch IB Gateway
  - Auto-login configuration

#### Step 8.3: Supervisor Configuration
- [ ] Create supervisor configs:
  - `ibgateway.conf` - Auto-start IB Gateway
  - `trader.conf` - Auto-start trader script
- [ ] Set up log file rotation

#### Step 8.4: Cron Jobs
- [ ] Create cron schedule:
  - 6:55 AM - Start trader
  - 4:05 PM - Stop trader
  - 4:15 PM - Generate daily report
  - 4:30 PM - Health check
  - Sunday 2 AM - Database backup

#### Step 8.5: Deployment Script
- [ ] Create `scripts/deploy.sh`:
  - Pull latest code
  - Update dependencies
  - Run migrations
  - Restart services
  - Run health check

---

### Phase 9: Documentation (Week 5-6)

#### Step 9.1: User Documentation
- [ ] Create main `README.md`:
  - System overview
  - Quick start guide
  - Configuration options
  - Deployment instructions
- [ ] Create `SETUP.md`:
  - Step-by-step IB account setup
  - Droplet provisioning
  - First-time deployment

#### Step 9.2: Developer Documentation
- [ ] Create `ARCHITECTURE.md`:
  - System design diagram
  - Component descriptions
  - Data flow
  - Code organization
- [ ] Create `TROUBLESHOOTING.md`:
  - Common issues and solutions
  - Log analysis guide
  - Recovery procedures

#### Step 9.3: API Documentation
- [ ] Document key classes and methods:
  - IB client API
  - Database schema
  - Configuration options
  - Extension points

---

### Phase 10: Testing & Validation (Week 6)

#### Step 10.1: Unit Tests
- [ ] Write tests for:
  - Gap detector
  - Opening range tracker
  - Position sizer
  - Catalyst scorer
  - Kill switch
- [ ] Achieve >80% code coverage

#### Step 10.2: Integration Tests
- [ ] Test full trade lifecycle with mock IB
- [ ] Test database operations
- [ ] Test error recovery
- [ ] Test state persistence

#### Step 10.3: Paper Trading Validation
- [ ] Run system for 2-4 weeks on droplet
- [ ] Monitor daily:
  - System uptime
  - Trade execution correctness
  - Stop loss accuracy
  - EOD close timing
- [ ] Review logs for errors
- [ ] Validate P&L calculations

---

## Success Criteria (Before Going Live)

### System Reliability
- [ ] 95%+ uptime during market hours over 2 weeks
- [ ] Zero missed gap opportunities from watchlist
- [ ] All trades logged correctly in database
- [ ] No duplicate entries or exits
- [ ] Clean error recovery (no manual intervention needed)

### Trading Performance
- [ ] Win rate >40%
- [ ] Average R:R ratio >1.5:1
- [ ] Max drawdown <15%
- [ ] Catalyst scoring producing 5-10 signals per week

### Code Quality
- [ ] All unit tests passing
- [ ] No critical bugs in 2 weeks
- [ ] Clean, documented, maintainable code
- [ ] Security review (no credentials in code)

---

## Next Steps to Get Started

### For the User (You):
1. **Complete Week 0 tasks** - Set up IB paper trading account and droplet
2. **Provide credentials** - Share account details securely (DM or encrypted file)
3. **Test SSH access** - Verify you can connect to droplet
4. **Review configuration** - Approve `config/settings.yaml` parameters

### For the Developer (Me):
1. **Set up project structure** - Create directories, files, dependencies
2. **Implement IB client** - Build connection and order execution
3. **Integrate announcements** - Move existing scraper into new structure
4. **Build trading logic** - Gap detection, OR tracking, entries/exits
5. **Create deployment package** - Scripts for easy droplet deployment

---

## Timeline Summary

| Week | User Tasks | Developer Tasks |
|------|-----------|----------------|
| 0 | IB account setup, Droplet creation | - |
| 1 | Provide credentials | Project structure, IB client, database |
| 2 | Review watchlists | Core signals (gap, OR), announcements |
| 3 | Test IB connection | Risk management, position sizing |
| 4 | Review config | Trade execution engine, main loop |
| 5 | Deploy to droplet | Monitoring, reporting, deployment scripts |
| 6 | Paper trading validation | Bug fixes, performance tuning |

---

## Communication Checkpoints

We'll sync at these milestones:
1. ✅ **Checkpoint 1:** After IB account setup complete
2. **Checkpoint 2:** After IB client tested successfully
3. **Checkpoint 3:** After first end-to-end test on droplet
4. **Checkpoint 4:** After 1 week of paper trading
5. **Checkpoint 5:** After 4 weeks - decision to go live or continue testing

---

## Questions to Answer Before Starting

1. **Do you have the IB paper trading account set up?** (If not, start with Week 0 tasks)
2. **Do you have a Digital Ocean droplet ready?** (Or preferred cloud provider?)
3. **What are your preferred trading hours?** (Will you monitor manually or fully automated?)
4. **Risk tolerance:** Are you comfortable with the default 2% risk per trade?
5. **Position limits:** Max 3 concurrent positions OK, or prefer different limit?

Let me know when you've completed the Week 0 setup tasks and we can begin implementation!
