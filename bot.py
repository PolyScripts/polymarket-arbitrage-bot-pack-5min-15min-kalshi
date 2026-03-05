#!/usr/bin/env python3
"""
Kalshi Arbitrage Bot

A Python bot that finds arbitrage opportunities in Kalshi prediction markets.
It identifies two types of opportunities:
1. Arbitrage: Markets where probabilities don't sum to 100%
2. Immediate Trades: Orderbook spreads where you can buy low and sell high instantly

Author: DexorynLabs
License: MIT
"""
import os
import time
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

from kalshi_client import KalshiClient
from arbitrage_analyzer import ArbitrageAnalyzer, ArbitrageOpportunity
from trade_executor import TradeExecutor, TradeOpportunity

load_dotenv()


class KalshiArbitrageBot:
    """
    Main bot class for finding and analyzing arbitrage opportunities.
    
    The bot scans Kalshi markets for two types of profitable opportunities:
    - Arbitrage: When YES + NO probabilities don't sum to 100%
    - Immediate Trades: When bid price > ask price (instant profit)
    """
    
    def __init__(self, auto_execute_trades: bool = False):
        """
        Initialize the bot.
        
        Args:
            auto_execute_trades: If True, automatically execute profitable trades
        """
        # Initialize API client
        self.client = KalshiClient()
        
        # Initialize analyzers
        self.arbitrage_analyzer = ArbitrageAnalyzer()
        self.trade_executor = TradeExecutor(
            client=self.client,
            min_profit_cents=int(os.getenv("MIN_PROFIT_CENTS", "2")),
            max_position_size=int(os.getenv("MAX_POSITION_SIZE", "1000")),
            auto_execute=auto_execute_trades
        )
        
        # Configuration from environment variables
        self.min_profit_per_day = float(os.getenv("MIN_PROFIT_PER_DAY", "0.1"))
        self.min_liquidity = int(os.getenv("MIN_LIQUIDITY", "10000"))  # $100 default
    
    def filter_markets_by_liquidity(self, markets: List[Dict]) -> List[Dict]:
        """
        Filter markets to only include those with sufficient liquidity.
        
        Only includes markets that have:
        - Liquidity >= minimum threshold
        - Both bid and ask prices available (tradeable)
        
        Args:
            markets: List of market dictionaries from API
            
        Returns:
            Filtered list of markets with sufficient liquidity
        """
        filtered = []
        for market in markets:
            # Check liquidity threshold
            if market.get("liquidity", 0) < self.min_liquidity:
                continue
            
            # Check that market has bid/ask prices (is tradeable)
            yes_bid = market.get("yes_bid")
            yes_ask = market.get("yes_ask")
            no_bid = market.get("no_bid")
            no_ask = market.get("no_ask")
            
            # Market must have both bid AND ask for at least one side
            has_yes_liquidity = yes_bid is not None and yes_ask is not None and yes_bid != yes_ask
            has_no_liquidity = no_bid is not None and no_ask is not None and no_bid != no_ask
            
            if has_yes_liquidity or has_no_liquidity:
                filtered.append(market)
        
        return filtered
    
    def scan_arbitrage_opportunities(self, limit: int = 100) -> List[ArbitrageOpportunity]:
        """
        Scan markets for arbitrage opportunities.
        
        Arbitrage occurs when YES + NO probabilities don't sum to 100%.
        Example: YES at 52¢ and NO at 50¢ = 102% total (2% arbitrage)
        
        Args:
            limit: Maximum number of markets to scan
            
        Returns:
            List of arbitrage opportunities sorted by profit per day
        """
        print(f"[{datetime.now()}] Scanning {limit} markets for arbitrage opportunities...")
        
        # Fetch active markets
        markets = self.client.get_markets(limit=limit, status="open")
        if not markets:
            print("No markets found or API error.")
            return []
        
        # Filter by liquidity
        original_count = len(markets)
        markets = self.filter_markets_by_liquidity(markets)
        print(f"Found {original_count} active markets. "
              f"Filtered to {len(markets)} markets with liquidity >= ${self.min_liquidity/100:.2f}")
        
        if not markets:
            return []
        
        # Find arbitrage opportunities
        opportunities = self.arbitrage_analyzer.find_opportunities(markets, client=self.client)
        
        # Filter by minimum profit per day
        filtered = [
            opp for opp in opportunities 
            if opp.profit_per_day >= self.min_profit_per_day
        ]
        
        return filtered
    
    def scan_immediate_trades(self, limit: int = 100, auto_execute: bool = False) -> List[TradeOpportunity]:
        """
        Scan markets for immediate trade opportunities.
        
        Immediate trades occur when bid price > ask price (can buy low, sell high instantly).
        Example: Someone wants to buy YES at 43¢, someone wants to sell YES at 42¢
        
        Args:
            limit: Maximum number of markets to scan
            auto_execute: If True, automatically execute profitable trades
            
        Returns:
            List of trade opportunities sorted by net profit
        """
        print(f"[{datetime.now()}] Scanning {limit} markets for immediate trade opportunities...")
        
        # Fetch active markets
        markets = self.client.get_markets(limit=limit, status="open")
        if not markets:
            print("No markets found or API error.")
            return []
        
        # Filter by liquidity
        original_count = len(markets)
        markets = self.filter_markets_by_liquidity(markets)
        print(f"Found {original_count} active markets. "
              f"Filtered to {len(markets)} markets with liquidity >= ${self.min_liquidity/100:.2f}")
        
        if not markets:
            return []
        
        # Temporarily update auto_execute setting
        original_auto_execute = self.trade_executor.auto_execute
        self.trade_executor.auto_execute = auto_execute
        
        # Find immediate trade opportunities
        opportunities = self.trade_executor.scan_and_execute(markets, limit=limit)
        
        # Restore original setting
        self.trade_executor.auto_execute = original_auto_execute
        
        # Sort by net profit (descending)
        opportunities.sort(key=lambda x: x.net_profit, reverse=True)
        
        return opportunities
    
    def scan_all_opportunities(self, limit: int = 100, auto_execute: bool = False):
        """
        Scan for both arbitrage and immediate trade opportunities.
        
        Args:
            limit: Maximum number of markets to scan
            auto_execute: If True, automatically execute profitable trades
            
        Returns:
            Tuple of (arbitrage_opportunities, trade_opportunities, executed_count)
        """
        print(f"[{datetime.now()}] Scanning {limit} markets for all opportunities...")
        
        # Fetch markets once
        markets = self.client.get_markets(limit=limit, status="open")
        if not markets:
            print("No markets found or API error.")
            return [], [], 0
        
        # Filter by liquidity
        original_count = len(markets)
        markets = self.filter_markets_by_liquidity(markets)
        print(f"Found {original_count} active markets. "
              f"Filtered to {len(markets)} markets with liquidity >= ${self.min_liquidity/100:.2f}")
        
        if not markets:
            return [], [], 0
        
        # Scan for arbitrage opportunities
        arbitrage_opps = self.arbitrage_analyzer.find_opportunities(markets, client=self.client)
        arbitrage_opps = [
            opp for opp in arbitrage_opps 
            if opp.profit_per_day >= self.min_profit_per_day
        ]
        
        # Scan for immediate trade opportunities
        original_auto_execute = self.trade_executor.auto_execute
        self.trade_executor.auto_execute = False  # Don't auto-execute during scan
        trade_opps = self.trade_executor.scan_and_execute(markets, limit=limit)
        self.trade_executor.auto_execute = original_auto_execute
        trade_opps.sort(key=lambda x: x.net_profit, reverse=True)
        
        # Execute trades if requested
        executed_count = 0
        if auto_execute:
            for trade_opp in trade_opps:
                if trade_opp.net_profit > 0:
                    success, message = self.trade_executor.execute_trade(trade_opp)
                    if success:
                        print(f"[AUTO-EXECUTE] {message}")
                        executed_count += 1
        
        return arbitrage_opps, trade_opps, executed_count
    
    def display_arbitrage_opportunity(self, opp: ArbitrageOpportunity, index: int = None):
        """Display details of an arbitrage opportunity."""
        prefix = f"[{index}] " if index is not None else ""
        print(f"\n{prefix}{'='*60}")
        print(f"Market: {opp.market_title}")
        print(f"Ticker: {opp.market_ticker}")
        print(f"Total Probability: {opp.total_probability:.2f}%")
        print(f"Deviation from 100%: {opp.deviation:.2f}%")
        print(f"Expiration: {opp.expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Days to Expiration: {opp.days_to_expiration:.2f}")
        print(f"\nProfit Analysis:")
        print(f"  Gross Profit: ${opp.gross_profit:.2f}")
        print(f"  Net Profit (after fees): ${opp.net_profit:.2f}")
        print(f"  Profit per Day: ${opp.profit_per_day:.2f}")
        print(f"\nRecommended Trades:")
        for i, trade in enumerate(opp.trades, 1):
            print(f"  {i}. {trade['action'].upper()} {trade['quantity']} contracts "
                  f"of {trade['ticker']} at {trade['price']}¢ "
                  f"(side: {trade['side']})")
        print(f"{'='*60}\n")
    
    def display_trade_opportunity(self, opp: TradeOpportunity, index: int = None):
        """Display details of an immediate trade opportunity."""
        prefix = f"[{index}] " if index is not None else ""
        print(f"\n{prefix}{'='*60}")
        print(f"Market: {opp.market_title}")
        print(f"Ticker: {opp.market_ticker}")
        print(f"Side: {opp.side.upper()}")
        print(f"Buy Price: {opp.buy_price}¢")
        print(f"Sell Price: {opp.sell_price}¢")
        print(f"Spread: {opp.spread}¢")
        print(f"Quantity: {opp.quantity} contracts")
        print(f"\nProfit Analysis:")
        print(f"  Gross Profit: ${opp.gross_profit:.2f}")
        print(f"  Net Profit (after fees): ${opp.net_profit:.2f}")
        print(f"  Profit per Contract: ${opp.net_profit / opp.quantity:.4f}")
        print(f"{'='*60}\n")
    
    def run_scan(self, limit: int = 100, display_all: bool = False, auto_execute: bool = False):
        """
        Run a single scan and display results.
        
        Scans for both arbitrage and immediate trade opportunities, then displays them.
        
        Args:
            limit: Maximum number of markets to scan
            display_all: If True, display all opportunities; if False, only top 10
            auto_execute: If True, automatically execute profitable trades
        """
        arbitrage_opps, trade_opps, executed_count = self.scan_all_opportunities(
            limit=limit, auto_execute=auto_execute
        )
        
        if not arbitrage_opps and not trade_opps:
            print("\nNo opportunities found that meet the criteria.")
            if executed_count > 0:
                print(f"Executed {executed_count} trades automatically.")
            return
        
        # Display immediate trade opportunities first (they're instant)
        if trade_opps:
            print(f"\n{'='*70}")
            print(f"IMMEDIATE TRADE OPPORTUNITIES: Found {len(trade_opps)} opportunities!")
            print(f"{'='*70}\n")
            
            display_count = len(trade_opps) if display_all else min(10, len(trade_opps))
            for i, opp in enumerate(trade_opps[:display_count], 1):
                self.display_trade_opportunity(opp, index=i)
            
            if len(trade_opps) > display_count:
                print(f"\n... and {len(trade_opps) - display_count} more immediate trade opportunities.")
        
        # Display arbitrage opportunities
        if arbitrage_opps:
            print(f"\n{'='*70}")
            print(f"ARBITRAGE OPPORTUNITIES: Found {len(arbitrage_opps)} opportunities!")
            print(f"{'='*70}\n")
            
            display_count = len(arbitrage_opps) if display_all else min(10, len(arbitrage_opps))
            for i, opp in enumerate(arbitrage_opps[:display_count], 1):
                self.display_arbitrage_opportunity(opp, index=i)
            
            if len(arbitrage_opps) > display_count:
                print(f"\n... and {len(arbitrage_opps) - display_count} more arbitrage opportunities.")
        
        # Summary comparison
        if trade_opps and arbitrage_opps:
            print(f"\n{'='*70}")
            print("COMPARISON:")
            print(f"{'='*70}")
            best_trade = trade_opps[0]
            best_arb = arbitrage_opps[0]
            
            print(f"Immediate Trade: ${best_trade.net_profit:.2f} profit (instant)")
            print(f"Arbitrage: ${best_arb.profit_per_day:.2f}/day (over {best_arb.days_to_expiration:.1f} days)")
            
            if best_trade.net_profit > best_arb.profit_per_day * best_arb.days_to_expiration:
                print(f"\n→ RECOMMENDATION: Immediate trade is more profitable!")
            elif best_arb.profit_per_day > 0:
                print(f"\n→ RECOMMENDATION: Arbitrage opportunity may be better long-term!")
        
        if executed_count > 0:
            print(f"\n[AUTO-EXECUTE] Executed {executed_count} trades automatically.")
    
    def run_continuous(self, scan_interval: int = 300, limit: int = 100, 
                      auto_execute: bool = False, max_scans: int = None):
        """
        Run continuous scanning mode.
        
        Scans markets periodically and displays opportunities found.
        
        Args:
            scan_interval: Seconds between scans
            limit: Maximum number of markets to scan per iteration
            auto_execute: If True, automatically execute profitable trades
            max_scans: Maximum number of scans (None = infinite)
        """
        print(f"Starting continuous scanning (every {scan_interval} seconds)...")
        if auto_execute:
            print("⚠️  AUTO-EXECUTE ENABLED: Trades will be executed automatically!")
        if max_scans:
            print(f"Maximum scans: {max_scans}")
        print("Press Ctrl+C to stop.\n")
        
        scan_count = 0
        try:
            while True:
                scan_count += 1
                if max_scans and scan_count > max_scans:
                    print(f"\nReached maximum scan count ({max_scans}). Stopping.")
                    break
                
                arbitrage_opps, trade_opps, executed_count = self.scan_all_opportunities(
                    limit=limit, auto_execute=auto_execute
                )
                
                total_opps = len(arbitrage_opps) + len(trade_opps)
                
                if total_opps > 0:
                    print(f"\n✅ FOUND {total_opps} OPPORTUNITIES!")
                    print(f"  - {len(trade_opps)} immediate trades")
                    print(f"  - {len(arbitrage_opps)} arbitrage opportunities")
                else:
                    print(f"\nNo opportunities found (scan #{scan_count})")
                
                print(f"\nWaiting {scan_interval} seconds until next scan...\n")
                time.sleep(scan_interval)
        except KeyboardInterrupt:
            print("\n\nScanning stopped by user.")


def main():
    """Main entry point for the bot."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Kalshi Arbitrage Bot - Find trading opportunities in prediction markets"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous scanning mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Scan interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of markets to scan (default: 100)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Display all opportunities (not just top 10)"
    )
    parser.add_argument(
        "--trades-only",
        action="store_true",
        dest="trades_only",
        help="Scan ONLY for immediate trade opportunities"
    )
    parser.add_argument(
        "--arbitrage-only",
        action="store_true",
        dest="arbitrage_only",
        help="Scan ONLY for arbitrage opportunities"
    )
    parser.add_argument(
        "--auto-execute",
        action="store_true",
        dest="auto_execute",
        help="Automatically execute profitable trades (USE WITH CAUTION)"
    )
    parser.add_argument(
        "--min-liquidity",
        type=int,
        default=None,
        help="Minimum liquidity in cents (default: 10000 = $100)"
    )
    parser.add_argument(
        "--max-scans",
        type=int,
        default=None,
        help="Maximum number of scans in continuous mode (default: infinite)"
    )
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = KalshiArbitrageBot(auto_execute_trades=args.auto_execute)
    
    # Override min_liquidity if provided
    if args.min_liquidity is not None:
        bot.min_liquidity = args.min_liquidity
    
    # Run based on mode
    if args.continuous:
        bot.run_continuous(
            scan_interval=args.interval,
            limit=args.limit,
            auto_execute=args.auto_execute,
            max_scans=args.max_scans
        )
    elif args.trades_only:
        opportunities = bot.scan_immediate_trades(limit=args.limit, auto_execute=args.auto_execute)
        if opportunities:
            display_count = len(opportunities) if args.all else min(10, len(opportunities))
            for i, opp in enumerate(opportunities[:display_count], 1):
                bot.display_trade_opportunity(opp, index=i)
    elif args.arbitrage_only:
        opportunities = bot.scan_arbitrage_opportunities(limit=args.limit)
        if opportunities:
            display_count = len(opportunities) if args.all else min(10, len(opportunities))
            for i, opp in enumerate(opportunities[:display_count], 1):
                bot.display_arbitrage_opportunity(opp, index=i)
    else:
        # Default: scan both types
        bot.run_scan(limit=args.limit, display_all=args.all, auto_execute=args.auto_execute)


if __name__ == "__main__":
    main()
