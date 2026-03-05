# Kalshi Arbitrage Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP%208-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A production-ready Python bot that identifies and executes arbitrage opportunities in Kalshi prediction markets. The bot analyzes market inefficiencies where contract probabilities don't sum to 100%, calculates net profit after fees, and can automatically execute trades when profitable opportunities are detected.

**Repository**: [polymarket-kalshi-arbitrage-trading-bot-v1](https://github.com/dexorynLabs/polymarket-kalshi-arbitrage-trading-bot-v1)

## Overview

This project demonstrates production-ready software engineering practices:

- **API Integration**: Robust client with rate limiting, retry logic, and comprehensive error handling
- **Financial Analysis**: Accurate fee calculations and profit modeling with real-world trading considerations
- **Algorithm Design**: Efficient market scanning algorithms that filter and prioritize opportunities
- **Software Engineering**: Clean architecture, type hints, modular design, and comprehensive documentation
- **Production Readiness**: Error handling, configuration management, and safe defaults

### Key Achievements

- ✅ **Modular Architecture**: Clean separation of concerns with single-responsibility modules
- ✅ **Type Safety**: Comprehensive type hints for better IDE support and maintainability
- ✅ **Error Resilience**: Graceful handling of API failures, rate limits, and edge cases
- ✅ **Financial Accuracy**: Precise fee calculations ensuring realistic profit estimates
- ✅ **Production Ready**: Environment-based configuration, logging, and safe execution defaults

## Features

- **Dual Opportunity Detection**: Scans for both arbitrage and immediate trade opportunities
- **Arbitrage Detection**: Identifies markets where YES + NO probabilities don't sum to 100%
- **Immediate Trades**: Finds orderbook spreads where bid > ask (instant profit)
- **Fee Calculation**: Accurately calculates trading fees based on contract prices
- **Profit Analysis**: Computes net profit after fees and ranks by profitability
- **Continuous Monitoring**: Optional continuous scanning mode
- **Auto-Execution**: Optional automatic trade execution (use with caution)

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Modules

- **`bot.py`** - Main orchestration layer that coordinates scanning and execution
- **`kalshi_client.py`** - API abstraction layer with rate limiting, retry logic, and error handling
- **`arbitrage_analyzer.py`** - Business logic for detecting probability-based arbitrage
- **`trade_executor.py`** - Orderbook analysis and trade execution engine
- **`fee_calculator.py`** - Fee calculation module with tiered fee structure support


### Design Decisions

- **Modular Design**: Each module has a single responsibility
- **Error Handling**: Comprehensive try-catch blocks with graceful degradation
- **Rate Limiting**: Built-in rate limiting to respect API constraints
- **Type Safety**: Type hints throughout for better IDE support and maintainability
- **Configuration**: Environment-based configuration for flexibility
- **Fee Accuracy**: Precise fee calculations ensure profit estimates are realistic

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dexorynLabs/polymarket-kalshi-arbitrage-trading-bot-v1.git
cd polymarket-kalshi-arbitrage-trading-bot-v1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Kalshi API credentials

# Run the bot
python bot.py
```

## Setup

### Prerequisites

- Python 3.8+
- Kalshi API credentials (API key and secret)
- pip (Python package manager)

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Kalshi API credentials:
```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and replace the placeholder values with your actual credentials:
```
# From your Kalshi account:
# - API Key ID goes in KALSHI_API_KEY
# - Private Key goes in KALSHI_API_SECRET
KALSHI_API_KEY=your_api_key_id_here
KALSHI_API_SECRET=your_private_key_here
KALSHI_API_BASE_URL=https://api.elections.kalshi.com/trade-api/v2
MIN_PROFIT_PER_DAY=0.1
MAX_POSITION_SIZE=1000
```

**Note**: In your Kalshi account settings:
- **API Key ID** → use for `KALSHI_API_KEY`
- **Private Key** → use for `KALSHI_API_SECRET`

### Optional Configuration

You can adjust these parameters in `.env`:
- `MIN_PROFIT_PER_DAY`: Minimum profit per day threshold for arbitrage opportunities (default: $0.10)
- `MAX_POSITION_SIZE`: Maximum position size for trades (default: 1000 contracts)
- `MIN_PROFIT_CENTS`: Minimum profit in cents per contract for immediate trades (default: 2)

**Note**: The bot automatically calculates the minimum profitable deviation based on actual trading fees. Any opportunity with positive net profit (after fees) will be considered, ensuring you don't miss profitable opportunities even if they're very small.

## Usage

### Single Scan

Run a one-time scan (automatically scans both arbitrage and immediate trades):
```bash
python bot.py
```

The bot will automatically:
- Scan for immediate trade opportunities (buy low, sell high instantly)
- Scan for arbitrage opportunities (probability mismatches)
- Compare both types and show recommendations
- Display the best opportunities from each category

Display all opportunities (not just top 10):
```bash
python bot.py --all
```

Scan more markets:
```bash
python bot.py --limit 500
```

### Continuous Monitoring

Run continuous scanning (checks every 5 minutes by default):
```bash
python bot.py --continuous
```

Custom scan interval (in seconds):
```bash
python bot.py --continuous --interval 60
```

### Automatic Trade Execution

**⚠️ WARNING**: Automatically execute trades (USE WITH CAUTION):
```bash
python bot.py --auto-execute
```

With `--auto-execute`, the bot will:
- Automatically execute immediate trade opportunities (instant profit)
- Prioritize immediate trades over arbitrage (no waiting required)
- Execute trades only when net profit is positive after fees

### Legacy Options (for specific scanning)

If you want to scan only one type of opportunity:
```bash
# Only immediate trades
python bot.py --trades-only

# Only arbitrage opportunities
python bot.py --arbitrage-only
```

**Note**: By default, the bot scans both types automatically and compares them.

### Command Line Options

```
--continuous       Run continuous scanning mode
--interval N       Scan interval in seconds (default: 300)
--limit N          Maximum number of markets to scan (default: 100)
--all              Display all opportunities (not just top 10)
--auto-execute     Automatically execute profitable trades (USE WITH CAUTION)
--trades-only      Scan ONLY for immediate trade opportunities
--arbitrage-only   Scan ONLY for arbitrage opportunities
--min-liquidity N   Minimum liquidity in cents (default: 10000 = $100)
--max-scans N      Maximum number of scans in continuous mode
```

**Default Behavior**: The bot automatically scans both arbitrage and immediate trade opportunities, compares them, and shows recommendations.

## How It Works

The bot scans Kalshi markets for two types of profitable opportunities:

### 1. Arbitrage Opportunities

Arbitrage occurs when YES + NO probabilities don't sum to 100%:

**Example:**
- YES contracts trading at 52¢
- NO contracts trading at 50¢
- Total: 102% (2% arbitrage opportunity)

**How it works:**
1. Fetches active markets from Kalshi API
2. Calculates total probability (YES price + NO price)
3. Identifies markets where total ≠ 100%
4. Calculates gross profit and net profit (after fees)
5. Ranks by profit per day based on expiration date

### 2. Immediate Trade Opportunities

Immediate trades occur when bid price > ask price (can buy low, sell high instantly):

**Example:**
- Someone wants to buy YES at 43¢ (bid)
- Someone wants to sell YES at 42¢ (ask)
- Profit: 1¢ per contract (minus fees)

**How it works:**
1. Scans orderbooks for profitable spreads
2. Identifies cases where bid > ask
3. Calculates net profit after fees
4. Optionally executes trades automatically

### Comparison

The bot compares both types and recommends the best option:
- **Immediate Trades**: Instant profit, no waiting required
- **Arbitrage**: Time-based profit, requires holding until expiration

## Fee Structure

The bot uses an approximation of Kalshi's fee structure:
- Contracts priced near 50¢: ~3.5% fee
- Contracts at extremes (near 0¢ or 100¢): ~1% fee
- Maker orders (limit orders): 50% discount on fees

**Note**: Actual fees may vary. Check Kalshi's official fee schedule for precise values.

## Example Output

```
[2024-01-15 10:30:00] Scanning 100 markets for arbitrage opportunities...
Found 87 active markets. Analyzing...

============================================================
Found 3 arbitrage opportunities!
============================================================

[1] ============================================================
Market: Will Bitcoin reach $50,000 by end of month?
Ticker: BTC-50K-JAN
Total Probability: 102.5%
Deviation from 100%: 2.50%
Expiration: 2024-01-31 23:59:59
Days to Expiration: 16.50

Profit Analysis:
  Gross Profit: $25.00
  Net Profit (after fees): $22.50
  Profit per Day: $1.36

Recommended Trades:
  1. SELL 100 contracts of BTC-50K-JAN-YES at 52¢ (side: yes)
  2. SELL 100 contracts of BTC-50K-JAN-NO at 50¢ (side: no)
============================================================
```

## Important Notes

- **API Access**: You need valid Kalshi API credentials to use this bot
- **Market Hours**: Kalshi operates nearly 24/7 with maintenance windows
- **Risk**: Arbitrage opportunities may be fleeting and require quick execution
- **Liquidity**: Ensure markets have sufficient liquidity before executing trades
- **Testing**: Test thoroughly with small positions before scaling up
- **Auto-Execute Warning**: The `--auto-execute` flag will automatically place trades. Use with extreme caution and test thoroughly first. Always monitor your account and positions.
- **Order Execution**: Limit orders are used by default for safety. Market orders may execute at worse prices but provide instant execution.

## Technical Details

### Error Handling

The bot includes comprehensive error handling:
- **API Errors**: Graceful handling of rate limits, network errors, and API failures
- **Data Validation**: Checks for missing or invalid market data before processing
- **Trade Execution**: Validates opportunities before execution to prevent losses
- **Rate Limiting**: Automatic rate limit detection and backoff strategies

### Performance Considerations

- **Efficient Scanning**: Filters markets by liquidity before detailed analysis
- **Rate Limiting**: Built-in delays to respect API constraints
- **Batch Processing**: Processes multiple markets efficiently
- **Memory Management**: Streams data rather than loading everything into memory

### Security

- **Credential Management**: Uses environment variables, never hardcoded
- **API Key Protection**: `.env` file is gitignored
- **Safe Defaults**: Auto-execution disabled by default
- **Input Validation**: Validates all inputs before API calls

## Testing

Before using with real money:

1. **Dry Run**: Run without `--auto-execute` to see opportunities
2. **Small Test**: Start with `--limit 10` and `--min-liquidity 1000`
3. **Monitor**: Watch output and verify behavior matches expectations

## Disclaimer

This bot is for educational and informational purposes only. Trading involves risk, and past performance does not guarantee future results. Always:
- Understand the risks involved
- Test thoroughly before using real money
- Monitor your positions
- Comply with Kalshi's terms of service
- Consult with financial advisors if needed


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Highlights

This project showcases several important software engineering skills:

### Technical Skills Demonstrated

- **API Design**: Clean abstraction layer for external API integration
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Rate Limiting**: Intelligent rate limit detection and backoff strategies
- **Financial Modeling**: Accurate fee calculations and profit analysis
- **Algorithm Optimization**: Efficient filtering and prioritization algorithms
- **Code Quality**: Type hints, docstrings, and PEP 8 compliance
- **Configuration Management**: Environment-based configuration with validation
- **Production Practices**: Safe defaults, logging, and comprehensive testing utilities

### Code Quality Metrics

- **5 Core Modules**: Clean, focused, single-responsibility design
- **~1,674 Lines**: Well-documented, maintainable codebase
- **Type Hints**: Throughout for better IDE support and type safety
- **Error Handling**: Comprehensive try-catch blocks with meaningful error messages
- **Documentation**: Extensive docstrings and README documentation

### Real-World Application

This bot solves a real financial problem:
- Identifies market inefficiencies in prediction markets
- Calculates realistic profit estimates after fees
- Provides actionable trading recommendations
- Can execute trades automatically (with safety defaults)

## Author

**DexorynLabs**

- **GitHub**: [dexorynLabs](https://github.com/dexorynLabs/polymarket-kalshi-arbitrage-trading-bot-v1)
- **Telegram**: [@dexoryn_12](https://t.me/dexoryn_12)

Built with Python 3.8+, demonstrating production-ready software engineering practices.

---

**Portfolio Project**: This project demonstrates proficiency in API integration, financial analysis, algorithm design, and software engineering best practices. The codebase showcases clean architecture, comprehensive error handling, and production-ready code quality.

