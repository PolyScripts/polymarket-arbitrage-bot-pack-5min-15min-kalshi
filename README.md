# Polymarket Kalshi Arbitrage Bot | Cross-Platform Crypto Binary Options Trading

> **Language:** [English](README.md) | [中文 (Chinese)](README_ZH.md)

---

## 📬 Contact

**Telegram:** [@movez_x](https://t.me/movez_x)

---

## What Is This Bot?

The **Polymarket Kalshi Arbitrage Bot** is an automated trading bot that captures **risk-free arbitrage opportunities** between two leading prediction markets: **Polymarket** and **Kalshi**.

### Strategy in Simple Terms

Both platforms offer **15-minute binary options** on crypto (BTC, ETH, SOL). Each market asks: *"Will the price go UP or DOWN by the end of this 15-minute window?"* — one side always wins and pays $1.00.

The bot finds moments when the **combined cost of both sides across platforms is less than $1.00**. By buying both legs, you lock in a **guaranteed profit** regardless of which way the market moves. No directional bet, no guesswork — just pure arbitrage.

- **Intra-platform:** Buy UP + DOWN on Polymarket when sum < $1.00 (after fees)
- **Cross-platform:** Buy UP on Polymarket + NO on Kalshi (or DOWN + YES) when sum < $1.00

Real-time WebSocket feeds, 2-tick confirmation, and strict profit thresholds keep execution fast and reliable.

---

## Screenshots

*Real trade history and live performance — see the bot in action.*

**Bot Running**

![Bot Running](images/1.png)

**Trade Log**

![Trade Log](images/2.png)

**Order Fill**

![Order Fill](images/3.png)

---

## 5 Advantages for Traders

1. **Passive Income Potential** — Run 24/7 on a VPS; the bot scans every second and trades automatically when arbitrage appears. No need to watch charts.

2. **Low Risk, Guaranteed Payouts** — One side always wins. You buy both sides for less than $1.00 and receive $1.00. No directional exposure.

3. **Real Trade History** — See actual trades in the screenshots above. All trades are logged in `arb_scanner_live/trade_log.json` and `arb_scanner_live/live_trades.json`.

4. **High Frequency** — 96 windows per day (15-min each). More opportunities = more chances to capture small, consistent profits.

5. **Automated & Emotion-Free** — No FOMO, no guesswork. The bot strictly follows arbitrage rules and profit thresholds.

### Advanced: Telegram Bot Integration

The bot integrates with **Telegram** for real-time alerts and remote control. Get instant notifications for trade opens, partial fills, hedge results, and new windows - plus use the `/status` command to check balances and bot status from anywhere.

---

**Want to add features, get help, access premium support, or get full source code?** Contact via Telegram: [@movez_x](https://t.me/movez_x)

---

## Quick Start

### Prerequisites

- Python 3.8+
- Polymarket account (with USDC)
- Kalshi account (with USD)

### Setup

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd polymarket-kalshi-arbitrage-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials**
   - Copy `credentials_template.py` to `credentials.py`
   - Fill in your Polymarket API keys and Kalshi API keys

4. **Run the bot**
   ```bash
   python ws_scanner.py
   ```
   For ETH or SOL: `python ws_scanner.py eth` or `python ws_scanner.py sol`

5. **Check balances**
   ```bash
   python check_balance.py
   ```

---

## Contact

**Telegram:** [@movez_x](https://t.me/movez_x)
