"""
Arbitrage Detection Module

Identifies arbitrage opportunities in Kalshi prediction markets.

Arbitrage occurs when the sum of YES and NO contract probabilities doesn't equal 100%.
For example:
- YES at 52¢ + NO at 50¢ = 102% total (2% arbitrage opportunity)
- YES at 48¢ + NO at 50¢ = 98% total (2% arbitrage opportunity)

The module calculates:
- Gross profit from the arbitrage
- Net profit after trading fees
- Profit per day based on expiration date
- Recommended trades to execute
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dateutil import parser as date_parser
from fee_calculator import FeeCalculator


class ArbitrageOpportunity:
    """Represents an arbitrage opportunity."""
    
    def __init__(self, market_ticker: str, market_title: str, 
                 total_probability: float, deviation: float,
                 expiration_date: datetime, trades: List[Dict],
                 gross_profit: float, net_profit: float,
                 days_to_expiration: float):
        self.market_ticker = market_ticker
        self.market_title = market_title
        self.total_probability = total_probability
        self.deviation = deviation
        self.expiration_date = expiration_date
        self.trades = trades
        self.gross_profit = gross_profit
        self.net_profit = net_profit
        self.days_to_expiration = days_to_expiration
        self.profit_per_day = net_profit / max(days_to_expiration, 0.01)
    
    def __repr__(self):
        return (f"ArbitrageOpportunity(ticker={self.market_ticker}, "
                f"deviation={self.deviation:.2f}%, "
                f"profit_per_day=${self.profit_per_day:.2f})")


class ArbitrageAnalyzer:
    """Analyzes markets for arbitrage opportunities."""
    
    def __init__(self, min_deviation: float = None):
        """
        Initialize the analyzer.
        
        Args:
            min_deviation: DEPRECATED - No longer used. Filtering is now based on net profit > 0.
                          Kept for backwards compatibility but ignored.
        """
        # min_deviation is deprecated - we now filter by net_profit > 0 instead
        pass
    
    def analyze_market(self, market_data: Dict, orderbook: Optional[Dict] = None) -> Optional[ArbitrageOpportunity]:
        """
        Analyze a single market for arbitrage opportunities.
        
        Args:
            market_data: Market information dictionary
            orderbook: Optional orderbook data for more accurate pricing
        
        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        try:
            market_ticker = market_data.get("ticker", "")
            market_title = market_data.get("title", "")
            
            # Get expiration date
            expiration_str = market_data.get("expiration_time") or market_data.get("expiration_date")
            if not expiration_str:
                return None
            
            expiration_date = date_parser.parse(expiration_str)
            days_to_expiration = (expiration_date - datetime.now(expiration_date.tzinfo)).total_seconds() / 86400
            
            # Skip markets that have already expired
            if days_to_expiration <= 0:
                return None
            
            # Handle binary markets (yes/no) - most common on Kalshi
            market_type = market_data.get("market_type", "")
            
            # Get prices for binary markets
            yes_bid = market_data.get("yes_bid")
            yes_ask = market_data.get("yes_ask")
            no_bid = market_data.get("no_bid")
            no_ask = market_data.get("no_ask")
            
            total_prob = 0.0
            contract_prices = []
            
            # For binary markets, check if yes + no prices sum to 100
            if market_type == "binary" and (yes_bid is not None or yes_ask is not None):
                # Use bid prices for selling arbitrage (yes_bid + no_bid > 100)
                # Use ask prices for buying arbitrage (yes_ask + no_ask < 100)
                
                # Check selling arbitrage first (more common - we can sell both sides at bid prices)
                if yes_bid is not None and no_bid is not None:
                    total_prob_bid = (yes_bid + no_bid) / 100.0
                    if total_prob_bid > 1.0:
                        # Selling arbitrage opportunity
                        contract_prices = [
                            {
                                'ticker': market_ticker,
                                'side': 'yes',
                                'price': yes_bid,
                                'probability': yes_bid / 100.0
                            },
                            {
                                'ticker': market_ticker,
                                'side': 'no',
                                'price': no_bid,
                                'probability': no_bid / 100.0
                            }
                        ]
                        total_prob = total_prob_bid
                
                # Check buying arbitrage (yes_ask + no_ask < 100)
                if not contract_prices and yes_ask is not None and no_ask is not None:
                    total_prob_ask = (yes_ask + no_ask) / 100.0
                    if total_prob_ask < 1.0:
                        # Buying arbitrage opportunity
                        contract_prices = [
                            {
                                'ticker': market_ticker,
                                'side': 'yes',
                                'price': yes_ask,
                                'probability': yes_ask / 100.0
                            },
                            {
                                'ticker': market_ticker,
                                'side': 'no',
                                'price': no_ask,
                                'probability': no_ask / 100.0
                            }
                        ]
                        total_prob = total_prob_ask
                
                # Fallback: use average of bid/ask if available (for analysis, not arbitrage)
                if not contract_prices:
                    yes_price = None
                    no_price = None
                    
                    if yes_bid is not None and yes_ask is not None:
                        yes_price = (yes_bid + yes_ask) / 2
                    elif yes_bid is not None:
                        yes_price = yes_bid
                    elif yes_ask is not None:
                        yes_price = yes_ask
                    
                    if no_bid is not None and no_ask is not None:
                        no_price = (no_bid + no_ask) / 2
                    elif no_bid is not None:
                        no_price = no_bid
                    elif no_ask is not None:
                        no_price = no_ask
                    
                    if yes_price is not None and no_price is not None:
                        total_prob = (yes_price + no_price) / 100.0
                        contract_prices = [
                            {
                                'ticker': market_ticker,
                                'side': 'yes',
                                'price': int(yes_price),
                                'probability': yes_price / 100.0
                            },
                            {
                                'ticker': market_ticker,
                                'side': 'no',
                                'price': int(no_price),
                                'probability': no_price / 100.0
                            }
                        ]
            
            # Fallback: Try to find contracts/outcomes array (for non-binary markets)
            if not contract_prices:
                contracts = market_data.get("contracts", [])
                if not contracts:
                    outcomes = market_data.get("outcomes", [])
                    if outcomes:
                        contracts = outcomes
                
                if contracts:
                    for contract in contracts:
                        price_cents = contract.get("last_price")
                        if price_cents is None:
                            yes_bid_c = contract.get("yes_bid")
                            yes_ask_c = contract.get("yes_ask")
                            if yes_bid_c is not None and yes_ask_c is not None:
                                price_cents = (yes_bid_c + yes_ask_c) / 2
                            elif yes_bid_c is not None:
                                price_cents = yes_bid_c
                            elif yes_ask_c is not None:
                                price_cents = yes_ask_c
                        
                        if price_cents is not None:
                            prob = price_cents / 100.0
                            total_prob += prob
                            contract_prices.append({
                                'ticker': contract.get("ticker", market_ticker),
                                'side': 'yes',
                                'price': int(price_cents),
                                'probability': prob
                            })
            
            if not contract_prices:
                return None
            
            # Check for arbitrage opportunity
            deviation = abs(total_prob - 1.0) * 100  # Convert to percentage
            
            # No longer filter by deviation - we'll filter by net profit instead
            # This ensures we catch any profitable opportunity, even if tiny
            
            # Calculate arbitrage trades
            # If total_prob > 1.0, contracts are overpriced - we can sell them
            # If total_prob < 1.0, contracts are underpriced - we can buy them
            
            trades = []
            gross_profit = 0.0
            base_quantity = 100  # Base quantity per contract - could be optimized
            
            if total_prob > 1.0:
                # Contracts are overpriced - sell them
                # Strategy: Sell contracts at current prices, profit from the overpricing
                # When they expire, we pay out $1 per contract, but we received more than $1 total
                overpricing = total_prob - 1.0
                
                # Calculate how many contracts to sell for each outcome
                # We want to sell enough so that total received > $1 per set
                for contract in contract_prices:
                    # Normalize the probability to see how much we should sell
                    normalized_prob = contract['probability'] / total_prob
                    # Sell proportionally to create a balanced position
                    quantity = int(base_quantity * normalized_prob)
                    
                    if quantity > 0:
                        trades.append({
                            'ticker': contract['ticker'],
                            'side': contract.get('side', 'yes'),
                            'action': 'sell',
                            'price': contract['price'],
                            'quantity': quantity
                        })
                
                # Gross profit: We receive (total_prob * base_quantity) but only pay out (1.0 * base_quantity)
                # Profit per set = (total_prob - 1.0) * price_per_contract
                gross_profit = overpricing * base_quantity  # In contract units, convert to dollars
            
            else:  # total_prob < 1.0
                # Contracts are underpriced - buy them
                # Strategy: Buy contracts at current prices, profit from the underpricing
                # When they expire, we receive $1 per contract, but we paid less than $1 total
                underpricing = 1.0 - total_prob
                
                # Calculate how many contracts to buy for each outcome
                for contract in contract_prices:
                    # Normalize the probability to see how much we should buy
                    normalized_prob = contract['probability'] / total_prob
                    # Buy proportionally to create a balanced position
                    quantity = int(base_quantity * normalized_prob)
                    
                    if quantity > 0:
                        trades.append({
                            'ticker': contract['ticker'],
                            'side': contract.get('side', 'yes'),
                            'action': 'buy',
                            'price': contract['price'],
                            'quantity': quantity
                        })
                
                # Gross profit: We pay (total_prob * base_quantity) but receive (1.0 * base_quantity)
                # Profit per set = (1.0 - total_prob) * price_per_contract
                gross_profit = underpricing * base_quantity  # In contract units, convert to dollars
            
            if not trades:
                return None
            
            # Calculate net profit after fees
            # Assume we're using limit orders (maker orders) to reduce fees
            net_profit = FeeCalculator.calculate_net_profit(
                gross_profit,
                [{'price': t['price'], 'quantity': t['quantity']} for t in trades],
                all_maker=True
            )
            
            # Only return opportunities with positive net profit (after fees)
            # This dynamically calculates the minimum based on actual fees
            if net_profit <= 0:
                return None
            
            return ArbitrageOpportunity(
                market_ticker=market_ticker,
                market_title=market_title,
                total_probability=total_prob * 100,
                deviation=deviation,
                expiration_date=expiration_date,
                trades=trades,
                gross_profit=gross_profit,
                net_profit=net_profit,
                days_to_expiration=days_to_expiration
            )
        
        except Exception as e:
            print(f"Error analyzing market {market_data.get('ticker', 'unknown')}: {e}")
            return None
    
    def find_opportunities(self, markets: List[Dict], 
                          client=None) -> List[ArbitrageOpportunity]:
        """
        Find arbitrage opportunities across multiple markets.
        
        Args:
            markets: List of market dictionaries
            client: Optional KalshiClient to fetch orderbooks
        
        Returns:
            List of ArbitrageOpportunity objects
        """
        opportunities = []
        
        for market in markets:
            orderbook = None
            if client:
                try:
                    import time
                    time.sleep(0.2)  # 200ms delay between orderbook requests
                    orderbook = client.get_market_orderbook(market.get("ticker", ""))
                except:
                    pass
            
            opportunity = self.analyze_market(market, orderbook)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by profit per day (descending)
        opportunities.sort(key=lambda x: x.profit_per_day, reverse=True)
        
        return opportunities

