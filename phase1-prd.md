# Phase 1 PRD: ASX Catalyst Trading System - Paper Trading MVP

**Version:** 1.0  
**Author:** Harry's Trading System Development  
**Last Updated:** October 22, 2025  
**Target Completion:** 4-6 weeks

---

## Executive Summary

Build a fully automated paper trading system for ASX stocks that detects catalyst-driven price movements, identifies gap-ups at market open, and executes opening range breakout trades via Interactive Brokers API. This Phase 1 focuses on proving the core trading logic works in a risk-free paper trading environment before deploying real capital.

**Success Criteria:**
- Successfully execute 20+ paper trades over 2-4 weeks
- System runs autonomously during market hours without crashes
- All trades logged with entry/exit reasons and P&L

---

## System Overview

### Core Trading Strategy
**Entry:** Buy on break of 15-minute Opening Range (OR) high for stocks that:
1. Released price-sensitive announcements pre-market
2. Gapped up 3%+ at market open
3. Show volume confirmation on OR break

**Exit:** 
- Stop loss at low of day (or OR low)
- EOD exit: Close all positions at 3:50 PM if still open
- Optional: Trailing stop once position moves 2R in profit

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Live Trading System                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │  Pre-Market  │────────▶│  Market Open │              │
│  │   Scanner    │  7-10AM │  Gap Detect  │  10:00 AM    │
│  │              │         │              │              │
│  │ • Scrape ASX │         │ • Identify   │              │
│  │ • Score News │         │   Gap Ups    │              │
│  │ • Watchlist  │         │ • Filter by  │              │
│  └──────────────┘         │   Volume     │              │
│                           └──────────────┘              │
│                                  │                       │
│                                  ▼                       │
│                      ┌──────────────────┐               │
│                      │  Opening Range   │               │
│                      │    10:00-10:15   │               │
│                      │                  │               │
│                      │ • Track OR High  │               │
│                      │ • Track OR Low   │               │
│                      └──────────────────┘               │
│                                  │                       │
│                                  ▼                       │
│                      ┌──────────────────┐               │
│                      │  Breakout Monitor│               │
│                      │   10:15-15:45    │               │
│                      │                  │               │
│                      │ • Detect Breaks  │               │
│                      │ • Volume Check   │               │
│                      │ • Execute Entry  │               │
│                      └──────────────────┘               │
│                                  │                       │
│                                  ▼                       │
│                      ┌──────────────────┐               │
│                      │ Position Manager │               │
│                      │   Continuous     │               │
│                      │                  │               │
│                      │ • Monitor Stops  │               │
│                      │ • Trail Stops    │               │
│                      │ • EOD Close      │               │
│                      └──────────────────┘               │
│                                                           │
└─────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
   ┌──────────────┐                   ┌──────────────┐
   │   IB Gateway  │                   │   Database   │
   │  Paper Trade  │                   │   SQLite     │
   └──────────────┘                   └──────────────┘
```

---

## Phase 1 Scope

### In Scope
✅ Interactive Brokers paper trading account setup  
✅ IB Gateway headless configuration  
✅ ASX announcement scraper integration  
✅ Catalyst scoring algorithm (rule-based)  
✅ Gap detection at market open  
✅ Opening range calculation (15-min)  
✅ Automated entry execution via IB API  
✅ Stop loss placement (at OR low or LOD)  
✅ EOD position closure  
✅ Trade logging to SQLite database  
✅ Daily performance reporting  
✅ Deployment to Digital Ocean droplet  

### Out of Scope (Future Phases)
❌ Live trading with real money  
❌ Machine learning catalyst scoring  
❌ Advanced exit strategies (trailing stops, profit targets)  
❌ Multi-timeframe analysis  
❌ Portfolio-level risk management  
❌ Web dashboard/UI  
❌ Slack/Telegram notifications  

---

## Technical Requirements

### 1. Infrastructure

**Digital Ocean Droplet Specs:**
- **Size:** Basic ($12/month)
- **CPU:** 2 vCPUs
- **RAM:** 2 GB
- **Storage:** 60 GB SSD
- **OS:** Ubuntu 25.04 x64
- **Region:** Sydney

**Software Dependencies:**
```
Python 3.11+
IB Gateway (Standalone headless version)
PostgreSQL 14 or SQLite3
xvfb (virtual display for IB Gateway)
supervisor (process management)
```

### 2. Interactive Brokers Setup

**Account Requirements:**
- Paper trading account (free)
- No minimum deposit required
- Real-time ASX data subscription ($0 for paper trading)

**IB Gateway Configuration:**
- Port: 4002 (paper trading)
- Socket client enabled
- Auto-restart enabled
- Read-only API disabled (we need write access)
- Download orders enabled
- Master API client ID: 1

### 3. Python Environment

**Key Libraries:**
```python
ib_insync==0.9.86        # IB API wrapper
pandas==2.1.0             # Data manipulation
numpy==1.25.0             # Numerical computing
sqlalchemy==2.0.20        # Database ORM
requests==2.31.0          # HTTP requests
beautifulsoup4==4.12.2    # Web scraping (if needed)
python-dotenv==1.0.0      # Environment variables
schedule==1.2.0           # Task scheduling
loguru==0.7.0             # Enhanced logging
pyyaml==6.0               # Config files
```

### 4. Database Schema

```sql
-- trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    entry_time TIMESTAMP,
    entry_price REAL,
    quantity INTEGER,
    stop_price REAL,
    exit_time TIMESTAMP,
    exit_price REAL,
    exit_reason TEXT,  -- 'stop_hit', 'eod_close', 'manual'
    pnl REAL,
    pnl_percent REAL,
    r_multiple REAL,   -- How many R's (risk units)
    catalyst_text TEXT,
    gap_percent REAL,
    or_high REAL,
    or_low REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- announcements table
CREATE TABLE announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    announcement_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    header TEXT,
    pdf_url TEXT,
    page_count INTEGER,
    catalyst_score INTEGER,  -- 1-10 score
    selected_for_watchlist BOOLEAN,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- daily_performance table
CREATE TABLE daily_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL UNIQUE,
    trades_count INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl REAL,
    win_rate REAL,
    avg_winner REAL,
    avg_loser REAL,
    largest_winner REAL,
    largest_loser REAL,
    notes TEXT
);

-- system_logs table
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_level TEXT,  -- 'INFO', 'WARNING', 'ERROR'
    component TEXT,  -- 'scanner', 'ib_client', 'trader', etc.
    message TEXT,
    context TEXT     -- JSON string with additional context
);
```

### 5. Configuration Files

**config/settings.yaml**
```yaml
trading:
  market_open: "10:00"
  market_close: "16:00"
  opening_range_minutes: 15
  eod_close_time: "15:50"
  
  gap:
    min_gap_percent: 3.0
    max_gap_percent: 15.0  # Avoid extreme gaps (may be halted)
  
  volume:
    min_avg_volume: 100000  # Minimum 100k average volume
    breakout_volume_multiplier: 1.5  # Volume on break must be 1.5x average
  
  risk:
    max_position_size_percent: 10  # Max 10% of capital per trade
    max_daily_loss_percent: 5      # Kill switch at -5% daily
    max_concurrent_positions: 3
    use_or_low_for_stop: true      # If false, use low of day

catalyst_scoring:
  keywords_high:  # Score +3 each
    - "acquisition"
    - "takeover"
    - "upgraded"
    - "record"
    - "breakthrough"
    - "FDA approval"
    - "major contract"
  
  keywords_medium:  # Score +2 each
    - "growth"
    - "expansion"
    - "partnership"
    - "revenue increase"
    - "beat expectations"
  
  keywords_low:  # Score +1 each
    - "update"
    - "announcement"
    - "report"
  
  keywords_negative:  # Score -5 each (filter out)
    - "downgrade"
    - "loss"
    - "investigation"
    - "suspend"
    - "delay"

ib:
  host: "127.0.0.1"
  port: 4002  # Paper trading
  client_id: 1
  account: "DU123456"  # Your paper trading account ID
  timeout: 60

database:
  type: "sqlite"
  path: "data/trading.db"

logging:
  level: "INFO"
  file: "logs/trader.log"
  max_size_mb: 100
  backup_count: 5
```

---

## Setup Instructions

### Step 1: Interactive Brokers Account Setup

**1.1 Create Paper Trading Account**

1. Go to https://www.interactivebrokers.com
2. Click "Open an Account" → "Individual Account"
3. Select "Paper Trading" during application
4. Complete the application (no financial information required)
5. Wait for approval email (~10 minutes)
6. Set up 2FA authentication

**1.2 Enable API Access**

1. Log into Account Management: https://gdcdyn.interactivebrokers.com/sso/Login
2. Navigate to Settings → API → Settings
3. Enable the following:
   - ☑ Enable ActiveX and Socket Clients
   - ☑ Create API message log file
   - ☑ Include market data in API log file
   - ☐ Read-Only API (UNCHECK THIS - we need write access)
4. Set "Master API client ID": 1
5. Click "OK" and "Continue"

**1.3 Enable ASX Market Data**

1. In Account Management: Market Data → Subscriptions
2. Click "Australian Securities Exchange"
3. Select:
   - ☑ ASX Real-Time + Delayed - Free for paper trading
   - ☑ ASX Depth
4. Accept agreements
5. Submit (no charge for paper trading)

**1.4 Note Your Account Details**
You'll need:
- Paper Trading Account ID (format: DU123456)
- Username
- Password

---

### Step 2: Digital Ocean Droplet Setup

**2.1 Create Droplet**

```bash
# Via DO web console:
# 1. Create Droplet
# 2. Choose Ubuntu 24.04 LTS
# 3. Select Basic plan ($12/mo, 2GB RAM)
# 4. Choose Singapore region
# 5. Add SSH key
# 6. Create Droplet

# SSH into your droplet
ssh root@your-droplet-ip
```

**2.2 Initial Server Setup**

Create setup script: `scripts/setup_server.sh`

```bash
#!/bin/bash

# Update system
echo "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install essential packages
echo "Installing dependencies..."
apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    git \
    wget \
    unzip \
    xvfb \
    libxtst6 \
    libxrender1 \
    libxi6 \
    supervisor \
    sqlite3 \
    openjdk-17-jre-headless \
    x11vnc

# Create trading user
echo "Creating trading user..."
useradd -m -s /bin/bash trader
usermod -aG sudo trader

# Create directory structure
echo "Setting up directories..."
mkdir -p /home/trader/asx-trader
mkdir -p /home/trader/ib-gateway
mkdir -p /home/trader/.vnc
chown -R trader:trader /home/trader

echo "Server setup complete!"
echo "Next: Switch to trader user and continue setup"
echo "Command: su - trader"
```

Make executable and run:
```bash
chmod +x scripts/setup_server.sh
./scripts/setup_server.sh
su - trader
```

---

### Step 3: IB Gateway Installation

**3.1 Download and Install IB Gateway**

Create script: `scripts/setup_ib_gateway.sh`

```bash
#!/bin/bash

echo "Installing IB Gateway..."

cd /home/trader/ib-gateway

# Download IB Gateway (check for latest version at https://www.interactivebrokers.com/en/trading/ibgateway-stable.php)
wget https://download2.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh

# Make installer executable
chmod +x ibgateway-latest-standalone-linux-x64.sh

# Install IB Gateway (headless)
./ibgateway-latest-standalone-linux-x64.sh -q -dir /home/trader/ib-gateway/installed

echo "IB Gateway installed to /home/trader/ib-gateway/installed"
```

**3.2 Configure IB Gateway**

Create config file: `scripts/ib_gateway_config.ini`

```ini
[IBGateway]
TradingMode=paper
Region=am
MainWindow.Height=300
MainWindow.Width=400
MainWindow.x=0
MainWindow.y=0
ApiLogging=info
```

**3.3 Create IB Gateway Startup Script**

Create: `scripts/start_ib_gateway.sh`

```bash
#!/bin/bash

export DISPLAY=:1
Xvfb :1 -screen 0 1024x768x24 &
sleep 2

# Start IB Gateway
/home/trader/ib-gateway/installed/ibgateway \
    --tws-path=/home/trader/ib-gateway/installed \
    --tws-settings-path=/home/trader/ib-gateway/settings \
    --ibc-ini=/home/trader/asx-trader/config/ib_gateway_config.ini \
    --ibc-path=/home/trader/ib-gateway/ibc \
    --on-second-factor-authentication-manual=exit \
    --log-to-console &

echo "IB Gateway started"
```

**3.4 Configure Supervisor to Auto-Start IB Gateway**

Create: `/etc/supervisor/conf.d/ibgateway.conf`

```ini
[program:ibgateway]
command=/home/trader/asx-trader/scripts/start_ib_gateway.sh
user=trader
autostart=true
autorestart=true
stderr_logfile=/home/trader/logs/ibgateway.err.log
stdout_logfile=/home/trader/logs/ibgateway.out.log
environment=DISPLAY=":1"
```

Update supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ibgateway
```

**3.5 Initial IB Gateway Login**

Since IB Gateway requires 2FA on first login, you'll need to do this manually once:

```bash
# Start VNC server for first-time setup
x11vnc -display :1 -bg -nopw -listen localhost -xkb

# Create SSH tunnel from your local machine
ssh -L 5900:localhost:5900 trader@your-droplet-ip

# Connect with VNC viewer to localhost:5900
# Enter IB credentials and complete 2FA
# Check "Store credentials" option
# Once logged in, you can close VNC
```

After first login, IB Gateway will auto-login with stored credentials.

---

### Step 4: Trading System Setup

**4.1 Clone Repository Structure**

```bash
cd /home/trader
git init asx-trader
cd asx-trader

# Create directory structure
mkdir -p {config,data,logs,scripts,src,tests}
mkdir -p data/{announcements,watchlists,trades}
mkdir -p src/{brokers,scrapers,signals,strategy,execution,risk,utils}
```

**4.2 Create Python Virtual Environment**

```bash
cd /home/trader/asx-trader
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**4.3 Create requirements.txt**

Create: `requirements.txt`

```
ib_insync==0.9.86
pandas==2.1.0
numpy==1.25.0
sqlalchemy==2.0.20
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
schedule==1.2.0
loguru==0.7.0
pyyaml==6.0
pytest==7.4.0
pytest-cov==4.1.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

**4.4 Create .env File**

Create: `.env`

```bash
# Interactive Brokers
IB_HOST=127.0.0.1
IB_PORT=4002
IB_CLIENT_ID=1
IB_ACCOUNT=DU123456  # Replace with your paper account ID

# Database
DATABASE_PATH=data/trading.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trader.log

# Trading Parameters
PAPER_TRADING=true
MAX_POSITION_SIZE_PERCENT=10
MAX_DAILY_LOSS_PERCENT=5
MIN_GAP_PERCENT=3.0
```

**4.5 Initialize Database**

Create: `scripts/init_database.py`

```python
import sqlite3
from pathlib import Path

def init_database():
    db_path = Path("data/trading.db")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            symbol TEXT NOT NULL,
            entry_time TIMESTAMP,
            entry_price REAL,
            quantity INTEGER,
            stop_price REAL,
            exit_time TIMESTAMP,
            exit_price REAL,
            exit_reason TEXT,
            pnl REAL,
            pnl_percent REAL,
            r_multiple REAL,
            catalyst_text TEXT,
            gap_percent REAL,
            or_high REAL,
            or_low REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create announcements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            announcement_date DATE NOT NULL,
            symbol TEXT NOT NULL,
            header TEXT,
            pdf_url TEXT,
            page_count INTEGER,
            catalyst_score INTEGER,
            selected_for_watchlist BOOLEAN,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create daily_performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL UNIQUE,
            trades_count INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            total_pnl REAL,
            win_rate REAL,
            avg_winner REAL,
            avg_loser REAL,
            largest_winner REAL,
            largest_loser REAL,
            notes TEXT
        )
    """)
    
    # Create system_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            log_level TEXT,
            component TEXT,
            message TEXT,
            context TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
```

Run it:
```bash
python scripts/init_database.py
```

---

### Step 5: Core Component Implementation

**5.1 Database Utility**

Create: `src/utils/database.py`

```python
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import os

class Database:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'data/trading.db')
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
    
    def fetch_all(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
```

**5.2 Logger Setup**

Create: `src/utils/logger.py`

```python
from loguru import logger
import sys
import os

def setup_logger():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/trader.log')
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=log_level
    )
    
    # Add file handler
    logger.add(
        log_file,
        rotation="100 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        level=log_level
    )
    
    return logger

# Initialize logger
log = setup_logger()
```

**5.3 IB Client Implementation**

Create: `src/brokers/ib_client.py`

```python
from ib_insync import IB, Stock, MarketOrder, StopOrder, util
from typing import Optional, List
import os
from src.utils.logger import log

class IBClient:
    def __init__(self):
        self.ib = IB()
        self.host = os.getenv('IB_HOST', '127.0.0.1')
        self.port = int(os.getenv('IB_PORT', 4002))
        self.client_id = int(os.getenv('IB_CLIENT_ID', 1))
        self.account = os.getenv('IB_ACCOUNT')
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to IB Gateway"""
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            log.info(f"Connected to IB Gateway at {self.host}:{self.port}")
            log.info(f"Account: {self.account}")
            return True
        except Exception as e:
            log.error(f"Failed to connect to IB Gateway: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IB Gateway"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            log.info("Disconnected from IB Gateway")
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.ib.isConnected()
    
    def get_contract(self, symbol: str, exchange='ASX', currency='AUD') -> Stock:
        """Create ASX stock contract"""
        contract = Stock(symbol, exchange, currency)
        self.ib.qualifyContracts(contract)
        return contract
    
    def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            contract = self.get_contract(symbol)
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data
            
            # Try different price fields
            if ticker.last and ticker.last > 0:
                return ticker.last
            elif ticker.close and ticker.close > 0:
                return ticker.close
            elif ticker.bid and ticker.bid > 0:
                return ticker.bid
            
            log.warning(f"No price data available for {symbol}")
            return None
            
        except Exception as e:
            log.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_bars(self, symbol: str, duration='2 D', bar_size='1 day'):
        """Get historical bars"""
        try:
            contract = self.get_contract(symbol)
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            return bars
        except Exception as e:
            log.error(f"Error getting bars for {symbol}: {e}")
            return []
    
    def place_market_order(self, symbol: str, quantity: int, action='BUY'):
        """Place market order"""
        try:
            contract = self.get_contract(symbol)
            order = MarketOrder(action, quantity)
            trade = self.ib.placeOrder(contract, order)
            
            # Wait for order to fill
            while not trade.isDone():
                self.ib.waitOnUpdate()
                self.ib.sleep(0.1)
            
            log.info(f"Market order executed: {action} {quantity} {symbol}")
            return trade
            
        except Exception as e:
            log.error(f"Error placing market order for {symbol}: {e}")
            return None
    
    def place_stop_order(self, symbol: str, quantity: int, stop_price: float, action='SELL'):
        """Place stop loss order"""
        try:
            contract = self.get_contract(symbol)
            order = StopOrder(action, quantity, stopPrice=stop_price)
            trade = self.ib.placeOrder(contract, order)
            log.info(f"Stop order placed: {action} {quantity} {symbol} @ ${stop_price:.2f}")
            return trade
            
        except Exception as e:
            log.error(f"Error placing stop order for {symbol}: {e}")
            return None
    
    def cancel_order(self, trade):
        """Cancel an order"""
        try:
            self.ib.cancelOrder(trade.order)
            log.info(f"Order cancelled: {trade.order.orderId}")
        except Exception as e:
            log.error(f"Error cancelling order: {e}")
    
    def get_positions(self) -> List:
        """Get current positions"""
        return self.ib.positions()
    
    def get_open_orders(self) -> List:
        """Get open orders"""
        return self.ib.openOrders()
    
    def get_account_value(self, tag='NetLiquidation') -> float:
        """Get account value"""
        try:
            account_values = self.ib.accountValues()
            for item in account_values:
                if item.tag == tag and item.account == self.account:
                    return float(item.value)
            return 0.0
        except Exception as e:
            log.error(f"Error getting account value: {e}")
            return 0.0
    
    def get_buying_power(self) -> float:
        """Get available buying power"""
        return self.get_account_value('BuyingPower')
```

**5.4 Test IB Connection**

Create: `scripts/test_ib_connection.py`

```python
import sys
sys.path.insert(0, '/home/trader/asx-trader')

from src.brokers.ib_client import IBClient
from src.utils.logger import log
from dotenv import load_dotenv

def test_connection():
    load_dotenv()
    
    log.info("Testing IB Gateway connection...")
    
    client = IBClient()
    
    # Test connection
    if not client.connect():
        log.error("Failed to connect")
        return
    
    # Test account info
    log.info(f"Account value: ${client.get_account_value():,.2f}")
    log.info(f"Buying power: ${client.get_buying_power():,.2f}")
    
    # Test market data (BHP is always liquid)
    log.info("Testing market data for BHP...")
    price = client.get_market_price('BHP')
    if price:
        log.info(f"BHP current price: ${price:.2f}")
    else:
        log.warning("Could not retrieve BHP price")
    
    # Test historical data
    log.info("Testing historical data for BHP...")
    bars = client.get_bars('BHP')
    if bars:
        log.info(f"Retrieved {len(bars)} historical bars")
        log.info(f"Latest close: ${bars[-1].close:.2f}")
    
    # Get positions (should be empty initially)
    positions = client.get_positions()
    log.info(f"Current positions: {len(positions)}")
    
    client.disconnect()
    log.info("Test complete!")

if __name__ == "__main__":
    test_connection()
```

Run the test:
```bash
cd /home/trader/asx-trader
source venv/bin/activate
python scripts/test_ib_connection.py
```

---

## Development Checklist

### Week 1: Infrastructure & IB Integration
- [x] Set up Digital Ocean droplet
- [ ] Install IB Gateway
- [ ] Configure supervisor for auto-start
- [ ] Complete first-time IB Gateway login
- [ ] Set up Python environment
- [ ] Initialize database
- [ ] Implement and test IB client
- [ ] Verify market data access

### Week 2: Core Trading Logic
- [ ] Implement catalyst scorer (integrate existing scraper)
- [ ] Implement gap detector
- [ ] Implement opening range tracker
- [ ] Write unit tests for each component
- [ ] Test components individually with historical data

### Week 3: Trade Execution
- [ ] Implement position sizer
- [ ] Implement order manager
- [ ] Implement stop loss logic
- [ ] Implement EOD close logic
- [ ] Write integration tests

### Week 4: Live Trading Loop
- [ ] Implement main trading loop (`live_trader.py`)
- [ ] Add error handling and recovery
- [ ] Implement daily reporting
- [ ] Add system health checks
- [ ] Deploy to droplet and test end-to-end

### Week 5-6: Paper Trading
- [ ] Run system live for 2-4 weeks
- [ ] Monitor daily performance
- [ ] Fix bugs as they appear
- [ ] Tune catalyst scoring
- [ ] Document edge cases and issues

---

## Testing Strategy

### Unit Tests
Each component should have unit tests:
- `test_ib_client.py` - Connection, orders, data retrieval
- `test_gap_detector.py` - Gap calculation logic
- `test_opening_range.py` - OR high/low tracking
- `test_catalyst_scorer.py` - Scoring algorithm
- `test_position_sizer.py` - Position sizing calculations

### Integration Tests
- End-to-end test with mock IB responses
- Database read/write operations
- Full trade lifecycle (entry → stop → exit)

### Manual Testing Checklist
Daily verification during paper trading:
- [ ] System starts automatically at 7 AM
- [ ] Announcements scraped successfully
- [ ] Watchlist generated and logged
- [ ] Gap detection works at 10:00 AM
- [ ] OR high/low calculated correctly
- [ ] Entries execute on OR breaks
- [ ] Stops placed correctly
- [ ] Positions close at EOD
- [ ] All trades logged to database
- [ ] No memory leaks over 6+ hours

---

## Monitoring & Observability

### Daily Health Checks

Create: `scripts/daily_health_check.py`

```python
import sys
sys.path.insert(0, '/home/trader/asx-trader')

from src.brokers.ib_client import IBClient
from src.utils.database import Database
from src.utils.logger import log
from datetime import datetime, date
from dotenv import load_dotenv

def health_check():
    load_dotenv()
    
    log.info("=== Daily Health Check ===")
    
    # Check IB connection
    client = IBClient()
    if not client.connect():
        log.error("❌ IB Gateway not connected")
        return False
    else:
        log.info("✅ IB Gateway connected")
    
    # Check account value
    account_value = client.get_account_value()
    log.info(f"Account value: ${account_value:,.2f}")
    
    # Check positions
    positions = client.get_positions()
    log.info(f"Open positions: {len(positions)}")
    for pos in positions:
        log.info(f"  - {pos.contract.symbol}: {pos.position} shares")
    
    client.disconnect()
    
    # Check database
    db = Database()
    today = date.today()
    
    # Count today's trades
    trades = db.fetch_all(
        "SELECT COUNT(*) as count FROM trades WHERE trade_date = ?",
        (today,)
    )
    log.info(f"Trades today: {trades[0]['count']}")
    
    # Check for errors in logs
    errors = db.fetch_all(
        "SELECT COUNT(*) as count FROM system_logs WHERE log_level = 'ERROR' AND DATE(log_time) = ?",
        (today,)
    )
    if errors[0]['count'] > 0:
        log.warning(f"⚠️  {errors[0]['count']} errors logged today")
    else:
        log.info("✅ No errors logged today")
    
    log.info("=== Health Check Complete ===")
    return True

if __name__ == "__main__":
    health_check()
```

Schedule this as a cron job:
```bash
# Run health check at 4:30 PM daily
30 16 * * 1-5 cd /home/trader/asx-trader && venv/bin/python scripts/daily_health_check.py
```

### Performance Report

Create: `scripts/generate_daily_report.py`

```python
import sys
sys.path.insert(0, '/home/trader/asx-trader')

from src.utils.database import Database
from datetime import date, timedelta
import pandas as pd

def generate_report():
    db = Database()
    today = date.today()
    
    # Get today's trades
    trades = db.fetch_all("""
        SELECT * FROM trades 
        WHERE trade_date = ? 
        ORDER BY entry_time
    """, (today,))
    
    if not trades:
        print(f"\n📊 Daily Report - {today}")
        print("No trades today")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(t) for t in trades])
    
    # Calculate metrics
    total_trades = len(df)
    winning_trades = len(df[df['pnl'] > 0])
    losing_trades = len(df[df['pnl'] < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_pnl = df['pnl'].sum()
    avg_winner = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
    avg_loser = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
    
    largest_winner = df['pnl'].max()
    largest_loser = df['pnl'].min()
    
    # Print report
    print(f"\n📊 Daily Report - {today}")
    print("=" * 50)
    print(f"Total Trades: {total_trades}")
    print(f"Winners: {winning_trades} | Losers: {losing_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"Avg Winner: ${avg_winner:,.2f}")
    print(f"Avg Loser: ${avg_loser:,.2f}")
    print(f"Best Trade: ${largest_winner:,.2f}")
    print(f"Worst Trade: ${largest_loser:,.2f}")
    print("=" * 50)
    
    # Show individual trades
    print("\nTrade Details:")
    for _, trade in df.iterrows():
        print(f"{trade['symbol']:6} | Entry: ${trade['entry_price']:.2f} | Exit: ${trade['exit_price']:.2f} | P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.1f}%) | {trade['exit_reason']}")
    
    # Save to daily_performance table
    db.execute("""
        INSERT OR REPLACE INTO daily_performance 
        (trade_date, trades_count, winning_trades, losing_trades, total_pnl, 
         win_rate, avg_winner, avg_loser, largest_winner, largest_loser)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (today, total_trades, winning_trades, losing_trades, total_pnl,
          win_rate, avg_winner, avg_loser, largest_winner, largest_loser))
    
    print("\n✅ Report saved to database")

if __name__ == "__main__":
    generate_report()
```

---

## Risk Management & Safety

### Kill Switch Implementation

Create: `src/risk/kill_switch.py`

```python
from src.utils.database import Database
from src.utils.logger import log
from datetime import date
import os

class KillSwitch:
    def __init__(self):
        self.db = Database()
        self.max_daily_loss_percent = float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5.0))
        self.starting_balance = None
        
    def check(self) -> bool:
        """
        Check if kill switch should be triggered
        Returns True if trading should continue, False if should stop
        """
        today = date.today()
        
        # Get today's P&L
        result = self.db.fetch_one("""
            SELECT SUM(pnl) as total_pnl 
            FROM trades 
            WHERE trade_date = ?
        """, (today,))
        
        if not result or result['total_pnl'] is None:
            return True  # No trades yet, continue
        
        total_pnl = result['total_pnl']
        
        # Get starting balance (would need to implement this properly)
        # For now, using a placeholder
        if self.starting_balance is None:
            # In real implementation, get from IB at start of day
            self.starting_balance = 100000  # Placeholder
        
        loss_percent = (total_pnl / self.starting_balance) * 100
        
        if loss_percent <= -self.max_daily_loss_percent:
            log.critical(f"🛑 KILL SWITCH TRIGGERED: Daily loss {loss_percent:.2f}% exceeds limit of {self.max_daily_loss_percent}%")
            return False
        
        return True
```

### Position Size Limits

Create: `src/risk/position_sizer.py`

```python
import os
from src.utils.logger import log

class PositionSizer:
    def __init__(self):
        self.max_position_percent = float(os.getenv('MAX_POSITION_SIZE_PERCENT', 10.0))
    
    def calculate_position_size(self, account_value: float, entry_price: float, 
                                stop_price: float, risk_percent: float = 2.0) -> int:
        """
        Calculate position size based on risk
        
        Args:
            account_value: Total account value
            entry_price: Entry price per share
            stop_price: Stop loss price
            risk_percent: % of account to risk (default 2%)
        
        Returns:
            Number of shares to buy
        """
        # Calculate risk per share
        risk_per_share = entry_price - stop_price
        
        if risk_per_share <= 0:
            log.warning("Invalid stop price - stop must be below entry")
            return 0
        
        # Calculate position size based on risk
        risk_amount = account_value * (risk_percent / 100)
        shares = int(risk_amount / risk_per_share)
        
        # Check max position size constraint
        position_value = shares * entry_price
        max_position_value = account_value * (self.max_position_percent / 100)
        
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            log.info(f"Position size reduced due to max position limit")
        
        log.info(f"Position size: {shares} shares (risk: ${risk_amount:.2f}, R: ${risk_per_share:.2f})")
        
        return shares
```

---

## Deployment Automation

### Deployment Script

Create: `scripts/deploy.sh`

```bash
#!/bin/bash

echo "🚀 Deploying ASX Catalyst Trader..."

# Navigate to project directory
cd /home/trader/asx-trader

# Activate virtual environment
source venv/bin/activate

# Pull latest code (if using git)
# git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations if needed
python scripts/init_database.py

# Restart services
sudo supervisorctl restart ibgateway
sudo supervisorctl restart trader

# Run health check
sleep 5
python scripts/daily_health_check.py

echo "✅ Deployment complete!"
```

### Supervisor Config for Main Trader

Create: `/etc/supervisor/conf.d/trader.conf`

```ini
[program:trader]
command=/home/trader/asx-trader/venv/bin/python /home/trader/asx-trader/scripts/live_trader.py
directory=/home/trader/asx-trader
user=trader
autostart=false  # We'll start this manually at 7 AM via cron
autorestart=true
stderr_logfile=/home/trader/logs/trader.err.log
stdout_logfile=/home/trader/logs/trader.out.log
environment=PATH="/home/trader/asx-trader/venv/bin"
```

### Cron Jobs

Add to trader user's crontab:
```bash
crontab -e
```

```bash
# Start trader at 6:55 AM Mon-Fri (5 mins before market prep)
55 6 * * 1-5 /usr/bin/supervisorctl start trader

# Stop trader at 4:05 PM Mon-Fri (after market close)
5 16 * * 1-5 /usr/bin/supervisorctl stop trader

# Generate daily report at 4:15 PM
15 16 * * 1-5 cd /home/trader/asx-trader && venv/bin/python scripts/generate_daily_report.py

# Health check at 4:30 PM
30 16 * * 1-5 cd /home/trader/asx-trader && venv/bin/python scripts/daily_health_check.py

# Weekly backup of database (Sunday 2 AM)
0 2 * * 0 cp /home/trader/asx-trader/data/trading.db /home/trader/asx-trader/data/backups/trading_$(date +\%Y\%m\%d).db
```

---

## Success Metrics (Phase 1)

After 2-4 weeks of paper trading, evaluate:

**System Reliability:**
- [ ] 95%+ uptime during market hours
- [ ] Zero missed gap opportunities from watchlist
- [ ] All trades logged correctly
- [ ] No duplicate entries/exits

**Trading Performance:**
- [ ] Win rate >40%
- [ ] Average R:R ratio >1.5:1
- [ ] Max drawdown <15%
- [ ] Catalyst scoring producing 5-10 signals per week

**Code Quality:**
- [ ] All unit tests passing
- [ ] No critical bugs in 2 weeks
- [ ] Clean, readable, maintainable code

---

## Troubleshooting Guide

### IB Gateway Issues

**Problem:** IB Gateway won't connect
```bash
# Check if IB Gateway is running
ps aux | grep ibgateway

# Check logs
tail -f /home/trader/logs/ibgateway.out.log

# Restart IB Gateway
sudo supervisorctl restart ibgateway

# If still failing, try manual login via VNC
x11vnc -display :1 -bg -nopw -listen localhost -xkb
```

**Problem:** "Connection refused" error
- Check port 4002 is correct (4001 for live, 4002 for paper)
- Verify IB Gateway is logged in (check via VNC)
- Ensure firewall isn't blocking connection

**Problem:** Market data not available
- Verify ASX subscription in IB Account Management
- Check if market is open
- Try different symbols (BHP, CBA, WES are always liquid)

### Trading System Issues

**Problem:** No gaps detected
- Verify announcement scraper is working
- Check if market opened (10 AM AEST)
- Manually verify gaps exist (check ASX website)

**Problem:** Orders not executing
- Check account has buying power
- Verify contract is qualified correctly
- Check for trading halts on symbol
- Review order status in IB Gateway

**Problem:** System not starting automatically
- Check cron jobs: `crontab -l`
- Verify supervisor is running: `sudo supervisorctl status`
- Check system logs: `tail -f /home/trader/logs/trader.out.log`

---

## Next Steps After Phase 1

Once paper trading is successful:

**Phase 2: Live Trading**
- Switch to live IB account (port 4001)
- Start with 10-20% of capital
- Implement Telegram notifications
- Add daily email reports

**Phase 3: Strategy Refinement**
- A/B test different catalyst scoring methods
- Implement trailing stops
- Test profit targets
- Add volume profile analysis

**Phase 4: Scale**
- Increase position sizes gradually
- Add more sophisticated risk management
- Build web dashboard for monitoring
- Implement backtesting framework

---

## Support & Resources

**IB API Documentation:**
- Official docs: https://interactivebrokers.github.io/tws-api/
- ib_insync docs: https://ib-insync.readthedocs.io/

**ASX Information:**
- Market announcements: https://www.asx.com.au/markets/trade-our-cash-market/announcements
- Trading hours: https://www.asx.com.au/markets/market-resources/trading-hours-calendar

**Python Libraries:**
- pandas: https://pandas.pydata.org/docs/
- loguru: https://loguru.readthedocs.io/

---

## Appendix A: Complete File Tree

```
/home/trader/asx-trader/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.yaml
│   └── ib_gateway_config.ini
├── data/
│   ├── trading.db
│   ├── announcements/
│   ├── watchlists/
│   └── backups/
├── logs/
│   ├── trader.log
│   ├── ibgateway.out.log
│   └── ibgateway.err.log
├── scripts/
│   ├── setup_server.sh
│   ├── setup_ib_gateway.sh
│   ├── start_ib_gateway.sh
│   ├── init_database.py
│   ├── test_ib_connection.py
│   ├── live_trader.py
│   ├── daily_health_check.py
│   ├── generate_daily_report.py
│   └── deploy.sh
├── src/
│   ├── __init__.py
│   ├── brokers/
│   │   ├── __init__.py
│   │   ├── ib_client.py
│   │   └── ib_market_data.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── asx_announcements.py
│   │   └── catalyst_scorer.py
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── gap_detector.py
│   │   └── opening_range.py
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── entry_logic.py
│   │   └── exit_logic.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── order_manager.py
│   │   └── position_tracker.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── position_sizer.py
│   │   ├── risk_manager.py
│   │   └── kill_switch.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── database.py
├── tests/
│   ├── __init__.py
│   ├── test_ib_client.py
│   ├── test_gap_detector.py
│   ├── test_opening_range.py
│   └── test_position_sizer.py
└── venv/
```

---

## Appendix B: Environment Variables Reference

```bash
# Interactive Brokers
IB_HOST=127.0.0.1              # IB Gateway host
IB_PORT=4002                   # 4002 for paper, 4001 for live
IB_CLIENT_ID=1                 # Client ID for connection
IB_ACCOUNT=DU123456            # Paper trading account ID

# Database
DATABASE_PATH=data/trading.db  # SQLite database path

# Logging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/trader.log       # Log file location

# Trading Parameters
PAPER_TRADING=true             # Safety flag
MAX_POSITION_SIZE_PERCENT=10   # Max % of capital per trade
MAX_DAILY_LOSS_PERCENT=5       # Daily loss kill switch
MAX_CONCURRENT_POSITIONS=3     # Max simultaneous positions
MIN_GAP_PERCENT=3.0            # Minimum gap % to consider
MAX_GAP_PERCENT=15.0           # Maximum gap % (avoid halts)
OPENING_RANGE_MINUTES=15       # Opening range period
RISK_PER_TRADE_PERCENT=2.0     # % of capital to risk per trade

# Market Hours (AEST)
MARKET_OPEN=10:00              # ASX open
MARKET_CLOSE=16:00             # ASX close
EOD_CLOSE_TIME=15:50           # When to close all positions

# System
TIMEZONE=Australia/Sydney      # System timezone
```

---

**END OF PRD**

*This document should be treated as a living document and updated as the system evolves.*
