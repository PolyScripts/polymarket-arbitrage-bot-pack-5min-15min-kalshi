"""
Immediate Trade Execution Module

Finds and executes immediate trade opportunities from orderbook spreads.

An immediate trade opportunity occurs when:
- Bid price > Ask price (can buy low, sell high instantly)
- Example: Buy YES at 42¢, sell YES at 43¢ = 1¢ profit per contract

The module:
- Scans orderbooks for profitable spreads
- Calculates net profit after fees
- Optionally executes trades automatically
- Tracks executed trades for monitoring
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from kalshi_client import KalshiClient
from fee_calculator import FeeCalculator


class TradeOpportunity:
    """Represents an immediate trade opportunity from orderbook spreads."""
    
    def __init__(self, market_ticker: str, market_title: str, side: str,
                 buy_price: int, sell_price: int, quantity: int,
                 gross_profit: float, net_profit: float):
        self.market_ticker = market_ticker
        self.market_title = market_title
        self.side = side  # 'yes' or 'no'
        self.buy_price = buy_price  # Price to buy at (cents)
        self.sell_price = sell_price  # Price to sell at (cents)
        self.quantity = quantity
        self.gross_profit = gross_profit
        self.net_profit = net_profit
        self.spread = sell_price - buy_price
    
    def __repr__(self):
        return (f"TradeOpportunity(ticker={self.market_ticker}, "
                f"side={self.side}, buy={self.buy_price}¢, "
                f"sell={self.sell_price}¢, qty={self.quantity}, "
                f"net_profit=${self.net_profit:.2f})")


class TradeExecutor:
    """Executes trades automatically when profitable opportunities are found."""
    
    def __init__(self, client: KalshiClient, min_profit_cents: int = 2, 
                 max_position_size: int = 1000, auto_execute: bool = False):
        """
        Initialize the trade executor.
        
        Args:
            client: KalshiClient instance for API calls
            min_profit_cents: Minimum profit in cents per contract to execute
            max_position_size: Maximum number of contracts per trade
            auto_execute: If True, automatically execute trades without confirmation
        """
        self.client = client
        self.min_profit_cents = min_profit_cents
        self.max_position_size = max_position_size
        self.auto_execute = auto_execute
        self.executed_trades = []
    
    def analyze_orderbook_spread(self, market_data: Dict, 
                                  orderbook: Optional[Dict] = None) -> List[TradeOpportunity]:
        """
        Analyze orderbook for immediate arbitrage opportunities.
        Finds cases where we can buy low and sell high instantly.
        
        Args:
            market_data: Market information dictionary
            orderbook: Optional orderbook data with bids and asks
        
        Returns:
            List of TradeOpportunity objects
        """
        opportunities = []
        market_ticker = market_data.get("ticker", "")
        market_title = market_data.get("title", "")
        
        # Get prices from market data
        yes_bid = market_data.get("yes_bid")  # Best price to sell YES
        yes_ask = market_data.get("yes_ask")  # Best price to buy YES
        no_bid = market_data.get("no_bid")    # Best price to sell NO
        no_ask = market_data.get("no_ask")    # Best price to buy NO
        
        # Check YES side: if ask < bid, we can buy at ask and sell at bid
        if yes_ask is not None and yes_bid is not None:
            spread = yes_bid - yes_ask
            if spread >= self.min_profit_cents:
                # Calculate maximum quantity we can trade
                # This would ideally come from orderbook depth, but we'll use a conservative estimate
                quantity = min(self.max_position_size, 100)  # Start conservative
                
                # Calculate profit
                gross_profit_per_contract = spread / 100.0  # Convert cents to dollars
                gross_profit = gross_profit_per_contract * quantity
                
                # Calculate fees (we pay fees on both buy and sell)
                buy_fee = FeeCalculator.calculate_fee(yes_ask, quantity, is_maker=False)
                sell_fee = FeeCalculator.calculate_fee(yes_bid, quantity, is_maker=False)
                total_fees = buy_fee + sell_fee
                
                net_profit = gross_profit - total_fees
                
                if net_profit > 0:
                    opportunities.append(TradeOpportunity(
                        market_ticker=market_ticker,
                        market_title=market_title,
                        side='yes',
                        buy_price=yes_ask,
                        sell_price=yes_bid,
                        quantity=quantity,
                        gross_profit=gross_profit,
                        net_profit=net_profit
                    ))
        
        # Check NO side: if ask < bid, we can buy at ask and sell at bid
        if no_ask is not None and no_bid is not None:
            spread = no_bid - no_ask
            if spread >= self.min_profit_cents:
                quantity = min(self.max_position_size, 100)  # Start conservative
                
                gross_profit_per_contract = spread / 100.0
                gross_profit = gross_profit_per_contract * quantity
                
                buy_fee = FeeCalculator.calculate_fee(no_ask, quantity, is_maker=False)
                sell_fee = FeeCalculator.calculate_fee(no_bid, quantity, is_maker=False)
                total_fees = buy_fee + sell_fee
                
                net_profit = gross_profit - total_fees
                
                if net_profit > 0:
                    opportunities.append(TradeOpportunity(
                        market_ticker=market_ticker,
                        market_title=market_title,
                        side='no',
                        buy_price=no_ask,
                        sell_price=no_bid,
                        quantity=quantity,
                        gross_profit=gross_profit,
                        net_profit=net_profit
                    ))
        
        # If we have orderbook data, use it for more accurate quantity calculation
        if orderbook:
            opportunities = self._refine_with_orderbook(opportunities, orderbook)
        
        return opportunities
    
    def _refine_with_orderbook(self, opportunities: List[TradeOpportunity], 
                               orderbook: Dict) -> List[TradeOpportunity]:
        """
        Refine opportunities using detailed orderbook data.
        
        Args:
            opportunities: List of trade opportunities
            orderbook: Detailed orderbook data
        
        Returns:
            Refined list of opportunities with accurate quantities
        """
        refined = []
        
        for opp in opportunities:
            # Try to get orderbook depth for this side
            # Orderbook structure may vary, so we'll try common formats
            yes_data = orderbook.get("yes", {})
            no_data = orderbook.get("no", {})
            
            if opp.side == 'yes' and yes_data:
                bids = yes_data.get("bids", [])
                asks = yes_data.get("asks", [])
                
                if asks and bids:
                    # Find best ask (lowest price) and best bid (highest price)
                    best_ask = asks[0] if isinstance(asks[0], dict) else {'price': opp.buy_price, 'count': 100}
                    best_bid = bids[0] if isinstance(bids[0], dict) else {'price': opp.sell_price, 'count': 100}
                    
                    # Quantity is limited by available liquidity
                    ask_qty = best_ask.get('count', 100) if isinstance(best_ask, dict) else 100
                    bid_qty = best_bid.get('count', 100) if isinstance(best_bid, dict) else 100
                    max_qty = min(ask_qty, bid_qty, self.max_position_size)
                    
                    if max_qty > 0:
                        opp.quantity = max_qty
                        # Recalculate profit with new quantity
                        gross_profit_per_contract = opp.spread / 100.0
                        opp.gross_profit = gross_profit_per_contract * max_qty
                        buy_fee = FeeCalculator.calculate_fee(opp.buy_price, max_qty, is_maker=False)
                        sell_fee = FeeCalculator.calculate_fee(opp.sell_price, max_qty, is_maker=False)
                        opp.net_profit = opp.gross_profit - buy_fee - sell_fee
                        
                        if opp.net_profit > 0:
                            refined.append(opp)
            
            elif opp.side == 'no' and no_data:
                bids = no_data.get("bids", [])
                asks = no_data.get("asks", [])
                
                if asks and bids:
                    best_ask = asks[0] if isinstance(asks[0], dict) else {'price': opp.buy_price, 'count': 100}
                    best_bid = bids[0] if isinstance(bids[0], dict) else {'price': opp.sell_price, 'count': 100}
                    
                    ask_qty = best_ask.get('count', 100) if isinstance(best_ask, dict) else 100
                    bid_qty = best_bid.get('count', 100) if isinstance(best_bid, dict) else 100
                    max_qty = min(ask_qty, bid_qty, self.max_position_size)
                    
                    if max_qty > 0:
                        opp.quantity = max_qty
                        gross_profit_per_contract = opp.spread / 100.0
                        opp.gross_profit = gross_profit_per_contract * max_qty
                        buy_fee = FeeCalculator.calculate_fee(opp.buy_price, max_qty, is_maker=False)
                        sell_fee = FeeCalculator.calculate_fee(opp.sell_price, max_qty, is_maker=False)
                        opp.net_profit = opp.gross_profit - buy_fee - sell_fee
                        
                        if opp.net_profit > 0:
                            refined.append(opp)
            else:
                # Keep original opportunity if we can't refine it
                refined.append(opp)
        
        return refined
    
    def execute_trade(self, opportunity: TradeOpportunity, use_market_orders: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Execute a trade opportunity.
        
        Args:
            opportunity: TradeOpportunity to execute
            use_market_orders: If True, use market orders for instant execution.
                             If False, use limit orders at exact prices (safer but may not execute immediately)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import time
            
            # Execute buy order first
            # For market orders, we still specify price as a limit to avoid slippage
            buy_result = self.client.place_order(
                market_ticker=opportunity.market_ticker,
                side=opportunity.side,
                action='buy',
                count=opportunity.quantity,
                price=opportunity.buy_price,
                order_type='market' if use_market_orders else 'limit'
            )
            
            if not buy_result:
                return False, f"Failed to execute buy order for {opportunity.market_ticker}"
            
            # Small delay to ensure order is processed
            time.sleep(0.5)
            
            # Execute sell order
            sell_result = self.client.place_order(
                market_ticker=opportunity.market_ticker,
                side=opportunity.side,
                action='sell',
                count=opportunity.quantity,
                price=opportunity.sell_price,
                order_type='market' if use_market_orders else 'limit'
            )
            
            if not sell_result:
                return False, f"Failed to execute sell order for {opportunity.market_ticker}"
            
            # Record the trade
            trade_record = {
                'timestamp': datetime.now(),
                'market_ticker': opportunity.market_ticker,
                'side': opportunity.side,
                'buy_price': opportunity.buy_price,
                'sell_price': opportunity.sell_price,
                'quantity': opportunity.quantity,
                'net_profit': opportunity.net_profit,
                'buy_order': buy_result,
                'sell_order': sell_result
            }
            self.executed_trades.append(trade_record)
            
            return True, (f"Successfully executed trade: {opportunity.quantity} contracts, "
                          f"profit: ${opportunity.net_profit:.2f}")
        
        except Exception as e:
            return False, f"Error executing trade: {str(e)}"
    
    def scan_and_execute(self, markets: List[Dict], limit: int = 50) -> List[TradeOpportunity]:
        """
        Scan markets for immediate trade opportunities and optionally execute them.
        
        Args:
            markets: List of market dictionaries to scan
            limit: Maximum number of markets to scan
        
        Returns:
            List of TradeOpportunity objects found
        """
        all_opportunities = []
        
        for market in markets[:limit]:
            market_ticker = market.get("ticker", "")
            if not market_ticker:
                continue
            
            # Get orderbook for more accurate analysis (with rate limiting)
            orderbook = None
            try:
                import time
                time.sleep(0.2)  # 200ms delay between orderbook requests
                orderbook = self.client.get_market_orderbook(market_ticker)
            except:
                pass
            
            opportunities = self.analyze_orderbook_spread(market, orderbook)
            
            for opp in opportunities:
                if self.auto_execute:
                    success, message = self.execute_trade(opp)
                    if success:
                        print(f"[AUTO-EXECUTE] {message}")
                        all_opportunities.append(opp)
                    else:
                        print(f"[AUTO-EXECUTE FAILED] {message}")
                else:
                    all_opportunities.append(opp)
        
        return all_opportunities
    
    def display_opportunity(self, opp: TradeOpportunity, index: int = None):
        """Display details of a trade opportunity."""
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

